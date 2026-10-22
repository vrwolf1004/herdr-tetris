import os
import random
import re
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import ladder  # noqa: E402
from ladder import Ladder, PATH_COLOR  # noqa: E402

ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")


def ladder_with(rungs, columns):
    lad = Ladder(columns=columns, rows=len(rungs), rng=random.Random(0))
    lad.rungs = [list(r) for r in rungs]
    return lad


class TraceTest(unittest.TestCase):
    def test_follows_rungs_to_the_right_then_right(self):
        lad = ladder_with([[True, False], [False, True]], columns=3)
        end, steps = lad.trace(0)
        self.assertEqual(end, 2)
        self.assertEqual(steps, [(0, 1), (1, 2)])

    def test_follows_a_rung_to_the_left(self):
        lad = ladder_with([[True, False], [False, True]], columns=3)
        end, steps = lad.trace(1)
        self.assertEqual(end, 0)
        self.assertEqual(steps, [(1, 0), (0, 0)])

    def test_no_rungs_goes_straight_down(self):
        lad = ladder_with([[False, False]] * 3, columns=3)
        for start in range(3):
            self.assertEqual(lad.trace(start)[0], start)

    def test_random_ladder_is_a_permutation_with_no_touching_rungs(self):
        for seed in range(50):
            lad = Ladder(columns=5, rows=8, rng=random.Random(seed))
            for row in lad.rungs:
                for c in range(len(row) - 1):
                    self.assertFalse(row[c] and row[c + 1], "rungs must not touch")
            ends = sorted(lad.trace(s)[0] for s in range(5))
            self.assertEqual(ends, list(range(5)), f"seed {seed} is not a permutation")

    def test_steps_chain_from_one_row_to_the_next(self):
        lad = Ladder(columns=4, rows=6, rng=random.Random(3))
        end, steps = lad.trace(2)
        self.assertEqual(steps[0][0], 2)
        for (_, after), (before, _) in zip(steps, steps[1:]):
            self.assertEqual(after, before)
        self.assertEqual(steps[-1][1], end)


class RenderTest(unittest.TestCase):
    def test_one_line_per_row_plus_top_and_bottom_labels(self):
        lad = Ladder(columns=4, rows=6, rng=random.Random(1))
        self.assertEqual(len(lad.render()), 6 + 2)

    def test_lines_fit_within_the_expected_width(self):
        lad = Ladder(columns=4, rows=6, rng=random.Random(1))
        width = 4 * 3 + 3
        for line in lad.render(selected=0):
            self.assertLessEqual(len(ANSI.sub("", line)), width)

    def test_labels_show_column_numbers(self):
        lad = Ladder(columns=4, rows=2, rng=random.Random(1))
        top = ANSI.sub("", lad.render()[0])
        self.assertEqual(top.split(), ["1", "2", "3", "4"])

    def test_selected_path_is_colored_and_unselected_is_not(self):
        lad = Ladder(columns=4, rows=6, rng=random.Random(1))
        self.assertNotIn(PATH_COLOR, "\n".join(lad.render()))
        self.assertIn(PATH_COLOR, "\n".join(lad.render(selected=1)))

    def test_bottom_label_marks_the_end_column(self):
        lad = Ladder(columns=4, rows=6, rng=random.Random(1))
        end = lad.trace(2)[0]
        bottom = lad.render(selected=2)[-1]
        self.assertIn(PATH_COLOR + str(end + 1), bottom)


class EightColumnTest(unittest.TestCase):
    def test_default_ladder_has_twelve_columns(self):
        self.assertEqual(Ladder(rng=random.Random(0)).columns, 12)

    def test_eight_column_random_ladder_is_a_permutation(self):
        for seed in range(50):
            lad = Ladder(columns=8, rows=6, rng=random.Random(seed))
            ends = sorted(lad.trace(s)[0] for s in range(8))
            self.assertEqual(ends, list(range(8)), f"seed {seed} is not a permutation")

    def test_rungs_never_touch_or_share_a_slot(self):
        for seed in range(50):
            lad = Ladder(columns=8, rows=6, rng=random.Random(seed))
            for row in lad.rungs:
                self.assertEqual(len(row), 7)
                for c in range(6):
                    self.assertFalse(row[c] and row[c + 1], "rungs must not touch")

    def test_path_from_the_last_column_stays_in_range(self):
        lad = Ladder(columns=8, rows=6, rng=random.Random(4))
        end, steps = lad.trace(7)
        self.assertTrue(0 <= end <= 7)
        self.assertEqual(len(steps), 6)

    def test_all_eight_numbers_are_shown_at_a_normal_width(self):
        lad = Ladder(columns=8, rows=6, rng=random.Random(1))
        top = ANSI.sub("", lad.render(width=80)[0])
        self.assertEqual(top.split(), [str(n) for n in range(1, 9)])

    def test_gap_shrinks_to_fit_a_narrow_width(self):
        lad = Ladder(columns=8, rows=6, rng=random.Random(1))
        for width in (30, 40, 50):
            lines = lad.render(width=width)
            for line in lines:
                self.assertLessEqual(len(ANSI.sub("", line)), width, width)
            top = ANSI.sub("", lines[0])
            self.assertEqual(top.split(), [str(n) for n in range(1, 9)], width)

    def test_gap_stays_at_the_default_when_the_width_is_large(self):
        lad = Ladder(columns=8, rows=6, rng=random.Random(1))
        self.assertEqual(len(ANSI.sub("", lad.render(width=200)[1])), 4 * 7 + 3)


class TwelveColumnTest(unittest.TestCase):
    def test_twelve_column_random_ladder_is_a_permutation(self):
        for seed in range(50):
            lad = Ladder(columns=12, rows=9, rng=random.Random(seed))
            ends = sorted(lad.trace(s)[0] for s in range(12))
            self.assertEqual(ends, list(range(12)), f"seed {seed} is not a permutation")

    def test_twelve_column_rungs_never_touch(self):
        for seed in range(50):
            lad = Ladder(columns=12, rows=9, rng=random.Random(seed))
            for row in lad.rungs:
                self.assertEqual(len(row), 11)
                for c in range(10):
                    self.assertFalse(row[c] and row[c + 1], "rungs must not touch")

    def test_path_from_the_last_column(self):
        lad = Ladder(columns=12, rows=9, rng=random.Random(4))
        end, steps = lad.trace(11)
        self.assertTrue(0 <= end <= 11)
        self.assertEqual(len(steps), 9)

    def test_all_twelve_numbers_are_shown_at_40_60_and_80(self):
        lad = Ladder(columns=12, rows=9, rng=random.Random(1))
        for width in (40, 60, 80):
            lines = lad.render(width=width)
            for line in lines:
                self.assertLessEqual(len(ANSI.sub("", line)), width, width)
            for top in (lines[0], lines[-1]):
                self.assertEqual(ANSI.sub("", top).split(), [str(n) for n in range(1, 13)], width)

    def test_two_digit_numbers_do_not_shift_the_rungs(self):
        lad = Ladder(columns=12, rows=9, rng=random.Random(1))
        body = [ANSI.sub("", line) for line in lad.render(width=80)[1:-1]]
        # 모든 줄에서 세로선은 같은 칸에 있어야 한다.
        bars = {tuple(i for i, ch in enumerate(line) if ch == "|") for line in body}
        self.assertEqual(len(bars), 1)

    def test_height_is_nine_rows_on_a_tall_terminal(self):
        with mock.patch.object(ladder.shutil, "get_terminal_size", return_value=os.terminal_size((80, 40))):
            self.assertEqual(ladder.default_rows(), 9)
            self.assertEqual(len(Ladder(rng=random.Random(1)).render(width=80)), 9 + 2)

    def test_height_shrinks_on_a_short_terminal_but_not_below_four(self):
        with mock.patch.object(ladder.shutil, "get_terminal_size", return_value=os.terminal_size((80, 16))):
            self.assertEqual(ladder.default_rows(), 7)
        with mock.patch.object(ladder.shutil, "get_terminal_size", return_value=os.terminal_size((80, 5))):
            self.assertEqual(ladder.default_rows(), 4)


if __name__ == "__main__":
    unittest.main()
