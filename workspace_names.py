#!/usr/bin/env python3
"""Name Herdr workspaces after the session title of the coding agent inside.

Runs on Herdr startup and on agent/focus events. Each run reconciles every
workspace: if it contains an agent whose terminal title is a real session
title (e.g. Claude Code's auto-generated summary), the workspace is renamed
to it. A workspace is only touched while it still has Herdr's default label
(its directory name) or the label this plugin set last time, so manual
renames always win.
"""

import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys

MAX_LEN = int(os.environ.get("HERDR_WORKSPACE_NAMES_MAX_LEN", "40"))
# Titles that are not a session summary: the bare app name, or the shell
# command line that launched the agent (e.g. "claude --model haiku").
GENERIC_TITLES = {"Claude Code", "OpenAI Codex", "Codex", "opencode"}

HERDR = os.environ.get("HERDR_BIN_PATH", "herdr")


def herdr(*args):
    out = subprocess.run(
        [HERDR, *args], capture_output=True, text=True, timeout=10, check=True
    ).stdout
    return json.loads(out)["result"]


def session_title(agent):
    title = " ".join((agent.get("terminal_title_stripped") or "").split())
    name = agent.get("agent") or ""
    if not title or title in GENERIC_TITLES:
        return None
    if name and re.match(rf"{re.escape(name)}(\s|$)", title):
        return None
    if len(title) > MAX_LEN:
        title = title[:MAX_LEN].rsplit(" ", 1)[0] + "…"
    return title


def main():
    state_dir = os.environ.get("HERDR_PLUGIN_STATE_DIR") or os.path.expanduser(
        "~/.local/state/herdr-agent-workspace-names"
    )
    os.makedirs(state_dir, exist_ok=True)
    # Workspace ids are per server, so keep one state file per socket.
    socket_key = hashlib.sha1(
        os.environ.get("HERDR_SOCKET_PATH", "").encode()
    ).hexdigest()[:12]
    state_path = os.path.join(state_dir, f"labels-{socket_key}.json")

    with open(os.path.join(state_dir, ".lock"), "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            with open(state_path) as f:
                last = json.load(f)
        except (OSError, ValueError):
            last = {}

        workspaces = herdr("workspace", "list")["workspaces"]
        agents = herdr("agent", "list")["agents"]
        panes = herdr("pane", "list")["panes"]

        dirs = {}
        for p in panes:
            for key in ("cwd", "foreground_cwd"):
                if p.get(key):
                    dirs.setdefault(p["workspace_id"], set()).add(
                        os.path.basename(p[key].rstrip("/"))
                    )

        titles = {}
        for a in agents:
            title = session_title(a)
            if title:
                titles.setdefault(a["workspace_id"], title)

        live = {w["workspace_id"] for w in workspaces}
        last = {k: v for k, v in last.items() if k in live}

        for w in workspaces:
            ws, label = w["workspace_id"], w["label"]
            title = titles.get(ws)
            if not title or title == label:
                continue
            if label != last.get(ws) and label not in dirs.get(ws, set()):
                continue  # renamed by hand: leave it alone
            herdr("workspace", "rename", ws, title)
            last[ws] = title

        with open(state_path, "w") as f:
            json.dump(last, f)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # never break Herdr over a cosmetic rename
        print(f"herdr-agent-workspace-names: {e}", file=sys.stderr)
