import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from sysmetrics import (  # noqa: E402
    CpuMeter, Usage, cpu_percent, memory_percent, parse_meminfo, parse_proc_stat,
)


class CpuPercentTest(unittest.TestCase):
    def test_busy_share_of_the_time_between_two_reads(self):
        # 전체가 100 늘었고 idle 이 25 늘었으면 바쁜 시간은 75%다.
        self.assertAlmostEqual(cpu_percent((1000, 2000), (1025, 2100)), 75.0)

    def test_fully_idle_is_zero_and_fully_busy_is_hundred(self):
        self.assertAlmostEqual(cpu_percent((0, 0), (100, 100)), 0.0)
        self.assertAlmostEqual(cpu_percent((0, 0), (0, 100)), 100.0)

    def test_missing_read_or_no_time_passed_gives_none(self):
        self.assertIsNone(cpu_percent(None, (1, 2)))
        self.assertIsNone(cpu_percent((1, 2), None))
        self.assertIsNone(cpu_percent((1, 2), (1, 2)))

    def test_result_stays_in_range(self):
        self.assertLessEqual(cpu_percent((0, 0), (500, 100)), 100)
        self.assertGreaterEqual(cpu_percent((500, 0), (0, 100)), 0)


class MemoryPercentTest(unittest.TestCase):
    def test_used_share_of_total(self):
        self.assertAlmostEqual(memory_percent(1000, 250), 75.0)

    def test_zero_total_gives_none(self):
        self.assertIsNone(memory_percent(0, 0))

    def test_all_available_is_zero_percent(self):
        self.assertAlmostEqual(memory_percent(1000, 1000), 0.0)


class ParseProcStatTest(unittest.TestCase):
    def test_first_cpu_line_gives_idle_and_total(self):
        text = "cpu  100 0 50 800 50 0 0 0 0 0\ncpu0 50 0 25 400 25 0 0 0 0 0\n"
        # idle 은 idle + iowait = 850. 전체는 user..steal 합 = 1000.
        self.assertEqual(parse_proc_stat(text), (850, 1000))

    def test_guest_columns_are_not_counted_twice(self):
        text = "cpu 10 0 10 80 0 0 0 0 999 999\n"
        self.assertEqual(parse_proc_stat(text), (80, 100))

    def test_missing_or_short_line_gives_none(self):
        self.assertIsNone(parse_proc_stat(""))
        self.assertIsNone(parse_proc_stat("cpu 1 2\n"))


class ParseMeminfoTest(unittest.TestCase):
    def test_uses_memtotal_and_memavailable(self):
        text = "MemTotal:       16000000 kB\nMemFree:  1000 kB\nMemAvailable:    4000000 kB\n"
        self.assertAlmostEqual(parse_meminfo(text), 75.0)

    def test_missing_fields_give_none(self):
        self.assertIsNone(parse_meminfo("MemTotal: 100 kB\n"))
        self.assertIsNone(parse_meminfo(""))


class FakeMeter:
    def __init__(self, values):
        self._values = list(values)

    def read(self):
        return self._values.pop(0)


class CpuMeterTest(unittest.TestCase):
    def test_first_read_has_no_percent_then_differences_give_one(self):
        reads = [(1000, 2000), (1025, 2100)]
        meter = CpuMeter(lambda: reads.pop(0))
        self.assertIsNone(meter.read())
        self.assertAlmostEqual(meter.read(), 75.0)

    def test_failed_read_keeps_the_last_good_counters(self):
        reads = [(0, 100), None, (50, 200)]
        meter = CpuMeter(lambda: reads.pop(0))
        meter.read()
        self.assertIsNone(meter.read())
        self.assertAlmostEqual(meter.read(), 50.0)


class UsageTest(unittest.TestCase):
    def test_snapshot_is_empty_before_the_first_sample(self):
        usage = Usage(FakeMeter([]), lambda: None)
        self.assertEqual(usage.snapshot(), (None, None))

    def test_sample_stores_cpu_and_memory_for_the_screen(self):
        usage = Usage(FakeMeter([33.0]), lambda: 66.0)
        usage.sample()
        self.assertEqual(usage.snapshot(), (33.0, 66.0))

    def test_later_sample_replaces_the_values(self):
        usage = Usage(FakeMeter([10.0, 20.0]), iter([50.0, 60.0]).__next__)
        usage.sample()
        usage.sample()
        self.assertEqual(usage.snapshot(), (20.0, 60.0))


if __name__ == "__main__":
    unittest.main()
