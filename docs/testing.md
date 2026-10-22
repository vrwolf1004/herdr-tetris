# Testing

[**English**](testing.md) | [한국어](testing.ko.md)

## Run

From the repository root:

```
python -m unittest discover -s tests -v
```

The `-s tests` option is needed. `tests/` has no `__init__.py`, so a bare `python -m unittest` from the root does not look there (**inferred**: not checked in this environment). Every test file adds `src/` to `sys.path` itself (`tests/test_game.py:6`, `tests/test_i18n.py:6`).

The last run in this environment: Python 3.12.10 on Windows 11, 74 tests, all passed.

## What is covered

### `tests/test_game.py` (12 tests)

- Rotation: four rotations return each piece to its starting shape (`tests/test_game.py:21`). T rotation has the expected cells (`tests/test_game.py:31-33`). A vertical I at the right wall kicks left when it rotates (`tests/test_game.py:35`).
- Movement: a move into the wall is refused (`tests/test_game.py:47`).
- Line clears: one line and two lines, with the expected points (`tests/test_game.py:63`, `tests/test_game.py:71`). Rows above a cleared line shift down (`tests/test_game.py:77`).
- Scoring and level: soft drop gives 1 point per row (`tests/test_game.py:86`). The level rises every 10 lines (`tests/test_game.py:92`).
- 7-bag: each set of seven draws contains all seven kinds (`tests/test_game.py:101`).
- Game over: a blocked spawn sets `game_over`, and actions are ignored afterwards (`tests/test_game.py:110`, `tests/test_game.py:119`).

### `tests/test_i18n.py` (13 tests)

- `en.json` and `ko.json` have the same keys and the same control line count (`tests/test_i18n.py:12`, `:17`).
- The `monitor` command strings have the same keys in both files (`tests/test_i18n.py:23`). The dashboard text is not in the language files (`tests/test_i18n.py:29`).
- System locale mapping: Windows Korean name, POSIX Korean, unsupported falls back to `en`, and a missing locale uses `LANG` (`tests/test_i18n.py:35`, `:39`, `:43`, `:47`).
- Priority: `--lang` beats the environment variable, the environment variable beats `config.json`, and `auto` or invalid values fall through to the system locale (`tests/test_i18n.py:59`, `:63`). The old `TETRIS_LANG` variable is ignored (`tests/test_i18n.py:69`). The config file beats the system locale (`tests/test_i18n.py:75`, `:81`).

### `tests/test_monitor.py` (27 tests)

- The header shows the host, region, version, clock, and uptime (`tests/test_monitor.py:42`). The footer repeats host, region, version, and uptime (`tests/test_monitor.py:54`).
- The dashboard stays English when the language is Korean (`tests/test_monitor.py:64`). Command responses follow the language (`tests/test_monitor.py:74`).
- No hint line is drawn (`tests/test_monitor.py:84`). Every service row is shown (`tests/test_monitor.py:88`).
- Every row fits the terminal width from 30 to 160 columns (`tests/test_monitor.py:93`). Wide rows show memory and latency, and narrow rows drop them (`tests/test_monitor.py:101`).
- A log row shows timestamp, level, module in brackets, and message (`tests/test_monitor.py:113`). Log levels use gray for INFO and bold white for WARN and ERROR, with the text label (`tests/test_monitor.py:122`). Only white and gray codes appear in the whole frame (`tests/test_monitor.py:140`).
- The chart row is drawn from the totals (`tests/test_monitor.py:148`).
- A step adds one log entry and changes the metrics (`tests/test_monitor.py:156`). The log history is bounded (`tests/test_monitor.py:163`). The dashboard shows the latest log line (`tests/test_monitor.py:169`).
- The frame height stays fixed, and the input line sits above the footer (`tests/test_monitor.py:175`).
- Typing and backspace edit the command line (`tests/test_monitor.py:183`). An empty submit does nothing (`tests/test_monitor.py:190`).
- An unknown word prints `command not found` (`tests/test_monitor.py:195`). `game` returns `game` and is not in `help` (`tests/test_monitor.py:201`).
- `status` lists every service with latency (`tests/test_monitor.py:209`). `logs` prints recent lines (`tests/test_monitor.py:216`). `clear` empties the output (`tests/test_monitor.py:224`).
- The output area shows only the latest lines (`tests/test_monitor.py:232`).
- `tick` waits for the step interval (`tests/test_monitor.py:240`). Metrics stay in their bounds over 1000 steps (`tests/test_monitor.py:248`).
- The monitor source does not import the game (`tests/test_monitor.py:258`).

### `tests/test_tetris_view.py` (13 tests)

Keys are injected into `tetris.play`, and `draw` is replaced by a recorder. Unless a test says otherwise, the key list is consumed in order and then `interrupt` ends the loop.

- The game starts on the monitor, and `Ctrl+T` (`switch`) opens the game (`tests/test_tetris_view.py:40`).
- `Ctrl+T` again returns to the monitor (`tests/test_tetris_view.py:47`).
- Letters, digits, and space are typed into the command line on the monitor, and the game does not move (`tests/test_tetris_view.py:51`).
- The game screen shows the `Ctrl+T: switch` hint (`tests/test_tetris_view.py:57`).
- `Ctrl+T` in the game returns to the monitor, and the game stays frozen (`tests/test_tetris_view.py:61`).
- `q` is typed on the monitor, and `interrupt` (Ctrl+C) quits (`tests/test_tetris_view.py:66`). `Q` quits on the game screen (`tests/test_tetris_view.py:71`).
- `SPECIAL_KEYS` maps `\x14` to `switch`, and Tab is not mapped (`tests/test_tetris_view.py:75`).
- Typing `game` and pressing Enter opens the game (`tests/test_tetris_view.py:81`). An unknown word prints `command not found` (`tests/test_tetris_view.py:85`). `help` lists the commands without `game` (`tests/test_tetris_view.py:89`).
- Backspace edits the command line (`tests/test_tetris_view.py:95`). `clear` empties the output (`tests/test_tetris_view.py:99`).

### `tests/test_plugin.py` (9 tests)

- Manifest: id, minimum herdr version, platforms, unique action ids, `start` / `stop` for each platform, and the right interpreter per OS (`tests/test_plugin.py:19`, `:24`, `:28`, `:35`).
- Dock start: does not relaunch while the game is running (`tests/test_plugin.py:54`). Otherwise sets the dock title to `mon`, allocates the dock pane under the key `herdr-tetris`, and runs `host` in it (`tests/test_plugin.py:64`).
- Dock stop: closes only its own pane when other blocks share the dock (`tests/test_plugin.py:77`). Closes the workspace when the dock is empty (`tests/test_plugin.py:97`).
- The dock key is `herdr-tetris` and the agent display name is `mon` (`tests/test_plugin.py:113`).

## Not covered

- Real key reading in a terminal (`src/tetris.py`: `_read_key_windows`, `_read_key_posix`) and the terminal raw mode. Only the screen flow with injected keys is covered.
- Platform key input: the Windows and POSIX readers are not tested. Whether `Ctrl+T` reaches the program on each platform is not tested.
- The actual terminal width. The tests pass widths explicitly, and the default path uses `shutil.get_terminal_size`, which is not tested.
- Gravity timing and pause behavior, except through the screen-switch tests.
- The herdr side of the plugin: the real dock pane, agent registration in herdr, and `pane run`. The tests mock the herdr CLI and socket calls.

## Manual check

```
python src/tetris.py
python src/tetris.py --lang ko
```

Watch the monitor, type `help` and `status` on the command line, then type `game` to open the game. Play a few moves, press `Ctrl+T` to go back, and check that the game is frozen while the monitor is shown. Also try pause, quit, and restart after game over.
