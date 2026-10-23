import os
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import plugin  # noqa: E402


class StartWithMarkerTest(unittest.TestCase):
    """running 표식: 호스트가 살아 있을 때만 '이미 실행 중'으로 보고, 죽었거나 옛 형식이면 표식을 지우고 시작한다."""

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.state = plugin.State(self.folder.name)
        self.state.write("pane.id", "p1")
        self.args = SimpleNamespace(state=self.folder.name)

    def start(self, marker, alive_pid):
        if marker is not None:
            self.state.write("running", marker)
        with mock.patch.object(plugin, "pane_alive", return_value=True), \
                mock.patch.object(plugin, "pid_alive", side_effect=lambda pid: alive_pid == pid), \
                mock.patch.object(plugin.dock, "register_dock"), \
                mock.patch.object(plugin.dock, "ensure_dock_pane", return_value=("w1", "p1")) as ensure, \
                mock.patch.object(plugin.herdr_api, "cli") as cli:
            code = plugin.cmd_start(self.args)
        return code, ensure, cli

    def test_marker_of_a_dead_host_starts_again_in_the_normal_path(self):
        code, ensure, cli = self.start("4242", alive_pid=None)
        self.assertEqual(code, 0)
        ensure.assert_called_once()
        self.assertIn(("pane", "run"), [call.args[:2] for call in cli.call_args_list])
        self.assertIsNone(self.state.read("running"))

    def test_marker_of_a_live_host_does_nothing(self):
        code, ensure, cli = self.start("4242", alive_pid=4242)
        self.assertEqual(code, 0)
        ensure.assert_not_called()
        cli.assert_not_called()

    def test_old_format_marker_starts_again_and_is_removed(self):
        code, ensure, cli = self.start("1700000000.25", alive_pid=None)
        self.assertEqual(code, 0)
        ensure.assert_called_once()
        self.assertIsNone(self.state.read("running"))

    def test_no_marker_starts_normally(self):
        code, ensure, cli = self.start(None, alive_pid=None)
        ensure.assert_called_once()

    def test_host_alive_ignores_values_that_are_not_pids(self):
        for value in (None, "", "abc", "1700000000.25"):
            with self.subTest(value=value):
                self.assertFalse(plugin.host_alive(value))

    def test_host_writes_its_own_pid_as_the_marker(self):
        seen = {}

        def fake_main(args):
            seen["marker"] = self.state.read("running")
            return 0

        with mock.patch.object(plugin.tetris, "main", side_effect=fake_main), \
                mock.patch.object(plugin.herdr_api, "try_request"), \
                mock.patch.object(plugin, "keep_at_bottom"):
            args = SimpleNamespace(state=self.folder.name, pane="p1", game_args=[])
            plugin.cmd_host(args)
        self.assertEqual(seen["marker"], str(os.getpid()))
        self.assertIsNone(self.state.read("running"))  # 정상 종료하면 표식을 지운다


class PidAliveTest(unittest.TestCase):
    def test_this_process_is_alive(self):
        self.assertTrue(plugin.pid_alive(os.getpid()))

    def test_missing_pid_is_not_alive(self):
        self.assertFalse(plugin.pid_alive(None))

    def test_a_finished_process_is_not_alive(self):
        child = subprocess.Popen([sys.executable, "-c", "pass"])
        child.wait()
        self.assertFalse(plugin.pid_alive(child.pid))


if __name__ == "__main__":
    unittest.main()
