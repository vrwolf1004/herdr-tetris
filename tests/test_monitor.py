import os
import random
import re
import sys
import time
import unittest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SRC = os.path.join(ROOT, "src")
sys.path.insert(0, SRC)

import i18n  # noqa: E402
from monitor import (  # noqa: E402
    BOLD, DIM, GRAY, LOG_HISTORY, NAME_WIDTH, OUTPUT_LINES, RESET, SERVICES, STEP_SECONDS, WHITE, Monitor,
    display_width,
)

ANSI = re.compile(r"\x1b\[[0-9;]*m")
# 렌더링 결과의 줄 위치 (기본 폭, 줄 수 22):
# 0 헤더, 1 구분선, 2 표 제목, 3~8 서비스, 9 점 그래프, 10 구분선, 11 로그 제목,
# 12~15 로그, 16 빈 줄, 17~19 명령 결과, 20 입력줄, 21 푸터
HEADER_ROW = 0
SERVICE_ROW = 3
CHART_ROW = 9
LOG_ROWS = slice(12, 16)
OUTPUT_ROWS = slice(17, 17 + OUTPUT_LINES)
INPUT_ROW = 20
FOOTER_ROW = 21
KOREAN_LETTERS = re.compile(r"[가-힣]")


def plain(text):
    return ANSI.sub("", text)


def make_monitor(lang="en", seed=1):
    strings = i18n.load_strings(lang)
    return Monitor(strings["monitor"], random.Random(seed))


class MonitorTest(unittest.TestCase):
    def test_header_has_host_region_version_clock_and_uptime(self):
        mon = make_monitor()
        mon.tick(1_700_000_000.0)
        mon.tick(1_700_000_065.0)
        header = plain(mon.render(120)[HEADER_ROW])
        self.assertIn("SYSTEM MONITOR", header)
        self.assertIn("host ops-node-07", header)
        self.assertIn("region ap-northeast-2", header)
        self.assertIn("v4.2.1", header)
        self.assertIn("UP 00:01:05", header)
        self.assertIn(time.strftime("%H:%M:%S", time.localtime(1_700_000_065.0)), header)

    def test_footer_repeats_host_region_version_and_uptime(self):
        mon = make_monitor()
        mon.tick(1_700_000_000.0)
        mon.tick(1_700_000_100.0)
        footer = plain(mon.render(120)[FOOTER_ROW])
        self.assertIn("ops-node-07", footer)
        self.assertIn("ap-northeast-2", footer)
        self.assertIn("v4.2.1", footer)
        self.assertIn("up 00:01:40", footer)

    def test_dashboard_stays_english_when_the_language_is_korean(self):
        mon = make_monitor("ko")
        for i in range(12):
            mon.step(1_700_000_000.0 + i)
        dashboard = [plain(line) for line in mon.render(120)[:OUTPUT_ROWS.start]]
        self.assertIn("SYSTEM MONITOR", dashboard[HEADER_ROW])
        self.assertTrue(any("SERVICE" in line for line in dashboard))
        self.assertTrue(any("RECENT EVENTS" in line for line in dashboard))
        self.assertFalse(any(KOREAN_LETTERS.search(line) for line in dashboard))

    def test_command_responses_follow_the_language(self):
        mon = make_monitor("ko")
        mon.buffer = "status"
        mon.submit()
        self.assertEqual(mon.output[0], "$ status")
        self.assertIn("서비스 상태", mon.output[1])
        mon.buffer = "nope"
        mon.submit()
        self.assertEqual(mon.output[-1], "nope: 명령을 찾을 수 없습니다")

    def test_no_hint_line_is_drawn(self):
        lines = make_monitor().render(78)
        self.assertFalse(any("Ctrl+T" in plain(line) for line in lines))

    def test_every_service_row_is_shown(self):
        lines = [plain(line) for line in make_monitor().render(78)]
        for name in SERVICES:
            self.assertTrue(any(line.startswith(f" {name:<{NAME_WIDTH}}") for line in lines), name)

    def test_rows_fit_the_terminal_width(self):
        mon = make_monitor()
        for i in range(10):
            mon.step(1_700_000_000.0 + i)
        for width in (30, 40, 52, 72, 100, 160):
            for line in mon.render(width):
                self.assertLessEqual(display_width(plain(line)), width, (width, plain(line)))

    def test_wide_rows_show_more_fields_and_narrow_rows_drop_them(self):
        mon = make_monitor()
        for i in range(20):
            mon.step(1_700_000_000.0 + i)
        wide = plain(mon.render(120)[SERVICE_ROW])
        narrow = plain(mon.render(30)[SERVICE_ROW])
        self.assertGreaterEqual(display_width(wide), 80)
        self.assertIn("mem", wide)
        self.assertIn("p95", wide)
        self.assertNotIn("mem", narrow)
        self.assertLessEqual(display_width(narrow), 30)

    def test_log_row_has_timestamp_level_module_and_message(self):
        mon = make_monitor()
        mon.logs = [("10:00:01", "warn", "db.pool", "slow query detected duration=812ms")]
        row = plain(mon.render(120)[LOG_ROWS][0])  # 로그는 위에서부터 쌓인다
        self.assertIn("10:00:01", row)
        self.assertIn("WARN", row)
        self.assertIn("[db.pool]", row)
        self.assertTrue(row.endswith("slow query detected duration=812ms"))

    def test_log_levels_use_gray_and_bold_white(self):
        mon = make_monitor()
        mon.logs = [
            ("10:00:00", "info", "http.server", "all good"),
            ("10:00:01", "warn", "db.pool", "slow query"),
            ("10:00:02", "error", "scheduler", "boom"),
        ]
        lines = mon.render(120)

        def line_with(text):
            return next(line for line in lines if text in plain(line))

        self.assertIn(GRAY, line_with("all good"))
        self.assertIn(BOLD + WHITE, line_with("slow query"))
        self.assertIn(BOLD + WHITE, line_with("boom"))
        self.assertIn("WARN", plain(line_with("slow query")))
        self.assertIn("ERROR", plain(line_with("boom")))

    def test_only_white_and_gray_colors_are_used(self):
        mon = make_monitor()
        for i in range(30):
            mon.step(1_700_000_000.0 + i)
        mon.logs.append(("10:00:02", "error", "scheduler", "boom"))
        codes = set(re.findall(r"\x1b\[[0-9;]*m", "\n".join(mon.render(120))))
        self.assertTrue(codes <= {RESET, BOLD, DIM, GRAY, WHITE, BOLD + WHITE}, codes)

    def test_chart_row_is_drawn_from_totals(self):
        mon = make_monitor()
        for i in range(5):
            mon.step(1_700_000_000.0 + i)
        chart = plain(mon.render(78)[CHART_ROW])
        self.assertTrue(chart.startswith(" rps "))
        self.assertGreater(len(chart.strip()), len("rps"))

    def test_step_appends_one_log_line_and_changes_metrics(self):
        mon = make_monitor()
        before = {name: dict(m) for name, m in mon.metrics.items()}
        mon.step(1_700_000_000.0)
        self.assertEqual(len(mon.logs), 1)
        self.assertNotEqual(before, mon.metrics)

    def test_log_history_is_bounded(self):
        mon = make_monitor()
        for i in range(LOG_HISTORY + 10):
            mon.step(1_700_000_000.0 + i)
        self.assertEqual(len(mon.logs), LOG_HISTORY)

    def test_dashboard_shows_the_latest_log_line_last(self):
        mon = make_monitor()
        for i in range(7):
            mon.step(1_700_000_000.0 + i)
        self.assertTrue(plain(mon.render(120)[LOG_ROWS][-1]).endswith(mon.logs[-1][3]))

    def test_render_has_fixed_height_with_input_line_above_footer(self):
        mon = make_monitor()
        first = len(mon.render(78))
        mon.type_char("x")
        lines = mon.render(78)
        self.assertEqual(len(lines), first)
        self.assertEqual(plain(lines[INPUT_ROW]), "$ x")

    def test_typing_and_backspace(self):
        mon = make_monitor()
        for ch in "abc":
            mon.type_char(ch)
        mon.backspace()
        self.assertEqual(mon.buffer, "ab")

    def test_empty_submit_does_nothing(self):
        mon = make_monitor()
        self.assertIsNone(mon.submit())
        self.assertEqual(mon.output, [])

    def test_unknown_command_is_reported_plainly(self):
        mon = make_monitor()
        mon.buffer = "nope"
        self.assertIsNone(mon.submit())
        self.assertEqual(mon.output[-1], "nope: command not found")

    def test_game_command_returns_game_and_is_not_in_help(self):
        mon = make_monitor()
        mon.buffer = "game"
        self.assertEqual(mon.submit(), "game")
        mon.buffer = "help"
        mon.submit()
        self.assertNotIn("game", [line.split()[0] for line in mon.output if not line.startswith("$")])

    def test_status_lists_every_service_with_latency(self):
        mon = make_monitor()
        mon.buffer = "status"
        mon.submit()
        for name in SERVICES:
            self.assertTrue(any(line.startswith(name) and "p95" in line for line in mon.output), name)

    def test_logs_command_prints_recent_lines(self):
        mon = make_monitor()
        for i in range(3):
            mon.step(1_700_000_000.0 + i)
        mon.buffer = "logs"
        mon.submit()
        self.assertEqual(mon.output[-3:], [mon._plain_log(entry) for entry in mon.logs[-3:]])

    def test_clear_empties_output(self):
        mon = make_monitor()
        mon.buffer = "help"
        mon.submit()
        mon.buffer = "clear"
        mon.submit()
        self.assertEqual(mon.output, [])

    def test_output_region_shows_latest_lines_only(self):
        mon = make_monitor()
        for _ in range(OUTPUT_LINES + 2):
            mon.buffer = "help"
            mon.submit()
        rows = [plain(line) for line in mon.render(78)[OUTPUT_ROWS]]
        self.assertEqual(rows, [" " + line for line in mon.output[-OUTPUT_LINES:]])

    def test_tick_waits_for_the_step_interval(self):
        mon = make_monitor()
        mon.tick(100.0)
        mon.tick(100.0 + STEP_SECONDS / 2)
        self.assertEqual(len(mon.logs), 1)
        mon.tick(100.0 + STEP_SECONDS)
        self.assertEqual(len(mon.logs), 2)

    def test_metrics_stay_in_bounds(self):
        mon = make_monitor()
        for i in range(1000):
            mon.step(1_700_000_000.0 + i)
        for metric in mon.metrics.values():
            self.assertTrue(2 <= metric["cpu"] <= 98)
            self.assertTrue(10 <= metric["mem"] <= 95)
            self.assertTrue(15 <= metric["p95"] <= 900)
            self.assertGreaterEqual(metric["rps"], 0)

    def test_monitor_does_not_depend_on_game_rules(self):
        with open(os.path.join(SRC, "monitor.py"), encoding="utf-8") as file:
            source = file.read()
        self.assertNotIn("import game", source)
        self.assertNotIn("from game", source)


if __name__ == "__main__":
    unittest.main()
