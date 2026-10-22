"""이 PC 의 CPU 와 메모리 사용률을 잰다. 표준 라이브러리만 쓴다.

Windows 는 ctypes 로 GetSystemTimes 와 GlobalMemoryStatusEx 를 부른다.
그 밖의 OS 는 /proc/stat 과 /proc/meminfo 를 읽는다. /proc 이 없으면 CPU 만 os.getloadavg 로 어림한다.
못 읽으면 None 을 돌려주고, 화면에서는 "--" 로 보인다.

계산 함수(cpu_percent, memory_percent, parse_*)는 입력값만 받으므로 테스트에서 측정 없이 검사한다.
Usage 는 SAMPLE_SECONDS 마다 백그라운드 스레드에서 재고, 화면은 snapshot() 으로 최근 값만 읽는다.
"""

import os
import threading
import time

SAMPLE_SECONDS = 1.0


def clamp(value, low, high):
    return max(low, min(high, value))


def cpu_percent(prev, cur):
    """(idle, total) 두 번 읽은 누적값으로 사용률을 구한다. 한쪽이 없거나 변화가 없으면 None."""
    if prev is None or cur is None:
        return None
    d_total = cur[1] - prev[1]
    d_idle = cur[0] - prev[0]
    if d_total <= 0:
        return None
    return clamp(100 * (1 - d_idle / d_total), 0, 100)


def memory_percent(total, available):
    """전체와 쓸 수 있는 양(바이트 또는 kB)으로 사용률을 구한다."""
    if not total:
        return None
    return clamp(100 * (total - available) / total, 0, 100)


def parse_proc_stat(text):
    """/proc/stat 의 첫 줄 cpu 합계를 (idle, total) 로 바꾼다. 이 목록에서 guest 는 user 에 이미 들어 있어 뺀다."""
    for line in text.splitlines():
        if line.startswith("cpu "):
            fields = [int(value) for value in line.split()[1:9]]
            if len(fields) < 4:
                return None
            # user nice system idle iowait irq softirq steal. idle 에는 iowait 을 더한다.
            idle = fields[3] + (fields[4] if len(fields) > 4 else 0)
            return idle, sum(fields)
    return None


def parse_meminfo(text):
    """/proc/meminfo 에서 MemTotal 과 MemAvailable 로 사용률을 구한다."""
    values = {}
    for line in text.splitlines():
        key, _, rest = line.partition(":")
        parts = rest.split()
        if parts and parts[0].isdigit():
            values[key.strip()] = int(parts[0])
    if "MemTotal" not in values or "MemAvailable" not in values:
        return None
    return memory_percent(values["MemTotal"], values["MemAvailable"])


def _read_file(path):
    try:
        with open(path, encoding="utf-8") as file:
            return file.read()
    except OSError:
        return None


def _windows_cpu_times():
    import ctypes
    from ctypes import wintypes

    class FILETIME(ctypes.Structure):
        _fields_ = [("low", wintypes.DWORD), ("high", wintypes.DWORD)]

    idle, kernel, user = FILETIME(), FILETIME(), FILETIME()
    if not ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)):
        return None

    def value(ft):
        return (ft.high << 32) | ft.low

    # Windows 에서 kernel 시간에는 idle 이 포함된다. 전체 = kernel + user.
    return value(idle), value(kernel) + value(user)


def _windows_memory_percent():
    import ctypes
    from ctypes import wintypes

    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [
            ("length", wintypes.DWORD),
            ("memory_load", wintypes.DWORD),
            ("total_phys", ctypes.c_ulonglong),
            ("avail_phys", ctypes.c_ulonglong),
            ("total_page_file", ctypes.c_ulonglong),
            ("avail_page_file", ctypes.c_ulonglong),
            ("total_virtual", ctypes.c_ulonglong),
            ("avail_virtual", ctypes.c_ulonglong),
            ("avail_extended_virtual", ctypes.c_ulonglong),
        ]

    stat = MEMORYSTATUSEX()
    stat.length = ctypes.sizeof(MEMORYSTATUSEX)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
        return None
    return memory_percent(stat.total_phys, stat.avail_phys)


class CpuMeter:
    """누적 카운터를 읽고, 이번에 읽은 값과 지난번 값의 차이로 사용률을 낸다."""

    def __init__(self, read_times):
        self._read_times = read_times
        self._prev = None

    def read(self):
        cur = self._read_times()
        percent = cpu_percent(self._prev, cur)
        if cur is not None:
            self._prev = cur
        return percent


class LoadAvgMeter:
    """/proc 이 없는 OS 용 어림값. 1분 평균 부하를 코어 수로 나눈다."""

    def read(self):
        try:
            load = os.getloadavg()[0]
        except (OSError, AttributeError):
            return None
        cores = os.cpu_count() or 1
        return clamp(100 * load / cores, 0, 100)


def default_cpu_meter():
    if os.name == "nt":
        return CpuMeter(_windows_cpu_times)
    if os.path.exists("/proc/stat"):
        return CpuMeter(lambda: parse_proc_stat(_read_file("/proc/stat") or ""))
    return LoadAvgMeter()


def read_memory_percent():
    if os.name == "nt":
        return _windows_memory_percent()
    return parse_meminfo(_read_file("/proc/meminfo") or "")


class Usage:
    """CPU 와 메모리 사용률을 SAMPLE_SECONDS 마다 잰다. 측정은 스레드에서 하고 화면은 최근 값만 읽는다."""

    def __init__(self, cpu_meter, read_memory, interval=SAMPLE_SECONDS):
        self._cpu_meter = cpu_meter
        self._read_memory = read_memory
        self._interval = interval
        self._lock = threading.Lock()
        self._cpu = None
        self._mem = None

    def sample(self):
        cpu = self._cpu_meter.read()
        mem = self._read_memory()
        with self._lock:
            self._cpu, self._mem = cpu, mem

    def snapshot(self):
        with self._lock:
            return self._cpu, self._mem

    def start(self):
        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()
        return self

    def _run(self):
        while True:
            self.sample()
            time.sleep(self._interval)


def start_default_usage():
    return Usage(default_cpu_meter(), read_memory_percent).start()
