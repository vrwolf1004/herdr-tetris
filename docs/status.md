# Status

[**English**](status.md) | [한국어](status.ko.md)

## Status

**In progress.** The game and the herdr plugin work in unit tests. Several parts are not yet checked in a real terminal or in herdr (see [Unverified items](#unverified-items)).

## Features

Each feature cites the code that implements it. Line numbers are for the files as they are now.

### Screens

- The game starts on the monitor screen. `run` sets `in_monitor = True` (`src/tetris.py:276`).
- The monitor is a fake dashboard in English. The header and footer show host, region, version, and uptime. Services show bars, sparklines, and latency that keep moving. A dot chart shows throughput, and a white and gray log stream shows level, module, and message. The colors are only white and gray. It ends with a result area and a `$ ` command line (`src/monitor.py:308` render, `src/monitor.py:245` header, `src/monitor.py:303` footer). The monitor has no hint line. The switch key is listed on the game screen (`toggle_hint` in `src/locales/*.json`).
- `Ctrl+T` switches between the monitor and the game on either screen. It arrives as `\x14` and is mapped to `switch` (`src/tetris.py:33`). The switch is handled in `play` (`src/tetris.py:212`).
- While the monitor is shown, the game is frozen: gravity does not run and game keys are not applied (`src/tetris.py:198-201`, `src/tetris.py:223-228`).

### Command line

- On the monitor, typed characters go to the command line, not to the game (`src/tetris.py:223-228`). `Backspace` deletes the last character (`src/monitor.py:196`). The line holds at most 80 characters (`src/monitor.py:50`).
- `Enter` runs the line (`src/tetris.py:214-215`, `src/monitor.py:199`).
- Commands:
  - `help` lists the commands from `HELP_COMMANDS` (`src/monitor.py:65`, `src/monitor.py:221`).
  - `status` prints a made-up status line per service (`src/monitor.py:225`).
  - `logs` prints the last 8 log lines (`src/monitor.py:234`).
  - `clear` empties the result area (`src/monitor.py:238`).
  - `game` switches to the game screen. It is checked before the help list, so it is not listed there (`src/monitor.py:207-208`).
- Any other word prints `command not found` in English or `명령을 찾을 수 없습니다` in Korean (`src/monitor.py:199-216`, `src/locales/*.json` `not_found`).

### Game controls

Game key map: `src/tetris.py:42-55`. Arrow keys are read per platform (`src/tetris.py:39-40`, `src/tetris.py:126-135`, `src/tetris.py:149-162`).

| Action | Keys |
|---|---|
| Move | `A`/`D` or `←`/`→` |
| Rotate | `W` or `↑` |
| Soft drop | `S` or `↓` (+1 point per row) |
| Hard drop | `Space` (+2 points per row) |
| Pause | `P` |
| Restart after game over | `R` |
| Quit | `Q` (game screen only) |

### Quit

- `Q` quits on the game screen. On the monitor, `Q` is typed into the command line (`src/tetris.py:42-55`, `src/tetris.py:223-228`).
- `Ctrl+C` quits from either screen. On Windows it arrives as `\x03` and is mapped to `interrupt` (`src/tetris.py:36`). On POSIX it is a signal, caught in `main` (`src/tetris.py:279`).

### Run

```
python src/tetris.py
python src/tetris.py --lang ko
```

- Needs an interactive terminal. Otherwise it prints the `tty_required` message and exits with code 1 (`src/tetris.py:269-271`).
- `--lang auto|en|ko` (`src/tetris.py:261`). Priority: `--lang`, `HERDR_TETRIS_LANG`, `config.json`, system locale, English (`src/i18n.py:38`).

### herdr dock integration

- The manifest declares the plugin `herdr-tetris` with `start` and `stop` actions for each platform (`herdr-plugin.toml:1`, `:15`, `:22`, `:31`, `:38`). Windows action ids end with `-windows`.
- The dock registration key is `herdr-tetris` (`src/plugin.py:36`, `DOCK_KEY`). The marker file is `herdr-tetris.dock`.
- The agent id is `mon` and its display name is `mon` (`src/plugin.py:38`, `AGENT_ID`). `cmd_start` sets the dock title with `register_dock` (`src/plugin.py:108`).
- `cmd_start` allocates the dock pane and runs `host` in it (`src/plugin.py:104-114`). `cmd_host` reports the agent and its display name, then runs the game (`src/plugin.py:136-160`, `report_agent` at `:139`, `report_metadata` at `:145`).
- `cmd_stop` releases the agent, closes the pane (or the workspace if the dock is empty), and releases the dock allocation (`src/plugin.py:116-132`).

### Tests

64 tests run with `python -m unittest discover -s tests -v`. Their list is in [testing](testing.md).

## Unverified items

These are not checked yet. Each one is marked in the code or docs where it matters.

1. **Real key play.** The screen switch, the command line, and the game keys are tested by injecting keys into `play` (`tests/test_tetris_view.py:40`, `tests/test_tetris_view.py:81`). Nobody has played in a real terminal yet.
2. **herdr start/stop.** The dock logic is tested with mocks (`tests/test_plugin.py:54`, `tests/test_plugin.py:77`). `herdr-dock-grid` was detected, and its original `dock_layout.py` was loaded. `herdr-tetris` itself is not installed in herdr, so `start` and `stop` were not run inside herdr.
3. **macOS `Ctrl+T`.** On macOS, `Ctrl+T` may send `SIGINFO` and never reach the program. This is **inferred** from terminal defaults and was not checked (see [usage](usage.md#switching-screens)).
4. **Linux and macOS.** The termios path (`src/tetris.py:149-162`, `src/tetris.py:168-186`) and the ESC arrow-key parsing have not been run.
5. **Windows arrow keys.** The `msvcrt` arrow path (`src/tetris.py:126-135`) was not tested with real presses.

Related details are in [usage](usage.md#verification-status) and [testing](testing.md#not-covered).
