import os
import sys
import tempfile
import tomllib
import unittest
from unittest import mock

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))

import plugin  # noqa: E402


class ManifestTest(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(ROOT, "herdr-plugin.toml"), "rb") as file:
            self.manifest = tomllib.load(file)

    def test_plugin_identity(self):
        self.assertEqual(self.manifest["id"], "herdr-tetris")
        self.assertEqual(self.manifest["min_herdr_version"], "0.9.0")
        self.assertEqual(sorted(self.manifest["platforms"]), ["linux", "macos", "windows"])

    def test_action_ids_are_unique(self):
        ids = [action["id"] for action in self.manifest["actions"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_start_and_stop_exist_for_each_platform(self):
        actions = {action["id"]: action for action in self.manifest["actions"]}
        self.assertEqual(actions["start"]["platforms"], ["linux", "macos"])
        self.assertEqual(actions["stop"]["platforms"], ["linux", "macos"])
        self.assertEqual(actions["start-windows"]["platforms"], ["windows"])
        self.assertEqual(actions["stop-windows"]["platforms"], ["windows"])

    def test_commands_use_the_right_interpreter_per_os(self):
        for action in self.manifest["actions"]:
            with self.subTest(action=action["id"]):
                expected = "python" if action["platforms"] == ["windows"] else "python3"
                self.assertEqual(action["command"][0], expected)
                self.assertEqual(action["command"][1:3], ["-X", "utf8"])
                self.assertEqual(action["command"][3], "src/plugin.py")
                self.assertIn(action["command"][4], ("start", "stop"))


class StartStopTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state = plugin.State(self.tmp.name)
        self.args = type("Args", (), {"state": self.tmp.name, "pane": None, "game_args": []})()

    def tearDown(self):
        self.tmp.cleanup()

    def test_start_does_not_relaunch_while_game_is_running(self):
        self.state.write("pane.id", "w1:p2")
        self.state.write("running", "1")
        with mock.patch.object(plugin, "pane_alive", return_value=True), \
                mock.patch.object(plugin.dock, "ensure_dock_pane") as ensure, \
                mock.patch.object(plugin.herdr_api, "cli") as cli:
            self.assertEqual(plugin.cmd_start(self.args), 0)
        ensure.assert_not_called()
        cli.assert_not_called()

    def test_start_allocates_dock_pane_and_runs_host(self):
        with mock.patch.object(plugin, "pane_alive", return_value=False), \
                mock.patch.object(plugin.dock, "register_dock") as register, \
                mock.patch.object(plugin.dock, "ensure_dock_pane", return_value=("w1", "w1:p2")) as ensure, \
                mock.patch.object(plugin.herdr_api, "cli") as cli:
            plugin.cmd_start(self.args)
        register.assert_called_once_with(plugin.DOCK_KEY, title="mon")
        ensure.assert_called_once_with(plugin.DOCK_KEY, plugin.PROJECT_DIR)
        run_args = cli.call_args[0]
        self.assertEqual(run_args[:3], ("pane", "run", "w1:p2"))
        self.assertIn("host", run_args)
        self.assertEqual(self.state.read("pane.id"), "w1:p2")

    def test_stop_closes_only_own_pane_when_dock_has_other_blocks(self):
        self.state.write("workspace.id", "w1")
        self.state.write("pane.id", "w1:p2")
        panes = {"panes": [
            {"pane_id": "w1:p2", "workspace_id": "w1", "tokens": {}},
            {"pane_id": "w1:p3", "workspace_id": "w1", "tokens": {}},
        ]}

        def fake_cli(*args, check=True):
            return panes if args == ("pane", "list") else None

        with mock.patch.object(plugin.herdr_api, "cli", side_effect=fake_cli) as cli, \
                mock.patch.object(plugin.herdr_api, "try_request"), \
                mock.patch.object(plugin.dock, "release_dock_pane") as release:
            plugin.cmd_stop(self.args)
        cli.assert_any_call("pane", "close", "w1:p2", check=False)
        self.assertNotIn(("workspace", "close", "w1"), [c.args for c in cli.call_args_list])
        release.assert_called_once_with(plugin.DOCK_KEY)
        self.assertIsNone(self.state.read("pane.id"))

    def test_stop_closes_workspace_when_dock_is_empty(self):
        self.state.write("workspace.id", "w1")
        self.state.write("pane.id", "w1:p2")
        panes = {"panes": [{"pane_id": "w1:p2", "workspace_id": "w1", "tokens": {}}]}

        def fake_cli(*args, check=True):
            return panes if args == ("pane", "list") else None

        with mock.patch.object(plugin.herdr_api, "cli", side_effect=fake_cli) as cli, \
                mock.patch.object(plugin.herdr_api, "try_request"), \
                mock.patch.object(plugin.dock, "release_dock_pane"):
            plugin.cmd_stop(self.args)
        cli.assert_any_call("workspace", "close", "w1", check=False)


class AgentKeyTest(unittest.TestCase):
    def test_dock_key_is_plugin_id_and_agent_label_is_mon(self):
        self.assertEqual(plugin.DOCK_KEY, "herdr-tetris")
        self.assertEqual(plugin.AGENT_ID, "mon")


if __name__ == "__main__":
    unittest.main()
