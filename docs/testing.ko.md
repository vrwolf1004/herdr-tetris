# 테스트

[English](testing.md) | [**한국어**](testing.ko.md)

## 실행

저장소 루트에서 실행합니다.

```
python -m unittest discover -s tests -v
```

`-s tests` 옵션이 필요합니다. `tests/`에 `__init__.py`가 없어서 루트에서 `python -m unittest`만 실행하면 거기를 보지 않습니다(**추측**: 이 환경에서 확인하지 않음). 테스트 파일마다 `src/`를 `sys.path`에 직접 추가합니다(`tests/test_game.py:6`, `tests/test_i18n.py:6`).

이 환경에서 마지막으로 돌린 결과: Windows 11, Python 3.12.10, 74개 테스트 모두 통과.

## 검증 범위

### `tests/test_game.py` (12개)

- 회전: 네 번 돌리면 각 블록이 처음 모양으로 돌아옵니다(`tests/test_game.py:21`). T 회전 좌표가 기대값과 같습니다(`tests/test_game.py:31-33`). 오른쪽 벽의 세로 I 블록은 회전할 때 왼쪽으로 밀립니다(`tests/test_game.py:35`).
- 이동: 벽으로 가는 이동은 거부됩니다(`tests/test_game.py:47`).
- 줄 제거: 1줄과 2줄 제거, 기대 점수(`tests/test_game.py:63`, `tests/test_game.py:71`). 지운 줄 위의 줄이 내려갑니다(`tests/test_game.py:77`).
- 점수와 레벨: 소프트 드롭은 한 칸마다 1점입니다(`tests/test_game.py:86`). 10줄마다 레벨이 오릅니다(`tests/test_game.py:92`).
- 7-bag: 7개씩 뽑으면 7종이 모두 한 번씩 나옵니다(`tests/test_game.py:101`).
- 게임 오버: 스폰 자리가 막히면 `game_over`가 참이 되고, 그 뒤 동작은 무시됩니다(`tests/test_game.py:110`, `tests/test_game.py:119`).

### `tests/test_i18n.py` (13개)

- `en.json`과 `ko.json`의 키와 조작 안내 줄 수가 같습니다(`tests/test_i18n.py:12`, `:17`).
- `monitor` 명령 문구의 키는 두 파일이 같습니다(`tests/test_i18n.py:23`). 대시보드 문구는 언어 파일에 없습니다(`tests/test_i18n.py:29`).
- 시스템 로케일 매핑: Windows 한국어 이름, POSIX 한국어, 지원하지 않는 값은 `en`, 로케일이 없으면 `LANG` 사용(`tests/test_i18n.py:35`, `:39`, `:43`, `:47`).
- 우선순위: `--lang`이 환경 변수보다, 환경 변수가 `config.json`보다 우선합니다. `auto`나 잘못된 값은 시스템 로케일로 넘어갑니다(`tests/test_i18n.py:59`, `:63`). 예전 `TETRIS_LANG`은 무시합니다(`tests/test_i18n.py:69`). 설정 파일은 시스템 로케일보다 우선합니다(`tests/test_i18n.py:75`, `:81`).

### `tests/test_monitor.py` (27개)

- 헤더에 호스트, 리전, 버전, 시계, 가동 시간이 있습니다(`tests/test_monitor.py:42`). 푸터는 호스트, 리전, 버전, 가동 시간을 다시 보여 줍니다(`tests/test_monitor.py:54`).
- 언어가 한국어여도 대시보드는 영어입니다(`tests/test_monitor.py:64`). 명령 응답은 언어 설정을 따릅니다(`tests/test_monitor.py:74`).
- 힌트 줄은 그려지지 않습니다(`tests/test_monitor.py:84`). 모든 서비스 줄이 보입니다(`tests/test_monitor.py:88`).
- 30칸부터 160칸까지 모든 줄이 단말 폭 안에 들어갑니다(`tests/test_monitor.py:93`). 넓은 줄에는 메모리와 지연 시간이 있고, 좁은 줄에서는 빠집니다(`tests/test_monitor.py:101`).
- 로그 줄에는 시각, 수준, 대괄호 모듈, 메시지가 있습니다(`tests/test_monitor.py:113`). 로그 수준은 INFO를 회색으로, WARN과 ERROR를 굵은 흰색으로 구분하고 글자 표기도 씁니다(`tests/test_monitor.py:122`). 화면 전체에서 흰색과 회색 코드만 나옵니다(`tests/test_monitor.py:140`).
- 점 그래프 줄은 처리량 기록으로 그려집니다(`tests/test_monitor.py:148`).
- 한 단계마다 로그 항목 하나가 붙고 지표가 바뀝니다(`tests/test_monitor.py:156`). 로그 보관 길이는 제한됩니다(`tests/test_monitor.py:163`). 대시보드에는 가장 최근 로그가 마지막에 보입니다(`tests/test_monitor.py:169`).
- 화면 높이는 고정이고, 입력줄은 푸터 위에 있습니다(`tests/test_monitor.py:175`).
- 입력과 백스페이스로 명령 입력줄을 편집합니다(`tests/test_monitor.py:183`). 빈 입력은 아무 일도 하지 않습니다(`tests/test_monitor.py:190`).
- 모르는 단어는 `command not found`를 출력합니다(`tests/test_monitor.py:195`). `game`은 `game`을 돌려주고, `help` 목록에는 없습니다(`tests/test_monitor.py:201`).
- `status`는 모든 서비스를 지연 시간과 함께 보여 줍니다(`tests/test_monitor.py:209`). `logs`는 최근 로그를 출력합니다(`tests/test_monitor.py:216`). `clear`는 출력을 지웁니다(`tests/test_monitor.py:224`).
- 결과 영역에는 최근 줄만 보입니다(`tests/test_monitor.py:232`).
- `tick`은 단계 간격을 기다립니다(`tests/test_monitor.py:240`). 1000단계 동안 지표는 범위 안에 머뭅니다(`tests/test_monitor.py:248`).
- 모니터 소스는 게임을 import하지 않습니다(`tests/test_monitor.py:258`).

### `tests/test_tetris_view.py` (13개)

키를 `tetris.play`에 주입하고, `draw`는 그려진 프레임을 모으는 함수로 바꿉니다. 테스트에서 따로 말하지 않으면 키 목록을 순서대로 쓰고, 끝나면 `interrupt`로 루프를 끝냅니다.

- 게임은 모니터에서 시작하고, `Ctrl+T`(`switch`)를 누르면 게임 화면으로 바뀝니다(`tests/test_tetris_view.py:40`).
- `Ctrl+T`를 다시 누르면 모니터로 돌아갑니다(`tests/test_tetris_view.py:47`).
- 모니터에서 글자, 숫자, 공백은 명령 입력줄로 가고 게임은 움직이지 않습니다(`tests/test_tetris_view.py:51`).
- 게임 화면에는 `Ctrl+T: switch` 힌트가 보입니다(`tests/test_tetris_view.py:57`).
- 게임에서 `Ctrl+T`를 누르면 모니터로 돌아가고, 게임은 멈춰 있습니다(`tests/test_tetris_view.py:61`).
- 모니터에서 `q`는 글자로 입력되고, `interrupt`(Ctrl+C)는 종료합니다(`tests/test_tetris_view.py:66`). 게임 화면의 `Q`는 종료합니다(`tests/test_tetris_view.py:71`).
- `SPECIAL_KEYS`는 `\x14`를 `switch`로 바꾸고, Tab은 매핑하지 않습니다(`tests/test_tetris_view.py:75`).
- `game`을 입력하고 Enter를 누르면 게임 화면으로 갑니다(`tests/test_tetris_view.py:81`). 모르는 단어는 `command not found`를 출력합니다(`tests/test_tetris_view.py:85`). `help`는 `game`을 뺀 목록을 보여 줍니다(`tests/test_tetris_view.py:89`).
- 백스페이스로 명령 입력줄을 편집합니다(`tests/test_tetris_view.py:95`). `clear`는 출력을 지웁니다(`tests/test_tetris_view.py:99`).

### `tests/test_plugin.py` (9개)

- 매니페스트: id, 최소 herdr 버전, 지원 OS, 액션 id 중복 없음, OS별 `start` / `stop`, OS에 맞는 실행기(`tests/test_plugin.py:19`, `:24`, `:28`, `:35`).
- dock 시작: 게임이 떠 있으면 다시 띄우지 않습니다(`tests/test_plugin.py:54`). 그렇지 않으면 dock 제목을 `mon`으로 정하고, 키 `herdr-tetris`로 dock pane을 받아 그 안에서 `host`를 실행합니다(`tests/test_plugin.py:64`).
- dock 종료: dock에 다른 블록이 있으면 자기 pane만 닫습니다(`tests/test_plugin.py:77`). dock이 비어 있으면 workspace를 닫습니다(`tests/test_plugin.py:97`).
- dock 등록 키는 `herdr-tetris`, agent 표시 이름은 `mon`입니다(`tests/test_plugin.py:113`).

## 검증하지 않은 범위

- 터미널에서 실제 키 읽기(`src/tetris.py`의 `_read_key_windows`, `_read_key_posix`)와 터미널 raw 모드. 주입한 키로 화면 흐름만 확인합니다.
- 플랫폼별 키 입력: Windows와 POSIX 읽기 경로를 테스트하지 않았습니다. 플랫폼마다 `Ctrl+T`가 프로그램까지 오는지도 테스트하지 않았습니다.
- 실제 단말 폭. 테스트는 폭을 직접 넘기고, 기본 경로(`shutil.get_terminal_size`)는 테스트하지 않았습니다.
- 중력 타이밍과 일시정지 동작. 화면 전환 테스트에서만 일부 확인합니다.
- herdr 쪽 플러그인 동작: 실제 dock pane, herdr에 agent 등록, `pane run`. 테스트는 herdr CLI와 socket 호출을 흉내 냅니다.

## 수동 확인

```
python src/tetris.py
python src/tetris.py --lang ko
```

모니터를 보다가 명령 입력줄에 `help`와 `status`를 입력해 보고, `game`을 입력해 게임을 여세요. 몇 번 움직인 뒤 `Ctrl+T`로 돌아오고, 모니터가 보이는 동안 게임이 멈춰 있는지 확인하세요. 일시정지, 종료, 게임 오버 후 다시 시작도 해 보세요.
