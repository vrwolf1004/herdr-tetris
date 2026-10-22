import os
import random
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from game import HEIGHT, WIDTH, ROTATIONS, KINDS, Game  # noqa: E402


def make_game(kind, rotation=0, row=0, col=0):
    game = Game(random.Random(1))
    game.kind = kind
    game.rotation = rotation
    game.row = row
    game.col = col
    return game


class RotationTest(unittest.TestCase):
    def test_four_rotations_return_to_start_shape(self):
        for kind in KINDS:
            with self.subTest(kind=kind):
                game = make_game(kind)
                start = game.active_cells()
                for _ in range(4):
                    self.assertTrue(game.rotate())
                self.assertEqual(game.rotation, 0)
                self.assertEqual(sorted(game.active_cells()), sorted(start))

    def test_t_piece_rotates_clockwise(self):
        # 아래를 향한 T를 시계 방향으로 돌리면 왼쪽을 향한다.
        self.assertEqual(ROTATIONS["T"][1], ((0, 1), (1, 0), (1, 1), (2, 1)))

    def test_rotation_kicks_away_from_right_wall(self):
        # 세로 I 블록이 오른쪽 벽 근처에서 가로로 바뀌면 벽 밖으로 나간다.
        # 벽 킥으로 왼쪽으로 밀려서 회전해야 한다.
        game = make_game("I", rotation=1, row=5, col=8)
        self.assertTrue(game.rotate())
        self.assertEqual(game.rotation, 2)
        self.assertEqual(game.col, 6)
        for _, c in game.active_cells():
            self.assertTrue(0 <= c < WIDTH)


class MoveTest(unittest.TestCase):
    def test_move_blocked_by_wall(self):
        game = make_game("O", col=0)
        self.assertFalse(game.move(-1))
        self.assertEqual(game.col, 0)


class LineClearTest(unittest.TestCase):
    def setUp(self):
        self.game = make_game("O", col=0)

    def fill_bottom_rows(self, rows, open_cols):
        for r in range(HEIGHT - rows, HEIGHT):
            for c in range(WIDTH):
                if c not in open_cols:
                    self.game.board[r][c] = "X"

    def test_single_line_clear_scores_100_at_level_1(self):
        self.fill_bottom_rows(rows=1, open_cols={0, 1})
        self.game.hard_drop()
        # O 블록은 바닥 두 줄에 걸쳐 떨어진다. 바닥 줄 하나만 지워진다.
        # 하드 드롭 18칸 * 2 = 36점, 1줄 제거 100 * 레벨 1 = 100점.
        self.assertEqual(self.game.lines, 1)
        self.assertEqual(self.game.score, 36 + 100)

    def test_double_line_clear_scores_300_at_level_1(self):
        self.fill_bottom_rows(rows=2, open_cols={0, 1})
        self.game.hard_drop()
        self.assertEqual(self.game.lines, 2)
        self.assertEqual(self.game.score, 36 + 300)

    def test_rows_above_cleared_line_shift_down(self):
        self.fill_bottom_rows(rows=1, open_cols={0, 1})
        self.game.board[HEIGHT - 2][5] = "X"
        self.game.hard_drop()
        self.assertEqual(self.game.board[HEIGHT - 1][5], "X")
        self.assertIsNone(self.game.board[HEIGHT - 2][5])


class ScoreAndLevelTest(unittest.TestCase):
    def test_soft_drop_adds_one_point_per_cell(self):
        game = make_game("T", row=0, col=3)
        game.soft_drop()
        self.assertEqual(game.row, 1)
        self.assertEqual(game.score, 1)

    def test_level_rises_every_ten_lines(self):
        game = Game(random.Random(1))
        game.lines = 9
        self.assertEqual(game.level, 1)
        game.lines = 10
        self.assertEqual(game.level, 2)


class BagTest(unittest.TestCase):
    def test_each_seven_draws_contain_all_kinds_once(self):
        game = Game(random.Random(7))
        for _ in range(3):
            game._bag = []  # 새 가방에서 7번 뽑는다고 가정
            drawn = [game._draw_kind() for _ in range(7)]
            self.assertEqual(sorted(drawn), sorted(KINDS))


class GameOverTest(unittest.TestCase):
    def test_game_over_when_next_piece_cannot_spawn(self):
        game = make_game("O", col=0)
        # 모든 블록의 시작 행은 열 3~6 중 하나를 쓰므로, 이 칸을 막으면 스폰이 막힌다.
        # 행 전체를 채우면 줄 제거로 사라지므로 일부만 채운다.
        for c in range(3, 7):
            game.board[0][c] = "X"
        game.hard_drop()
        self.assertTrue(game.game_over)

    def test_actions_are_ignored_after_game_over(self):
        game = make_game("O", col=0)
        game.game_over = True
        self.assertFalse(game.move(1))
        self.assertFalse(game.rotate())


if __name__ == "__main__":
    unittest.main()
