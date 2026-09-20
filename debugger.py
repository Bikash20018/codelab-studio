"""Asynchronous GDB/MI debugger; the UI consumes ``events`` without touching GDB.

Compile with -g -O0. Supply all program input to start(); live stdin is deliberately
separate from the MI command pipe. Each instance owns one debugging session.
"""
from collections import deque
import codecs
import json
import os
from pathlib import Path
import queue
import re
import shlex
import subprocess
import tempfile
import threading
import time

from execution import stop_process


class _MIValues:
    """Read MI tuples/lists and C strings (MI strings are not quite JSON)."""
    def __init__(self, text):
        self.text, self.pos = text, 0

    def string(self):
        self.pos += 1
        result = bytearray()
        escapes = {'n': 10, 'r': 13, 't': 9, 'b': 8, 'f': 12, 'v': 11, 'a': 7}
        while self.pos < len(self.text):
            char = self.text[self.pos]
            self.pos += 1
            if char == '"':
                return result.decode('utf-8', 'replace')
            if char == '\\':
                char = self.text[self.pos]
                self.pos += 1
                if char in '01234567':
                    digits = char
                    while len(digits) < 3 and self.pos < len(self.text) and self.text[self.pos] in '01234567':
                        digits += self.text[self.pos]
                        self.pos += 1
                    result.append(int(digits, 8) & 255)
                    continue
                if char in escapes:
                    result.append(escapes[char])
                    continue
            result.extend(char.encode('utf-8'))
        raise ValueError('Unterminated MI string')

    def result(self):
        end = self.text.index('=', self.pos)
        name = self.text[self.pos:end]
        self.pos = end + 1
        return name, self.value()

    def values(self, end=''):
        result = {}
        while self.pos < len(self.text) and self.text[self.pos] != end:
            name, value = self.result()
            result[name] = value
            if self.pos >= len(self.text) or self.text[self.pos] != ',':
                break
            self.pos += 1
        return result

    def value(self):
        char = self.text[self.pos]
        if char == '"':
            return self.string()
        if char == '{':
            self.pos += 1
            result = self.values('}')
            if self.text[self.pos] != '}':
                raise ValueError('Invalid MI tuple')
            self.pos += 1
            return result
        if char == '[':
            self.pos += 1
            result = []
            while self.text[self.pos] != ']':
                if self.text[self.pos] in '"{[':
                    result.append(self.value())
                else:
                    name, value = self.result()
                    result.append({name: value})
                if self.text[self.pos] != ',':
                    break
                self.pos += 1
            if self.text[self.pos] != ']':
                raise ValueError('Invalid MI list')
            self.pos += 1
            return result
        raise ValueError('Invalid MI value')


def parse_mi(line):
    """Return (token, record prefix, class, payload), or None for a prompt."""
    match = re.match(r'^(\d*)([\^*+=~@&])(.*)$', line.rstrip('\r\n'))
    if not match:
        return None
    token, prefix, body = match.groups()
    token = int(token) if token else None
    try:
        if prefix in '~@&':
            return token, prefix, '', _MIValues(body).string()
        kind, _, data = body.partition(',')
        return token, prefix, kind, _MIValues(data).values()
    except (ValueError, IndexError) as exc:
        raise ValueError('Malformed GDB/MI record') from exc


class _Finished(Exception):
    pass


class Debugger:
    """One worker serializes commands; one reader drains GDB's bounded MI pipe.

    events: ('running', None), ('stopped', {file, line, reason, locals}),
    ('output', text), ('error', text), and exactly one final ('done', reason).
    next/step/continue_ only act while stopped. stop is nonblocking; join is
    available for shutdown/tests and must not be called from Tk's event loop.
    """
    def __init__(self, gdb, executable, cwd=None, env=None, *, output_limit=200_000):
        self.gdb = os.fspath(gdb)
        self.executable = os.path.abspath(executable)
        self.cwd = os.path.abspath(cwd or os.path.dirname(self.executable))
        self.env = env
        self.output_limit = max(1, int(output_limit))
        self.events = queue.Queue()
        self._records = queue.Queue(maxsize=256)
        self._commands = queue.Queue()
        self._cancel = threading.Event()
        self._lock = threading.Lock()
        self._state = 'new'
        self._thread = None
        self._process = None
        self._pending_stops = deque()
        self._token = 0
        self._output = None
        self._output_bytes = 0
        self._decoder = codecs.getincrementaldecoder('utf-8')('replace')
        self._end_reason = ''

    def start(self, breakpoints=(), input_text=''):
        with self._lock:
            if self._state != 'new':
                raise RuntimeError('Create a new Debugger for each session')
            self._state = 'starting'
        self._thread = threading.Thread(target=self._run,
                                        args=(list(breakpoints), input_text), daemon=True)
        self._thread.start()

    def _resume(self, command):
        with self._lock:
            if self._state != 'stopped':
                return
            self._state = 'resuming'
        self._commands.put(command)

    def next(self):
        self._resume('-exec-next')

    def step(self):
        self._resume('-exec-step')

    def continue_(self):
        self._resume('-exec-continue')

    def stop(self):
        self._cancel.set()

    def join(self, timeout=None):
        if self._thread:
            self._thread.join(timeout)

    def is_alive(self):
        return bool(self._thread and self._thread.is_alive())

    def _read_mi(self):
        try:
            while not self._cancel.is_set():
                raw = self._process.stdout.readline(262_145)
                if not raw:
                    break
                if len(raw) > 262_144:
                    raise ValueError('GDB response exceeded the size limit')
                record = parse_mi(raw.decode('utf-8', 'replace'))
                if record:
                    self._queue_record(record)
        except (OSError, ValueError) as exc:
            self._queue_record((None, '!', 'error', str(exc)))
        finally:
            self._queue_record((None, '!', 'eof', None))

    def _queue_record(self, record):
        while not self._cancel.is_set():
            try:
                self._records.put(record, timeout=.1)
                return
            except queue.Full:
                pass

    def _drain_output(self):
        if self._output is None:
            return
        # A separate file prevents inferior output being mistaken for MI records.
        while True:
            raw = self._output.read(min(8192, self.output_limit - self._output_bytes + 1))
            if not raw:
                return
            remaining = self.output_limit - self._output_bytes
            self._output_bytes += min(len(raw), remaining)
            text = self._decoder.decode(raw[:remaining])
            if text:
                self.events.put(('output', text))
            if len(raw) > remaining:
                raise _Finished('Program output limit reached')

    def _receive(self, timeout=.03):
        if self._cancel.is_set():
            raise _Finished('Debugging stopped')
        self._drain_output()
        try:
            return self._records.get(timeout=timeout)
        except queue.Empty:
            return None

    def _handle(self, record):
        _, prefix, kind, payload = record
        if prefix == '!':
            if kind == 'error':
                raise RuntimeError(payload)
            raise RuntimeError('GDB closed unexpectedly')
        if prefix == '*' and kind == 'running':
            with self._lock:
                self._state = 'running'
            self.events.put(('running', None))
        elif prefix == '*' and kind == 'stopped':
            reason = payload.get('reason', 'stopped')
            if reason.startswith('exited'):
                code = payload.get('exit-code')
                self._end_reason = reason + (f' (code {code})' if code else '')
            else:
                self._pending_stops.append(payload)

    def _command(self, command, timeout=15):
        self._token += 1
        token = self._token
        self._process.stdin.write(f'{token}{command}\n'.encode('utf-8'))
        self._process.stdin.flush()
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            record = self._receive()
            if not record:
                continue
            if record[0] == token and record[1] == '^':
                if record[2] == 'error':
                    raise RuntimeError(record[3].get('msg', 'GDB command failed'))
                return record[3]
            self._handle(record)
        raise RuntimeError('GDB did not respond within 15 seconds')

    def _report_stop(self, payload):
        frame = payload.get('frame', {})
        filename = frame.get('fullname') or frame.get('file', '')
        if filename and not os.path.isabs(filename):
            filename = os.path.join(self.cwd, filename)
        variables = self._command('-stack-list-variables --all-values').get('variables', [])
        locals_ = [{'name': value.get('name', ''), 'value': value.get('value', '<unavailable>')}
                   for value in variables]
        with self._lock:
            self._state = 'stopped'
        self.events.put(('stopped', {
            'file': os.path.abspath(filename) if filename else '',
            'line': int(frame.get('line', '0')),
            'reason': payload.get('reason', 'stopped'), 'locals': locals_}))

    def _run(self, breakpoints, input_text):
        reason = 'Debugging stopped'
        reader = None
        temp = None
        try:
            temp = tempfile.TemporaryDirectory(prefix='CodeLab debug ')
            input_path = Path(temp.name) / 'program input.txt'
            output_path = Path(temp.name) / 'program output.txt'
            input_path.write_bytes(input_text.encode('utf-8'))
            output_path.touch()
            self._output = output_path.open('rb')
            self._process = subprocess.Popen(
                [self.gdb, '--quiet', '--nx', '--interpreter=mi2'],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                cwd=self.cwd, env=self.env, bufsize=0,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                start_new_session=os.name != 'nt')
            reader = threading.Thread(target=self._read_mi, daemon=True)
            reader.start()
            self._command('-gdb-set pagination off')
            self._command('-gdb-set confirm off')
            self._command('-gdb-set mi-async on')
            self._command('-gdb-set print elements 100')
            self._command('-file-exec-and-symbols ' + json.dumps(self.executable, ensure_ascii=False))
            if breakpoints:
                for filename, line in breakpoints:
                    if int(line) < 1:
                        raise ValueError('Breakpoint lines must be positive')
                    location = f'{os.path.abspath(filename).replace(chr(92), "/")}:{int(line)}'
                    self._command('-break-insert ' + json.dumps(location, ensure_ascii=False))
            else:
                self._command('-break-insert -t main')
            # GDB's console run supports inferior redirection; user input is never
            # interpolated into a command. Popen itself never invokes a shell.
            def quote_path(path):
                return '"' + path.as_posix() + '"' if os.name == 'nt' else shlex.quote(str(path))
            command = f'run < {quote_path(input_path)} > {quote_path(output_path)} 2>&1'
            self._command('-interpreter-exec console ' + json.dumps(command, ensure_ascii=False))
            while not self._end_reason:
                if self._pending_stops:
                    self._report_stop(self._pending_stops.popleft())
                try:
                    command = self._commands.get_nowait()
                except queue.Empty:
                    command = None
                if command:
                    self._command(command)
                record = self._receive()
                if record:
                    self._handle(record)
            self._drain_output()
            reason = self._end_reason
            self._command('-gdb-exit', timeout=3)
        except _Finished as exc:
            reason = str(exc)
        except Exception as exc:
            reason = 'Debugging failed'
            self.events.put(('error', str(exc)))
        finally:
            self._cancel.set()
            if self._process:
                if self._process.poll() is None:
                    stop_process(self._process)
                try:
                    self._process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self._process.kill()
                    self._process.wait(timeout=5)
                if reader:
                    reader.join(timeout=2)
                self._process.stdin.close()
                self._process.stdout.close()
            if self._output:
                self._output.close()
            if temp:
                temp.cleanup()
            with self._lock:
                self._state = 'done'
            self.events.put(('done', reason))
