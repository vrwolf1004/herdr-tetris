# Usage and controls

[**English**](usage.md) | [한국어](usage.ko.md)

## Run

```
python src/tetris.py
```

Run from the repository root. The game needs an interactive terminal: if stdin is not a TTY, it prints the `tty_required` message and exits with code 1 (`src/tetris.py:269-271`).

The first screen is a fake system monitor (`src/monitor.py`), not the game. Its header shows the host, region, version, clock, and uptime. Below it, each service shows CPU, memory, p95 latency, and requests per second, with bars and sparklines that keep moving. A dot chart shows total throughput, and a log stream shows timestamp, level, module, and message in white and gray. INFO is gray, and WARN and ERROR are bold white, with the text label. A command result area and a `$ ` command line sit at the bottom, and a footer repeats the host, region, version, and uptime. The dashboard text is always in English. Only command responses follow the language setting. The screen has no hint line; the switch key is listed on the game screen. Roughly:

```
 SYSTEM MONITOR  host ops-node-07  region ap-northeast-2  v4.2.1     07:13:20  UP 00:12:04
 ---------------------------------------------------------------------------------------------
 SERVICE        CPU        MEM     P95    RPS
 gateway        cpu [##..........]  21%  :-:---------:.::  mem  20%  p95   15ms  rps   70
 ...
 rps #%@@%%%%@%%@@%%%
 ---------------------------------------------------------------------------------------------
 RECENT EVENTS
 07:13:32  WARN   [config.loader]  orders-db configuration reloaded revision=54
 07:13:33  ERROR  [db.pool]        cache-redis slow query detected duration=435ms

 help    show this list
 status  show service status

$ _
 ops-node-07 | ap-northeast-2 | v4.2.1 | up 00:12:04 | 6 services | 16 events
```

## Switching screens

- `Ctrl+T` switches between the monitor and the game, on either screen.
- While the monitor is shown, the game is frozen. Game keys do nothing.
- `Ctrl+T` is handled as `switch` in the key reader (`src/tetris.py:30-38`). `Ctrl+T` arrives as the character `\x14` on Windows (`src/tetris.py:33`).
- `Enter` submits the command line on the monitor. On the game screen it does nothing.
- Tab is not used.

## Command line

Type a command on the `$ ` line and press `Enter`. Keys typed on the monitor go to the command line, not to the game. `Backspace` deletes the last character.

| Command | What it does |
|---|---|
| `help` | Lists the commands below. |
| `status` | Prints a made-up status line for each service. |
| `logs` | Prints the last 8 log lines. |
| `clear` | Clears the command result area. |
| `game` | Switches to the game screen. Not listed in `help`. |

Any other word prints `<word>: command not found` (English) or `<word>: 명령을 찾을 수 없습니다` (Korean). Commands are matched by the first word, and extra words are ignored (`src/monitor.py:199-216`).

The `help` list comes from `HELP_COMMANDS` (`src/monitor.py:65`). The `game` command is handled before the list lookup, so it never appears there (`src/monitor.py:207-208`).

The command line shows at most 80 characters (`src/monitor.py:50`).

## Language

The language is chosen in this order, highest priority first:

1. `--lang auto|en|ko|ja|de|es|fr|ru` (`src/tetris.py:416-420`)
2. `HERDR_TETRIS_LANG` environment variable (`src/i18n.py:49`). The old `TETRIS_LANG` is no longer read.
3. `language` in `config.json` at the repository root (`src/i18n.py:30-35`, `config.json`)
4. System locale: if it is one of the supported languages, that language (`src/i18n.py:18-41`)
5. Fallback `en` (`src/i18n.py:15`)

`auto` means "not set", so the next source is checked. Values that are not supported languages are ignored in the environment variable and `config.json`.

Screen strings live in `src/locales/<language>.json`, one file per language. Every file must have every key from `en.json`, including the `monitor` block with the prompt, command descriptions, command responses, and log templates. The keys are checked by `tests/test_locales.py` and `tests/test_i18n.py`.

The `--help` text is English only (`src/tetris.py:416-420`).

## Other games

On the game screen, keys `1`–`4` pick a game: `1` Tetris, `2` Ladder, `3` Snake, `4` Minesweeper (`src/tetris.py:213-214`). While a game is in progress, the number keys are ignored, so the current game is not thrown away. Once that game has ended, a number key switches to its game and starts it fresh. "In progress" means: Tetris is not game over; Snake is playing; Minesweeper is playing and its first cell has been opened; Ladder is always treated as finished. Snake's best score is remembered only while the program runs and is not saved. This guide describes only Tetris. The controls and rules of the other three games are in their source files (`src/ladder.py`, `src/snake.py`, `src/minesweeper.py`) and are not yet documented here.

## Controls

Game screen:

| Action | Keys |
|---|---|
| Switch to the monitor | `Ctrl+T` |
| Move left | `A` or `←` |
| Move right | `D` or `→` |
| Soft drop (+1 point per row) | `S` or `↓` |
| Rotate clockwise | `W` or `↑` |
| Hard drop (+2 points per row, locks at once) | `Space` |
| Pause / resume | `P` |
| Quit | `Q` |
| Restart (only after game over) | `R` |

Monitor screen:

| Action | Keys |
|---|---|
| Switch to the game | `Ctrl+T` or the `game` command |
| Run the command line | `Enter` |
| Edit the command line | letters, digits, `Backspace` |
| Quit | `Ctrl+C` |

Game letter keys are case-insensitive. The game key map is in `src/tetris.py:42-55`. Arrow keys map to game actions there too.

Quit with `Q` works only on the game screen, because letters typed on the monitor go to the command line. `Ctrl+C` quits from either screen.

Arrow keys are read differently per platform. Windows uses `msvcrt` codes (`src/tetris.py:39`, `src/tetris.py:126-135`). Other platforms read ESC sequences (`src/tetris.py:40`, `src/tetris.py:149-162`). The Windows path was not tested with real key presses in this environment. The ESC path has not been run at all.

On macOS, `Ctrl+T` sends `SIGINFO` by default, which may not reach the program. This is not verified here (**inferred** from terminal defaults).

## Game over

When a new piece cannot appear at the top, the screen shows `GAME OVER - R: restart, Q: quit` (`src/tetris.py:89-90`). `R` starts a new game and `Q` exits (`src/tetris.py:233-236`). A new game after `R` opens directly on the game screen.

## herdr plugin (dock)

The repository is also a herdr plugin (`herdr-plugin.toml`). Its actions run `src/plugin.py`:

| Action | Linux/macOS id | Windows id | Command |
|---|---|---|---|
| Start the game in the dock | `start` | `start-windows` | `src/plugin.py start` |
| Stop the game and hide the dock pane | `stop` | `stop-windows` | `src/plugin.py stop` |

- `start` takes a pane from the shared `herdr-dock` workspace and runs the game in it. If the game is already running, it does nothing. If the host process was killed and left a marker behind, `start` ignores that marker and starts the game again.
- The dock registration key is `herdr-tetris` (`DOCK_KEY`), so the dock marker file is `herdr-tetris.dock`. `start` sets the dock title to `mon` with `register_dock`.
- The plugin registers a fake agent with the id `mon` (`AGENT_ID`) and sets its display name to `mon` (`src/plugin.py`).
- `stop` closes the game pane, which stops the game. It removes the agent registration and releases the dock pane. If the dock has no other blocks, it closes the whole workspace.
- The dock layout comes from the installed `herdr-dock-grid` when present. Otherwise it uses the copy in `src/dock_layout.py`. Both `src/dock_layout.py` and `src/herdr_api.py` are copies of the herdr-dock-grid files.

Windows uses `python` and the other platforms use `python3 -X utf8`, following the timekit manifest.

## Verification status

- Checked on Windows 11 with Python 3.12.10: the game starts and redraws frames, and it was stopped by a timeout. This was a smoke run, not manual play.
- The monitor, command line, and screen switch are checked by unit tests that inject keys (`tests/test_tetris_view.py`, `tests/test_monitor.py`). Real key presses were not checked.
- The herdr plugin files are checked by unit tests (`tests/test_plugin.py`). With herdr 0.9.4 installed here, `herdr-dock-grid` is detected and its dock layout is loaded. `herdr-tetris` itself is not installed in herdr, so the start/stop actions were not run inside herdr.
- Not checked: pressing keys to play in a real terminal, macOS and Linux (termios path), the dock pane flow inside herdr, and whether `Ctrl+T` reaches the program on each platform.
