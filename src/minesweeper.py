"""지뢰찾기. 9x9 격자에 지뢰 10개를 숨기고, 지뢰가 없는 칸을 모두 열면 이긴다.

격자, 지뢰 배치, 숫자, 연쇄 열기, 깃발, 커서, 상태, 경과 시간은 Minesweeper 가 맡는다.
render 는 화면 줄 목록만 만든다. 키와 시간은 tetris.py 의 play_minesweeper 가 맡는다.
표준 라이브러리만 쓰고 소리는 넣지 않는다. 패널 문구는 영어로 고정한다.
"""

import random
import re
import shutil
import unicodedata

ROWS = 9
COLS = 18
MINES = 20
DIRECTIONS = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))
# 키 입력. 방향키와 WASD 로 커서를 옮긴다. Space, Enter 로 열고 F 로 깃발을 꽂는다. 1, 2, 3, 4, Q, R 은 쓰지 않는다.
KEY_MOVES = {
    "up": (-1, 0),
    "w": (-1, 0),
    "down": (1, 0),
    "s": (1, 0),
    "left": (0, -1),
    "a": (0, -1),
    "right": (0, 1),
    "d": (0, 1),
}


ANSI_RE = re.compile(chr(27) + r"\[[0-9;]*m")


def plain(text):
    """색 코드를 뺀 글자만 돌려준다."""
    return ANSI_RE.sub("", text)


def display_width(text):
    """화면에 차지하는 칸 수. 한글, 일본어 같은 글자는 두 칸으로 센다."""
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in text)


def label(text, width=7):
    """패널 이름을 표시 폭 기준으로 width 칸에 맞춘다. 한글, 일본어 같은 글자는 두 칸으로 센다."""
    used = sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in text)
    return text + " " * max(0, width - used)

ESC = chr(27)
RESET = ESC + "[0m"
BOLD = ESC + "[1m"
REVERSE = ESC + "[7m"  # 커서 칸은 색을 뒤집어 보여 준다. 글자는 그대로 남는다.
GRAY = ESC + "[90m"
WHITE = ESC + "[97m"
RED = ESC + "[1;31m"  # 깃발과 지뢰
# 숫자 1~8 은 각자 다른 색이다.
NUMBER_COLORS = {
    1: ESC + "[34m",
    2: ESC + "[32m",
    3: ESC + "[33m",
    4: ESC + "[35m",
    5: ESC + "[36m",
    6: ESC + "[94m",
    7: ESC + "[97m",
    8: ESC + "[38;5;208m",
}
PANEL_GAP = "  "

# 패널 문구의 기본값(영어). 언어 파일에 키가 빠져도 이 값을 쓴다.
DEFAULT_TEXT = {
    "title": "MINESWEEPER",
    "mines": "MINES",
    "time": "TIME",
    "boom": "BOOM! - R: restart",
    "clear": "CLEAR! - R: play again",
    "controls": "Arrows/WASD: move",
    "open": "Space/Enter: open   F: flag",
    "quit": "Q: quit   R: restart",
    "switch": "1-4: games   Ctrl+T: monitor",
}


class Minesweeper:
    def __init__(self, rng=None, mines=None, rows=ROWS, cols=COLS):
        """mines 를 주면 지뢰 자리를 고정한다(테스트용). 주지 않으면 첫 칸을 연 뒤에 무작위로 놓는다."""
        self.rng = rng or random.Random()
        self.rows = rows
        self.cols = cols
        self.fixed_mines = None if mines is None else set(mines)
        self.restart()

    def restart(self):
        self.mines = set(self.fixed_mines) if self.fixed_mines is not None else None
        self.revealed = set()
        self.flags = set()
        self.cursor = (self.rows // 2, self.cols // 2)
        self.lost = False
        self.started_at = None
        self.ended_at = None

    def mine_total(self):
        return len(self.fixed_mines) if self.fixed_mines is not None else MINES

    def inside(self, r, c):
        return 0 <= r < self.rows and 0 <= c < self.cols

    def neighbours(self, r, c):
        for dr, dc in DIRECTIONS:
            if self.inside(r + dr, c + dc):
                yield (r + dr, c + dc)

    def count(self, r, c):
        """그 칸 둘레의 지뢰 수."""
        return sum(1 for pos in self.neighbours(r, c) if pos in self.mines)

    def status(self):
        """'lost' 지뢰를 열었음, 'won' 지뢰가 아닌 칸을 모두 열었음, 'playing' 진행 중이다."""
        if self.lost:
            return "lost"
        if self.mines is not None and len(self.revealed) == self.rows * self.cols - len(self.mines):
            return "won"
        return "playing"

    def mines_left(self):
        """남은 지뢰 수 = 지뢰 수 − 깃발 수. 깃발을 지뢰보다 많이 꽂으면 음수가 된다."""
        return self.mine_total() - len(self.flags)

    def reveal(self, r, c, now=None):
        """그 칸을 연다. 연 칸이 있었으면 True 를 돌려준다. now 는 경과 시간을 재는 시각이다."""
        if self.status() != "playing" or (r, c) in self.flags or (r, c) in self.revealed:
            return False
        if self.started_at is None and now is not None:
            self.started_at = now
        if self.mines is None:
            self._place_mines(first=(r, c))
        if (r, c) in self.mines:
            self.lost = True
            self.revealed.add((r, c))
            self.revealed |= self.mines
            self.ended_at = now
            return True
        self._open(r, c)
        if self.status() == "won":
            self.ended_at = now
        return True

    def _place_mines(self, first):
        safe = {first} | set(self.neighbours(*first))
        candidates = [(r, c) for r in range(self.rows) for c in range(self.cols) if (r, c) not in safe]
        self.mines = set(self.rng.sample(candidates, self.mine_total()))

    def _open(self, r, c):
        """빈 칸이면 주변을 연쇄로 연다. 숫자 칸이면 그 칸만 연다."""
        stack = [(r, c)]
        while stack:
            pos = stack.pop()
            if pos in self.revealed or pos in self.flags:
                continue
            self.revealed.add(pos)
            if self.count(*pos) == 0:
                stack.extend(n for n in self.neighbours(*pos) if n not in self.revealed)

    def toggle_flag(self, r, c, now=None):
        """안 열린 칸에 깃발을 꽂거나 뺀다. 바뀌었으면 True 를 돌려준다."""
        if self.status() != "playing" or (r, c) in self.revealed:
            return False
        if self.started_at is None and now is not None:
            self.started_at = now
        if (r, c) in self.flags:
            self.flags.remove((r, c))
        else:
            self.flags.add((r, c))
        return True

    def move_cursor(self, dr, dc):
        r, c = self.cursor
        self.cursor = (min(self.rows - 1, max(0, r + dr)), min(self.cols - 1, max(0, c + dc)))

    def elapsed(self, now):
        """경과 시간(초). 처음 칸을 열거나 깃발을 꽂은 때부터 재고, 끝나면 멈춘다."""
        if self.started_at is None:
            return 0
        end = self.ended_at if self.ended_at is not None else now
        return max(0, int(end - self.started_at))

    def render(self, now=None, text=None, width=None):
        """화면 줄 목록. 왼쪽은 격자(테두리 포함), 오른쪽은 패널이다.
        글자만 봐도 읽힌다: # 덮임, F 깃발, * 지뢰, 1~8 숫자, . 빈 칸.
        칸 하나는 가로 두 칸으로 그린다. 세로로 길어 보이지 않도록 하기 위해서다.
        text 는 패널 문구 사전이다. 빠진 키는 영어 기본값을 쓴다.
        width 는 pane 폭이다. 없으면 터미널 폭을 쓴다. 폭이 모자라면 패널을 격자 아래로 내리고 폭에 맞춘다.
        """
        panel = self._panel(now, {**DEFAULT_TEXT, **(text or {})})
        border = GRAY + "#" * (2 * self.cols + 2) + RESET
        grid = [border]
        for r in range(self.rows):
            cells = [GRAY + "#" + RESET]
            for c in range(self.cols):
                cells.append(self._cell(r, c))
            cells.append(GRAY + "#" + RESET)
            grid.append("".join(cells))
        grid.append(border)
        grid_width = 2 * self.cols + 2
        if width is None:
            width = shutil.get_terminal_size((80, 24)).columns
        panel_width = max(display_width(plain(line)) for line in panel)
        if width >= grid_width + len(PANEL_GAP) + panel_width:
            out = []
            for r in range(max(len(grid), len(panel))):
                left = grid[r] if r < len(grid) else " " * grid_width
                right = panel[r] if r < len(panel) else ""
                out.append(left + PANEL_GAP + right)
            return out
        # 폭이 모자라면 패널을 격자 아래로 내린다. 글자 색은 빼고, 줄은 폭에 맞춰 자른다.
        below = [plain(line)[:width] for line in panel]
        return grid + [""] + below

    def _cell(self, r, c):
        pos = (r, c)
        if pos in self.revealed and self.mines is not None and pos in self.mines:
            text, code = "* ", RED
        elif pos in self.revealed:
            n = self.count(r, c)
            if n == 0:
                text, code = "  ", GRAY
            else:
                text, code = str(n) + " ", NUMBER_COLORS[n]
        elif pos in self.flags:
            text, code = "F ", RED
        else:
            text, code = "##", GRAY
        out = code + text + RESET
        if pos == self.cursor:
            out = REVERSE + out + RESET
        return out

    def _panel(self, now, t):
        messages = {"lost": t["boom"], "won": t["clear"]}
        return [
            BOLD + WHITE + t["title"] + RESET,
            "",
            f"{label(t['mines'])}{self.mines_left()}",
            f"{label(t['time'])}{self.elapsed(now or 0)}s",
            "",
            messages.get(self.status(), ""),
            "",
            t["controls"],
            t["open"],
            t["quit"],
            t["switch"],
        ]
