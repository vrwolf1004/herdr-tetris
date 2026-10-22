"""herdr-tetris: 공용 herdr-dock workspace 의 pane 하나에서 테트리스를 띄운다.

명령
  start   dock pane 을 확보하고 그 안에서 host 를 실행한다 (액션 start)
  stop    host pane 을 닫고 dock 자리를 돌려준다 (액션 stop)
  host    pane 안에서 도는 진입점. 가짜 agent(표시 이름 mon)로 등록하고 게임을 돌린 뒤 해제한다

게임 화면과 규칙은 tetris.py 와 game.py 가 맡고, 이 파일은 dock 과 herdr 연결만 맡는다.
stop 은 pane 을 닫아 게임 프로세스를 끝낸다. 그래서 host 의 finally 가 실행되지 않을 수 있고,
agent 해제와 상태 파일 정리는 stop 에서도 한다.
"""

import argparse
import os
import sys
import time

import herdr_api


def load_dock_layout():
    """설치된 herdr-dock-grid 가 있으면 그 원본을, 없으면 이 plugin 의 복사본(src/dock_layout.py)을 쓴다."""
    grid = herdr_api.installed_plugin_path("herdr-dock-grid")
    if grid:
        sys.path.insert(0, os.path.join(grid, "src"))
    import dock_layout
    return dock_layout


dock = load_dock_layout()
import tetris  # noqa: E402

PLUGIN_ID = "herdr-tetris"
SOURCE = f"plugin:{PLUGIN_ID}"
# dock 등록 key 이자 표시 파일 이름(<key>.dock). 기존 식별자라 바꾸지 않는다.
DOCK_KEY = "herdr-tetris"
# agent 표시 이름. dock 안에서 이 이름으로 보인다.
AGENT_ID = "mon"
SIDEBAR_TOKEN_PREFIX = "herdr-sidebar"
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def default_state_dir():
    path = os.environ.get("HERDR_PLUGIN_STATE_DIR")
    if path:
        return path
    base = os.environ.get("LOCALAPPDATA") if herdr_api.IS_WINDOWS else os.path.expanduser("~/.local/state")
    return os.path.join(base or os.path.expanduser("~"), "herdr", "plugins", PLUGIN_ID)


class State:
    """pane 과 workspace id 를 파일로 기억한다. 액션마다 다른 프로세스가 돌기 때문이다."""

    def __init__(self, directory):
        self.directory = directory
        os.makedirs(directory, exist_ok=True)

    def read(self, name):
        try:
            with open(os.path.join(self.directory, name), encoding="utf-8") as file:
                return file.read().strip() or None
        except OSError:
            return None

    def write(self, name, value):
        with open(os.path.join(self.directory, name), "w", encoding="utf-8") as file:
            file.write(value)

    def remove(self, name):
        try:
            os.remove(os.path.join(self.directory, name))
        except OSError:
            pass


def workspace_panes(workspace_id):
    panes = herdr_api.cli("pane", "list").get("panes", [])
    return [p for p in panes if p["workspace_id"] == workspace_id]


def is_sidebar(pane):
    return any(name.startswith(SIDEBAR_TOKEN_PREFIX) for name in (pane.get("tokens") or {}))


def pane_alive(pane_id):
    if not pane_id:
        return False
    return herdr_api.cli("pane", "get", pane_id, check=False) is not None


def keep_at_bottom(workspace_id):
    """공용 dock 을 사이드바 맨 아래에 둔다. timekit 과 같은 규칙이다."""
    workspaces = herdr_api.request("workspace.list", {}).get("workspaces", [])
    ids = [w["workspace_id"] for w in workspaces]
    if workspace_id in ids and ids[-1] != workspace_id:
        # insert_index 는 옮기기 전 목록 기준 "이 위치 앞에 넣기"다. 길이를 주면 맨 뒤로 간다.
        herdr_api.try_request("workspace.move", {"workspace_id": workspace_id, "insert_index": len(ids)})


def host_command(state_dir, pane_id):
    return [sys.executable, "-X", "utf8", os.path.abspath(__file__), "host", "--state", state_dir, "--pane", pane_id]


def cmd_start(args):
    state = State(args.state)
    if pane_alive(state.read("pane.id")) and state.read("running"):
        return 0  # 이미 게임이 떠 있으면 같은 pane 에 명령을 또 입력하지 않는다
    dock.register_dock(DOCK_KEY, title=AGENT_ID)
    workspace_id, pane_id = dock.ensure_dock_pane(DOCK_KEY, PROJECT_DIR)
    state.write("workspace.id", workspace_id)
    state.write("pane.id", pane_id)
    herdr_api.cli("pane", "run", pane_id, *host_command(args.state, pane_id))
    return 0


def cmd_stop(args):
    state = State(args.state)
    workspace_id = state.read("workspace.id")
    pane_id = state.read("pane.id")
    if pane_id:
        herdr_api.try_request("pane.release_agent", {"pane_id": pane_id, "source": SOURCE, "agent": AGENT_ID})
    if workspace_id:
        # dock 은 다른 플러그인과 같이 쓴다. 자기 pane 만 닫고, 남은 게 herdr-sidebar 뿐이면 workspace 도 닫는다.
        others = [p for p in workspace_panes(workspace_id) if p["pane_id"] != pane_id and not is_sidebar(p)]
        if others:
            if pane_id:
                herdr_api.cli("pane", "close", pane_id, check=False)
        else:
            herdr_api.cli("workspace", "close", workspace_id, check=False)
    for name in ("workspace.id", "pane.id", "running"):
        state.remove(name)
    dock.release_dock_pane(DOCK_KEY)
    return 0


def cmd_host(args):
    state = State(args.state)
    state.write("running", str(time.time()))
    herdr_api.try_request("pane.report_agent", {
        "pane_id": args.pane,
        "source": SOURCE,
        "agent": AGENT_ID,
        "state": "idle",
    })
    herdr_api.try_request("pane.report_metadata", {
        "pane_id": args.pane,
        "source": SOURCE,
        "display_agent": AGENT_ID,
        "tokens": {},
    })
    workspace_id = state.read("workspace.id")
    if workspace_id:
        keep_at_bottom(workspace_id)
    try:
        return tetris.main(args.game_args)
    finally:
        herdr_api.try_request("pane.release_agent", {"pane_id": args.pane, "source": SOURCE, "agent": AGENT_ID})
        state.remove("running")


def main(argv=None):
    parser = argparse.ArgumentParser(prog=PLUGIN_ID)
    parser.add_argument("command", choices=["start", "stop", "host"])
    parser.add_argument("--state", default=default_state_dir())
    parser.add_argument("--pane", default=os.environ.get("HERDR_PANE_ID"))
    # host 가 받은 나머지 인자(예: --lang ko)는 게임에 그대로 넘긴다.
    args, game_args = parser.parse_known_args(argv)
    args.game_args = game_args
    commands = {"start": cmd_start, "stop": cmd_stop, "host": cmd_host}
    try:
        return commands[args.command](args)
    except herdr_api.HerdrError as error:
        print(f"{PLUGIN_ID}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
