"""Bounded subprocess capture shared by compilation and panel execution."""
from dataclasses import dataclass
import codecs
import os
import queue
import signal
import subprocess
import threading
import time


@dataclass
class ProcessResult:
    returncode: int
    stdout: str
    stderr: str
    reason: str = ""


def stop_process(process):
    """Stop this job and its children (gcc itself launches compiler/linker tools)."""
    if process.poll() is not None:
        return
    if os.name == "nt":
        try:
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           creationflags=subprocess.CREATE_NO_WINDOW, timeout=5)
        except (OSError, subprocess.TimeoutExpired):
            pass  # Still terminate the direct process if taskkill is unavailable.
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    if process.poll() is None:
        process.kill()


def run_process(command, *, input_text="", cwd=None, env=None, timeout=10,
                cancel=None, output_limit=200_000):
    """Capture at most output_limit bytes per stream; terminate noisy/hung jobs.

    Readers drain both pipes concurrently, so stderr cannot deadlock stdout.
    Input has its own writer because a program may never read its stdin.
    No worker accesses Tk widgets.
    """
    cancel = cancel or threading.Event()
    if cancel.is_set():
        return ProcessResult(-1, "", "", "cancelled")
    buffers = [bytearray(), bytearray()]
    overflow = threading.Event()
    process = subprocess.Popen(
        command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        cwd=cwd, env=env, creationflags=0x08000000 if os.name == "nt" else 0,
        start_new_session=os.name != "nt")

    def read(pipe, buffer):
        try:
            while True:
                chunk = pipe.read1(8192)
                if not chunk:
                    break
                remaining = max(0, output_limit - len(buffer))
                buffer.extend(chunk[:remaining])
                if len(chunk) > remaining:
                    overflow.set()
        finally:
            pipe.close()

    def write():
        try:
            process.stdin.write(input_text.encode("utf-8"))
            process.stdin.flush()
        except (BrokenPipeError, OSError):
            pass
        finally:
            try:
                process.stdin.close()
            except OSError:
                pass

    readers = [threading.Thread(target=read, args=(pipe, buf), daemon=True)
               for pipe, buf in zip((process.stdout, process.stderr), buffers)]
    writer = threading.Thread(target=write, daemon=True)
    for thread in readers + [writer]:
        thread.start()
    deadline = time.monotonic() + timeout
    reason = ""
    try:
        while process.poll() is None:
            if cancel.is_set():
                reason = "cancelled"
            elif overflow.is_set():
                reason = "output_limit"
            elif time.monotonic() >= deadline:
                reason = "timeout"
            if reason:
                stop_process(process)
                break
            cancel.wait(.02)
        process.wait(timeout=5)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        for thread in readers + [writer]:
            thread.join(timeout=1)
    if not reason and overflow.is_set():
        reason = "output_limit"
    return ProcessResult(process.returncode, *(bytes(b).decode("utf-8", "replace") for b in buffers), reason)


class _WindowsProcessTree:
    """Keep descendants addressable even after the original process exits."""

    def __init__(self, process):
        import ctypes
        from ctypes import wintypes

        self._api = ctypes.WinDLL("kernel32", use_last_error=True)
        signatures = {
            "CreateJobObjectW": ([ctypes.c_void_p, wintypes.LPCWSTR], wintypes.HANDLE),
            "OpenProcess": ([wintypes.DWORD, wintypes.BOOL, wintypes.DWORD], wintypes.HANDLE),
            "AssignProcessToJobObject": ([wintypes.HANDLE, wintypes.HANDLE], wintypes.BOOL),
            "TerminateJobObject": ([wintypes.HANDLE, wintypes.UINT], wintypes.BOOL),
            "CloseHandle": ([wintypes.HANDLE], wintypes.BOOL),
        }
        for name, (args, result) in signatures.items():
            function = getattr(self._api, name)
            function.argtypes, function.restype = args, result
        self._handle = self._api.CreateJobObjectW(None, None)
        if not self._handle:
            raise ctypes.WinError(ctypes.get_last_error())
        child = self._api.OpenProcess(0x0100 | 0x0001, False, process.pid)
        try:
            if not child or not self._api.AssignProcessToJobObject(self._handle, child):
                error = ctypes.get_last_error()
                # A program may legitimately finish before job assignment.
                if process.poll() is None:
                    raise ctypes.WinError(error)
        except OSError:
            self.close()
            raise
        finally:
            if child:
                self._api.CloseHandle(child)

    def terminate(self):
        if self._handle:
            self._api.TerminateJobObject(self._handle, 1)

    def close(self):
        if self._handle:
            self.terminate()
            self._api.CloseHandle(self._handle)
            self._handle = None


class InteractiveProcess:
    """Live, bounded UTF-8 transport; consumers poll ``events`` on their UI thread.

    ``send`` accepts exact text (including any desired newline) without waiting
    for the child to read it. It returns False after EOF/completion or when the
    pending input exceeds 200 KB. ``close_input`` sends EOF after queued input.
    ``stop`` requests asynchronous cancellation. A final ("done", ProcessResult)
    event follows every output event, so the consumer can safely finish there.
    Output is capped at output_limit bytes per stream, including queued events.
    """

    def __init__(self, command, cwd=None, env=None, timeout=120,
                 output_limit=200_000):
        if timeout <= 0 or output_limit < 0:
            raise ValueError("timeout must be positive and output_limit nonnegative")
        self.command, self.cwd, self.env = command, cwd, env
        self.timeout, self.output_limit = timeout, output_limit
        self.events = queue.Queue()
        self._input = queue.Queue()
        self._lock = threading.Lock()
        self._cancel = threading.Event()
        self._overflow = threading.Event()
        self._process = None
        self._tree = None
        self._started = False
        self._input_closed = False
        self._pending_input = 0
        self._buffers = [bytearray(), bytearray()]

    def start(self):
        """Launch once; launch errors propagate to the caller."""
        with self._lock:
            if self._started:
                raise RuntimeError("This process has already been started")
            self._started = True
            if self._cancel.is_set():
                self._input_closed = True
                self.events.put(("done", ProcessResult(-1, "", "", "cancelled")))
                return
            self._process = subprocess.Popen(
                self.command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, cwd=self.cwd, env=self.env, bufsize=0,
                creationflags=0x08000000 if os.name == "nt" else 0,
                start_new_session=os.name != "nt")
            if os.name == "nt":
                try:
                    self._tree = _WindowsProcessTree(self._process)
                except OSError:
                    # Job objects nest, but an outer job (an MSIX package runs
                    # inside one) can refuse the assignment.  Running without a
                    # job is a degradation, not a failure: _run already falls
                    # back to stop_process, which kills the tree with taskkill.
                    self._tree = None
        threading.Thread(target=self._run, daemon=True).start()

    def send(self, text):
        # Check character count before encoding to avoid allocating huge pastes.
        if len(text) > 200_000:
            return False
        data = text.encode("utf-8")
        with self._lock:
            if (self._process is None or self._input_closed or self._cancel.is_set()
                    or self._process.poll() is not None
                    or self._pending_input + len(data) > 200_000):
                return False
            if data:
                self._pending_input += len(data)
                self._input.put(data)
            return True

    def close_input(self):
        with self._lock:
            if not self._input_closed:
                self._input_closed = True
                self._input.put(None)

    def stop(self):
        self._cancel.set()

    def _read(self, pipe, index, kind):
        decoder = codecs.getincrementaldecoder("utf-8")("replace")
        buffer = self._buffers[index]
        try:
            while True:
                chunk = pipe.read(8192)
                if not chunk:
                    break
                remaining = max(0, self.output_limit - len(buffer))
                accepted = chunk[:remaining]
                buffer.extend(accepted)
                text = decoder.decode(accepted)
                if text:
                    self.events.put((kind, text))
                if len(chunk) > remaining:
                    self._overflow.set()
        finally:
            tail = decoder.decode(b"", final=True)
            if tail:
                self.events.put((kind, tail))
            pipe.close()

    def _write(self):
        pipe = self._process.stdin
        try:
            while True:
                data = self._input.get()
                if data is None or self._cancel.is_set():
                    break
                try:
                    pending = memoryview(data)
                    while pending:
                        pending = pending[pipe.write(pending):]
                finally:
                    with self._lock:
                        self._pending_input -= len(data)
        except (BrokenPipeError, OSError):
            pass
        finally:
            pipe.close()

    def _run(self):
        process = self._process
        readers = [threading.Thread(target=self._read,
                                    args=(pipe, index, kind), daemon=True)
                   for index, (pipe, kind) in enumerate(
                       ((process.stdout, "stdout"), (process.stderr, "stderr")))]
        writer = threading.Thread(target=self._write, daemon=True)
        for thread in readers + [writer]:
            thread.start()
        deadline = time.monotonic() + self.timeout
        reason = ""
        while process.poll() is None:
            if self._cancel.is_set():
                reason = "cancelled"
            elif self._overflow.is_set():
                reason = "output_limit"
            elif time.monotonic() >= deadline:
                reason = "timeout"
            if reason:
                if self._tree:
                    self._tree.terminate()
                else:
                    stop_process(process)
                break
            self._cancel.wait(.02)
        process.wait()
        if self._tree:
            self._tree.close()
        elif os.name != "nt":
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        self.close_input()
        for thread in readers + [writer]:
            thread.join()
        if not reason and self._overflow.is_set():
            reason = "output_limit"
        self.events.put(("done", ProcessResult(
            process.returncode,
            *(bytes(buffer).decode("utf-8", "replace") for buffer in self._buffers),
            reason)))
