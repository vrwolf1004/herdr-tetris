import os
import random
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import i18n  # noqa: E402
import minesweeper  # noqa: E402
import tetris  # noqa: E402
from game import Game  # noqa: E402
from monitor import Monitor  # noqa: E402
from usage_stub import FakeUsage  # noqa: E402


def keys_then_interrupt(keys):
    pending = list(keys)

    def fake_read_key(_timeout):
        return pending.pop(0) if pending else "interrupt"

    return fake_read_key


def run_minesweeper(keys, seed=1):
    frames = []
    with mock.patch.object(tetris, "read_key", side_effect=keys_then_interrupt(keys)), \
            mock.patch.object(tetris, "draw", side_effect=lambda lines: frames.append("\n".join(lines))):
        result = tetris.play_minesweeper(minesweeper.Minesweeper(rng=random.Random(seed)), i18n.load_strings("en"))
    return result, frames


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
    def test_key_4_on_the_game_screen_opens_minesweeper(self):
        result, _, _, _ = run_play(["4"], in_monitor=False)
        self.assertEqual(result, "4")

    def test_key_4_on_the_monitor_is_typed_not_a_game_key(self):
        result, _, _, monitor = run_play(["4"])
        self.assertEqual(result, "quit")
        self.assertEqual(monitor.buffer, "4")

    def test_keys_2_and_3_still_open_their_games(self):
        self.assertEqual(run_play(["2"], in_monitor=False)[0], "2")
        self.assertEqual(run_play(["3"], in_monitor=False)[0], "3")


class MinesweeperScreenTest(unittest.TestCase):
    def test_one_returns_to_the_tetris_game_screen(self):
        self.assertEqual(run_minesweeper(["1"])[0], "1")

    def test_ctrl_t_returns_to_the_monitor(self):
        self.assertEqual(run_minesweeper(["switch"])[0], "monitor")

    def test_q_and_interrupt_quit(self):
        self.assertEqual(run_minesweeper(["q"])[0], "quit")
        self.assertEqual(run_minesweeper(["interrupt"])[0], "quit")

    def test_a_digit_key_leaves_the_minesweeper_screen_for_that_game(self):
        result, frames = run_minesweeper(["2", "3", "4"])
        self.assertEqual(result, "2")
        self.assertIn("MINESWEEPER", frames[-1])

    def test_cursor_and_open_and_flag_keys_keep_the_screen(self):
        for key in ("up", "down", "left", "right", "w", "a", "s", "d", " ", "enter", "f"):
            result, frames = run_minesweeper([key])
            self.assertEqual(result, "quit", key)
            self.assertIn("MINESWEEPER", frames[-1], key)

    def test_open_then_flag_draws_the_board_with_numbers_or_flags(self):
        result, frames = run_minesweeper([" ", "f", "interrupt"])
        self.assertIn("MINES", frames[-1])

    def test_r_starts_a_new_round(self):
        result, frames = run_minesweeper(["r"])
        self.assertEqual(result, "quit")


class CellLayoutTest(unittest.TestCase):
    def board(self):
        ms = minesweeper.Minesweeper(mines={(0, 0)})
        ms.reveal(0, 1)  # 숫자 1
        ms.toggle_flag(2, 2)  # 깃발
        return ms

    def test_every_cell_state_is_two_columns_wide(self):
        ms = self.board()
        ms.cursor = (8, 8)
        for r in range(minesweeper.ROWS):
            for c in range(minesweeper.COLS):
                self.assertEqual(minesweeper.display_width(minesweeper.plain(ms._cell(r, c))), 2, (r, c))

    def test_a_covered_cell_is_drawn_as_two_hashes(self):
        ms = minesweeper.Minesweeper(mines={(0, 0)})
        self.assertEqual(minesweeper.plain(ms._cell(4, 4)), "##")

    def test_the_mine_is_two_columns_wide_after_game_over(self):
        ms = minesweeper.Minesweeper(mines={(0, 0)})
        ms.reveal(0, 0)
        self.assertEqual(minesweeper.plain(ms._cell(0, 0)), "* ")

    def test_each_grid_row_is_nine_cells_of_two_plus_the_border(self):
        ms = self.board()
        lines = ms.render(width=80)
        grid_width = 2 * minesweeper.COLS + 2
        for line in lines[: minesweeper.ROWS + 2]:
            visible = minesweeper.plain(line)[:grid_width]
            self.assertEqual(len(visible), grid_width)
            self.assertEqual(visible[0], "#")
            self.assertEqual(visible[-1], "#")

    def test_panel_stays_beside_the_grid_when_the_pane_is_wide(self):
        ms = self.board()
        lines = ms.render(width=80)
        self.assertIn("MINESWEEPER", minesweeper.plain(lines[0]))
        self.assertIn("MINES", minesweeper.plain(lines[2]))

    def test_panel_goes_below_the_grid_when_the_pane_is_narrow(self):
        ms = self.board()
        lines = [minesweeper.plain(line) for line in ms.render(width=30)]
        grid_rows = minesweeper.ROWS + 2
        self.assertEqual(lines[grid_rows], "")
        self.assertIn("MINESWEEPER", lines[grid_rows + 1])
        # 패널 줄만 폭에 맞춘다. 격자는 칸 크기를 유지하므로 그보다 좁은 pane 에서는 넘칠 수 있다.
        for line in lines[grid_rows + 1:]:
            self.assertLessEqual(minesweeper.display_width(line), 30)

    def test_the_cursor_cell_is_reversed_on_both_columns(self):
        ms = self.board()
        ms.cursor = (4, 4)
        cell = ms._cell(4, 4)
        self.assertTrue(cell.startswith(minesweeper.REVERSE))
        self.assertEqual(minesweeper.display_width(minesweeper.plain(cell)), 2)


class CursorStepTest(unittest.TestCase):
    def play(self, keys, start=(4, 4)):
        game = minesweeper.Minesweeper(mines={(0, 0)})
        game.cursor = start
        frames = []
        with mock.patch.object(tetris, "read_key", side_effect=keys_then_interrupt(keys)), \
                mock.patch.object(tetris, "draw", side_effect=lambda lines: frames.append(chr(10).join(lines))):
            tetris.play_minesweeper(game, i18n.load_strings("en"))
        return game, frames

    def test_one_arrow_press_moves_the_cursor_one_cell(self):
        for key, expected in (("down", (5, 4)), ("up", (3, 4)), ("right", (4, 5)), ("left", (4, 3))):
            game, _ = self.play([key])
            self.assertEqual(game.cursor, expected, key)

    def test_wasd_moves_the_same_way_as_the_arrows(self):
        for key, expected in (("s", (5, 4)), ("w", (3, 4)), ("d", (4, 5)), ("a", (4, 3))):
            game, _ = self.play([key])
            self.assertEqual(game.cursor, expected, key)

    def test_each_press_is_one_cell_even_when_repeated(self):
        game, _ = self.play(["down", "down", "down", "right"])
        self.assertEqual(game.cursor, (7, 5))

    def test_the_cursor_stops_at_the_edges(self):
        game, _ = self.play(["up"] * 12, start=(4, 4))
        self.assertEqual(game.cursor, (0, 4))
        game, _ = self.play(["left"] * 12, start=(4, 4))
        self.assertEqual(game.cursor, (4, 0))
        game, _ = self.play(["down"] * 12, start=(4, 4))
        self.assertEqual(game.cursor, (8, 4))
        game, _ = self.play(["right"] * 20, start=(4, 4))
        self.assertEqual(game.cursor, (4, 17))

    def test_only_the_cursor_cell_is_reversed(self):
        game, frames = self.play(["down"], start=(4, 4))
        last = frames[-1]
        reversed_cells = last.count(minesweeper.REVERSE)
        self.assertEqual(reversed_cells, 1)


class MainFlowTest(unittest.TestCase):
    class NoTerminal:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def test_startup_shows_the_monitor_first_and_no_game(self):
        # 시작하면 모니터가 먼저 떠야 한다. 아무 키도 없으면 게임 화면이나 다른 게임으로 가지 않는다.
        frames = []
        draw = mock.Mock(side_effect=lambda lines: frames.append(chr(10).join(lines)))
        with mock.patch.object(tetris, "read_key", side_effect=keys_then_interrupt([])):
            with mock.patch.object(tetris, "draw", draw):
                with mock.patch.object(tetris, "TerminalMode", self.NoTerminal):
                    with mock.patch.object(tetris.sys, "stdin") as stdin:
                        stdin.isatty.return_value = True
                        tetris.main(["--lang", "en"])
        self.assertIn("SYSTEM MONITOR", frames[0])
        self.assertFalse(any("SNAKE" in frame or "MINESWEEPER" in frame for frame in frames))


    def test_tetris_to_minesweeper_and_back_then_monitor_and_quit(self):
        keys = ["switch", "4", "1", "switch", "interrupt"]
        frames = []
        draw = mock.Mock(side_effect=lambda lines: frames.append("\n".join(lines)))
        with mock.patch.object(tetris, "read_key", side_effect=keys_then_interrupt(keys)), \
                mock.patch.object(tetris, "draw", draw), \
                mock.patch.object(tetris, "TerminalMode", self.NoTerminal), \
                mock.patch.object(tetris.sys, "stdin") as stdin:
            stdin.isatty.return_value = True
            code = tetris.main(["--lang", "en"])
        self.assertEqual(code, 0)
        self.assertTrue(any("MINESWEEPER" in frame for frame in frames))
        self.assertTrue(any("SYSTEM MONITOR" in frame for frame in frames))


if __name__ == "__main__":
    unittest.main()
