"""사다리게임(아미다쿠지). 세로선 여러 개를 가로선으로 잇고, 위 번호에서 아래까지 가는 길을 따라간다.

사다리 생성과 경로 계산, 화면 줄 만들기만 맡는다. 그리기와 키 입력은 tetris.py 가 맡는다.
"""

import random
import shutil

COLUMNS = 12
ROWS = 9  # 기본 세로 줄 수. 예전 6 의 1.5배 정도다. 터미널이 낮으면 default_rows 가 줄인다.
MIN_ROWS = 4
OVERHEAD = 9  # 사다리 줄 밖에 쓰는 줄 수(제목, 빈 줄, 번호 두 줄, 빈 줄, 고른 열, 설명, 힌트, 여유 한 줄)
COLUMN_WIDTH = 4  # 세로선 사이 칸 수. 가로선은 세로선 사이 빈칸을 채운다. 폭이 모자라면 이보다 줄인다.
MIN_GAP = 3  # 열 간격의 최소. 두 자리 번호(10~12)가 옆 번호와 붙지 않으려면 3칸이 필요하다.
PATH_COLOR = "\x1b[33m"  # 경로는 노랑으로 표시한다.
RESET = "\x1b[0m"


def default_rows():
    """사다리 화면이 pane 높이를 넘기지 않도록 세로 줄 수를 정한다. 기본은 ROWS 이고 MIN_ROWS 까지 줄인다."""
    lines = shutil.get_terminal_size((80, 24)).lines
    return max(MIN_ROWS, min(ROWS, lines - OVERHEAD))


class Ladder:
    def __init__(self, columns=COLUMNS, rows=None, rng=None):
        self.columns = columns
        rows = rows if rows is not None else default_rows()
        self.rows = rows
        rng = rng or random.Random()
        # rungs[r][c] 가 True 면 r 번째 줄에서 c 열과 c+1 열이 가로선으로 이어진다.
        self.rungs = []
        for _ in range(rows):
            row = [False] * (columns - 1)
            c = 0
            while c < columns - 1:
                if rng.random() < 0.5:
                    row[c] = True
                    c += 2  # 가로선이 겹치면 경로가 갈림길이 되므로 바로 다음 칸은 비운다.
                else:
                    c += 1
            self.rungs.append(row)

    def trace(self, start):
        """start 열(0부터)에서 아래로 내려간다. (도착 열, 줄마다 (들어간 열, 나온 열) 목록)을 돌려준다."""
        col = start
        steps = []
        for row in self.rungs:
            before = col
            if col < self.columns - 1 and row[col]:
                col += 1
            elif col > 0 and row[col - 1]:
                col -= 1
            steps.append((before, col))
        return col, steps

    def render(self, selected=None, width=None):
        """화면 줄 목록을 돌려준다. selected 는 고른 시작 열(0부터) 또는 None 이다.

        고른 경로는 PATH_COLOR 로 칠한다. 위와 아래 줄에는 열 번호를 쓴다.
        width 는 화면 폭이다. 없으면 터미널 폭을 쓴다. 열 간격은 이 폭에 맞게 COLUMN_WIDTH 를 넘지 않는 선에서 줄인다.
        """
        if width is None:
            width = shutil.get_terminal_size((80, 24)).columns
        gap = max(MIN_GAP, min(COLUMN_WIDTH, (width - 4) // (self.columns - 1)))
        total = gap * (self.columns - 1) + 4  # 마지막 번호가 두 자리여도 들어가도록 한 칸 더 둔다

        def x(col):
            return gap * col + 2

        end, steps = self.trace(selected) if selected is not None else (None, [])
        lines = []
        lines.append(self._labels(total, x, selected))
        for r in range(self.rows):
            chars = [" "] * total
            hot = [False] * total
            for c in range(self.columns):
                chars[x(c)] = "|"
            for c, has_rung in enumerate(self.rungs[r]):
                if has_rung:
                    for i in range(x(c) + 1, x(c + 1)):
                        chars[i] = "-"
            if steps:
                before, after = steps[r]
                for c in {before, after}:
                    hot[x(c)] = True
                if before != after:
                    for i in range(min(x(before), x(after)) + 1, max(x(before), x(after))):
                        hot[i] = True
            lines.append(self._join(chars, hot))
        lines.append(self._labels(total, x, end))
        return lines

    def _labels(self, width, x, picked):
        chars = [" "] * width
        hot = [False] * width
        for c in range(self.columns):
            # 두 자리 번호는 칸 두 개에 쓴다. 한 칸에 문자열을 넣으면 뒤쪽 줄이 밀린다.
            for i, ch in enumerate(str(c + 1)):
                chars[x(c) + i] = ch
                if c == picked:
                    hot[x(c) + i] = True
        return self._join(chars, hot)

    @staticmethod
    def _join(chars, hot):
        out = []
        for ch, on in zip(chars, hot):
            out.append(PATH_COLOR + ch + RESET if on else ch)
        return "".join(out).rstrip()
