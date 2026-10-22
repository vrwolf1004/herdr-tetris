# 상태

[English](status.md) | [**한국어**](status.ko.md)

## 상태

**개선 중 (in progress).** 게임과 herdr 플러그인은 단위 테스트에서 동작합니다. 다만 일부는 실제 터미널이나 herdr 안에서 아직 확인하지 않았습니다([미확인 사항](#미확인-사항)).

## 기능

각 기능 옆에 구현 위치를 적었습니다. 줄 번호는 현재 파일 기준입니다.

### 화면

- 게임은 모니터 화면으로 시작합니다. `run`에서 `in_monitor = True`로 설정합니다(`src/tetris.py:276`).
- 모니터는 영어로 된 가짜 대시보드입니다. 헤더와 푸터에 호스트, 리전, 버전, 가동 시간이 나옵니다. 서비스마다 움직이는 막대, 스파크라인, 지연 시간이 있고, 점 그래프로 처리량을 보여 주며, 흰색과 회색으로 된 로그 스트림은 수준, 모듈, 메시지를 보여 주며, 색은 흰색과 회색만 씁니다. 맨 아래에 결과 영역과 `$ ` 명령 입력줄이 있습니다(`src/monitor.py:308` render, `src/monitor.py:245` 헤더, `src/monitor.py:303` 푸터). 모니터에는 힌트 줄이 없습니다. 전환 키는 게임 화면의 조작 목록에 있습니다(`src/locales/*.json`의 `toggle_hint`).
- `Ctrl+T`로 모니터와 게임을 오갑니다. 어느 화면에서든 같은 키입니다. `Ctrl+T`는 `\x14`로 들어와 `switch`로 바뀝니다(`src/tetris.py:33`). 전환은 `play`에서 처리합니다(`src/tetris.py:212`).
- 모니터가 보이는 동안 게임은 멈춰 있습니다. 중력이 돌지 않고 게임 키도 적용되지 않습니다(`src/tetris.py:198-201`, `src/tetris.py:223-228`).

### 명령 입력줄

- 모니터에서 입력한 글자는 게임이 아니라 명령 입력줄로 갑니다(`src/tetris.py:223-228`). `Backspace`는 마지막 글자를 지웁니다(`src/monitor.py:196`). 입력줄은 최대 80글자입니다(`src/monitor.py:50`).
- `Enter`로 입력줄을 실행합니다(`src/tetris.py:214-215`, `src/monitor.py:199`).
- 명령:
  - `help`: `HELP_COMMANDS` 목록을 보여 줍니다(`src/monitor.py:65`, `src/monitor.py:221`).
  - `status`: 서비스마다 가짜 상태 줄을 출력합니다(`src/monitor.py:225`).
  - `logs`: 최근 로그 8줄을 출력합니다(`src/monitor.py:234`).
  - `clear`: 결과 영역을 지웁니다(`src/monitor.py:238`).
  - `game`: 게임 화면으로 바꿉니다. help 목록보다 먼저 처리하므로 목록에 나타나지 않습니다(`src/monitor.py:207-208`).
- 그 밖의 단어는 영어에서 `command not found`, 한국어에서 `명령을 찾을 수 없습니다`를 출력합니다(`src/monitor.py:199-216`, `src/locales/*.json`의 `not_found`).

### 게임 조작

게임 키 매핑: `src/tetris.py:42-55`. 방향키는 플랫폼마다 읽는 방식이 다릅니다(`src/tetris.py:39-40`, `src/tetris.py:126-135`, `src/tetris.py:149-162`).

| 동작 | 키 |
|---|---|
| 이동 | `A`/`D` 또는 `←`/`→` |
| 회전 | `W` 또는 `↑` |
| 소프트 드롭 | `S` 또는 `↓` (한 칸마다 +1점) |
| 하드 드롭 | `Space` (한 칸마다 +2점) |
| 일시정지 | `P` |
| 게임 오버 후 다시 시작 | `R` |
| 종료 | `Q` (게임 화면에서만) |

### 종료

- 게임 화면에서 `Q`로 종료합니다. 모니터에서 `Q`는 명령 입력줄에 글자로 들어갑니다(`src/tetris.py:42-55`, `src/tetris.py:223-228`).
- `Ctrl+C`는 두 화면 모두에서 종료합니다. Windows에서는 `\x03`으로 들어와 `interrupt`로 바뀝니다(`src/tetris.py:36`). POSIX에서는 신호로 들어오며 `main`에서 받습니다(`src/tetris.py:279`).

### 실행

```
python src/tetris.py
python src/tetris.py --lang ko
```

- 대화형 터미널이 필요합니다. 아니면 `tty_required` 메시지를 출력하고 종료 코드 1로 끝납니다(`src/tetris.py:269-271`).
- `--lang auto|en|ko`(`src/tetris.py:261`). 우선순위는 `--lang`, `HERDR_TETRIS_LANG`, `config.json`, 시스템 로케일, 영어 순입니다(`src/i18n.py:38`).

### herdr dock 연동

- 매니페스트는 `herdr-tetris` 플러그인을 선언하고, OS별 `start`와 `stop` 액션을 둡니다(`herdr-plugin.toml:1`, `:15`, `:22`, `:31`, `:38`). Windows 액션 id는 `-windows`로 끝납니다.
- dock 등록 키는 `herdr-tetris`입니다(`src/plugin.py:36`, `DOCK_KEY`). 표시 파일은 `herdr-tetris.dock`입니다.
- agent id와 표시 이름은 모두 `mon`입니다(`src/plugin.py:38`, `AGENT_ID`). `cmd_start`는 `register_dock`으로 dock 제목을 정합니다(`src/plugin.py:108`).
- `cmd_start`는 dock pane을 받아 그 안에서 `host`를 실행합니다(`src/plugin.py:104-114`). `cmd_host`는 agent와 표시 이름을 등록한 뒤 게임을 돌립니다(`src/plugin.py:136-160`, `report_agent` `:139`, `report_metadata` `:145`).
- `cmd_stop`은 agent를 해제하고, pane을 닫고(dock이 비면 workspace를 닫음), dock 배정을 돌려줍니다(`src/plugin.py:116-132`).

### 테스트

`python -m unittest discover -s tests -v`로 테스트 64개를 돌립니다. 목록은 [테스트](testing.ko.md)에 있습니다.

## 미확인 사항

아직 확인하지 않은 항목입니다. 관련 코드나 문서에 각각 표시했습니다.

1. **실제 키 입력 플레이.** 화면 전환, 명령 입력줄, 게임 키는 `play`에 키를 주입해서 테스트했습니다(`tests/test_tetris_view.py:40`, `tests/test_tetris_view.py:81`). 실제 터미널에서 플레이한 사람은 아직 없습니다.
2. **herdr start/stop.** dock 로직은 mock으로 테스트했습니다(`tests/test_plugin.py:54`, `tests/test_plugin.py:77`). `herdr-dock-grid`는 감지되었고 원본 `dock_layout.py`도 로드되었습니다. 하지만 `herdr-tetris`는 herdr에 설치되어 있지 않아서, herdr 안에서 `start`와 `stop`을 실행하지 않았습니다.
3. **macOS `Ctrl+T`.** macOS에서는 `Ctrl+T`가 `SIGINFO`를 보내서 프로그램까지 오지 않을 수 있습니다. 터미널 기본값에 근거한 **추측**이며 확인하지 않았습니다([실행 방법](usage.ko.md#화면-전환) 참고).
4. **Linux와 macOS.** termios 경로(`src/tetris.py:149-162`, `src/tetris.py:168-186`)와 ESC 방향키 처리를 실행하지 않았습니다.
5. **Windows 방향키.** `msvcrt` 방향키 경로(`src/tetris.py:126-135`)를 실제 키 입력으로 테스트하지 않았습니다.

관련 내용은 [실행 방법](usage.ko.md#검증-상태)과 [테스트](testing.ko.md#검증하지-않은-범위)에도 있습니다.
