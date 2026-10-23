"""게임 중 숫자 키 1~4 는 진행 중인 판을 건드리지 않는다. 끝난 뒤에는 그 숫자의 게임으로 간다.

진행 중의 기준 (코드 확인):
- 테트리스: game_over 가 아니면 진행 중이다.
- 스네이크: status() 가 "playing" 이면 진행 중이다 (벽·몸에 닿으면 "lost", 격자가 차면 "won").
- 지뢰찾기: status() 가 "playing" 이고 첫 칸을 연 뒤 (started_at 이 있다) 진행 중이다. 첫 칸을 열기 전에는 잃을 판이 없다.
- 사다리: 끝나는 판이 없어 숫자 키로 항상 넘어간다.
"""

import copy
import os
import random
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import i18n  # noqa: E402
import minesweeper  # noqa: E402
import snake  # noqa: E402
import tetris  # noqa: E402
from game import Game  # noqa: E402


class FakeKeys:
    """read_key 대신 쓴다. 준 키를 차례로 돌려주고, 다 떨어지면 interrupt 를 준다."""

    def __init__(self, keys):
        self.pending = list(keys)

    def __call__(self, _timeout):
        return self.pending.pop(0) if self.pending else "interrupt"


def run(func, *args, keys):
    with mock.patch.object(tetris, "read_key", side_effect=FakeKeys(keys)), \
            mock.patch.object(tetris, "draw", lambda lines: None):
        return func(*args)


class TetrisDigitTest(unittest.TestCase):
    def setUp(self):
        self.strings = i18n.load_strings("en")

    def test_digit_during_a_running_tetris_game_is_ignored_and_the_board_stays(self):
        game = Game(random.Random(1))
        board, score = copy.deepcopy(game.board), game.score
        result = run(tetris.play, game, self.strings, None, False, keys=["2", "3", "interrupt"])
        self.assertEqual(result, "quit")
        self.assertEqual(game.board, board)
        self.assertEqual(game.score, score)
        self.assertFalse(game.game_over)

    def test_digit_after_a_finished_tetris_game_switches(self):
        game = Game(random.Random(1))
        game.game_over = True
        self.assertEqual(run(tetris.play, game, self.strings, None, False, keys=["2"]), "2")


class SnakeDigitTest(unittest.TestCase):
    def setUp(self):
        self.strings = i18n.load_strings("en")

    def test_digit_during_a_running_snake_game_is_ignored(self):
        game = snake.Snake(rng=random.Random(1))
        body, score = list(game.body), game.score
        result = run(tetris.play_snake, game, self.strings, keys=["3", "interrupt"])
        self.assertEqual(result, "quit")
        self.assertEqual(list(game.body), body)
        self.assertEqual(game.score, score)
        self.assertFalse(game.dead)

    def test_digit_after_a_lost_snake_game_switches(self):
        game = snake.Snake(rng=random.Random(1))
        game.dead = True
        self.assertEqual(run(tetris.play_snake, game, self.strings, keys=["3"]), "3")


class MinesweeperDigitTest(unittest.TestCase):
    def setUp(self):
        self.strings = i18n.load_strings("en")

    def test_digit_after_the_first_reveal_is_ignored_and_the_board_stays(self):
        game = minesweeper.Minesweeper(random.Random(1))
        game.reveal(0, 0, now=1.0)  # 첫 칸을 열면 진행 중이다
        revealed = set(game.revealed)
        result = run(tetris.play_minesweeper, game, self.strings, keys=["4", "interrupt"])
        self.assertEqual(result, "quit")
        self.assertEqual(game.revealed, revealed)
        self.assertEqual(game.status(), "playing")

    def test_digit_before_the_first_reveal_switches(self):
        game = minesweeper.Minesweeper(random.Random(1))
        self.assertEqual(run(tetris.play_minesweeper, game, self.strings, keys=["4"]), "4")


class LadderDigitTest(unittest.TestCase):
    def test_digit_on_the_ladder_always_switches(self):
        strings = i18n.load_strings("en")
        state = tetris.new_ladder_state()
        self.assertEqual(run(tetris.play_ladder, strings, state, keys=["1"]), "1")


if __name__ == "__main__":
    unittest.main()
