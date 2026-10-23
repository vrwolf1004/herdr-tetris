import io
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
from usage_stub import FakeUsage  # noqa: E402


def run_play(keys, in_monitor=True):
    """tetris.play 를 키 목록으로 돌린다. 결과, 그려진 프레임, 게임, 모니터를 돌려준다."""
    strings = i18n.load_strings("en")
    monitor = Monitor(strings["monitor"], usage=FakeUsage())
    game = Game(random.Random(1))
    game.game_over = True  # 숫자 키로 넘어가는 경우를 보므로 판은 끝나 있다 (진행 중이면 숫자 키는 무시된다)
    frames = []
    pending = list(keys)

    def fake_read_key(_timeout):
        return pending.pop(0) if pending else "interrupt"

    with mock.patch.object(tetris, "read_key", side_effect=fake_read_key), \
            mock.patch.object(tetris, "draw", side_effect=lambda lines: frames.append("\n".join(lines))):
        result = tetris.play(game, strings, monitor, in_monitor)
    return result, frames, game, monitor


def keys_then_interrupt(keys):
    pending = list(keys)

    def fake_read_key(_timeout):
        return pending.pop(0) if pending else "interrupt"

    return fake_read_key


def run_ladder(keys, seed=1):
    strings = i18n.load_strings("en")
    frames = []
    pending = list(keys)

    def fake_read_key(_timeout):
        return pending.pop(0) if pending else "interrupt"

    with mock.patch.object(tetris, "read_key", side_effect=fake_read_key), \
            mock.patch.object(tetris, "draw", side_effect=lambda lines: frames.append("\n".join(lines))):
        result = tetris.play_ladder(strings, tetris.new_ladder_state())
    return result, frames


def finished_tetris(*args, **kwargs):
    """끝난 테트리스 판. 숫자 키는 진행 중인 판에서는 무시되므로, 넘어가기 흐름은 끝난 판으로 시작한다."""
    game = Game(*args, **kwargs)  # game.Game (tetris.Game 은 이 함수로 바뀌어 있다)
    game.game_over = True
    return game


class MonitorKeysTest(unittest.TestCase):
    def test_monitor_digits_are_command_input_not_game_keys(self):
        result, frames, _, monitor = run_play(["2"])
        self.assertEqual(result, "quit")
        self.assertEqual(monitor.buffer, "2")
        self.assertIn("SYSTEM MONITOR", frames[-1])

    def test_one_on_monitor_does_not_open_tetris(self):
        result, frames, _, monitor = run_play(["1"])
        self.assertEqual(result, "quit")
        self.assertEqual(monitor.buffer, "1")
        self.assertIn("SYSTEM MONITOR", frames[-1])

    def test_digit_typed_after_text_goes_to_command_line(self):
        result, _, _, monitor = run_play(["x", "1"])
        self.assertEqual(result, "quit")
        self.assertEqual(monitor.buffer, "x1")

    def test_ctrl_t_from_monitor_shows_tetris_then_2_opens_ladder(self):
        result, _, _, _ = run_play(["switch", "2"])
        self.assertEqual(result, "2")

    def test_two_on_tetris_screen_opens_ladder(self):
        result, _, _, _ = run_play(["2"], in_monitor=False)
        self.assertEqual(result, "2")

    def test_game_keys_are_unchanged(self):
        result, _, game, _ = run_play(["switch", "1", "x"])
        self.assertEqual(result, "1")  # 게임 화면에서 1 은 새 테트리스로 간다
        self.assertEqual(game.col, 3)


class LadderScreenTest(unittest.TestCase):
    def test_ctrl_t_returns_to_monitor(self):
        result, frames = run_ladder(["switch"])
        self.assertEqual(result, "monitor")
        self.assertIn("LADDER GAME", frames[0])

    def test_one_returns_to_tetris_game_screen(self):
        result, _ = run_ladder(["1"])
        self.assertEqual(result, "1")

    def test_q_and_interrupt_quit(self):
        self.assertEqual(run_ladder(["q"])[0], "quit")
        self.assertEqual(run_ladder(["interrupt"])[0], "quit")

    def test_arrow_right_picks_start_column_and_shows_path(self):
        _, frames = run_ladder(["right", "right"])
        self.assertIn("start 2 -> end", frames[-1])

    def test_right_stops_at_last_column(self):
        _, frames = run_ladder(["right"] * 20)
        self.assertIn("start 12 -> end", frames[-1])

    def test_left_stops_at_first_column(self):
        _, frames = run_ladder(["right", "left", "left"])
        self.assertIn("start 1 -> end", frames[-1])

    def test_digits_other_than_one_do_not_pick_a_column(self):
        _, frames = run_ladder(["3"])
        self.assertIn("No column picked yet", frames[-1])

    def test_r_makes_a_new_ladder_and_clears_selection(self):
        _, frames = run_ladder(["right", "r"])
        self.assertIn("No column picked yet", frames[-1])


class DrawClearTest(unittest.TestCase):
    def test_blank_rows_above_the_picture_are_cleared_not_skipped(self):
        # 위쪽 여백 줄마다 줄 지우기(ESC [2K)를 써야 이전 화면의 글자가 남지 않는다.
        clear_line = chr(27) + "[2K"
        with mock.patch.object(tetris.shutil, "get_terminal_size", return_value=(80, 40)),                 mock.patch("sys.stdout", new_callable=io.StringIO) as out:
            tetris.draw(["abc"])
        top = (40 - 1 - 1) // 2
        self.assertEqual(out.getvalue().count(clear_line), top)


class KeyFlowTest(unittest.TestCase):
    """게임을 뺀 뒤의 키 흐름: 2 는 사다리, 3 과 4 는 아무 일도 없고, 1 은 tetris, Ctrl+T 는 모니터다."""

    class NoTerminal:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def test_key_2_on_the_game_screen_opens_the_ladder(self):
        result, _, _, _ = run_play(["2"], in_monitor=False)
        self.assertEqual(result, "2")

    def test_key_4_on_the_game_screen_opens_minesweeper(self):
        result, _, _, _ = run_play(["4"], in_monitor=False)
        self.assertEqual(result, "4")

    def test_key_1_on_the_game_screen_returns_the_number_to_start_a_new_tetris(self):
        result, _, _, _ = run_play(["1"], in_monitor=False)
        self.assertEqual(result, "1")

    @mock.patch.object(tetris, "Game", new=finished_tetris)
    def test_tetris_to_ladder_and_back_then_monitor_and_quit(self):
        keys = ["switch", "2", "1", "switch", "interrupt"]
        frames = []
        draw = lambda lines: frames.append(chr(10).join(lines))
        with mock.patch.object(tetris, "read_key", side_effect=keys_then_interrupt(keys)):
            with mock.patch.object(tetris, "draw", side_effect=draw):
                with mock.patch.object(tetris, "TerminalMode", self.NoTerminal):
                    with mock.patch.object(tetris.sys, "stdin") as stdin:
                        stdin.isatty.return_value = True
                        code = tetris.main(["--lang", "en"])
        self.assertEqual(code, 0)
        self.assertTrue(any("LADDER GAME" in frame for frame in frames))
        self.assertTrue(any("SYSTEM MONITOR" in frame for frame in frames))


if __name__ == "__main__":
    unittest.main()
