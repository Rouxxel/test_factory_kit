"""Installer for the factory-loop session plugin.

What it is
----------
AI coding tools do not discover MCP servers by scanning a repository. Each tool
reads MCP servers from its own config file, and none of them read this plugin's
folder directly. This script registers the plugin's stdio MCP server
(``factory-session-hub``, implemented in ``factory_session_mcp.py`` next to this
file) in the config file of each AI tool you use, so the ``factory_session_*``
and ``factory_worker_*`` tools become available to the Orchestrator and its
subagents.

What it does
------------
1. Finds the main repository root (via ``git rev-parse --git-common-dir``, so it
   works from a worktree too; falls back to the folder that contains
   ``.agents/``).
2. Uses the Python interpreter running this script (``sys.executable``) as the
   server command, which avoids ``python`` vs ``python3`` vs ``py`` differences
   between Windows, macOS, and Linux. Requires Python 3.9+.
3. Writes absolute paths, because each tool launches MCP servers from its own
   working directory and relative paths would break.
4. Merges a ``factory-session-hub`` entry into each selected tool's config,
   keeping every other server entry untouched. Invalid existing config files
   are reported and left unchanged.
5. Copies the plugin's adapter skills (``skills/<name>/SKILL.md``) into the
   host's skill folder when present (Claude Code, Kiro, Devin, Antigravity).

Supported hosts and the file each one reads:
    claude       -> <repo>/.mcp.json                   (key: mcpServers)
    cursor       -> <repo>/.cursor/mcp.json            (key: mcpServers)
    vscode       -> <repo>/.vscode/mcp.json            (key: servers)
    kiro         -> <repo>/.kiro/settings/mcp.json     (key: mcpServers)
    devin        -> <repo>/.devin/mcp_config.local.json (key: mcpServers;
                    the gitignored local variant, since paths are machine-specific)
    antigravity  -> <repo>/.agents/mcp_config.json     (key: mcpServers)
    codex        -> $CODEX_HOME/config.toml, default ~/.codex/config.toml
                    (global, affects every project; only used when named explicitly)

Skill folders used for adapter skills:
    claude -> .claude/skills/   kiro -> .kiro/skills/
    devin  -> .devin/skills/    antigravity -> .agents/skills/

After installing, restart or reload the AI tool (most tools only read MCP
config at startup) and approve the server if the tool asks you to. The written
paths are specific to this machine, so prefer keeping these config files out of
version control or have each teammate run this installer.

Commands
--------
    python install.py                      Auto-detect hosts from existing files/folders
                                           (.claude/, .mcp.json, .cursor/, .vscode/,
                                           .kiro/, .devin/, GEMINI.md, ~/.gemini/config/)
    python install.py --host claude        Register for one host
    python install.py --host cursor vscode Register for several hosts
    python install.py --host kiro devin antigravity
    python install.py --host codex         Register in the global Codex config
    python install.py --dry-run            Show what would change without writing
    python install.py --uninstall          Remove the factory-session-hub entry
    python install.py --repo PATH          Target a repository other than the one
                                           containing this plugin
    python install.py --list-hosts         Print supported hosts and config paths
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SERVER_NAME = "factory-session-hub"
SCRIPT_DIR = Path(__file__).resolve().parent
PLUGIN_DIR = SCRIPT_DIR.parent
SERVER_SCRIPT = SCRIPT_DIR / "factory_session_mcp.py"
JSON_HOSTS = {
    "claude": (Path(".mcp.json"), "mcpServers"),
    "cursor": (Path(".cursor") / "mcp.json", "mcpServers"),
    "vscode": (Path(".vscode") / "mcp.json", "servers"),
    "kiro": (Path(".kiro") / "settings" / "mcp.json", "mcpServers"),
    "devin": (Path(".devin") / "mcp_config.local.json", "mcpServers"),
    "antigravity": (Path(".agents") / "mcp_config.json", "mcpServers"),
}
SKILL_DIRS = {
    "claude": Path(".claude") / "skills",
    "kiro": Path(".kiro") / "skills",
    "devin": Path(".devin") / "skills",
    "antigravity": Path(".agents") / "skills",
}
ALL_HOSTS = [*JSON_HOSTS, "codex"]


def find_repo_root(start: Path) -> Path:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            cwd=start, capture_output=True, text=True, check=True,
        ).stdout.strip()
        return Path(out).resolve().parent
    except (OSError, subprocess.CalledProcessError):
        return PLUGIN_DIR.parents[2] if start == PLUGIN_DIR else start.resolve()


def codex_config_path() -> Path:
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "config.toml"


def config_path(host: str, repo: Path) -> Path:
    return codex_config_path() if host == "codex" else repo / JSON_HOSTS[host][0]


def detect_hosts(repo: Path) -> list[str]:
    checks = {
        "claude": [".claude", ".mcp.json", "CLAUDE.md"],
        "cursor": [".cursor"],
        "vscode": [".vscode"],
        "kiro": [".kiro"],
        "devin": [".devin"],
        # .agents/ itself always exists (this plugin lives there), so look for other signals.
        "antigravity": ["GEMINI.md", ".agents/mcp_config.json", ".agents/rules", ".agents/skills",
                        Path.home() / ".gemini" / "config"],
    }
    return [h for h, names in checks.items() if any((repo / n).exists() for n in names)]


def write_text(path: Path, text: str, dry_run: bool) -> None:
    if dry_run:
        print(f"  [dry-run] would write {path}:\n{text}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def update_json(host: str, path: Path, entry: dict | None, dry_run: bool) -> str:
    key = JSON_HOSTS[host][1]
    data = {}
    if path.exists():
        raw = path.read_text(encoding="utf-8").strip()
        try:
            data = json.loads(raw) if raw else {}
        except json.JSONDecodeError as exc:
            raise SystemExit(f"error: {path} is not valid JSON ({exc}); fix or remove it, then re-run.")
    servers = data.setdefault(key, {})
    if entry is None:
        if servers.pop(SERVER_NAME, None) is None:
            return "not registered, nothing to remove"
        if not servers:
            data.pop(key)
    else:
        if host == "vscode":
            entry = {"type": "stdio", **entry}
        if servers.get(SERVER_NAME) == entry:
            return "already up to date"
        servers[SERVER_NAME] = entry
    write_text(path, json.dumps(data, indent=2) + "\n", dry_run)
    return "removed" if entry is None else "registered"


def update_toml(path: Path, entry: dict | None, dry_run: bool) -> str:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    block = re.compile(
        rf'^\[mcp_servers\.(?:"{SERVER_NAME}"|{SERVER_NAME})\][^\n]*\n(?:(?!\[)[^\n]*\n?)*',
        re.MULTILINE,
    )
    stripped = block.sub("", text).rstrip("\n")
    if entry is None:
        if stripped == text.rstrip("\n"):
            return "not registered, nothing to remove"
        new = stripped + "\n" if stripped else ""
    else:
        new_block = (
            f'[mcp_servers.{SERVER_NAME}]\n'
            f'command = {json.dumps(entry["command"])}\n'
            f'args = [{", ".join(json.dumps(a) for a in entry["args"])}]\n'
        )
        new = (stripped + "\n\n" if stripped else "") + new_block
        if new.rstrip("\n") == text.rstrip("\n"):
            return "already up to date"
    write_text(path, new, dry_run)
    return "removed" if entry is None else "registered"


def sync_skills(host: str, repo: Path, uninstall: bool, dry_run: bool) -> None:
    skills = PLUGIN_DIR / "skills"
    if host not in SKILL_DIRS or not skills.is_dir():
        return
    for skill in sorted(p for p in skills.iterdir() if (p / "SKILL.md").is_file()):
        dest = repo / SKILL_DIRS[host] / skill.name
        if dry_run:
            print(f"  [dry-run] would {'remove' if uninstall else 'copy'} skill {dest}")
        elif uninstall:
            shutil.rmtree(dest, ignore_errors=True)
        else:
            shutil.copytree(skill, dest, dirs_exist_ok=True)
        print(f"  skill {skill.name}: {'removed' if uninstall else 'synced'} ({dest})")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Register the factory-session-hub MCP server with AI coding tools.",
        epilog="See the module docstring at the top of this file for details.",
    )
    parser.add_argument("--host", nargs="+", choices=ALL_HOSTS, help="hosts to configure (default: auto-detect)")
    parser.add_argument("--repo", type=Path, help="target repository (default: repo containing this plugin)")
    parser.add_argument("--uninstall", action="store_true", help="remove the server entry instead of adding it")
    parser.add_argument("--dry-run", action="store_true", help="print changes without writing files")
    parser.add_argument("--list-hosts", action="store_true", help="list supported hosts and their config paths")
    args = parser.parse_args()

    if sys.version_info < (3, 9):
        raise SystemExit("error: Python 3.9+ is required; re-run with a newer interpreter.")

    repo = find_repo_root(args.repo.resolve() if args.repo else PLUGIN_DIR)

    if args.list_hosts:
        for host in ALL_HOSTS:
            print(f"{host:12} {config_path(host, repo)}")
        return 0

    hosts = args.host or detect_hosts(repo)
    if not hosts:
        print(
            "No AI tool config folders detected in " f"{repo}.\n"
            f"Choose one explicitly, e.g.: python install.py --host {' | '.join(ALL_HOSTS)}",
            file=sys.stderr,
        )
        return 1

    if not args.uninstall and not SERVER_SCRIPT.is_file():
        print(f"warning: {SERVER_SCRIPT} does not exist yet; the tool will fail to start the server until it does.")

    entry = None if args.uninstall else {
        "command": Path(sys.executable).as_posix(),
        "args": [SERVER_SCRIPT.as_posix()],
    }

    print(f"Repository: {repo}")
    for host in hosts:
        path = config_path(host, repo)
        result = update_toml(path, entry, args.dry_run) if host == "codex" else update_json(host, path, entry, args.dry_run)
        print(f"- {host}: {result} ({path})")
        sync_skills(host, repo, args.uninstall, args.dry_run)

    if not args.dry_run:
        print(
            "\nNext: restart or reload your AI tool so it picks up the change"
            " (most tools only read MCP config at startup), approve the"
            f" '{SERVER_NAME}' server if prompted, then check that"
            " factory_session_list is available."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
