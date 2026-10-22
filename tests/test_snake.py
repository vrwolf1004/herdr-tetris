import os
import random
import re
import sys
import unittest
from collections import deque

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import snake  # noqa: E402
from snake import FOOD_SCORE, HEIGHT, KEY_DIRECTIONS, MIN_SECONDS, WIDTH, Snake  # noqa: E402

ANSI = re.compile(chr(27) + r"\[[0-9;]*m")


class FirstChoice:
    def choice(self, seq):
        return seq[0]


def plain(text):
    return ANSI.sub("", text)


def fresh(rng=None):
    return Snake(rng=rng or FirstChoice())


class StartTest(unittest.TestCase):
    def test_starts_in_the_middle_length_three_moving_right(self):
        s = fresh()
        self.assertEqual(s.length(), 3)
        self.assertEqual(s.body[0], (HEIGHT // 2, WIDTH // 2))
        self.assertEqual(s.direction, (0, 1))
        self.assertEqual(s.status(), "playing")

    def test_food_is_on_an_empty_cell(self):
        for seed in range(30):
            s = Snake(rng=random.Random(seed))
            self.assertIsNotNone(s.food)
            self.assertNotIn(s.food, s.body)


class MovementTest(unittest.TestCase):
    def test_moves_one_cell_per_tick_in_its_direction(self):
        s = fresh()
        s.food = (0, 0)
        head = s.body[0]
        self.assertTrue(s.tick())
        self.assertEqual(s.body[0], (head[0], head[1] + 1))
        self.assertEqual(s.length(), 3)

    def test_turn_applies_on_the_next_tick(self):
        s = fresh()
        s.food = (0, 0)
        s.turn((-1, 0))
        s.tick()
        self.assertEqual(s.direction, (-1, 0))
        self.assertEqual(s.body[0], (HEIGHT // 2 - 1, WIDTH // 2))

    def test_reverse_turn_is_ignored(self):
        s = fresh()
        s.food = (0, 0)
        s.turn((0, -1))  # 오른쪽으로 가는 중에 바로 왼쪽은 무시한다
        s.tick()
        self.assertEqual(s.direction, (0, 1))
        self.assertEqual(s.body[0], (HEIGHT // 2, WIDTH // 2 + 1))

    def test_keys_map_to_directions_and_avoid_the_screen_keys(self):
        self.assertEqual(KEY_DIRECTIONS["up"], KEY_DIRECTIONS["w"])
        self.assertEqual(KEY_DIRECTIONS["left"], KEY_DIRECTIONS["a"])
        for key in KEY_DIRECTIONS:
            self.assertNotIn(key, ("1", "2", "3", "q", "r"))


class CollisionTest(unittest.TestCase):
    def test_hitting_the_wall_ends_the_game(self):
        s = fresh()
        s.body = deque([(0, 5), (1, 5), (2, 5)])
        s.direction = s.next_direction = (-1, 0)
        s.tick()
        self.assertEqual(s.status(), "lost")

    def test_hitting_its_own_body_ends_the_game(self):
        s = fresh()
        s.body = deque([(5, 5), (5, 4), (4, 4), (4, 5)])
        s.direction = s.next_direction = (0, -1)
        s.tick()  # 머리가 (5,4) 몸에 닿는다
        self.assertEqual(s.status(), "lost")

    def test_no_moves_after_game_over(self):
        s = fresh()
        s.body = deque([(0, 5), (1, 5), (2, 5)])
        s.direction = s.next_direction = (-1, 0)
        s.tick()
        before = list(s.body)
        self.assertFalse(s.tick())
        self.assertEqual(list(s.body), before)


class FoodTest(unittest.TestCase):
    def test_eating_food_grows_the_body_and_scores(self):
        s = fresh()
        s.food = (6, 11)  # 머리 앞
        s.tick()
        self.assertEqual(s.length(), 4)
        self.assertEqual(s.score, FOOD_SCORE)
        self.assertNotEqual(s.food, (6, 11))
        self.assertNotIn(s.food, s.body)

    def test_moving_without_food_keeps_the_length(self):
        s = fresh()
        s.food = (0, 0)
        s.tick()
        self.assertEqual(s.length(), 3)
        self.assertEqual(s.score, 0)

    def test_full_board_is_won(self):
        s = fresh()
        cells = [(r, c) for r in range(HEIGHT) for c in range(WIDTH)]
        s.body = deque([(0, 1)] + [cell for cell in cells if cell not in ((0, 0), (0, 1))])
        s.food = (0, 0)
        s.direction = s.next_direction = (0, -1)
        s.tick()
        self.assertEqual(s.status(), "won")


class SpeedTest(unittest.TestCase):
    def test_interval_starts_at_the_base_and_gets_faster_with_food(self):
        s = fresh()
        self.assertAlmostEqual(s.interval(), snake.BASE_SECONDS)
        s.score = 50
        self.assertLess(s.interval(), snake.BASE_SECONDS)

    def test_interval_has_a_floor(self):
        s = fresh()
        s.score = 10_000
        self.assertEqual(s.interval(), MIN_SECONDS)


class ScoreAndBestTest(unittest.TestCase):
    def test_best_is_kept_across_rounds(self):
        s = fresh()
        s.score = 30
        s.body = deque([(0, 5), (1, 5), (2, 5)])
        s.direction = s.next_direction = (-1, 0)
        s.tick()  # 벽에 닿아 끝난다
        self.assertEqual(s.best, 30)
        s.restart()
        self.assertEqual(s.score, 0)
        self.assertEqual(s.best, 30)

    def test_panel_shows_score_length_and_best(self):
        s = fresh()
        s.score = 20
        s.best = 40
        text = "\n".join(plain(line) for line in s.render())
        self.assertIn("SCORE  20", text)
        self.assertIn("LENGTH 3", text)
        self.assertIn("BEST   40", text)
        self.assertIn("1-4: games   Ctrl+T: monitor", text)

    def test_game_over_message_is_shown(self):
        s = fresh()
        s.body = deque([(0, 5), (1, 5), (2, 5)])
        s.direction = s.next_direction = (-1, 0)
        s.tick()
        text = "\n".join(plain(line) for line in s.render())
        self.assertIn("GAME OVER - R: restart", text)


class RenderTest(unittest.TestCase):
    def test_head_body_and_food_are_drawn_with_readable_characters(self):
        s = fresh()
        s.food = (0, 0)
        text = "\n".join(plain(line) for line in s.render())
        self.assertIn("@", text)
        self.assertIn("o", text)
        self.assertIn("*", text)

    def test_one_line_per_board_row_plus_borders(self):
        s = fresh()
        lines = s.render()
        self.assertGreaterEqual(len(lines), HEIGHT + 2)

    def test_only_the_stated_colors_are_used(self):
        s = fresh()
        codes = set(re.findall(chr(27) + r"\[[0-9;]*m", "\n".join(s.render())))
        allowed_fixed = {snake.RESET, snake.BOLD, snake.GRAY, snake.WHITE, snake.FOOD_COLOR, snake.HEAD_COLOR}
        for code in codes:
            if "38;5;" in code:
                self.assertTrue(any(f"38;5;{n}m" == code[len(chr(27) + "["):] for n in snake.BODY_GRADIENT), code)
            else:
                self.assertIn(code, allowed_fixed, code)


if __name__ == "__main__":
    unittest.main()
