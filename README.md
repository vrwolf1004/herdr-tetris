# herdr-tetris

[**English**](README.md) | [한국어](README.ko.md)

Languages: English (default) · Korean

A terminal Tetris game for herdr's shared `herdr-dock` workspace. It opens on a fake system monitor, and `Ctrl+T` switches to the game.

## Installation

From GitHub:

```sh
herdr plugin install vrwolf1004/herdr-tetris
```

From a local checkout:

```sh
herdr plugin link /path/to/herdr-tetris
```

## Actions

| Action | What it does | Linux / macOS | Windows |
| --- | --- | --- | --- |
| `start` | Run the game in a pane of the shared `herdr-dock` workspace | `start` | `start-windows` |
| `stop` | Stop the game and close its dock pane | `stop` | `stop-windows` |

Commands behind the actions:

- Linux / macOS: `python3 -X utf8 src/plugin.py start` and `... stop`
- Windows: `python -X utf8 src/plugin.py start` and `... stop`

On Windows, use the `-windows` action IDs:

```sh
herdr plugin action invoke start-windows --plugin herdr-tetris
```

Without herdr, run the game directly from the repository root with `python src/tetris.py`.

## Language

- The language is chosen in this order: `--lang auto|en|ko`, the `HERDR_TETRIS_LANG` environment variable, `language` in the repository's `config.json`, the system locale (Korean if the system is Korean, otherwise English), and English.
- The monitor screen's dashboard text is always English. Command responses (`help`, `status`, and others) and the game screen follow the chosen language.
- The environment variable follows the `HERDR_<NAME>_LANG` form used by other plugins. The older `TETRIS_LANG` is no longer read.

## Requirements

- herdr 0.9.0 or later
- Windows, Linux, or macOS
- Python 3 with the standard library only (no packages to install). The tests need Python 3.11 or later because they read the manifest with `tomllib`. The game was run on Python 3.12.10.

## Documentation

- [Status](docs/status.md)
- [Usage (English)](docs/usage.md)
- [사용법 (한국어)](docs/usage.ko.md)
- [Project structure (English)](docs/structure.md)
- [프로젝트 구조 (한국어)](docs/structure.ko.md)
- [Game rules (English)](docs/rules.md)
- [게임 규칙 (한국어)](docs/rules.ko.md)
- [Testing (English)](docs/testing.md)
- [테스트 (한국어)](docs/testing.ko.md)

## Support the project

If this project is useful to you, consider buying the developer a coffee.

[![Support on Ko-fi](https://img.shields.io/badge/Ko--fi-Support-FF5E5B?style=for-the-badge&logo=buymeacoffee&logoColor=white)](https://ko-fi.com/dev_ohyt)
