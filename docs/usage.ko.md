# 실행 방법과 조작법

[English](usage.md) | [**한국어**](usage.ko.md)

## 실행

```
python src/tetris.py
```

저장소 루트에서 실행합니다. 대화형 터미널이 필요합니다. stdin이 TTY가 아니면 `tty_required` 메시지를 출력하고 종료 코드 1로 끝납니다(`src/tetris.py:269-271`).

처음 보이는 화면은 게임이 아니라 가짜 시스템 모니터(`src/monitor.py`)입니다. 헤더에는 호스트, 리전, 버전, 시계, 가동 시간이 있습니다. 그 아래에서 서비스마다 CPU, 메모리, p95 지연, 초당 요청 수를 보여 주고, 막대와 스파크라인이 계속 움직입니다. 전체 처리량은 점 그래프로 보여 주고, 로그 스트림은 시각, 수준, 모듈, 메시지를 흰색과 회색으로 보여 줍니다. INFO는 회색이고, WARN과 ERROR는 굵은 흰색에 글자 표기를 함께 씁니다. 맨 아래에 명령 결과 영역과 `$ ` 명령 입력줄이 있고, 푸터에는 호스트, 리전, 버전, 가동 시간이 다시 나옵니다. 모니터 문구는 항상 영어입니다. 명령 응답만 언어 설정을 따릅니다. 이 화면에는 힌트 줄이 없고, 전환 키는 게임 화면의 조작 목록에 있습니다. 대략 다음과 같습니다.

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

 help    명령 목록 보기
 status  서비스 상태 보기

$ _
 ops-node-07 | ap-northeast-2 | v4.2.1 | up 00:12:04 | 6 services | 16 events
```

## 화면 전환

- `Ctrl+T`로 모니터와 게임 화면을 오갑니다. 어느 화면에서든 같은 키입니다.
- 모니터가 보이는 동안 게임은 멈춰 있고, 게임 조작 키는 아무 일도 하지 않습니다.
- `Ctrl+T`는 키 읽기 함수에서 `switch`로 바뀝니다(`src/tetris.py:30-38`). Windows에서 `Ctrl+T`는 `\x14` 문자로 들어옵니다(`src/tetris.py:33`).
- 모니터에서 `Enter`는 명령 입력줄을 실행합니다. 게임 화면에서는 아무 일도 하지 않습니다.
- Tab 키는 쓰지 않습니다.

## 명령 입력줄

`$ ` 줄에 명령을 입력하고 `Enter`를 누릅니다. 모니터에서 입력한 글자는 게임이 아니라 명령 입력줄로 갑니다. `Backspace`로 마지막 글자를 지웁니다.

| 명령 | 하는 일 |
|---|---|
| `help` | 아래 명령 목록을 보여 줍니다. |
| `status` | 서비스마다 가짜 상태 줄을 출력합니다. |
| `logs` | 최근 로그 8줄을 출력합니다. |
| `clear` | 명령 결과 영역을 지웁니다. |
| `game` | 게임 화면으로 바꿉니다. `help` 목록에는 없습니다. |

모르는 단어를 입력하면 `<단어>: command not found`(영어) 또는 `<단어>: 명령을 찾을 수 없습니다`(한국어)를 출력합니다. 명령은 첫 단어로 구분하며, 뒤에 붙은 단어는 무시합니다(`src/monitor.py:199-216`).

`help` 목록은 `HELP_COMMANDS`에서 만듭니다(`src/monitor.py:65`). `game` 명령은 목록을 찾기 전에 처리하므로 목록에 나타나지 않습니다(`src/monitor.py:207-208`).

명령 입력줄은 최대 80글자까지 받습니다(`src/monitor.py:50`).

## 언어

다음 순서로 언어를 정하며, 위에 있을수록 우선합니다.

1. `--lang auto|en|ko|ja|de|es|fr|ru` 옵션(`src/tetris.py:416-420`)
2. `HERDR_TETRIS_LANG` 환경 변수(`src/i18n.py:49`). 예전 `TETRIS_LANG`은 더 이상 읽지 않습니다.
3. 저장소 루트의 `config.json`에 있는 `language`(`src/i18n.py:30-35`, `config.json`)
4. 시스템 로케일: 지원하는 언어 중 하나면 그 언어, 그 밖이면 `en`(`src/i18n.py:18-41`)
5. 기본값 `en`(`src/i18n.py:15`)

`auto`는 "지정하지 않음"이라서 다음 단계로 넘어갑니다. 환경 변수와 `config.json`에서 지원하지 않는 언어 값은 무시합니다.

화면 문자열은 언어마다 `src/locales/<언어>.json`에 있습니다. 모든 파일은 `en.json`의 키를 모두 가져야 하며, 입력 프롬프트, 명령 설명, 명령 응답, 로그 문구를 담은 `monitor` 항목까지 포함해 `tests/test_locales.py`와 `tests/test_i18n.py`가 확인합니다.

`--help` 문구는 영어만 있습니다(`src/tetris.py:416-420`).

## 다른 게임

게임 화면에서 `1`~`4` 키로 게임을 고릅니다. `1` 테트리스, `2` 사다리 게임, `3` 스네이크, `4` 지뢰찾기입니다(`src/tetris.py:213-214`). 게임이 진행 중이어도 숫자 키로 다른 게임으로 갈 수 있습니다. 두고 온 판은 그대로 남아 있어 돌아가면 이어서 합니다. 끝난 판에 숫자 키로 들어가면 새로 시작합니다. "끝남"의 기준은 다음과 같습니다. 테트리스는 게임 오버일 때, 스네이크는 playing 상태가 아닐 때, 지뢰찾기는 playing 상태가 아닐 때입니다. 사다리 게임은 끝나는 판이 없어 넘어갈 때마다 새로 시작합니다. 스네이크의 최고 점수는 실행하는 동안만 기억하며 저장하지 않습니다. 이 문서는 테트리스만 설명합니다. 나머지 세 게임의 조작법과 규칙은 소스 파일(`src/ladder.py`, `src/snake.py`, `src/minesweeper.py`)에 있으며, 아직 이 문서에는 없습니다.

## 조작법

게임 화면:

| 동작 | 키 |
|---|---|
| 모니터로 전환 | `Ctrl+T` |
| 왼쪽 이동 | `A` 또는 `←` |
| 오른쪽 이동 | `D` 또는 `→` |
| 소프트 드롭(한 칸마다 +1점) | `S` 또는 `↓` |
| 시계 방향 회전 | `W` 또는 `↑` |
| 하드 드롭(한 칸마다 +2점, 즉시 고정) | `Space` |
| 일시정지 / 재개 | `P` |
| 종료 | `Q` |
| 다시 시작(게임 오버 후에만) | `R` |

모니터 화면:

| 동작 | 키 |
|---|---|
| 게임으로 전환 | `Ctrl+T` 또는 `game` 명령 |
| 명령 입력줄 실행 | `Enter` |
| 명령 입력줄 편집 | 글자, 숫자, `Backspace` |
| 종료 | `Ctrl+C` |

게임 키의 영문 글자는 대소문자를 구분하지 않습니다. 게임 키 매핑은 `src/tetris.py:42-55`에 있고, 방향키도 여기서 게임 동작으로 바뀝니다.

`Q` 종료는 게임 화면에서만 동작합니다. 모니터에서 입력한 글자는 명령 입력줄로 가기 때문입니다. `Ctrl+C`는 두 화면 모두에서 종료합니다.

방향키는 플랫폼마다 읽는 방식이 다릅니다. Windows는 `msvcrt` 코드를 씁니다(`src/tetris.py:39`, `src/tetris.py:126-135`). 그 밖의 플랫폼은 ESC 시퀀스를 읽습니다(`src/tetris.py:40`, `src/tetris.py:149-162`). Windows 경로는 이 환경에서 실제 키 입력으로 테스트하지 않았습니다. ESC 경로는 아직 실행하지 않았습니다.

macOS에서는 기본 설정상 `Ctrl+T`가 `SIGINFO` 신호를 보내서 프로그램까지 오지 않을 수 있습니다. 이 환경에서는 확인하지 않았습니다(터미널 기본값에 근거한 **추측**).

## 게임 오버

새 블록을 맨 위에 놓을 수 없으면 `게임 오버 - R: 다시 시작, Q: 종료` 문구가 나옵니다(`src/tetris.py:89-90`). `R`은 새 판을 시작하고 `Q`는 종료합니다(`src/tetris.py:233-236`). `R`로 시작한 새 판은 바로 게임 화면으로 갑니다.

## herdr 플러그인(dock)

이 저장소는 herdr 플러그인이기도 합니다(`herdr-plugin.toml`). 액션은 `src/plugin.py`를 실행합니다.

| 동작 | Linux/macOS id | Windows id | 명령 |
|---|---|---|---|
| dock에서 게임 시작 | `start` | `start-windows` | `src/plugin.py start` |
| 게임 종료와 dock pane 숨기기 | `stop` | `stop-windows` | `src/plugin.py stop` |

- `start`는 공용 `herdr-dock` workspace에서 pane 하나를 받아 그 안에서 게임을 돌립니다. 게임이 이미 떠 있으면 아무것도 하지 않습니다. 호스트 프로세스가 강제로 종료돼 표식만 남은 경우에는 그 표식을 무시하고 게임을 다시 띄웁니다.
- dock 등록 키는 `herdr-tetris`(`DOCK_KEY`)라서 dock 표시 파일은 `herdr-tetris.dock`입니다. `start`는 `register_dock`으로 dock 제목을 `mon`으로 등록합니다.
- 플러그인은 `mon` id(`AGENT_ID`)의 가짜 agent로 등록되고, 표시 이름도 `mon`입니다(`src/plugin.py`).
- `stop`은 게임 pane을 닫아 게임을 끝냅니다. agent 등록을 해제하고 dock pane을 돌려줍니다. dock에 다른 블록이 없으면 workspace 전체를 닫습니다.
- dock 배치는 설치된 `herdr-dock-grid`가 있으면 그 원본을 쓰고, 없으면 `src/dock_layout.py` 복사본을 씁니다. `src/dock_layout.py`와 `src/herdr_api.py`는 herdr-dock-grid 파일의 복사본입니다.

Windows는 `python`, 그 밖의 플랫폼은 `python3 -X utf8`을 씁니다. timekit 매니페스트와 같은 방식입니다.

## 검증 상태

- Windows 11, Python 3.12.10에서 확인: 게임이 시작되고 화면을 다시 그립니다. 타임아웃으로 멈춘 스모크 실행이며, 직접 플레이한 확인은 아닙니다.
- 모니터, 명령 입력줄, 화면 전환은 키 입력을 주입하는 단위 테스트로 확인했습니다(`tests/test_tetris_view.py`, `tests/test_monitor.py`). 실제 키 입력은 확인하지 않았습니다.
- herdr 플러그인 파일은 단위 테스트로 확인했습니다(`tests/test_plugin.py`). 이 환경에 설치된 herdr 0.9.4에서 `herdr-dock-grid`가 감지되고 그 dock 배치가 로드되는 것을 확인했습니다. `herdr-tetris`는 herdr에 설치되어 있지 않아서 start/stop 액션을 herdr 안에서 실행하지는 않았습니다.
- 확인하지 않음: 실제 터미널에서 키를 눌러 플레이하기, macOS와 Linux(termios 경로), herdr 안에서의 dock pane 흐름, 플랫폼별로 `Ctrl+T`가 프로그램까지 전달되는지.
