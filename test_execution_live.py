"""Real subprocess checks for the live console transport."""
import queue
import os
import sys
import time
import unittest

import execution


class InteractiveExecutionTests(unittest.TestCase):
    def launch(self, source, **kwargs):
        self.assertTrue(hasattr(execution, "InteractiveProcess"),
                        "The live subprocess transport is not implemented")
        job = execution.InteractiveProcess([sys.executable, "-u", "-c", source],
                                           **kwargs)
        job.start()
        self.addCleanup(job.stop)
        return job

    def collect(self, job, until_done=True, expected=None, seconds=8):
        streams = {"stdout": "", "stderr": ""}
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            try:
                kind, value = job.events.get(timeout=.1)
            except queue.Empty:
                continue
            if kind == "done":
                return streams, value
            streams[kind] += value
            if not until_done and expected in streams["stdout"]:
                return streams, None
        self.fail("Live process did not emit the expected output/completion")

    def test_prompt_is_visible_before_input_and_two_answers_can_be_sent(self):
        job = self.launch("print('First?', end='', flush=True); "
                          "a=input(); print('Second?', end='', flush=True); "
                          "b=input(); print(a + ':' + b)")
        first, result = self.collect(job, False, "First?")
        self.assertIsNone(result)
        self.assertTrue(job.send("one\n"))
        second, result = self.collect(job, False, "Second?")
        self.assertIsNone(result)
        self.assertTrue(job.send("two\n"))
        last, result = self.collect(job)
        self.assertEqual(first["stdout"] + second["stdout"] + last["stdout"],
                         "First?Second?one:two" + os.linesep)
        self.assertEqual(result.stdout, "First?Second?one:two" + os.linesep)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.reason, "")
        self.assertFalse(job.send("late\n"))

    def test_eof_delivers_queued_input_then_closes(self):
        job = self.launch("import sys; print(sys.stdin.read().upper())")
        self.assertTrue(job.send("hello\n"))
        job.close_input()
        self.assertFalse(job.send("late"))
        streams, result = self.collect(job)
        self.assertEqual(streams["stdout"], "HELLO" + os.linesep * 2)
        self.assertEqual(result.returncode, 0)

    def test_cancellation_unblocks_a_writer_and_is_nonblocking(self):
        job = self.launch("import time; print('ready'); time.sleep(60)")
        self.collect(job, False, "ready")
        self.assertTrue(job.send("x" * 190_000))
        start = time.monotonic()
        job.stop()
        self.assertLess(time.monotonic() - start, .5)
        _, result = self.collect(job)
        self.assertEqual(result.reason, "cancelled")

    def test_input_budget_rejects_large_input_without_blocking(self):
        job = self.launch("import time; time.sleep(60)")
        self.assertFalse(job.send("x" * 200_001))
        job.stop()
        self.collect(job)

    def test_timeout(self):
        job = self.launch("import time; time.sleep(60)", timeout=.15)
        _, result = self.collect(job)
        self.assertEqual(result.reason, "timeout")

    def test_parent_exit_cleans_up_descendants_holding_output_open(self):
        job = self.launch("import subprocess,sys,time; "
                          "subprocess.Popen([sys.executable, '-c', "
                          "'import time; time.sleep(3)']); "
                          "time.sleep(.15); print('parent finished')")
        streams, result = self.collect(job, seconds=1.5)
        self.assertEqual(streams["stdout"].strip(), "parent finished")
        self.assertEqual(result.returncode, 0)

    def test_output_flood_is_bounded_on_both_streams(self):
        job = self.launch("import os\nwhile True:\n"
                          " os.write(1, b'x' * 8192)\n"
                          " os.write(2, b'y' * 8192)", output_limit=2048)
        streams, result = self.collect(job)
        self.assertEqual(result.reason, "output_limit")
        self.assertLessEqual(len(result.stdout), 2048)
        self.assertLessEqual(len(result.stderr), 2048)
        self.assertEqual(streams["stdout"], result.stdout)
        self.assertEqual(streams["stderr"], result.stderr)

    def test_split_utf8_is_decoded_incrementally_and_done_is_last(self):
        job = self.launch("import os,time\n"
                          "for b in 'नमस्ते 🌍'.encode('utf-8'):\n"
                          " os.write(1, bytes([b])); time.sleep(.005)\n"
                          "os.write(2, b'final error\\n')")
        streams, result = self.collect(job)
        self.assertEqual(streams["stdout"], "नमस्ते 🌍")
        self.assertEqual(streams["stdout"], result.stdout)
        self.assertEqual(streams["stderr"], "final error\n")
        self.assertTrue(job.events.empty())


if __name__ == "__main__":
    unittest.main()
