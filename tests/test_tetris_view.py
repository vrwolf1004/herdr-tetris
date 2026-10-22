import os
import random
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import i18n  # noqa: E402
import tetris  # noqa: E402
from game import Game  # noqa: E402
from monitor import Monitor  # noqa: E402


def run_play(keys, in_monitor=True):
    """키 목록을 순서대로 넣고 play() 를 돌린다. 결과, 그려진 프레임, 게임, 모니터를 돌려준다.

    키가 모두 끝나면 interrupt 를 넣어 루프를 끝낸다.
    """
    strings = i18n.load_strings("en")
    monitor = Monitor(strings["monitor"], random.Random(1))
    game = Game(random.Random(1))
    frames = []
    pending = list(keys)

    def fake_read_key(_timeout):
        return pending.pop(0) if pending else "interrupt"

    with mock.patch.object(tetris, "read_key", side_effect=fake_read_key), \
            mock.patch.object(tetris, "draw", side_effect=lambda lines: frames.append("\n".join(lines))):
        result = tetris.play(game, strings, monitor, in_monitor)
    return result, frames, game, monitor


def type_line(text):
    return list(text) + ["enter"]


class ViewSwitchTest(unittest.TestCase):
    def test_starts_on_monitor_and_switch_key_opens_game(self):
        result, frames, _, _ = run_play(["switch"])
        self.assertEqual(result, "quit")
        self.assertIn("SYSTEM MONITOR", frames[0])
        self.assertNotIn("SCORE", frames[0])
        self.assertIn("SCORE", frames[-1])

    def test_switch_again_returns_to_monitor(self):
        _, frames, _, _ = run_play(["switch", "switch"])
        self.assertIn("SYSTEM MONITOR", frames[-1])

    def test_game_keys_are_typed_as_text_on_monitor(self):
        _, _, game, monitor = run_play(["a", "w", " "])
        self.assertEqual(game.col, 3)
        self.assertEqual(game.score, 0)
        self.assertEqual(monitor.buffer, "aw ")

    def test_game_hint_shows_the_switch_key(self):
        _, frames, _, _ = run_play(["switch"])
        self.assertIn("Ctrl+T: switch", frames[-1])

    def test_switch_in_game_returns_to_monitor_and_game_stays_frozen(self):
        _, frames, game, _ = run_play(["switch", "a", "switch"])
        self.assertEqual(game.col, 2)  # 게임 화면에서 한 번 움직였다
        self.assertIn("SYSTEM MONITOR", frames[-1])

    def test_q_is_text_on_monitor_and_interrupt_quits(self):
        result, _, _, monitor = run_play(["q", "interrupt"])
        self.assertEqual(result, "quit")
        self.assertEqual(monitor.buffer, "q")

    def test_quit_key_works_in_game_view(self):
        result, _, _, _ = run_play(["switch", "q"])
        self.assertEqual(result, "quit")

    def test_ctrl_t_is_the_switch_key_and_tab_is_not(self):
        self.assertEqual(tetris.SPECIAL_KEYS["\x14"], "switch")
        self.assertNotIn("\t", tetris.SPECIAL_KEYS)


class CommandLineTest(unittest.TestCase):
    def test_game_command_switches_to_game(self):
        _, frames, _, _ = run_play(type_line("game"))
        self.assertIn("SCORE", frames[-1])

    def test_unknown_command_says_command_not_found(self):
        _, frames, _, _ = run_play(type_line("nope"))
        self.assertIn("nope: command not found", frames[-1])

    def test_help_lists_commands_without_game(self):
        _, _, _, monitor = run_play(type_line("help"))
        # output[0] 은 입력 echo("$ help") 이고, 그 다음이 help 목록이다.
        names = [line.split()[0] for line in monitor.output[1:]]
        self.assertEqual(names, ["help", "status", "logs", "clear"])

    def test_backspace_edits_the_input_line(self):
        _, _, _, monitor = run_play(["h", "x", "backspace", "e", "l", "p"])
        self.assertEqual(monitor.buffer, "help")

    def test_clear_empties_the_output(self):
        _, _, _, monitor = run_play(type_line("help") + type_line("clear"))
        self.assertEqual(monitor.output, [])


if __name__ == "__main__":
    unittest.main()
