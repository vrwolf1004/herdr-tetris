import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import i18n  # noqa: E402
import tetris  # noqa: E402


class FakeKeys:
    """read_key 대신 쓴다. 키가 다 떨어지면 interrupt 를 준다."""

    def __init__(self, keys):
        self.pending = list(keys)

    def __call__(self, _timeout):
        return self.pending.pop(0) if self.pending else "interrupt"


class NoTerminal:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def run_main(keys):
    """main 전체를 키 순서대로 돌리고, 그려진 화면들을 순서대로 돌려준다."""
    frames = []
    with mock.patch.object(tetris, "read_key", side_effect=FakeKeys(keys)), \
            mock.patch.object(tetris, "draw", side_effect=lambda lines: frames.append(chr(10).join(lines))), \
            mock.patch.object(tetris, "TerminalMode", NoTerminal), \
            mock.patch.object(tetris.sys, "stdin") as stdin:
        stdin.isatty.return_value = True
        code = tetris.main(["--lang", "en"])
    return code, frames


def first_index(frames, marker, start=0):
    for i in range(start, len(frames)):
        if marker in frames[i]:
            return i
    return -1


class DigitSwitchTest(unittest.TestCase):
    def test_a_digit_switches_straight_from_one_game_to_another(self):
        # 모니터 → tetris 게임 → 스네이크 → 바로 사다리
        code, frames = run_main(["switch", "3", "2", "interrupt"])
        self.assertEqual(code, 0)
        snake_at = first_index(frames, "SNAKE")
        ladder_at = first_index(frames, "LADDER GAME", snake_at)
        self.assertGreater(snake_at, 0)
        self.assertGreater(ladder_at, snake_at)

    def test_digit_1_from_a_game_goes_to_tetris(self):
        code, frames = run_main(["switch", "2", "1", "interrupt"])
        ladder_at = first_index(frames, "LADDER GAME")
        tetris_at = first_index(frames, "SCORE", ladder_at)
        self.assertGreater(tetris_at, ladder_at)

    def test_the_old_game_state_is_dropped_when_a_digit_switches(self):
        # 사다리에서 열을 고른 뒤 3 으로 갔다가 2 로 돌아오면, 고른 열은 사라져 있다.
        code, frames = run_main(["switch", "2", "right", "right", "3", "2", "interrupt"])
        last_ladder = max(i for i, frame in enumerate(frames) if "LADDER GAME" in frame)
        self.assertIn("No column picked yet", frames[last_ladder])
        self.assertNotIn("start 2 -> end", frames[last_ladder])

    def test_the_same_digit_again_starts_that_game_over(self):
        code, frames = run_main(["switch", "2", "right", "2", "interrupt"])
        last_ladder = max(i for i, frame in enumerate(frames) if "LADDER GAME" in frame)
        self.assertIn("No column picked yet", frames[last_ladder])

    def test_ctrl_t_on_a_game_shows_the_monitor_and_keeps_the_game_state(self):
        # 사다리에서 열을 고르고 Ctrl+T → 모니터 → Ctrl+T 로 돌아오면 고른 열이 그대로다.
        code, frames = run_main(["switch", "2", "right", "switch", "switch", "interrupt"])
        monitor_at = first_index(frames, "SYSTEM MONITOR", 1)
        self.assertGreater(monitor_at, 0)
        back = first_index(frames, "start 1 -> end", monitor_at)
        self.assertGreater(back, monitor_at)

    def test_ctrl_t_on_the_monitor_returns_to_the_screen_it_came_from(self):
        code, frames = run_main(["switch", "3", "switch", "switch", "interrupt"])
        snake_at = first_index(frames, "SNAKE")
        monitor_at = first_index(frames, "SYSTEM MONITOR", snake_at)
        self.assertGreater(monitor_at, snake_at)
        back = first_index(frames, "SNAKE", monitor_at)
        self.assertGreater(back, monitor_at)

    def test_digits_on_the_monitor_are_typed_not_switched(self):
        code, frames = run_main(["2", "3", "interrupt"])
        self.assertEqual(first_index(frames, "LADDER GAME"), -1)
        self.assertEqual(first_index(frames, "SNAKE"), -1)
        self.assertIn("$ 23", frames[-1])


class LocaleKeysTest(unittest.TestCase):
    def test_every_panel_key_is_in_both_languages(self):
        en = i18n.load_strings("en")
        ko = i18n.load_strings("ko")
        for section in ("snake", "minesweeper"):
            self.assertEqual(set(en[section]), set(ko[section]), section)
        self.assertEqual(set(en["ladder"]), set(ko["ladder"]))

    def test_missing_keys_fall_back_to_english(self):
        text = tetris.panel_strings({"snake": {"title": "뱀"}}, "snake")
        self.assertEqual(text["title"], "뱀")
        self.assertEqual(text["score"], "SCORE")

    def test_missing_section_falls_back_to_english(self):
        text = tetris.panel_strings({}, "minesweeper")
        self.assertEqual(text["title"], "MINESWEEPER")

    def test_hints_mention_the_number_keys(self):
        en = i18n.load_strings("en")
        self.assertIn("2: ladder", en["toggle_hint"])
        self.assertIn("4: minesweeper", en["toggle_hint"])


if __name__ == "__main__":
    unittest.main()
