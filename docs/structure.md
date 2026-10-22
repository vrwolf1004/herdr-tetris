# Project structure

[**English**](structure.md) | [한국어](structure.ko.md)

```
herdr-tetris/
├── README.md, README.ko.md   entry points (English default, Korean)
├── herdr-plugin.toml         herdr plugin manifest: start / stop actions
├── config.json               language setting: "auto" | "en" | "ko"
├── src/
│   ├── game.py               rules and state, no I/O
│   ├── tetris.py             terminal UI: rendering, keys, screen switch, main loop, --lang
│   ├── monitor.py            startup monitor screen, command line, no game rules
│   ├── plugin.py             herdr entry point: start / stop / host (dock pane, agent "mon")
│   ├── i18n.py               language resolution and string loading
│   ├── dock_layout.py        copy of herdr-dock-grid's dock layout module
│   ├── herdr_api.py          copy of herdr-dock-grid's herdr CLI/socket wrapper
│   └── locales/
│       ├── en.json           English strings (including the monitor block)
│       └── ko.json           Korean strings (including the monitor block)
├── tests/
│   ├── test_game.py          rule tests (12)
│   ├── test_i18n.py          language resolution and locale key match (13)
│   ├── test_monitor.py       monitor rendering, command line, metrics (27)
│   ├── test_tetris_view.py   screen switch and command line with injected keys (13)
│   └── test_plugin.py        manifest, dock start / stop, agent key (9)
├── docs/                     this documentation (English + Korean pairs)
└── .gitignore
```

## Files

### `src/game.py`

Game rules and state. It has no I/O, so it can be tested directly.

- Constants: board size, spawn column, scoring table, kick offsets, piece shapes (`src/game.py:5-24`)
- Rotation: coordinate transform and four precomputed states (`src/game.py:27-45`)
- `cells_at`: absolute cells of a piece (`src/game.py:48-49`)
- `Game`: state and actions (`src/game.py:52` onward)
  - `move`, `rotate` (with kicks), `tick`, `soft_drop`, `hard_drop`
  - `_draw_kind` (7-bag), `_fits`, `_spawn`, `_lock`, `_clear_lines`

### `src/tetris.py`

Terminal UI and game entry point.

- Colors (`src/tetris.py:25`), special keys (`src/tetris.py:30-37`: Enter, Ctrl+T as `switch`, Backspace, Ctrl+C as `interrupt`), arrow maps (`src/tetris.py:39-40`), game key map (`src/tetris.py:42-55`)
- `fall_interval`: gravity speed by level (`src/tetris.py:58-60`)
- `render`: board and side panel to a list of lines (`src/tetris.py:77`)
- `draw`: cursor home and redraw (`src/tetris.py:121`)
- `_read_key_windows`, `_read_key_posix`: platform key input. They return a key name, or the typed character as it is (`src/tetris.py:126`, `src/tetris.py:149`)
- `TerminalMode`: hides the cursor, enables raw/cbreak input, restores on exit (`src/tetris.py:168`)
- `play`: loop for one screen session. Shows the monitor or the game, switches on `switch` (Ctrl+T), sends typed keys to the command line on the monitor, returns `restart` or `quit` (`src/tetris.py:189`)
- `main`: parses `--lang`, checks TTY, starts on the monitor, then runs games. Catches Ctrl+C (`src/tetris.py:258`)

### `src/monitor.py`

Startup monitor screen and its command line. It has no dependency on `game.py`.

- `Monitor`: service metrics, log history, the input line (`buffer`), and command results (`output`)
- `type_char`, `backspace`: edit the input line (`src/monitor.py:192-197`)
- `submit`: runs the input line. Returns `game` for the `game` command, which is checked before the help list (`src/monitor.py:199-216`)
- Commands: `help`, `status`, `logs`, `clear` (`src/monitor.py:221-240`). `HELP_COMMANDS` is the list that `help` prints (`src/monitor.py:65`)
- `tick`: runs a step every `STEP_SECONDS`. `render` returns the header, the service table, the throughput dot chart, the log stream, the output area, the `$ ` input line, and the footer (`src/monitor.py:308`)
- Drawing helpers: `_header`, `_service_row` (drops fields when the terminal is narrow), `_chart_row`, `_log_row` (gray and bold-white levels), `_footer` (`src/monitor.py:245`, `src/monitor.py:260`, `src/monitor.py:282`, `src/monitor.py:294`, `src/monitor.py:303`)
- Dashboard text is fixed English in `monitor.py` (`TITLE`, `LOG_TEMPLATES`, `LEVEL_LABELS`). Only command responses come from the locale files
- Time and random numbers are passed in, so tests can fix them

### `src/plugin.py`

herdr entry point. It connects the game to the shared dock.

- `start`: allocates the dock pane, then runs `host` in it. Does nothing if the game is already running (`cmd_start`)
- `stop`: releases the agent, closes the pane (or the workspace if the dock is empty), releases the dock allocation (`cmd_stop`)
- `host`: registers the agent, keeps the dock at the bottom, runs `tetris.main`, and releases the agent on exit (`cmd_host`)
- `load_dock_layout`: uses the installed `herdr-dock-grid` if present, otherwise `src/dock_layout.py` (`src/plugin.py`, `load_dock_layout`)
- `DOCK_KEY = "herdr-tetris"`: the dock registration key, which gives the marker file `herdr-tetris.dock`. `AGENT_ID = "mon"`: the agent display name (`src/plugin.py`)

### `src/dock_layout.py`, `src/herdr_api.py`

Copies of the herdr-dock-grid files, identical to the originals at the time of copying. `dock_layout` owns dock allocation and release. `herdr_api` wraps the herdr CLI and socket.

### `src/i18n.py`

Language selection and string loading.

- `system_language`: maps the OS locale to `ko` or `en` (`src/i18n.py:18`)
- `_config_language`: reads `language` from `config.json` (`src/i18n.py:30`)
- `resolve_language`: applies the priority order (`src/i18n.py:38`)
- `load_strings`: loads `src/locales/<lang>.json` (`src/i18n.py:45`)

### `src/locales/*.json`

Screen strings: title, labels, control help, the switch hint (`toggle_hint`), status messages, TTY message, and the `monitor` block. The `monitor` block holds only the command responses: input prompt (`prompt`), help descriptions (`command_help`), and responses (`not_found`, `status_title`, `status_line`, `state_ok`, `state_warn`). Keys must match between `en.json` and `ko.json`.

### `herdr-plugin.toml`

Declares the plugin for herdr: id, version, platforms, and the `start` / `stop` actions. Windows action ids end with `-windows`. See [usage](usage.md#herdr-plugin-dock).

### `tests/`

See [testing](testing.md).

### `config.json`

One key: `language`. Default `"auto"`. Used as priority 3 in [usage](usage.md#language).
