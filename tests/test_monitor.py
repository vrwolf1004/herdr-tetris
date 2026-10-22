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
from usage_stub import FakeUsage  # noqa: E402
from monitor import (  # noqa: E402
    BOLD, DIM, GRAY, LOG_HISTORY, MEASURED_NAME, NAME_WIDTH, OUTPUT_LINES, RESET, SERVICES, STEP_SECONDS, USAGE_GRADIENT,
    WHITE, Monitor, display_width, heat_code, usage_value_text,
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


def make_monitor(lang="en", seed=1, cpu=42.0, mem=71.0):
    strings = i18n.load_strings(lang)
    return Monitor(strings["monitor"], random.Random(seed), FakeUsage(cpu, mem))


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
        lines = mon.render(120)
        others = [line for i, line in enumerate(lines) if i != CHART_ROW]  # 가운데 줄은 실제 값 색을 쓴다
        codes = set(re.findall(r"\x1b\[[0-9;]*m", "\n".join(others)))
        self.assertTrue(codes <= {RESET, BOLD, DIM, GRAY, WHITE, BOLD + WHITE}, codes)

    def test_middle_row_matches_the_confirmed_shape(self):
        mon = make_monitor(cpu=37.0, mem=69.0)
        mon.metrics[MEASURED_NAME]["p95"] = 319
        mon.metrics[MEASURED_NAME]["rps"] = 106
        mon.metrics[MEASURED_NAME]["graph"] = "###****++++++++="
        middle = plain(mon.render(120)[CHART_ROW])
        self.assertEqual(middle, f" {MEASURED_NAME:<{NAME_WIDTH}} cpu [####........]  37%  ###****++++++++=  mem  69%  p95  319ms  rps  106")

    def test_middle_row_fields_are_in_the_service_row_order(self):
        mon = make_monitor(cpu=37.0, mem=69.0)
        middle = plain(mon.render(120)[CHART_ROW])
        order = [middle.index(part) for part in ("cpu [", "37%", mon.metrics[MEASURED_NAME]["graph"], "mem", "p95", "rps")]
        self.assertEqual(order, sorted(order))

    def test_graph_characters_are_present_and_plain(self):
        mon = make_monitor(cpu=37.0, mem=69.0)
        graph = mon.metrics[MEASURED_NAME]["graph"]
        self.assertEqual(len(graph), 16)
        middle = mon.render(120)[CHART_ROW]
        self.assertIn(f"  {graph}  mem", middle)  # 그래프 글자는 색 코드 없이 흰색과 회색 자리에 있다

    def test_cpu_and_mem_percent_in_the_middle_row_are_the_measured_values(self):
        for cpu, mem in ((0.0, 7.4), (40.0, 52.0), (67.0, 99.6), (100.0, 0.0)):
            mon = make_monitor(cpu=cpu, mem=mem)
            middle = plain(mon.render(78)[CHART_ROW])
            self.assertIn(f"] {cpu:3.0f}%", middle, cpu)
            self.assertIn(f"  mem {mem:3.0f}%", middle, mem)

    def test_middle_row_bar_has_twelve_cells(self):
        mon = make_monitor(cpu=40.0, mem=52.0)
        middle = plain(mon.render(78)[CHART_ROW])
        self.assertEqual(len(re.search(r"cpu \[([#.]*)\]", middle).group(1)), 12)

    def test_filled_cells_and_cpu_percent_use_the_gradient(self):
        mon = make_monitor(cpu=40.0, mem=52.0)
        middle = mon.render(78)[CHART_ROW]
        for i in range(5):  # 40% 는 12칸 중 5칸을 채운다
            self.assertIn(heat_code((i + 1) / 12) + "#", middle, i)
        self.assertNotIn(heat_code(6 / 12) + "#", middle)
        self.assertIn(heat_code(0.40) + " 40%", middle)  # 숫자도 같은 사용률 색이다

    def test_mem_percent_uses_the_gradient_without_a_bar(self):
        mon = make_monitor(cpu=40.0, mem=100.0)
        middle = mon.render(78)[CHART_ROW]
        self.assertIn(heat_code(1.0) + "100%", middle)
        self.assertEqual(plain(middle).count("["), 1)  # 막대는 cpu 한 개뿐이다

    def test_unknown_values_are_drawn_as_double_dash(self):
        mon = make_monitor(cpu=None, mem=None)
        middle = plain(mon.render(78)[CHART_ROW])
        self.assertIn("]   --", middle)
        self.assertIn("mem   --", middle)

    def test_fake_fields_in_the_middle_row_are_white_or_gray(self):
        mon = make_monitor(cpu=40.0, mem=52.0)
        middle = mon.render(120)[CHART_ROW]
        graph = mon.metrics[MEASURED_NAME]["graph"]
        graph_text = middle[middle.index(graph):middle.index(graph) + len(graph)]
        rate_text = middle[middle.index("p95"):]
        self.assertNotIn(chr(27) + "[38;5;", graph_text)
        self.assertNotIn(chr(27) + "[38;5;", rate_text)

    def test_service_rows_use_only_white_and_gray(self):
        mon = make_monitor(cpu=100.0, mem=10.0)
        for index, line in enumerate(mon.render(120)):
            if index != CHART_ROW:
                self.assertNotIn(chr(27) + "[38;5;", line, index)

    def test_middle_row_fits_the_narrowest_width_and_keeps_cpu_and_mem(self):
        mon = make_monitor(cpu=42.0, mem=71.0)
        for width in (30, 40, 78, 160):
            text = plain(mon.render(width)[CHART_ROW])
            self.assertLessEqual(display_width(text), width, width)
            self.assertIn("42%", text, width)
            self.assertIn("71%", text, width)

    def test_heat_color_follows_the_usage_ratio(self):
        self.assertEqual(heat_code(0.0), "[38;5;45m")
        self.assertEqual(heat_code(1.0), "[38;5;196m")
        self.assertEqual(heat_code(0.5), "[38;5;226m")  # 가운데는 노랑
        self.assertEqual(heat_code(-1.0), heat_code(0.0))  # 범위를 벗어나면 끝 색으로 자른다
        self.assertEqual(heat_code(2.0), heat_code(1.0))

    def test_heat_color_gets_warmer_as_usage_rises(self):
        codes = [int(heat_code(r / 10)[len("[38;5;"):-1]) for r in range(11)]
        self.assertEqual(codes[0], 45)
        self.assertEqual(codes[-1], 196)
        for code in codes:
            self.assertIn(code, USAGE_GRADIENT)

    def test_usage_value_color_matches_the_bar_end_color(self):
        self.assertIn(heat_code(0.42), usage_value_text(42.0))
        self.assertEqual(plain(usage_value_text(42.0)), " 42%")
        self.assertEqual(plain(usage_value_text(None)), "  --")

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
