"""테트리스 규칙과 상태. 입출력이 없어서 단위 테스트로 바로 검증할 수 있다."""

import random

WIDTH = 10
HEIGHT = 20
SPAWN_COL = 3
LINES_PER_LEVEL = 10
# 한 번에 지운 줄 수(0~4)별 기본 점수. 실제 점수는 레벨을 곱한다.
LINE_SCORES = (0, 100, 300, 500, 800)
# 회전 시 막히면 좌우로 밀어서 다시 시도한다(벽 킥).
KICK_OFFSETS = (0, -1, 1, -2, 2)

# 블록 기본 형태. (row, col) 좌표이고 회전 상태 0을 기준으로 한다.
BASE_SHAPES = {
    "I": [(0, 0), (0, 1), (0, 2), (0, 3)],
    "O": [(0, 0), (0, 1), (1, 0), (1, 1)],
    "T": [(0, 0), (0, 1), (0, 2), (1, 1)],
    "S": [(0, 1), (0, 2), (1, 0), (1, 1)],
    "Z": [(0, 0), (0, 1), (1, 1), (1, 2)],
    "J": [(0, 0), (1, 0), (1, 1), (1, 2)],
    "L": [(0, 2), (1, 0), (1, 1), (1, 2)],
}
KINDS = tuple(BASE_SHAPES)


def _normalize(cells):
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _rotate_cw(cells):
    # 화면 좌표(행은 아래로, 열은 오른쪽으로) 기준 시계 방향 90도 회전.
    return _normalize([(c, -r) for r, c in cells])


def _build_rotations(cells):
    states = [_normalize(cells)]
    for _ in range(3):
        states.append(_rotate_cw(states[-1]))
    return tuple(states)


ROTATIONS = {kind: _build_rotations(cells) for kind, cells in BASE_SHAPES.items()}


def cells_at(kind, rotation, row, col):
    return [(row + r, col + c) for r, c in ROTATIONS[kind][rotation]]


class Game:
    def __init__(self, rng=None):
        self._rng = rng or random.Random()
        self.board = [[None] * WIDTH for _ in range(HEIGHT)]
        self.score = 0
        self.lines = 0
        self.game_over = False
        self._bag = []
        self.next_kind = self._draw_kind()
        self.kind = None
        self.rotation = 0
        self.row = 0
        self.col = SPAWN_COL
        self._spawn()

    @property
    def level(self):
        return self.lines // LINES_PER_LEVEL + 1

    def active_cells(self):
        return cells_at(self.kind, self.rotation, self.row, self.col)

    def move(self, dcol):
        if self.game_over or not self._fits(self.rotation, self.row, self.col + dcol):
            return False
        self.col += dcol
        return True

    def rotate(self):
        if self.game_over:
            return False
        new_rotation = (self.rotation + 1) % 4
        for offset in KICK_OFFSETS:
            if self._fits(new_rotation, self.row, self.col + offset):
                self.rotation = new_rotation
                self.col += offset
                return True
        return False

    def tick(self):
        """중력으로 한 칸 내린다. 더 내려갈 수 없으면 고정한다."""
        if not self.game_over and not self._try_down():
            self._lock()

    def soft_drop(self):
        if self.game_over:
            return
        if self._try_down():
            self.score += 1
        else:
            self._lock()

    def hard_drop(self):
        if self.game_over:
            return
        distance = 0
        while self._try_down():
            distance += 1
        self.score += 2 * distance
        self._lock()

    def _draw_kind(self):
        # 7-bag 방식: 7종을 모두 한 번씩 뽑은 뒤 다시 섞는다.
        if not self._bag:
            self._bag = list(KINDS)
            self._rng.shuffle(self._bag)
        return self._bag.pop()

    def _fits(self, rotation, row, col):
        for r, c in cells_at(self.kind, rotation, row, col):
            if not (0 <= r < HEIGHT and 0 <= c < WIDTH):
                return False
            if self.board[r][c] is not None:
                return False
        return True

    def _try_down(self):
        if self._fits(self.rotation, self.row + 1, self.col):
            self.row += 1
            return True
        return False

    def _spawn(self):
        self.kind = self.next_kind
        self.next_kind = self._draw_kind()
        self.rotation = 0
        self.row = 0
        self.col = SPAWN_COL
        if not self._fits(self.rotation, self.row, self.col):
            self.game_over = True

    def _lock(self):
        for r, c in self.active_cells():
            self.board[r][c] = self.kind
        cleared = self._clear_lines()
        if cleared:
            self.score += LINE_SCORES[cleared] * self.level
            self.lines += cleared
        self._spawn()

    def _clear_lines(self):
        kept = [row for row in self.board if any(cell is None for cell in row)]
        cleared = HEIGHT - len(kept)
        if cleared:
            self.board = [[None] * WIDTH for _ in range(cleared)] + kept
        return cleared
