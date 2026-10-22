# herdr-tetris

[English](README.md) | [**한국어**](README.ko.md)

지원 언어: 영어(기본) · 한국어

herdr 공유 `herdr-dock` workspace에서 도는 터미널 테트리스입니다. 가짜 시스템 모니터 화면으로 시작하고, `Ctrl+T`로 게임 화면을 엽니다.

## Installation

GitHub에서 설치:

```sh
herdr plugin install vrwolf1004/herdr-tetris
```

로컬 체크아웃에서 연결:

```sh
herdr plugin link /path/to/herdr-tetris
```

## Actions

| 액션 | 하는 일 | Linux / macOS | Windows |
| --- | --- | --- | --- |
| `start` | 공유 `herdr-dock` workspace의 pane에서 게임 실행 | `start` | `start-windows` |
| `stop` | 게임을 멈추고 dock pane 닫기 | `stop` | `stop-windows` |

액션 뒤의 명령:

- Linux / macOS: `python3 -X utf8 src/plugin.py start`, `... stop`
- Windows: `python -X utf8 src/plugin.py start`, `... stop`

Windows에서는 `-windows` 액션 id를 씁니다:

```sh
herdr plugin action invoke start-windows --plugin herdr-tetris
```

herdr 없이 실행하려면 저장소 루트에서 `python src/tetris.py`를 실행합니다.

## Language

- 언어는 다음 순서로 정합니다. `--lang auto|en|ko`, `HERDR_TETRIS_LANG` 환경 변수, 저장소의 `config.json`에 있는 `language`, 시스템 로케일(한국어 시스템이면 한국어, 그 밖이면 영어), 영어.
- 모니터 화면의 대시보드 문구는 항상 영어입니다. 명령 응답(`help`, `status` 등)과 게임 화면은 고른 언어를 따릅니다.
- 환경 변수는 다른 플러그인과 같은 `HERDR_<NAME>_LANG` 형식입니다. 예전 `TETRIS_LANG`은 더 이상 읽지 않습니다.

## Requirements

- herdr 0.9.0 이상
- Windows, Linux, macOS
- 표준 라이브러리만 쓰는 Python 3(설치할 패키지 없음). 테스트는 매니페스트를 `tomllib`으로 읽으므로 Python 3.11 이상이 필요합니다. 게임은 Python 3.12.10에서 실행했습니다.

## Documentation

- [상태](docs/status.ko.md)
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
