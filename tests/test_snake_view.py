import os
import random
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import i18n  # noqa: E402
import snake  # noqa: E402
import tetris  # noqa: E402
from game import Game  # noqa: E402
from monitor import Monitor  # noqa: E402
from usage_stub import FakeUsage  # noqa: E402


def keys_then_interrupt(keys):
    pending = list(keys)

    def fake_read_key(_timeout):
        return pending.pop(0) if pending else "interrupt"

    return fake_read_key


def run_snake(keys, best=0):
    frames = []
    game = snake.Snake(rng=random.Random(1))
    game.best = best
    with mock.patch.object(tetris, "read_key", side_effect=keys_then_interrupt(keys)), \
            mock.patch.object(tetris, "draw", side_effect=lambda lines: frames.append("\n".join(lines))):
        result = tetris.play_snake(game, i18n.load_strings("en"))
    return result, frames, game


def run_play(keys, in_monitor=True):
    strings = i18n.load_strings("en")
    monitor = Monitor(strings["monitor"], usage=FakeUsage())
    game = Game(random.Random(1))
    frames = []
    with mock.patch.object(tetris, "read_key", side_effect=keys_then_interrupt(keys)), \
            mock.patch.object(tetris, "draw", side_effect=lambda lines: frames.append("\n".join(lines))):
        result = tetris.play(game, strings, monitor, in_monitor)
    return result, frames, game, monitor


class GameScreenKeyTest(unittest.TestCase):
    def test_key_3_on_the_game_screen_opens_snake(self):
        result, _, _, _ = run_play(["3"], in_monitor=False)
        self.assertEqual(result, "3")

    def test_key_3_on_the_monitor_is_typed_not_a_game_key(self):
        result, _, _, monitor = run_play(["3"])
        self.assertEqual(result, "quit")
        self.assertEqual(monitor.buffer, "3")

    def test_key_2_still_opens_the_ladder(self):
        self.assertEqual(run_play(["2"], in_monitor=False)[0], "2")


class SnakeScreenTest(unittest.TestCase):
    def test_one_returns_to_the_tetris_game_screen(self):
        self.assertEqual(run_snake(["1"])[0], "1")

    def test_ctrl_t_returns_to_the_monitor(self):
        self.assertEqual(run_snake(["switch"])[0], "monitor")

    def test_q_and_interrupt_quit(self):
        self.assertEqual(run_snake(["q"])[0], "quit")
        self.assertEqual(run_snake(["interrupt"])[0], "quit")

    def test_a_digit_key_leaves_the_snake_screen_for_that_game(self):
        result, frames, _ = run_snake(["2", "3"])
        self.assertEqual(result, "2")  # 2 를 누르면 사다리로 바로 간다. 3 은 다음 화면이 처리한다.
        self.assertIn("SNAKE", frames[-1])

    def test_direction_keys_keep_the_screen(self):
        for key in ("up", "down", "left", "right", "w", "a", "s", "d"):
            result, frames, _ = run_snake([key])
            self.assertEqual(result, "quit", key)
            self.assertIn("SNAKE", frames[-1], key)

    def test_r_starts_a_new_round(self):
        result, frames, game = run_snake(["r"])
        self.assertEqual(result, "quit")
        self.assertEqual(game.status(), "playing")

    def test_best_score_survives_leaving_and_coming_back(self):
        _, _, game = run_snake(["q"], best=70)
        self.assertEqual(game.best, 70)


class MainFlowTest(unittest.TestCase):
    class NoTerminal:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def test_tetris_to_snake_and_back_then_monitor_and_quit(self):
        keys = ["switch", "3", "1", "switch", "interrupt"]
        frames = []
        draw = mock.Mock(side_effect=lambda lines: frames.append("\n".join(lines)))
        with mock.patch.object(tetris, "read_key", side_effect=keys_then_interrupt(keys)), \
                mock.patch.object(tetris, "draw", draw), \
                mock.patch.object(tetris, "TerminalMode", self.NoTerminal), \
                mock.patch.object(tetris.sys, "stdin") as stdin:
            stdin.isatty.return_value = True
            code = tetris.main(["--lang", "en"])
        self.assertEqual(code, 0)
        self.assertTrue(any("SNAKE" in frame for frame in frames))
        self.assertTrue(any("SYSTEM MONITOR" in frame for frame in frames))


if __name__ == "__main__":
    unittest.main()
