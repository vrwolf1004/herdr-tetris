"""모니터링 화면. 실행하면 처음 보이는 가짜 대시보드다.

헤더에는 호스트, 리전, 버전, 시계와 가동 시간이 있다. 서비스마다 수치 막대, 스파크라인, 지연 시간이 계속 움직이고,
전체 처리량은 점 그래프로 보여 준다. 로그 한 줄에는 시각, 수준, 모듈, 메시지가 모두 들어 있고 수준은 회색과 굵은 흰색으로 구분한다.
푸터에는 호스트와 리전, 버전, 가동 시간을 다시 보여 준다. 맨 아래에는 명령 입력줄이 있다.

대시보드 문구는 영어로 고정한다. 명령 응답(help, status 등)만 locales 의 언어를 따른다.
색은 흰색과 회색만 쓰고, 단말 폭이 좁으면 막대, 스파크라인, 열을 줄인다.
게임 규칙(game.py)과는 관계가 없다. 시간과 난수는 밖에서 받으므로 테스트에서 값을 고정할 수 있다.
"""

import random
import shutil
import time
import unicodedata
from collections import deque

TITLE = "SYSTEM MONITOR"
HOST = "ops-node-07"
REGION = "ap-northeast-2"
VERSION = "4.2.1"
SERVICES = ("gateway", "auth-api", "orders-db", "cache-redis", "queue-worker", "edge-proxy")
# 모듈 이름, 메시지 템플릿. 자리 표시자: service, ms, code, n
LOG_TEMPLATES = (
    ("http.server", "{service} request completed status={code} latency={ms}ms"),
    ("cache.redis", "{service} cache hit ratio {n}% over the last window"),
    ("queue.consumer", "{service} queue depth={n} consumer lag within limits"),
    ("db.pool", "{service} connection pool in use {n}/32"),
    ("db.pool", "{service} slow query detected duration={ms}ms"),
    ("scheduler", "{service} retry scheduled backoff={n}s"),
    ("config.loader", "{service} configuration reloaded revision={n}"),
    ("metrics.export", "{service} health check passed in {ms}ms"),
)
LOG_CODES = (200, 200, 200, 201, 304, 404, 500)
LEVEL_LABELS = {"info": "INFO", "warn": "WARN", "error": "ERROR"}
DEFAULT_WIDTH = 78
MIN_WIDTH = 30
MAX_WIDTH = 160
NAME_WIDTH = 14
MODULE_WIDTH = 14
BAR_WIDTH = 12
SPARK_LEN = 16
SPARK_GAP = 2
CHART_LEN = 60
LOG_LINES = 4  # 대시보드에 보이는 로그 줄 수
LOG_HISTORY = 50  # logs 명령이 읽을 수 있는 최대 줄 수
LOGS_COMMAND_LINES = 8  # logs 명령이 보여 주는 줄 수
OUTPUT_LINES = 3  # 명령 결과 영역에 보이는 줄 수
OUTPUT_HISTORY = 50
MAX_INPUT = 80
STEP_SECONDS = 0.6
STATUS_WARN_CPU = 80
# 수치를 점과 같은 글자로 그린다. 값이 클수록 뒤쪽 글자다.
RAMP = " .:-=+*#%@"
# 색은 흰색과 회색 계열만 쓴다. 본문은 밝은 흰색, 보조 텍스트는 회색, 강조는 굵은 흰색이다.
RESET = "\x1b[0m"
BOLD = "\x1b[1m"
DIM = "\x1b[2m"
GRAY = "\x1b[90m"
WHITE = "\x1b[97m"
# 수준은 색 대신 회색과 흰색 굵기로 구분한다. WARN 과 ERROR 는 같은 굵은 흰색이고 글자로 구별한다.
LEVEL_COLORS = {"info": GRAY, "warn": BOLD + WHITE, "error": BOLD + WHITE}
# help 목록. game 은 일부러 넣지 않는다. 입력하면 게임 화면으로 간다.
HELP_COMMANDS = ("help", "status", "logs", "clear")


def display_width(text):
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in text)


def fit(text, width):
    """표시 폭 기준으로 width 칸 안에 들어가는 앞부분만 남긴다."""
    out = ""
    used = 0
    for ch in text:
        w = 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
        if used + w > width:
            break
        out += ch
        used += w
    return out


def pad_to(text, width):
    return text + " " * max(0, width - display_width(text))


def color(text, code):
    return f"{code}{text}{RESET}"


def clamp(value, low, high):
    return max(low, min(high, value))


def level_color(percent):
    return BOLD + WHITE if percent >= 80 else WHITE


def ratio_color(ratio):
    return BOLD + WHITE if ratio >= 0.8 else WHITE


def bar(percent, width):
    if width <= 0:
        return ""
    filled = round(width * percent / 100)
    return color("#" * filled, level_color(percent)) + "." * (width - filled)


def sparkline(values, width):
    if width <= 0:
        return ""
    cells = []
    for value in list(values)[-width:]:
        index = clamp(round(value / 100 * (len(RAMP) - 1)), 0, len(RAMP) - 1)
        cells.append(color(RAMP[index], level_color(value)))
    return "".join(cells)


def format_duration(seconds):
    hours, rest = divmod(int(seconds), 3600)
    minutes, secs = divmod(rest, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


class Monitor:
    def __init__(self, strings, rng=None):
        self.strings = strings  # locales 의 "monitor" 항목: 명령 응답 문구만 쓴다
        self._rng = rng or random.Random()
        self._next_step = 0.0
        self._started = None
        self.now = 0.0
        self.metrics = {
            name: {
                "cpu": self._rng.uniform(10, 60),
                "mem": self._rng.uniform(20, 70),
                "p95": self._rng.randint(40, 300),
                "rps": self._rng.randint(20, 400),
            }
            for name in SERVICES
        }
        self.cpu_history = {name: deque([self.metrics[name]["cpu"]], maxlen=CHART_LEN) for name in SERVICES}
        self.totals = deque(maxlen=CHART_LEN)  # 전체 요청 수 기록
        self.logs = []  # (시각, 수준, 모듈, 메시지)
        self.buffer = ""  # 입력줄
        self.output = []  # 명령 결과

    def uptime(self):
        return int(self.now - self._started) if self._started is not None else 0

    def tick(self, now):
        """STEP_SECONDS 마다 한 번 값을 바꾸고 로그 줄을 붙인다. 그 사이에 불리면 시각만 갱신한다."""
        if self._started is None:
            self._started = now
        self.now = now
        if now < self._next_step:
            return
        self._next_step = now + STEP_SECONDS
        self.step(now)

    def step(self, now):
        if self._started is None:
            self._started = now
        self.now = now
        rng = self._rng
        for name in SERVICES:
            metric = self.metrics[name]
            metric["cpu"] = clamp(metric["cpu"] + rng.uniform(-9, 9), 2, 98)
            metric["mem"] = clamp(metric["mem"] + rng.uniform(-2, 2), 10, 95)
            metric["p95"] = clamp(metric["p95"] + rng.randint(-30, 30), 15, 900)
            metric["rps"] = max(0, metric["rps"] + rng.randint(-40, 40))
            self.cpu_history[name].append(metric["cpu"])
        self.totals.append(sum(metric["rps"] for metric in self.metrics.values()))
        code = rng.choice(LOG_CODES)
        ms = rng.randint(3, 900)
        module, template = rng.choice(LOG_TEMPLATES)
        text = template.format(service=rng.choice(SERVICES), ms=ms, code=code, n=rng.randint(1, 99))
        level = "error" if code == 500 else "warn" if code == 404 or ms > 700 else "info"
        self.logs.append((time.strftime("%H:%M:%S", time.localtime(now)), level, module, text))
        del self.logs[:-LOG_HISTORY]

    def type_char(self, ch):
        if len(self.buffer) < MAX_INPUT:
            self.buffer += ch

    def backspace(self):
        self.buffer = self.buffer[:-1]

    def submit(self):
        """입력줄을 실행하고 결과를 output 에 쌓는다. 게임 화면으로 가야 하면 'game' 을 돌려준다."""
        line = self.buffer.strip()
        self.buffer = ""
        if not line:
            return None
        self._print(self.strings["prompt"] + line)
        name = line.split()[0]
        if name == "game":
            return "game"
        handlers = {"help": self._help, "status": self._status, "logs": self._logs, "clear": self._clear}
        handler = handlers.get(name)
        if handler is None:
            self._print(self.strings["not_found"].format(name=name))
        else:
            handler()
        return None

    def _print(self, text):
        self.output.append(text)
        del self.output[:-OUTPUT_HISTORY]

    def _help(self):
        for name in HELP_COMMANDS:
            self._print(f"{name:<8}{self.strings['command_help'][name]}")

    def _status(self):
        self._print(self.strings["status_title"])
        for name in SERVICES:
            metric = self.metrics[name]
            state = self.strings["state_warn"] if metric["cpu"] >= STATUS_WARN_CPU else self.strings["state_ok"]
            self._print(self.strings["status_line"].format(
                service=name, state=state, cpu=metric["cpu"], mem=metric["mem"], p95=int(metric["p95"]),
            ))

    def _logs(self):
        for entry in self.logs[-LOGS_COMMAND_LINES:]:
            self._print(self._plain_log(entry))

    def _clear(self):
        self.output = []

    def _plain_log(self, entry):
        stamp, level, module, text = entry
        return f"{stamp} {LEVEL_LABELS[level]:<5} [{module}] {text}"

    def _header(self, width):
        clock = time.strftime("%H:%M:%S", time.localtime(self.now)) if self._started is not None else "--:--:--"
        left = f" {TITLE}  host {HOST}  region {REGION}  v{VERSION}"
        right = f"{clock}  UP {format_duration(self.uptime())} "
        if display_width(left) + display_width(right) + 1 > width:
            right = f"{clock} "
        if display_width(left) + display_width(right) + 1 > width:
            left = fit(left, width - display_width(right) - 1)
        gap = max(1, width - display_width(left) - display_width(right))
        return color(left, BOLD + WHITE) + " " * gap + right

    def _table_heading(self, width):
        heading = f" {'SERVICE':<{NAME_WIDTH}} {'CPU':<8} {'MEM':>5} {'P95':>7} {'RPS':>6}"
        return color(fit(heading, width), DIM)

    def _service_row(self, name, width):
        metric = self.metrics[name]
        cpu, mem, p95, rps = metric["cpu"], metric["mem"], int(metric["p95"]), metric["rps"]
        head = f" {name:<{NAME_WIDTH}} cpu [] {cpu:3.0f}%"
        tails = (
            f"  mem {mem:3.0f}%  p95 {p95:4d}ms  rps {rps:4d}",
            f"  rps {rps:4d}",
            "",
        )
        for tail in tails:
            extra = width - len(head) - len(tail)
            if extra >= 0:
                break
        bar_w = min(BAR_WIDTH, extra // 2)
        spark_w = min(SPARK_LEN, extra - bar_w - SPARK_GAP)
        if spark_w < 4:
            spark_w = 0
        row = f" {name:<{NAME_WIDTH}} cpu [{bar(cpu, bar_w)}] {cpu:3.0f}%"
        if spark_w:
            row += " " * SPARK_GAP + sparkline(self.cpu_history[name], spark_w)
        return row + tail

    def _chart_row(self, width):
        label = " rps "
        room = width - len(label)
        points = list(self.totals)[-room:] if room > 0 else []
        top = max(points) if points and max(points) > 0 else 1
        cells = []
        for point in points:
            ratio = point / top
            index = clamp(round(ratio * (len(RAMP) - 1)), 0, len(RAMP) - 1)
            cells.append(color(RAMP[index], ratio_color(ratio)))
        return color(label, GRAY) + "".join(cells)

    def _log_row(self, entry, width):
        stamp, level, module, text = entry
        label = pad_to(LEVEL_LABELS[level], 5)
        room = width - (1 + len(stamp) + 2 + len(label) + 2 + MODULE_WIDTH + 2 + 1)
        if room < 8:  # 아주 좁은 단말: 모듈 칸을 빼고 색 없이 줄인다
            return fit(f" {stamp}  {label} {text}", width)
        return (f" {color(stamp, DIM)}  {color(label, LEVEL_COLORS[level])}  "
                f"{pad_to('[' + module + ']', MODULE_WIDTH + 2)} {fit(text, room)}")

    def _footer(self, width):
        text = (f" {HOST} | {REGION} | v{VERSION} | up {format_duration(self.uptime())} | "
                f"{len(SERVICES)} services | {len(self.logs)} events")
        return color(fit(text, width), DIM)

    def render(self, width=None):
        if width is None:
            width = shutil.get_terminal_size((DEFAULT_WIDTH, 24)).columns
        width = clamp(width, MIN_WIDTH, MAX_WIDTH)
        rule = color("-" * width, DIM)
        lines = [self._header(width), rule, self._table_heading(width)]
        lines += [self._service_row(name, width) for name in SERVICES]
        lines.append(self._chart_row(width))
        lines.append(rule)
        lines.append(" RECENT EVENTS")
        recent = self.logs[-LOG_LINES:]
        lines += [self._log_row(entry, width) for entry in recent]
        lines += [""] * (LOG_LINES - len(recent))
        lines.append("")
        shown = self.output[-OUTPUT_LINES:]
        lines += [fit(f" {line}", width) for line in shown]
        lines += [""] * (OUTPUT_LINES - len(shown))
        lines.append(fit(self.strings["prompt"] + self.buffer, width))
        lines.append(self._footer(width))
        return lines
