"""스네이크. 격자 안에서 먹이를 먹고 몸을 늘린다. 벽이나 자기 몸에 닿으면 끝난다.

격자, 이동, 먹이, 길이, 점수, 속도, 최고 점수는 Snake 가 맡는다. render 는 화면 줄 목록만 만든다.
키와 시간은 tetris.py 의 play_snake 가 맡는다. 표준 라이브러리만 쓰고 소리는 넣지 않는다.
패널 문구는 영어로 고정한다. 최고 점수는 이 객체가 살아 있는 동안(판 사이)만 기억한다.
"""

import random
import unicodedata
from collections import deque

WIDTH = 20  # 격자 칸 수(가로)
HEIGHT = 12  # 격자 칸 수(세로)
START_LENGTH = 3
FOOD_SCORE = 10
BASE_SECONDS = 0.20  # 처음 한 칸 움직이는 간격
SPEED_STEP = 0.01  # 먹이 하나마다 줄어드는 간격
MIN_SECONDS = 0.07  # 가장 빠를 때의 간격(하한)

# 방향키와 WASD 로 방향을 바꾼다. 1, 2, 3, Q, R 은 쓰지 않는다.
KEY_DIRECTIONS = {
    "up": (-1, 0),
    "w": (-1, 0),
    "down": (1, 0),
    "s": (1, 0),
    "left": (0, -1),
    "a": (0, -1),
    "right": (0, 1),
    "d": (0, 1),
}


def label(text, width=7):
    """패널 이름을 표시 폭 기준으로 width 칸에 맞춘다. 한글, 일본어 같은 글자는 두 칸으로 센다."""
    used = sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in text)
    return text + " " * max(0, width - used)

ESC = chr(27)
RESET = ESC + "[0m"
BOLD = ESC + "[1m"
GRAY = ESC + "[90m"
WHITE = ESC + "[97m"
FOOD_COLOR = ESC + "[1;91m"  # 밝은 빨강: 먹이는 눈에 띄게
HEAD_COLOR = ESC + "[1;97m"  # 머리는 굵은 흰색
# 몸은 머리에서 꼬리로 갈수록 어두운 초록으로 바뀐다(256색 그라데이션).
BODY_GRADIENT = (46, 40, 34, 28, 22)
PANEL_GAP = "  "

# 패널 문구의 기본값(영어). 언어 파일에 키가 빠져도 이 값을 쓴다.
DEFAULT_TEXT = {
    "title": "SNAKE",
    "score": "SCORE",
    "length": "LENGTH",
    "best": "BEST",
    "game_over": "GAME OVER - R: restart",
    "full": "FULL! - R: play again",
    "controls": "Arrows/WASD: turn",
    "quit": "Q: quit   R: restart",
    "switch": "1-4: games   Ctrl+T: monitor",
}


class Snake:
    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.best = 0  # 판과 판 사이에 남는 최고 점수. restart 로도 지우지 않는다.
        self.restart()

    def restart(self):
        mid_r, mid_c = HEIGHT // 2, WIDTH // 2
        self.body = deque((mid_r, mid_c - i) for i in range(START_LENGTH))  # 머리가 앞
        self.direction = (0, 1)
        self.next_direction = (0, 1)
        self.score = 0
        self.dead = False
        self.food = None
        self._place_food()

    def length(self):
        return len(self.body)

    def status(self):
        """'lost' 벽이나 몸에 닿음, 'won' 격자가 가득 참, 'playing' 진행 중이다."""
        if self.dead:
            return "lost"
        if self.food is None:
            return "won"
        return "playing"

    def turn(self, direction):
        """다음 틱에 갈 방향을 정한다. 바로 뒤로 돌아가는 방향은 무시한다."""
        if self.length() > 1 and direction == (-self.direction[0], -self.direction[1]):
            return
        self.next_direction = direction

    def interval(self):
        """먹이를 먹을수록 짧아지는 틱 간격. MIN_SECONDS 아래로는 내려가지 않는다."""
        eaten = self.score // FOOD_SCORE
        return max(MIN_SECONDS, BASE_SECONDS - SPEED_STEP * eaten)

    def tick(self):
        """뱀을 한 칸 움직인다. 움직였으면 True 를 돌려준다."""
        if self.status() != "playing":
            return False
        self.direction = self.next_direction
        hr, hc = self.body[0]
        nr, nc = hr + self.direction[0], hc + self.direction[1]
        if not (0 <= nr < HEIGHT and 0 <= nc < WIDTH) or (nr, nc) in self.body:
            self.dead = True
            self.best = max(self.best, self.score)
            return False
        self.body.appendleft((nr, nc))
        if (nr, nc) == self.food:
            self.score += FOOD_SCORE
            self._place_food()
        else:
            self.body.pop()
        return True

    def _place_food(self):
        empty = [(r, c) for r in range(HEIGHT) for c in range(WIDTH) if (r, c) not in self.body]
        self.food = self.rng.choice(empty) if empty else None

    def render(self, text=None):
        """화면 줄 목록. 왼쪽은 격자(테두리 포함), 오른쪽은 패널이다. 글자만 봐도 읽힌다: @ 머리, o 몸, * 먹이.

        text 는 패널 문구 사전이다. 빠진 키는 영어 기본값을 쓴다.
        """
        panel = self._panel({**DEFAULT_TEXT, **(text or {})})
        border = GRAY + "#" * (2 * WIDTH + 2) + RESET
        lines = [border]
        for r in range(HEIGHT):
            cells = [GRAY + "#" + RESET]
            for c in range(WIDTH):
                cells.append(self._cell(r, c))
            cells.append(GRAY + "#" + RESET)
            lines.append("".join(cells))
        lines.append(border)
        out = []
        for r in range(max(len(lines), len(panel))):
            left = lines[r] if r < len(lines) else " " * (2 * WIDTH + 2)
            right = panel[r] if r < len(panel) else ""
            out.append(left + PANEL_GAP + right)
        return out

    def _cell(self, r, c):
        if self.body[0] == (r, c):
            return HEAD_COLOR + "@ " + RESET
        if (r, c) in self.body:
            index = list(self.body).index((r, c))
            code = BODY_GRADIENT[min(index - 1, len(BODY_GRADIENT) - 1)]
            return ESC + "[38;5;" + str(code) + "m" + "o " + RESET
        if (r, c) == self.food:
            return FOOD_COLOR + "* " + RESET
        return "  "

    def _panel(self, t):
        messages = {"lost": t["game_over"], "won": t["full"]}
        return [
            BOLD + WHITE + t["title"] + RESET,
            "",
            f"{label(t['score'])}{self.score}",
            f"{label(t['length'])}{self.length()}",
            f"{label(t['best'])}{self.best}",
            "",
            messages.get(self.status(), ""),
            "",
            t["controls"],
            t["quit"],
            t["switch"],
        ]
