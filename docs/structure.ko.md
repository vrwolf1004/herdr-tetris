# 프로젝트 구조

[English](structure.md) | [**한국어**](structure.ko.md)

```
herdr-tetris/
├── README.md, README.ko.md   진입 문서(기본 영어, 한국어)
├── herdr-plugin.toml         herdr 플러그인 매니페스트: start / stop 액션
├── config.json               언어 설정: "auto" | "en" | "ko"
├── src/
│   ├── game.py               규칙과 상태, 입출력 없음
│   ├── tetris.py             터미널 UI: 렌더링, 키 입력, 화면 전환, 메인 루프, --lang
│   ├── monitor.py            시작할 때 보이는 모니터 화면과 명령 입력줄, 게임 규칙 없음
│   ├── plugin.py             herdr 진입점: start / stop / host(dock pane, agent "mon")
│   ├── i18n.py               언어 결정과 문자열 로딩
│   ├── dock_layout.py        herdr-dock-grid의 dock 배치 모듈 복사본
│   ├── herdr_api.py          herdr-dock-grid의 herdr CLI/socket 래퍼 복사본
│   └── locales/
│       ├── en.json           영어 문자열(monitor 항목 포함)
│       └── ko.json           한국어 문자열(monitor 항목 포함)
├── tests/
│   ├── test_game.py          규칙 테스트(12개)
│   ├── test_i18n.py          언어 결정, 언어 파일 키 일치(13개)
│   ├── test_monitor.py       모니터 렌더링, 명령 입력줄, 지표(27개)
│   ├── test_tetris_view.py   주입한 키로 화면 전환과 명령 입력줄(13개)
│   └── test_plugin.py        매니페스트, dock start / stop, agent 키(9개)
├── docs/                     이 문서(영문/국문 쌍)
└── .gitignore
```

## 파일별 역할

### `src/game.py`

게임 규칙과 상태입니다. 입출력이 없어서 바로 테스트할 수 있습니다.

- 상수: 보드 크기, 스폰 열, 점수표, 킥 오프셋, 블록 모양(`src/game.py:5-24`)
- 회전: 좌표 변환과 미리 계산한 4가지 상태(`src/game.py:27-45`)
- `cells_at`: 블록의 절대 좌표(`src/game.py:48-49`)
- `Game`: 상태와 동작(`src/game.py:52` 이후)
  - `move`, `rotate`(킥 포함), `tick`, `soft_drop`, `hard_drop`
  - `_draw_kind`(7-bag), `_fits`, `_spawn`, `_lock`, `_clear_lines`

### `src/tetris.py`

터미널 UI와 게임 진입점입니다.

- 색(`src/tetris.py:25`), 특수 키(`src/tetris.py:30-37`: Enter, `\x14`인 Ctrl+T는 `switch`, Backspace, Ctrl+C는 `interrupt`), 방향키 매핑(`src/tetris.py:39-40`), 게임 키 매핑(`src/tetris.py:42-55`)
- `fall_interval`: 레벨별 낙하 속도(`src/tetris.py:58-60`)
- `render`: 보드와 사이드 패널을 줄 목록으로 만듦(`src/tetris.py:77`)
- `draw`: 커서를 맨 위로 옮기고 다시 그림(`src/tetris.py:121`)
- `_read_key_windows`, `_read_key_posix`: 플랫폼별 키 입력. 키 이름이나 입력한 글자를 그대로 돌려줍니다(`src/tetris.py:126`, `src/tetris.py:149`)
- `TerminalMode`: 커서를 숨기고 입력 모드를 바꾸며, 종료 시 복원(`src/tetris.py:168`)
- `play`: 한 번의 화면 세션 루프. 모니터 또는 게임을 보여 주고, `switch`(Ctrl+T)로 전환하며, 모니터에서는 입력한 글자를 명령 입력줄로 보냅니다. `restart` 또는 `quit`을 반환(`src/tetris.py:189`)
- `main`: `--lang` 파싱, TTY 확인, 모니터에서 시작한 뒤 판을 진행. Ctrl+C를 받아 종료(`src/tetris.py:258`)

### `src/monitor.py`

시작 화면의 모니터와 명령 입력줄입니다. `game.py`에 의존하지 않습니다.

- `Monitor`: 서비스 지표, 로그 기록, 입력줄(`buffer`), 명령 결과(`output`)
- `type_char`, `backspace`: 입력줄 편집(`src/monitor.py:192-197`)
- `submit`: 입력줄을 실행합니다. `game` 명령은 help 목록을 보기 전에 처리해서 `game`을 돌려줍니다(`src/monitor.py:199-216`)
- 명령: `help`, `status`, `logs`, `clear`(`src/monitor.py:221-240`). `help`가 보여 주는 목록은 `HELP_COMMANDS`입니다(`src/monitor.py:65`)
- `tick`: `STEP_SECONDS`마다 한 단계 진행합니다. `render`는 헤더, 서비스 표, 처리량 점 그래프, 로그 스트림, 결과 영역, `$ ` 입력줄, 푸터를 돌려줍니다(`src/monitor.py:308`)
- 그리기 함수: `_header`, `_service_row`(좁은 단말에서는 항목을 줄임), `_chart_row`, `_log_row`(회색과 굵은 흰색 수준 표시), `_footer`(`src/monitor.py:245`, `src/monitor.py:260`, `src/monitor.py:282`, `src/monitor.py:294`, `src/monitor.py:303`)
- 대시보드 문구는 `monitor.py`에 영어로 고정되어 있습니다(`TITLE`, `LOG_TEMPLATES`, `LEVEL_LABELS`). 언어 파일은 명령 응답만 담습니다.
- 시간과 난수는 밖에서 받으므로 테스트에서 고정할 수 있습니다.

### `src/plugin.py`

herdr 진입점입니다. 게임을 공용 dock에 연결합니다.

- `start`: dock pane을 확보한 뒤 그 안에서 `host`를 실행합니다. 게임이 이미 떠 있으면 아무것도 하지 않습니다(`cmd_start`).
- `stop`: agent를 해제하고 pane을 닫습니다(dock이 비면 workspace를 닫음). dock 배정도 반환합니다(`cmd_stop`).
- `host`: agent를 등록하고, dock을 맨 아래에 두고, `tetris.main`을 실행한 뒤 끝나면 agent를 해제합니다(`cmd_host`).
- `load_dock_layout`: 설치된 `herdr-dock-grid`가 있으면 그 원본, 없으면 `src/dock_layout.py`를 씁니다(`src/plugin.py`, `load_dock_layout`).
- `DOCK_KEY = "herdr-tetris"`: dock 등록 키이며 표시 파일은 `herdr-tetris.dock`입니다. `AGENT_ID = "mon"`: agent 표시 이름입니다(`src/plugin.py`).

### `src/dock_layout.py`, `src/herdr_api.py`

herdr-dock-grid 파일의 복사본이며, 복사 시점의 원본과 같습니다. `dock_layout`은 dock 배정과 반환을 맡고, `herdr_api`는 herdr CLI와 socket을 감쌉니다.

### `src/i18n.py`

언어 선택과 문자열 로딩입니다.

- `system_language`: OS 로케일을 `ko` 또는 `en`으로 바꿈(`src/i18n.py:18`)
- `_config_language`: `config.json`의 `language` 읽기(`src/i18n.py:30`)
- `resolve_language`: 우선순위 적용(`src/i18n.py:38`)
- `load_strings`: `src/locales/<언어>.json` 로드(`src/i18n.py:45`)

### `src/locales/*.json`

화면 문자열입니다. 제목, 라벨, 조작 안내, 화면 전환 힌트(`toggle_hint`), 상태 메시지, TTY 메시지, `monitor` 항목이 있습니다. `monitor` 항목에는 명령 응답만 들어 있습니다. 입력 프롬프트(`prompt`), 도움말 설명(`command_help`), 응답(`not_found`, `status_title`, `status_line`, `state_ok`, `state_warn`)입니다. `en.json`과 `ko.json`의 키는 같아야 합니다.

### `herdr-plugin.toml`

herdr에 플러그인을 알립니다. id, 버전, 지원 OS, `start` / `stop` 액션을 적습니다. Windows 액션 id는 `-windows`로 끝납니다. [실행 방법](usage.ko.md#herdr-플러그인dock)을 보세요.

### `tests/`

[테스트](testing.ko.md)를 보세요.

### `config.json`

키는 `language` 하나이며 기본값은 `"auto"`입니다. [실행 방법](usage.ko.md#언어)의 우선순위 3번으로 쓰입니다.
