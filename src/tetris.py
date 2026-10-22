"""터미널에서 실행하는 테트리스. 실행: python src/tetris.py [--lang auto|en|ko]

게임 규칙은 game.py에 있고, 여기서는 화면 출력과 키 입력만 다룬다.
처음 보이는 화면은 monitor.py 의 모니터링 화면이고, Ctrl+T 로 게임과 오간다.
화면 문자열은 locales/ 아래 언어 파일에서 읽는다(i18n.py 참고).
Windows(msvcrt)와 macOS/Linux(termios)를 모두 지원하며 표준 라이브러리만 쓴다.
"""

import argparse
import os
import sys
import time

from game import HEIGHT, WIDTH, ROTATIONS, Game
from i18n import load_strings, resolve_language
from monitor import Monitor

if os.name == "nt":
    import msvcrt
else:
    import select
    import termios
    import tty

ANSI_COLORS = {"I": 36, "O": 33, "T": 35, "S": 32, "Z": 31, "J": 34, "L": 37}
EMPTY_CELL = " ."
BLOCK_CELL = "[]"

# 특수 키는 이름으로 바꾼다. 나머지는 입력한 글자 그대로 돌려준다(대소문자 유지).
SPECIAL_KEYS = {
    "\r": "enter",
    "\n": "enter",
    "\x14": "switch",  # Ctrl+T: 게임과 모니터 전환
    "\x08": "backspace",
    "\x7f": "backspace",
    "\x03": "interrupt",  # Windows 에서 Ctrl+C 가 글자로 들어올 때
}
# 방향키: Windows 콘솔은 0x00/0xE0 뒤에 코드, 그 외 터미널은 ESC [ 뒤에 문자가 온다.
WIN_ARROW_KEYS = {"H": "up", "P": "down", "K": "left", "M": "right"}
ANSI_ARROW_KEYS = {"A": "up", "B": "down", "C": "right", "D": "left"}
# 게임 화면에서 키를 게임 동작으로 바꾼다. 방향키와 WASD 를 같이 쓴다.
GAME_ACTIONS = {
    "a": "left",
    "left": "left",
    "d": "right",
    "right": "right",
    "s": "down",
    "down": "down",
    "w": "rotate",
    "up": "rotate",
    " ": "drop",
    "p": "pause",
    "q": "quit",
    "r": "restart",
}


def fall_interval(level):
    # 레벨이 오를수록 빨라지고, 최소 0.05초 간격을 유지한다.
    return max(0.05, 0.8 - 0.07 * (level - 1))


def _cell(kind):
    if kind is None:
        return EMPTY_CELL
    return f"\x1b[{ANSI_COLORS[kind]}m{BLOCK_CELL}\x1b[0m"


def _preview_lines(kind):
    cells = set(ROTATIONS[kind][0])
    return [
        "".join(_cell(kind if (r, c) in cells else None) for c in range(4))
        for r in range(2)
    ]


def render(game, strings, paused=False):
    active = set(game.active_cells()) if not game.game_over else set()
    lines = []
    for r in range(HEIGHT):
        row = ""
        for c in range(WIDTH):
            kind = game.board[r][c]
            if kind is None and (r, c) in active:
                kind = game.kind
            row += _cell(kind)
        lines.append("|" + row + "|")

    if game.game_over:
        status = strings["status_game_over"]
    elif paused:
        status = strings["status_paused"]
    else:
        status = ""

    panel = [
        strings["title"],
        "",
        f"{strings['score']}  {game.score}",
        f"{strings['lines']}  {game.lines}",
        f"{strings['level']}  {game.level}",
        "",
        strings["next"],
        *_preview_lines(game.next_kind),
        "",
        *strings["controls"],
        strings["toggle_hint"],
        "",
        status,
    ]

    width = WIDTH * 2 + 2
    out = []
    for i in range(max(len(lines), len(panel))):
        left = lines[i] if i < len(lines) else " " * width
        right = panel[i] if i < len(panel) else ""
        out.append(left + "  " + right)
    return out


def draw(lines):
    sys.stdout.write("\x1b[H" + "".join(line + "\x1b[K\n" for line in lines) + "\x1b[J")
    sys.stdout.flush()


def _read_key_windows(timeout):
    deadline = time.monotonic() + timeout
    while not msvcrt.kbhit():
        if time.monotonic() >= deadline:
            return None
        time.sleep(0.01)
    ch = msvcrt.getwch()
    if ch in ("\x00", "\xe0"):
        return WIN_ARROW_KEYS.get(msvcrt.getwch())
    return SPECIAL_KEYS.get(ch, ch)


def _read_char_posix(fd):
    # UTF-8 글자는 여러 바이트일 수 있으므로 첫 바이트를 보고 나머지를 읽는다.
    first = os.read(fd, 1)
    if not first:
        return ""
    lead = first[0]
    extra = 3 if lead >= 0xF0 else 2 if lead >= 0xE0 else 1 if lead >= 0xC0 else 0
    rest = os.read(fd, extra) if extra else b""
    return (first + rest).decode("utf-8", errors="ignore")


def _read_key_posix(timeout):
    fd = sys.stdin.fileno()
    if not select.select([fd], [], [], timeout)[0]:
        return None
    ch = _read_char_posix(fd)
    if ch == "\x1b":
        if select.select([fd], [], [], 0.01)[0]:
            seq = os.read(fd, 2).decode(errors="ignore")
            if seq.startswith("["):
                return ANSI_ARROW_KEYS.get(seq[1:])
        return None
    if not ch:
        return None
    return SPECIAL_KEYS.get(ch, ch)


read_key = _read_key_windows if os.name == "nt" else _read_key_posix


class TerminalMode:
    """게임 중에는 커서를 숨기고, 끝나면 터미널 상태를 원래대로 되돌린다."""

    def __enter__(self):
        if os.name == "nt":
            os.system("")  # 콘솔에서 ANSI 이스케이프 처리를 켜는 관용 트릭
        else:
            self.fd = sys.stdin.fileno()
            self.saved = termios.tcgetattr(self.fd)
            tty.setcbreak(self.fd)
        sys.stdout.write("\x1b[2J\x1b[?25l")
        sys.stdout.flush()
        return self

    def __exit__(self, *exc):
        if os.name != "nt":
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.saved)
        sys.stdout.write("\x1b[?25h\x1b[0m\n")
        sys.stdout.flush()


def play(game, strings, monitor, in_monitor):
    """한 판을 진행한다. 'restart' 또는 'quit'을 반환한다.

    in_monitor 가 True 면 모니터링 화면을 보여 주고 게임은 멈춰 둔다.
    Ctrl+T 로 화면을 바꾸고, 모니터에서는 Enter 로 입력줄을 실행한다. game 명령도 게임 화면으로 간다.
    """
    paused = False
    next_fall = time.monotonic() + fall_interval(game.level)
    while True:
        if in_monitor:
            monitor.tick(time.time())
            draw(monitor.render())
            wait = 0.1
        else:
            draw(render(game, strings, paused))
            if game.game_over or paused:
                wait = 0.1
            else:
                wait = max(0.0, min(0.1, next_fall - time.monotonic()))
        key = read_key(wait)

        if key == "interrupt":
            return "quit"
        if key == "switch":
            switch = True
        elif in_monitor and key == "enter":
            switch = monitor.submit() == "game"
        else:
            switch = False
        if switch:
            in_monitor = not in_monitor
            next_fall = time.monotonic() + fall_interval(game.level)
            continue

        if in_monitor:
            if key == "backspace":
                monitor.backspace()
            elif key and len(key) == 1 and key.isprintable():
                monitor.type_char(key)
            continue

        action = GAME_ACTIONS.get(key.lower()) if key else None
        if action == "quit":
            return "quit"
        if game.game_over:
            if action == "restart":
                return "restart"
            continue
        if action == "pause":
            paused = not paused
            next_fall = time.monotonic() + fall_interval(game.level)
        elif paused:
            continue
        elif action == "left":
            game.move(-1)
        elif action == "right":
            game.move(1)
        elif action == "rotate":
            game.rotate()
        elif action == "down":
            game.soft_drop()
        elif action == "drop":
            game.hard_drop()

        if not paused and time.monotonic() >= next_fall:
            game.tick()
            next_fall = time.monotonic() + fall_interval(game.level)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Terminal Tetris")
    parser.add_argument(
        "--lang",
        choices=("auto", "en", "ko"),
        default="auto",
        help="display language (default: auto; overrides HERDR_TETRIS_LANG and config.json)",
    )
    args = parser.parse_args(argv)
    strings = load_strings(resolve_language(args.lang))

    if not sys.stdin.isatty():
        print(strings["tty_required"])
        return 1
    monitor = Monitor(strings["monitor"])
    try:
        with TerminalMode():
            # 처음에는 모니터링 화면을 보여 준다. 다시 시작한 판은 바로 게임 화면으로 간다.
            in_monitor = True
            while play(Game(), strings, monitor, in_monitor) == "restart":
                in_monitor = False
    except KeyboardInterrupt:
        pass  # POSIX 에서 Ctrl+C 는 글자가 아니라 신호로 들어온다. 터미널은 이미 복구됐다.
    return 0


if __name__ == "__main__":
    sys.exit(main())
