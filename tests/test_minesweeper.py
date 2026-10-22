import os
import random
import re
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import minesweeper  # noqa: E402
from minesweeper import COLS, MINES, NUMBER_COLORS, ROWS, KEY_MOVES, Minesweeper  # noqa: E402

ANSI = re.compile(chr(27) + r"\[[0-9;]*m")


def plain(text):
    return ANSI.sub("", text)


def board(mines):
    return Minesweeper(mines=mines)


class ConstantsTest(unittest.TestCase):
    def test_board_is_eighteen_by_nine_with_twenty_mines(self):
        self.assertEqual((ROWS, COLS, MINES), (9, 18, 20))

    def test_keys_do_not_use_the_screen_switch_digits_or_q_r(self):
        for key in KEY_MOVES:
            self.assertNotIn(key, ("1", "2", "3", "4", "q", "r", "f"))


class FirstOpenTest(unittest.TestCase):
    def test_the_first_open_and_its_neighbours_have_no_mines(self):
        for seed in range(60):
            ms = Minesweeper(rng=random.Random(seed))
            ms.reveal(4, 4)
            self.assertEqual(len(ms.mines), MINES, seed)
            safe = {(r, c) for r in range(3, 6) for c in range(3, 6)}
            self.assertFalse(ms.mines & safe, seed)

    def test_first_open_in_a_corner_is_also_safe(self):
        for seed in range(30):
            ms = Minesweeper(rng=random.Random(seed))
            ms.reveal(0, 0)
            self.assertNotIn((0, 0), ms.mines)
            self.assertFalse(ms.mines & {(0, 1), (1, 0), (1, 1)}, seed)


class NumberTest(unittest.TestCase):
    def test_count_is_the_number_of_mines_around_a_cell(self):
        ms = board({(0, 0), (0, 2)})
        self.assertEqual(ms.count(0, 1), 2)
        self.assertEqual(ms.count(1, 1), 2)
        self.assertEqual(ms.count(5, 5), 0)

    def test_opening_a_numbered_cell_opens_only_that_cell(self):
        ms = board({(0, 0)})
        ms.reveal(0, 1)
        self.assertEqual(ms.revealed, {(0, 1)})


class CascadeTest(unittest.TestCase):
    def test_opening_a_zero_opens_the_area_around_it(self):
        ms = board({(8, 8)})
        ms.reveal(0, 0)
        self.assertIn((8, 7), ms.revealed)  # 0 칸이 이어져 멀리까지 열린다
        self.assertNotIn((8, 8), ms.revealed)
        self.assertEqual(ms.status(), "won")  # 지뢰 말고 모두 열렸다

    def test_cascade_shows_numbers_but_does_not_spread_through_them(self):
        ms = board({(0, 2)})
        ms.reveal(0, 0)
        self.assertIn((0, 1), ms.revealed)  # 숫자 칸(1)은 열리지만
        self.assertNotIn((0, 2), ms.revealed)  # 지뢰는 열리지 않는다


class FlagTest(unittest.TestCase):
    def test_flag_toggles_on_and_off(self):
        ms = board({(0, 0)})
        self.assertTrue(ms.toggle_flag(4, 4))
        self.assertIn((4, 4), ms.flags)
        self.assertTrue(ms.toggle_flag(4, 4))
        self.assertNotIn((4, 4), ms.flags)

    def test_a_flagged_cell_cannot_be_opened(self):
        ms = board({(0, 0)})
        ms.toggle_flag(4, 4)
        self.assertFalse(ms.reveal(4, 4))
        self.assertNotIn((4, 4), ms.revealed)

    def test_a_revealed_cell_cannot_be_flagged(self):
        ms = board({(0, 0)})
        ms.reveal(4, 4)
        self.assertFalse(ms.toggle_flag(4, 4))

    def test_more_flags_than_mines_are_allowed_and_mines_left_goes_negative(self):
        ms = board({(0, 0)})
        for c in range(COLS):
            ms.toggle_flag(0, c)
        for c in range(COLS):
            ms.toggle_flag(1, c)
        self.assertEqual(len(ms.flags), 2 * COLS)
        self.assertEqual(ms.mines_left(), ms.mine_total() - 2 * COLS)

    def test_mines_left_counts_mines_minus_flags(self):
        ms = Minesweeper(mines={(0, 0), (1, 1)})
        ms.toggle_flag(5, 5)
        self.assertEqual(ms.mines_left(), 2 - 1)


class LoseTest(unittest.TestCase):
    def test_opening_a_mine_is_game_over_and_shows_all_mines(self):
        ms = board({(0, 0), (8, 8)})
        ms.reveal(0, 0)
        self.assertEqual(ms.status(), "lost")
        self.assertIn((8, 8), ms.revealed)

    def test_after_game_over_nothing_changes(self):
        ms = board({(0, 0)})
        ms.reveal(0, 0)
        self.assertFalse(ms.reveal(5, 5))
        self.assertFalse(ms.toggle_flag(5, 5))


class WinTest(unittest.TestCase):
    def test_opening_every_non_mine_cell_wins(self):
        ms = board({(0, 0)})
        for r in range(ROWS):
            for c in range(COLS):
                if (r, c) != (0, 0) and (r, c) not in ms.revealed and ms.status() == "playing":
                    ms.reveal(r, c)
        self.assertEqual(ms.status(), "won")

    def test_not_won_while_a_non_mine_cell_is_still_closed(self):
        ms = board({(0, 0)})
        ms.reveal(0, 1)  # 숫자 칸 하나만 열린다
        self.assertEqual(ms.status(), "playing")


class CursorTest(unittest.TestCase):
    def test_cursor_starts_in_the_middle(self):
        self.assertEqual(Minesweeper().cursor, (4, 9))

    def test_cursor_moves_and_stops_at_the_edges(self):
        ms = Minesweeper()
        for _ in range(20):
            ms.move_cursor(-1, -1)
        self.assertEqual(ms.cursor, (0, 0))
        for _ in range(20):
            ms.move_cursor(1, 1)
        self.assertEqual(ms.cursor, (ROWS - 1, COLS - 1))


class TimeTest(unittest.TestCase):
    def test_timer_starts_at_the_first_open_and_stops_at_the_end(self):
        ms = board({(0, 0), (0, 2)})
        self.assertEqual(ms.elapsed(100.0), 0)
        ms.reveal(0, 1, now=10.0)  # 숫자 칸만 열린다. 아직 끝나지 않았다
        self.assertEqual(ms.elapsed(13.5), 3)
        ms.reveal(0, 0, now=20.0)  # 지뢰를 연다. 여기서 멈춘다
        self.assertEqual(ms.elapsed(99.0), 10)


class RenderTest(unittest.TestCase):
    def test_hidden_flag_mine_and_numbers_are_readable_without_color(self):
        ms = board({(0, 0)})
        ms.toggle_flag(0, 8)  # 깃발을 먼저 꽂아 두면 연쇄 열기가 그 칸을 건너뛴다
        ms.reveal(8, 8)
        text = "\n".join(plain(line) for line in ms.render(now=1.0))
        self.assertIn("#", text)
        self.assertIn("F", text)
        self.assertIn("1", text)

    def test_mine_is_drawn_only_after_game_over(self):
        ms = board({(0, 0)})
        before = "\n".join(plain(line) for line in ms.render())
        self.assertNotIn("*", before)
        ms.reveal(0, 0)
        after = "\n".join(plain(line) for line in ms.render())
        self.assertIn("*", after)

    def test_each_number_has_its_own_color(self):
        self.assertEqual(len(set(NUMBER_COLORS.values())), 8)

    def test_panel_shows_mines_time_and_controls(self):
        ms = board({(0, 0)})
        text = "\n".join(plain(line) for line in ms.render(now=0.0))
        self.assertIn("MINES  1", text)
        self.assertIn("TIME   0s", text)
        self.assertIn("1-4: games   Ctrl+T: monitor", text)

    def test_game_over_message_is_shown(self):
        ms = board({(0, 0)})
        ms.reveal(0, 0)
        text = "\n".join(plain(line) for line in ms.render())
        self.assertIn("BOOM! - R: restart", text)

    def test_only_the_stated_colors_are_used(self):
        ms = board({(0, 0)})
        ms.reveal(8, 8)
        codes = set(re.findall(chr(27) + r"\[[0-9;]*m", "\n".join(ms.render())))
        allowed = {minesweeper.RESET, minesweeper.BOLD, minesweeper.REVERSE, minesweeper.GRAY, minesweeper.WHITE,
                   minesweeper.RED} | set(NUMBER_COLORS.values())
        self.assertTrue(codes <= allowed, codes)


if __name__ == "__main__":
    unittest.main()
