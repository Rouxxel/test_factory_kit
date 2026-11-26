"""factory-session-hub: stdio MCP server for the factory-loop plugin.

What it is
----------
A zero-dependency (Python 3.9+ standard library) Model Context Protocol server
that lets an Orchestrator session and its subagent worker sessions coordinate
through git worktrees and a shared, file-based mailbox. Every AI session
(Orchestrator and each worker) starts its own copy of this script through its
tool's MCP config (see ``install.py``); all copies read and write the same
session folder, which is the communication channel. No background listener is
needed: agents only act on their own turns, so each side calls a tool when it
wants to send or read something.

Where state lives
-----------------
``<main-repo-root>/.factory/sessions/``, where the main repository root is
resolved with ``git rev-parse --git-common-dir`` so calls made from inside a
worktree reach the same folder. The folder is added to the repository's local
``.git/info/exclude`` (never committed). Per session::

    sessions/<sessionId>/session.json    current record (atomic rewrite, locked)
    sessions/<sessionId>/inbox.jsonl     Orchestrator -> worker messages (append-only)
    sessions/<sessionId>/reports.jsonl   worker -> Orchestrator reports (append-only)
    sessions/<sessionId>/progress.jsonl  worker progress notes (append-only)
    sessions/archive/<sessionId>/        moved here by factory_session_teardown
    sessions/incidents.jsonl             project-wide incident log (append-only)

The "In-Flight Worktrees & Subagents" table in ``.factory/SESSION_STATE.md``
is regenerated between ``<!-- factory:sessions:start -->`` and
``<!-- factory:sessions:end -->``, and the open-incidents table between
``<!-- factory:incidents:start -->`` and ``<!-- factory:incidents:end -->``,
after every change; nothing else in that file is touched.

Session status lifecycle
------------------------
    IN_PROGRESS -> WAITING_FOR_REVIEW   factory_worker_report(status=WAITING_FOR_REVIEW)
    any active  -> BLOCKED              factory_worker_report(status=BLOCKED), or review round > 3
    any active  -> CHANGES_REQUESTED    factory_session_send_feedback
    CHANGES_REQUESTED -> IN_PROGRESS    factory_worker_check_inbox (worker read the feedback)
    any         -> ARCHIVED             factory_session_teardown

Tools
-----
Orchestrator:
    factory_session_dispatch       create worktree + branch + session record
    factory_session_list           list sessions (startup/resume), prune stale worktrees
    factory_session_get_status     session record, reports, messages, optional diff
    factory_session_send_feedback  queue review feedback or instructions for a worker
    factory_session_teardown       remove worktree (optional) and archive the session
    factory_resolve_incident       close an incident and list the sessions to unblock
Worker:
    factory_worker_report          report ready-for-review (green CI) or blocked
    factory_worker_check_inbox     read unread Orchestrator messages
    factory_worker_progress        record a one-line progress note (heartbeat)
Worker or Orchestrator:
    factory_report_incident        record a permission/security block, API or quota limit,
                                   credential problem, third-party or network failure

Every worker tool call records ``lastWorkerContactAt``, and
``factory_session_list`` reports ``minutesSinceWorkerContact`` and
``minutesSinceDispatch`` so the Orchestrator can tell a working session from a
stalled one. Reports carry a ``ciStatus`` (and ``blockerType`` when BLOCKED) so
infrastructure problems such as CI billing limits are reported, not retried.
Incidents are de-duplicated: the same open problem reported by several workers is
one incident with several occurrences, so the Orchestrator escalates it once.

Running
-------
Normally launched by an AI tool after ``python install.py``. Manually::

    python factory_session_mcp.py                 # serve MCP over stdin/stdout
    python factory_session_mcp.py --repo PATH     # target a specific repository
    FACTORY_REPO_ROOT=PATH python factory_session_mcp.py

Without ``--repo``/``FACTORY_REPO_ROOT`` the repository is found from this
script's location, then from the working directory. stdout carries protocol
messages only; logs go to stderr.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

SERVER_NAME = "factory-session-hub"
SERVER_VERSION = "1.0.0"
SUPPORTED_PROTOCOLS = ("2025-06-18", "2025-03-26", "2024-11-05")
MAX_REVIEW_ROUNDS = 3
ACTIVE_STATUSES = ("IN_PROGRESS", "WAITING_FOR_REVIEW", "CHANGES_REQUESTED", "BLOCKED")
ISSUE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
SESSION_ID_RE = re.compile(r"^sess_[a-z0-9][a-z0-9._-]*$")
# Machine-specific MCP configs written by install.py; copied into new worktrees so
# a session opened inside the worktree can reach this server too.
HOST_CONFIG_FILES = (
    ".mcp.json",
    ".cursor/mcp.json",
    ".vscode/mcp.json",
    ".kiro/settings/mcp.json",
    ".devin/mcp_config.local.json",
    ".agents/mcp_config.json",
)
STATE_START, STATE_END = "<!-- factory:sessions:start -->", "<!-- factory:sessions:end -->"
INCIDENTS_START, INCIDENTS_END = "<!-- factory:incidents:start -->", "<!-- factory:incidents:end -->"
MAX_DIFF_CHARS = 200_000
CI_STATUSES = ("GREEN", "NOT_CONFIGURED", "NO_CHECKS", "INFRA_BLOCKED", "FAILED_PREEXISTING", "FAILED")
BLOCKER_TYPES = ("RETRY_CAP", "INFRA", "NEEDS_DECISION")
INCIDENT_CATEGORIES = ("PERMISSION", "AUTH", "RATE_LIMIT", "THIRD_PARTY", "ENVIRONMENT", "OTHER")


class HubError(Exception):
    """An expected failure reported back to the agent as a tool error."""


def log(message: str) -> None:
    print(f"[{SERVER_NAME}] {message}", file=sys.stderr, flush=True)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def minutes_since(timestamp: Optional[str]) -> Optional[int]:
    if not timestamp:
        return None
    then = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    return int((datetime.now(timezone.utc) - then).total_seconds() // 60)


def run_git(args: list[str], cwd: Path) -> str:
    try:
        proc = subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
    except OSError as exc:
        raise HubError(f"Could not run git ({exc}). Is git installed and on PATH?") from exc
    if proc.returncode:
        raise HubError(f"git {' '.join(args)} failed: {(proc.stderr or proc.stdout).strip()}")
    return proc.stdout.strip()


def find_main_repo_root(start: Path) -> Path:
    common = Path(run_git(["rev-parse", "--git-common-dir"], start))
    if not common.is_absolute():
        common = start / common
    return common.resolve().parent


def default_repo_root() -> Path:
    env = os.environ.get("FACTORY_REPO_ROOT")
    if env:
        return find_main_repo_root(Path(env))
    for start in (Path(__file__).resolve().parent, Path.cwd()):
        try:
            return find_main_repo_root(start)
        except HubError:
            continue
    raise HubError("Could not locate a git repository. Pass --repo or set FACTORY_REPO_ROOT.")


def _retry(fn, attempts: int = 40):
    # Windows briefly denies access to files another process is replacing.
    for _ in range(attempts - 1):
        try:
            return fn()
        except PermissionError:
            time.sleep(0.05)
    return fn()


def read_json(path: Path) -> dict:
    return _retry(lambda: json.loads(path.read_text(encoding="utf-8")))


def write_atomic(path: Path, text: str) -> None:
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_text(text, encoding="utf-8")
    _retry(lambda: os.replace(tmp, path))


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    text = _retry(lambda: path.read_text(encoding="utf-8"))
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def append_jsonl(path: Path, record: dict) -> None:
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")


class FileLock:
    """Cross-process lock using an exclusively created lock file."""

    def __init__(self, path: Path, timeout: float = 10.0, stale_after: float = 30.0):
        self.path, self.timeout, self.stale_after = path, timeout, stale_after

    def __enter__(self) -> "FileLock":
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                os.close(os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
                return self
            except (FileExistsError, PermissionError):
                try:
                    if time.time() - self.path.stat().st_mtime > self.stale_after:
                        self.path.unlink()
                        continue
                except (FileNotFoundError, PermissionError):
                    pass
                if time.monotonic() > deadline:
                    raise HubError(f"Timed out waiting for lock {self.path}")
                time.sleep(0.02)

    def __exit__(self, *exc) -> None:
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


class SessionHub:
    def __init__(self, repo_root: Path):
        self.root = repo_root
        self.sessions = repo_root / ".factory" / "sessions"
        self.archive = self.sessions / "archive"

    # ---- helpers -----------------------------------------------------------

    def _session_dir(self, session_id: str) -> Path:
        if not SESSION_ID_RE.match(session_id or ""):
            raise HubError(f"Invalid sessionId {session_id!r}; expected something like 'sess_m1-02'.")
        path = self.sessions / session_id
        if not (path / "session.json").is_file():
            raise HubError(f"No active session {session_id!r}. Use factory_session_list to see sessions.")
        return path

    def _lock(self, session_dir: Path) -> FileLock:
        return FileLock(session_dir / "session.lock")

    def _save(self, session_dir: Path, session: dict) -> None:
        session["updatedAt"] = now()
        write_atomic(session_dir / "session.json", json.dumps(session, indent=2) + "\n")

    def _active_dirs(self) -> list[Path]:
        if not self.sessions.is_dir():
            return []
        return sorted(p for p in self.sessions.iterdir() if p.name != "archive" and (p / "session.json").is_file())

    def _exclude_locally(self, patterns: list[str]) -> None:
        common = Path(run_git(["rev-parse", "--git-common-dir"], self.root))
        exclude = (common if common.is_absolute() else self.root / common) / "info" / "exclude"
        exclude.parent.mkdir(parents=True, exist_ok=True)
        existing = exclude.read_text(encoding="utf-8").splitlines() if exclude.exists() else []
        missing = [p for p in patterns if p not in existing]
        if missing:
            prefix = "" if not existing or existing[-1] == "" else "\n"
            with exclude.open("a", encoding="utf-8") as fh:
                fh.write(prefix + "\n".join(["# factory-loop (machine-specific)", *missing]) + "\n")

    def _copy_host_configs(self, worktree: Path) -> list[str]:
        copied = []
        for rel in HOST_CONFIG_FILES:
            src, dst = self.root / rel, worktree / rel
            if src.is_file() and not dst.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                copied.append(rel)
        return copied

    def _sync_state(self) -> None:
        state = self.root / ".factory" / "SESSION_STATE.md"
        if not state.is_file():
            return
        self.sessions.mkdir(parents=True, exist_ok=True)
        with FileLock(self.sessions / "state.lock"):
            text = state.read_text(encoding="utf-8")
            rows = []
            for d in self._active_dirs():
                s = read_json(d / "session.json")
                contact = s.get("lastWorkerContactAt") or "never"
                note = ((s.get("lastProgress") or {}).get("note") or "").replace("|", "/")[:80]
                rows.append(
                    f"| `{s['issueId']}` | `{s['branchName']}` | `{s['worktreePath']}` "
                    f"| {s.get('prUrl') or '-'} | `{s['status']}`{self._status_suffix(s)} "
                    f"| {contact}{' - ' + note if note else ''} |"
                )
            table = "\n".join(
                [
                    "| Issue ID | Branch | Worktree Path | PR Link / # | Status | Last Worker Contact |",
                    "| :--- | :--- | :--- | :--- | :--- | :--- |",
                    *(rows or ["| *(None currently active)* | | | | | |"]),
                ]
            )
            incident_rows = [
                f"| {i['id']} | {i['category']} | {', '.join(i['sessions']) or '-'} "
                f"| {i['summary'].replace('|', '/')[:120]} | {'yes' if i['needsHuman'] else 'no'} "
                f"| {i['occurrences']} | {i['createdAt']} |"
                for i in self._incidents().values()
                if i["status"] == "OPEN"
            ]
            incidents = "\n".join(
                [
                    "| Incident | Category | Sessions | Summary | Needs Human | Occurrences | Reported |",
                    "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
                    *(incident_rows or ["| *(No open incidents)* | | | | | | |"]),
                ]
            )
            new = _replace_block(_replace_block(text, STATE_START, STATE_END, table), INCIDENTS_START, INCIDENTS_END, incidents)
            if new != text:
                write_atomic(state, new)

    # ---- incidents -----------------------------------------------------------

    def _incidents(self) -> dict:
        incidents: dict[str, dict] = {}
        for event in read_jsonl(self.sessions / "incidents.jsonl"):
            kind, inc = event["event"], incidents.get(event["id"])
            if kind == "open":
                incidents[event["id"]] = {
                    **{k: v for k, v in event.items() if k != "event"},
                    "status": "OPEN",
                    "occurrences": 1,
                    "sessions": [event["sessionId"]] if event.get("sessionId") else [],
                    "resolution": None,
                }
            elif inc and kind == "repeat":
                inc["occurrences"] += 1
                inc["lastSeenAt"] = event["at"]
                if event.get("sessionId") and event["sessionId"] not in inc["sessions"]:
                    inc["sessions"].append(event["sessionId"])
            elif inc and kind == "resolve":
                inc.update(status="RESOLVED", resolution=event["resolution"], resolvedAt=event["at"])
        return incidents

    def _open_incidents(self, session_id: Optional[str] = None) -> list[dict]:
        return [
            i for i in self._incidents().values()
            if i["status"] == "OPEN" and (session_id is None or session_id in i["sessions"])
        ]

    @staticmethod
    def _status_suffix(session: dict) -> str:
        if session.get("status") == "BLOCKED" and session.get("blockerType"):
            return f" ({session['blockerType']})"
        ci = session.get("ciStatus")
        return f" (CI: {ci})" if ci and ci != "GREEN" else ""

    @staticmethod
    def _summary(session: dict, worktree_missing: bool) -> dict:
        keys = (
            "sessionId", "issueId", "status", "branchName", "worktreePath", "prUrl", "reviewRound", "updatedAt",
            "lastWorkerContactAt", "lastProgress", "ciStatus", "ciDetails", "blockerType", "blockedReason",
        )
        return {
            **{k: session.get(k) for k in keys},
            "minutesSinceWorkerContact": minutes_since(session.get("lastWorkerContactAt")),
            "minutesSinceDispatch": minutes_since(session.get("createdAt")),
            "worktreeMissing": worktree_missing,
        }

    # ---- orchestrator tools --------------------------------------------------

    def dispatch(
        self,
        issueId: str,
        branchName: str,
        targetFiles: list[str],
        issueDescription: str,
        baseBranch: Optional[str] = None,
    ) -> dict:
        if not ISSUE_ID_RE.match(issueId):
            raise HubError(f"Invalid issueId {issueId!r}; use letters, digits, '.', '_' or '-' (e.g. 'M1-02').")
        session_id = "sess_" + issueId.lower()
        session_dir = self.sessions / session_id
        worktree = self.root.parent / f"wt-{issueId}"
        if worktree.exists():
            raise HubError(f"Worktree path already exists: {worktree.as_posix()}")
        base = baseBranch or run_git(["rev-parse", "--abbrev-ref", "HEAD"], self.root)
        self.sessions.mkdir(parents=True, exist_ok=True)
        try:
            session_dir.mkdir()
        except FileExistsError:
            raise HubError(f"Session {session_id} already exists. Tear it down before dispatching again.") from None
        try:
            run_git(["worktree", "add", str(worktree), "-b", branchName, base], self.root)
        except HubError:
            shutil.rmtree(session_dir, ignore_errors=True)
            raise
        copied = self._copy_host_configs(worktree)
        self._exclude_locally(["/.factory/sessions/", *("/" + rel for rel in copied)])
        session = {
            "sessionId": session_id,
            "issueId": issueId,
            "branchName": branchName,
            "baseBranch": base,
            "worktreePath": worktree.resolve().as_posix(),
            "targetFiles": targetFiles,
            "issueDescription": issueDescription,
            "status": "IN_PROGRESS",
            "reviewRound": 0,
            "prUrl": None,
            "lastReport": None,
            "blockedReason": None,
            "inboxReadCount": 0,
            "lastWorkerContactAt": None,
            "lastProgress": None,
            "createdAt": now(),
        }
        with self._lock(session_dir):
            self._save(session_dir, session)
            (session_dir / "inbox.jsonl").touch()
            (session_dir / "reports.jsonl").touch()
            (session_dir / "progress.jsonl").touch()
        self._sync_state()
        return {
            "sessionId": session_id,
            "worktreePath": session["worktreePath"],
            "branchName": branchName,
            "baseBranch": base,
            "copiedHostConfigs": copied,
            "nextStep": (
                "Spawn a subagent working inside worktreePath. Give it the sessionId and the issue block, and tell it "
                "to follow .factory/skills/subagent-worker.md (or bugfix-issue.md for bugs)."
            ),
        }

    def list_sessions(self, includeArchived: bool = False) -> dict:
        try:
            run_git(["worktree", "prune"], self.root)
        except HubError as exc:
            log(str(exc))
        sessions = []
        for d in self._active_dirs():
            s = read_json(d / "session.json")
            sessions.append(self._summary(s, not Path(s["worktreePath"]).exists()))
        result: dict[str, Any] = {"sessions": sessions, "openIncidents": self._open_incidents()}
        if includeArchived and self.archive.is_dir():
            result["archived"] = [
                self._summary(read_json(d / "session.json"), True)
                for d in sorted(self.archive.iterdir())
                if (d / "session.json").is_file()
            ]
        return result

    def get_status(self, sessionId: str, includeDiff: bool = False) -> dict:
        session_dir = self._session_dir(sessionId)
        session = read_json(session_dir / "session.json")
        reports = read_jsonl(session_dir / "reports.jsonl")
        messages = read_jsonl(session_dir / "inbox.jsonl")
        progress = read_jsonl(session_dir / "progress.jsonl")
        for i, msg in enumerate(messages):
            msg["read"] = i < session.get("inboxReadCount", 0)
        result: dict[str, Any] = {
            "session": session,
            "latestReport": reports[-1] if reports else None,
            "reports": reports,
            "messages": messages,
            "progress": progress[-50:],
            "incidents": [i for i in self._incidents().values() if sessionId in i["sessions"]],
        }
        if includeDiff:
            result["diff"] = self._diff(session)
        return result

    def _diff(self, session: dict) -> dict:
        source, text = None, None
        if session.get("prUrl", "") and str(session["prUrl"]).startswith("http") and shutil.which("gh"):
            try:
                proc = subprocess.run(
                    ["gh", "pr", "diff", session["prUrl"]],
                    cwd=self.root, capture_output=True, text=True, encoding="utf-8", errors="replace",
                )
                if proc.returncode == 0:
                    source, text = "gh pr diff", proc.stdout
            except OSError:
                pass
        if text is None:
            spec = f"{session['baseBranch']}...{session['branchName']}"
            source, text = f"git diff {spec}", run_git(["diff", spec], self.root)
        truncated = len(text) > MAX_DIFF_CHARS
        return {"source": source, "truncated": truncated, "text": text[:MAX_DIFF_CHARS]}

    def send_feedback(self, sessionId: str, feedbackMarkdown: str, round: Optional[int] = None) -> dict:
        session_dir = self._session_dir(sessionId)
        if round is not None and round < 1:
            raise HubError("round must be 1 or greater (omit it for non-review instructions).")
        with self._lock(session_dir):
            session = read_json(session_dir / "session.json")
            if round is not None and round > MAX_REVIEW_ROUNDS:
                session.update(status="BLOCKED", blockedReason="REVIEW_ROUNDS_EXCEEDED")
                self._save(session_dir, session)
                blocked = True
            else:
                blocked = False
                if round is not None:
                    session["reviewRound"] = max(session.get("reviewRound", 0), round)
                inbox = session_dir / "inbox.jsonl"
                append_jsonl(
                    inbox,
                    {
                        "index": len(read_jsonl(inbox)),
                        "kind": "review" if round is not None else "instruction",
                        "round": round,
                        "markdown": feedbackMarkdown,
                        "createdAt": now(),
                    },
                )
                session.update(status="CHANGES_REQUESTED", blockedReason=None)
                self._save(session_dir, session)
        self._sync_state()
        if blocked:
            return {
                "status": "BLOCKED",
                "escalate": True,
                "message": (
                    f"Review round limit ({MAX_REVIEW_ROUNDS}) exceeded; the feedback was NOT delivered. Escalate to "
                    "the human user. To continue after their decision, send an instruction without 'round'."
                ),
            }
        return {
            "status": "CHANGES_REQUESTED",
            "reviewRound": session["reviewRound"],
            "nextStep": (
                "Resume the worker subagent and tell it to call factory_worker_check_inbox. If it cannot be resumed, "
                "spawn a fresh subagent inside worktreePath with the same sessionId."
            ),
        }

    def teardown(self, sessionId: str, removeWorktree: bool) -> dict:
        session_dir = self._session_dir(sessionId)
        with self._lock(session_dir):
            session = read_json(session_dir / "session.json")
            worktree = Path(session["worktreePath"])
            removed = False
            if removeWorktree and worktree.exists():
                dirty = run_git(["status", "--porcelain"], worktree)
                if dirty:
                    raise HubError(
                        f"Worktree {worktree.as_posix()} has uncommitted changes; commit or discard them first:\n{dirty}"
                    )
                run_git(["worktree", "remove", str(worktree)], self.root)
                removed = True
            elif removeWorktree:
                run_git(["worktree", "prune"], self.root)
            session.update(status="ARCHIVED", archivedAt=now())
            self._save(session_dir, session)
        self.archive.mkdir(parents=True, exist_ok=True)
        dest = self.archive / sessionId
        if dest.exists():
            dest = self.archive / f"{sessionId}-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}"
        _retry(lambda: shutil.move(str(session_dir), str(dest)))
        self._sync_state()
        return {
            "sessionId": sessionId,
            "status": "ARCHIVED",
            "worktreeRemoved": removed,
            "archivePath": dest.as_posix(),
            "note": f"Branch {session['branchName']} was kept; delete it yourself if it is no longer needed.",
        }

    # ---- worker tools --------------------------------------------------------

    def worker_report(
        self,
        sessionId: str,
        status: str,
        prUrl: Optional[str] = None,
        testResults: Optional[str] = None,
        notesForLearnings: Optional[str] = None,
        blockedReason: Optional[str] = None,
        ciStatus: Optional[str] = None,
        ciDetails: Optional[str] = None,
        blockerType: Optional[str] = None,
    ) -> dict:
        if status not in ("WAITING_FOR_REVIEW", "BLOCKED"):
            raise HubError("status must be 'WAITING_FOR_REVIEW' or 'BLOCKED'.")
        if status == "BLOCKED" and not blockedReason:
            raise HubError("blockedReason is required when status is 'BLOCKED'.")
        if ciStatus is not None and ciStatus not in CI_STATUSES:
            raise HubError(f"ciStatus must be one of {list(CI_STATUSES)}.")
        if blockerType is not None and blockerType not in BLOCKER_TYPES:
            raise HubError(f"blockerType must be one of {list(BLOCKER_TYPES)}.")
        if status == "WAITING_FOR_REVIEW" and ciStatus == "FAILED":
            raise HubError(
                "CI failed because of your change: fix it and re-verify, or report BLOCKED. If the failure is "
                "infrastructure (billing, runners, secrets, permissions) use ciStatus INFRA_BLOCKED; if it comes from "
                "pre-existing code outside your Target Files use FAILED_PREEXISTING."
            )
        if ciStatus in ("INFRA_BLOCKED", "FAILED_PREEXISTING") and not ciDetails:
            raise HubError(f"ciDetails is required for ciStatus {ciStatus}: include the exact error message.")
        session_dir = self._session_dir(sessionId)
        with self._lock(session_dir):
            session = read_json(session_dir / "session.json")
            if status == "WAITING_FOR_REVIEW":
                if session["status"] == "CHANGES_REQUESTED":
                    raise HubError(
                        "Unread Orchestrator messages are waiting. Call factory_worker_check_inbox, address them, "
                        "re-verify, then report again."
                    )
                if not (prUrl or session.get("prUrl")):
                    raise HubError("prUrl is required (PR link, or the pushed branch name if no PR could be opened).")
            report = {
                "status": status,
                "prUrl": prUrl or session.get("prUrl"),
                "testResults": testResults,
                "notesForLearnings": notesForLearnings,
                "blockedReason": blockedReason,
                "ciStatus": ciStatus,
                "ciDetails": ciDetails,
                "blockerType": blockerType if status == "BLOCKED" else None,
                "createdAt": now(),
            }
            append_jsonl(session_dir / "reports.jsonl", report)
            session.update(
                status=status,
                prUrl=report["prUrl"],
                lastReport={"testResults": testResults, "notesForLearnings": notesForLearnings},
                blockedReason=blockedReason if status == "BLOCKED" else None,
                blockerType=report["blockerType"],
                ciStatus=ciStatus,
                ciDetails=ciDetails,
                lastWorkerContactAt=now(),
            )
            self._save(session_dir, session)
        self._sync_state()
        return {
            "status": status,
            "nextStep": (
                "Stop and return your Worker Completion Report. Keep the worktree; the Orchestrator will review and "
                "either merge or send feedback (check your inbox when you are resumed)."
            ),
        }

    def worker_check_inbox(self, sessionId: str) -> dict:
        session_dir = self._session_dir(sessionId)
        with self._lock(session_dir):
            session = read_json(session_dir / "session.json")
            messages = read_jsonl(session_dir / "inbox.jsonl")
            unread = messages[session.get("inboxReadCount", 0):]
            session["inboxReadCount"] = len(messages)
            session["lastWorkerContactAt"] = now()
            if session["status"] == "CHANGES_REQUESTED":
                session["status"] = "IN_PROGRESS"
            self._save(session_dir, session)
        self._sync_state()
        return {
            "sessionId": sessionId,
            "issueId": session["issueId"],
            "status": session["status"],
            "branchName": session["branchName"],
            "worktreePath": session["worktreePath"],
            "messages": unread,
            "nextStep": (
                "Address every message on the same branch, re-run local checks and CI, then call factory_worker_report."
                if unread
                else "No new messages."
            ),
        }


    def worker_progress(self, sessionId: str, note: str) -> dict:
        note = note.strip()
        if not note:
            raise HubError("note must not be empty.")
        session_dir = self._session_dir(sessionId)
        with self._lock(session_dir):
            session = read_json(session_dir / "session.json")
            entry = {"note": note[:500], "at": now()}
            append_jsonl(session_dir / "progress.jsonl", entry)
            session.update(lastProgress=entry, lastWorkerContactAt=entry["at"])
            self._save(session_dir, session)
        self._sync_state()
        return {
            "recorded": entry,
            "status": session["status"],
            "nextStep": (
                "Unread Orchestrator messages are waiting: call factory_worker_check_inbox."
                if session["status"] == "CHANGES_REQUESTED"
                else "Continue."
            ),
        }


    def report_incident(
        self,
        category: str,
        summary: str,
        details: str,
        suggestedActions: Optional[list[str]] = None,
        needsHuman: bool = False,
        blocking: bool = False,
        sessionId: Optional[str] = None,
    ) -> dict:
        if category not in INCIDENT_CATEGORIES:
            raise HubError(f"category must be one of {list(INCIDENT_CATEGORIES)}.")
        summary, details = summary.strip(), details.strip()
        if not summary or not details:
            raise HubError("summary and details must not be empty; include the exact error message in details.")
        session_dir = self._session_dir(sessionId) if sessionId else None
        self.sessions.mkdir(parents=True, exist_ok=True)
        log_path = self.sessions / "incidents.jsonl"
        with FileLock(self.sessions / "incidents.lock"):
            existing = next(
                (
                    i for i in self._incidents().values()
                    if i["status"] == "OPEN" and i["category"] == category
                    and i["summary"].strip().lower() == summary.lower()
                ),
                None,
            )
            if existing:
                incident_id = existing["id"]
                append_jsonl(log_path, {"event": "repeat", "id": incident_id, "sessionId": sessionId, "at": now()})
            else:
                incident_id = f"INC-{len(self._incidents()) + 1:03d}"
                append_jsonl(
                    log_path,
                    {
                        "event": "open",
                        "id": incident_id,
                        "category": category,
                        "summary": summary[:300],
                        "details": details[:4000],
                        "suggestedActions": suggestedActions or [],
                        "needsHuman": needsHuman,
                        "blocking": blocking,
                        "sessionId": sessionId,
                        "reporter": "worker" if sessionId else "orchestrator",
                        "createdAt": now(),
                    },
                )
        if session_dir:
            with self._lock(session_dir):
                session = read_json(session_dir / "session.json")
                session["incidents"] = sorted({*session.get("incidents", []), incident_id})
                session["lastWorkerContactAt"] = now()
                if blocking:
                    session.update(
                        status="BLOCKED",
                        blockedReason=f"{incident_id}: {summary}",
                        blockerType="NEEDS_DECISION" if needsHuman else "INFRA",
                    )
                self._save(session_dir, session)
        self._sync_state()
        incident = self._incidents()[incident_id]
        if not sessionId:
            next_step = "Triage it: apply a safe fix and call factory_resolve_incident, or ask the user."
        elif blocking:
            next_step = (
                "Stop work and return a short report naming " + incident_id + ". The Orchestrator will resolve it "
                "or ask the user, then resume you; check your inbox when resumed."
            )
        else:
            next_step = "Continue with work that doesn't depend on this, and mention " + incident_id + " in your report."
        return {
            "incidentId": incident_id,
            "isRepeat": existing is not None,
            "occurrences": incident["occurrences"],
            "sessions": incident["sessions"],
            "nextStep": next_step,
        }

    def resolve_incident(self, incidentId: str, resolution: str) -> dict:
        resolution = resolution.strip()
        if not resolution:
            raise HubError("resolution must describe what was done (or decided).")
        self.sessions.mkdir(parents=True, exist_ok=True)
        with FileLock(self.sessions / "incidents.lock"):
            incident = self._incidents().get(incidentId)
            if not incident:
                raise HubError(f"Unknown incident {incidentId!r}.")
            if incident["status"] == "RESOLVED":
                raise HubError(f"{incidentId} is already resolved: {incident['resolution']}")
            append_jsonl(
                self.sessions / "incidents.jsonl",
                {"event": "resolve", "id": incidentId, "resolution": resolution, "at": now()},
            )
        self._sync_state()
        to_unblock = []
        for sid in incident["sessions"]:
            try:
                s = read_json(self._session_dir(sid) / "session.json")
            except HubError:
                continue
            if s["status"] == "BLOCKED" and str(s.get("blockedReason", "")).startswith(incidentId):
                to_unblock.append(sid)
        return {
            "incidentId": incidentId,
            "status": "RESOLVED",
            "sessionsToUnblock": to_unblock,
            "nextStep": (
                "Send each session in sessionsToUnblock an instruction (factory_session_send_feedback without round) "
                "describing the resolution, then resume it. Add a LEARNINGS.md bullet if the fix is reusable."
                if to_unblock
                else "No blocked sessions are waiting on this incident."
            ),
        }


def _replace_block(text: str, start_marker: str, end_marker: str, body: str) -> str:
    start, end = text.find(start_marker), text.find(end_marker)
    if start == -1 or end < start:
        return text
    return text[: start + len(start_marker)] + "\n" + body + "\n" + text[end:]


# ---- MCP layer ---------------------------------------------------------------

_SID = {"type": "string", "description": "Session id returned by factory_session_dispatch, e.g. 'sess_m1-02'."}
TOOLS: list[dict] = [
    {
        "name": "factory_session_dispatch",
        "description": (
            "[Orchestrator] Create an isolated git worktree (../wt-<issueId>) on a new branch for one backlog issue and "
            "register a session for it. Returns sessionId and worktreePath to hand to the worker subagent."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "issueId": {"type": "string", "description": "Backlog issue id, e.g. 'M1-02'."},
                "branchName": {"type": "string", "description": "New branch, e.g. 'feat/M1-02-auth-middleware'."},
                "targetFiles": {"type": "array", "items": {"type": "string"}, "description": "Target Files from the issue."},
                "issueDescription": {"type": "string", "description": "The exact issue block from BACKLOG.md."},
                "baseBranch": {"type": "string", "description": "Branch to start from (default: current branch)."},
            },
            "required": ["issueId", "branchName", "targetFiles", "issueDescription"],
        },
        "method": "dispatch",
    },
    {
        "name": "factory_session_list",
        "description": (
            "[Orchestrator] List sessions with status, branch, worktree, PR, last worker progress note, and minutes "
            "since the worker last made contact (stall detection). Use on startup/resume and while waiting."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"includeArchived": {"type": "boolean", "description": "Also list archived sessions."}},
        },
        "method": "list_sessions",
    },
    {
        "name": "factory_session_get_status",
        "description": (
            "[Orchestrator or worker] Full session record, all worker reports, and all Orchestrator messages. "
            "Workers started fresh for an existing session use this to rebuild context."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "sessionId": _SID,
                "includeDiff": {"type": "boolean", "description": "Include the PR diff (gh) or base...branch git diff."},
            },
            "required": ["sessionId"],
        },
        "method": "get_status",
    },
    {
        "name": "factory_session_send_feedback",
        "description": (
            "[Orchestrator] Queue review feedback (with round 1-3) or an instruction (no round, e.g. 'rebase onto "
            "main' or a human decision) for a worker. Sets status CHANGES_REQUESTED; round > 3 blocks the session."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "sessionId": _SID,
                "feedbackMarkdown": {"type": "string", "description": "Concrete, line-specific feedback."},
                "round": {"type": "integer", "description": "Review round number; omit for non-review instructions."},
            },
            "required": ["sessionId", "feedbackMarkdown"],
        },
        "method": "send_feedback",
    },
    {
        "name": "factory_session_teardown",
        "description": (
            "[Orchestrator] After merge (or abandonment): optionally remove the worktree (refused if it has "
            "uncommitted changes) and archive the session. The branch is kept."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"sessionId": _SID, "removeWorktree": {"type": "boolean"}},
            "required": ["sessionId", "removeWorktree"],
        },
        "method": "teardown",
    },
    {
        "name": "factory_worker_report",
        "description": (
            "[Worker] Report WAITING_FOR_REVIEW once local checks pass and the PR is open, with ciStatus describing "
            "remote CI (infrastructure problems such as billing limits are INFRA_BLOCKED: report them, don't retry), "
            "or BLOCKED with a reason and blockerType when a retry cap, infrastructure blocker, or decision stops you."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "sessionId": _SID,
                "status": {"type": "string", "enum": ["WAITING_FOR_REVIEW", "BLOCKED"]},
                "prUrl": {"type": "string", "description": "PR link (or pushed branch name if no PR could be opened)."},
                "testResults": {"type": "string", "description": "Build/lint/test/CI results summary."},
                "notesForLearnings": {"type": "string", "description": "Reusable gotchas for LEARNINGS.md, if any."},
                "blockedReason": {"type": "string", "description": "Required when status is BLOCKED."},
                "ciStatus": {
                    "type": "string",
                    "enum": list(CI_STATUSES),
                    "description": "Remote CI result. FAILED cannot be reported as WAITING_FOR_REVIEW.",
                },
                "ciDetails": {
                    "type": "string",
                    "description": "Exact CI message; required for INFRA_BLOCKED and FAILED_PREEXISTING.",
                },
                "blockerType": {"type": "string", "enum": list(BLOCKER_TYPES), "description": "Why BLOCKED."},
            },
            "required": ["sessionId", "status"],
        },
        "method": "worker_report",
    },
    {
        "name": "factory_worker_check_inbox",
        "description": (
            "[Worker] Return unread Orchestrator messages and mark them read. Call at startup and whenever resumed; "
            "do not poll in a loop."
        ),
        "inputSchema": {"type": "object", "properties": {"sessionId": _SID}, "required": ["sessionId"]},
        "method": "worker_check_inbox",
    },
    {
        "name": "factory_worker_progress",
        "description": (
            "[Worker] Record a one-line progress note (heartbeat) at startup and after each major step, e.g. "
            "'local checks passing', 'PR opened, waiting for CI'. Lets the Orchestrator detect stalled sessions."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "sessionId": _SID,
                "note": {"type": "string", "description": "Short description of the step just completed or started."},
            },
            "required": ["sessionId", "note"],
        },
        "method": "worker_progress",
    },
    {
        "name": "factory_report_incident",
        "description": (
            "[Worker or Orchestrator] Record something outside your control instead of retrying it: tool/OS/security "
            "permission blocks (e.g. Windows Controlled Folder Access), missing or expired credentials, API key/rate/"
            "quota/billing limits, CI/CD or third-party failures, network problems, missing tools. Duplicate open "
            "incidents are merged. blocking=true also marks the session BLOCKED."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": list(INCIDENT_CATEGORIES),
                    "description": (
                        "PERMISSION (tool/OS/security block), AUTH (credentials/secrets), RATE_LIMIT (rate, quota, "
                        "API key or billing limits), THIRD_PARTY (CI/CD, external API/service, network), "
                        "ENVIRONMENT (missing tool/dependency, disk, OS), OTHER."
                    ),
                },
                "summary": {"type": "string", "description": "One line, stable wording (used to merge duplicates)."},
                "details": {
                    "type": "string",
                    "description": "Exact error message, where it happened, and what you already tried.",
                },
                "suggestedActions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Concrete options to resolve it, e.g. 'Allow node.exe in Controlled Folder Access'.",
                },
                "needsHuman": {"type": "boolean", "description": "True if only the user can fix or decide it."},
                "blocking": {"type": "boolean", "description": "True if you cannot continue your issue."},
                "sessionId": {**_SID, "description": "Your sessionId (workers). Omit when the Orchestrator reports."},
            },
            "required": ["category", "summary", "details"],
        },
        "method": "report_incident",
    },
    {
        "name": "factory_resolve_incident",
        "description": (
            "[Orchestrator] Close an incident after applying a fix or getting the user's decision. Returns the "
            "sessions blocked by it so you can send them instructions and resume them."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "incidentId": {"type": "string", "description": "e.g. 'INC-001'."},
                "resolution": {"type": "string", "description": "What was done or decided."},
            },
            "required": ["incidentId", "resolution"],
        },
        "method": "resolve_incident",
    },
]
TOOLS_BY_NAME = {t["name"]: t for t in TOOLS}
_JSON_TYPES = {"string": str, "boolean": bool, "integer": int, "array": list, "object": dict}


def _validate(tool: dict, args: Any) -> dict:
    if not isinstance(args, dict):
        raise HubError("arguments must be an object.")
    schema = tool["inputSchema"]
    props = schema.get("properties", {})
    missing = [k for k in schema.get("required", []) if args.get(k) is None]
    if missing:
        raise HubError(f"Missing required argument(s): {', '.join(missing)}.")
    clean = {}
    for key, value in args.items():
        if key not in props or value is None:
            continue
        expected = props[key]["type"]
        ok = isinstance(value, _JSON_TYPES[expected]) and not (expected == "integer" and isinstance(value, bool))
        if not ok:
            raise HubError(f"Argument '{key}' must be of type {expected}.")
        if "enum" in props[key] and value not in props[key]["enum"]:
            raise HubError(f"Argument '{key}' must be one of {props[key]['enum']}.")
        clean[key] = value
    return clean


class McpServer:
    def __init__(self, repo_root: Optional[Path] = None):
        self._repo_root = repo_root
        self._hub: Optional[SessionHub] = None

    @property
    def hub(self) -> SessionHub:
        if self._hub is None:
            root = find_main_repo_root(self._repo_root) if self._repo_root else default_repo_root()
            self._hub = SessionHub(root)
            log(f"using repository {root.as_posix()}")
        return self._hub

    def call_tool(self, params: dict) -> dict:
        tool = TOOLS_BY_NAME[params["name"]]
        try:
            args = _validate(tool, params.get("arguments") or {})
            data = getattr(self.hub, tool["method"])(**args)
            return {"content": [{"type": "text", "text": json.dumps(data, indent=2)}], "isError": False}
        except HubError as exc:
            return {"content": [{"type": "text", "text": str(exc)}], "isError": True}
        except Exception as exc:  # report unexpected failures as tool errors instead of crashing the server
            log(traceback.format_exc())
            return {"content": [{"type": "text", "text": f"Internal error: {exc}"}], "isError": True}

    def handle(self, msg: Any) -> Optional[dict]:
        if not isinstance(msg, dict) or msg.get("jsonrpc") != "2.0":
            return _error(msg.get("id") if isinstance(msg, dict) else None, -32600, "Invalid Request")
        method, msg_id, is_request = msg.get("method"), msg.get("id"), "id" in msg
        if method is None:
            return None  # a response to something we never send; ignore
        params = msg.get("params") or {}
        if method == "initialize":
            requested = params.get("protocolVersion")
            result: Any = {
                "protocolVersion": requested if requested in SUPPORTED_PROTOCOLS else SUPPORTED_PROTOCOLS[0],
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                "instructions": (
                    "Session hub for the factory-loop workflow. Orchestrators use factory_session_* tools; workers use "
                    "factory_worker_* tools with the sessionId they were given."
                ),
            }
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            result = {"tools": [{k: v for k, v in t.items() if k != "method"} for t in TOOLS]}
        elif method == "tools/call":
            if params.get("name") not in TOOLS_BY_NAME:
                return _error(msg_id, -32602, f"Unknown tool: {params.get('name')}") if is_request else None
            result = self.call_tool(params)
        elif not is_request:
            return None  # notifications such as notifications/initialized need no reply
        else:
            return _error(msg_id, -32601, f"Method not found: {method}")
        return {"jsonrpc": "2.0", "id": msg_id, "result": result} if is_request else None

    def serve(self, stdin=None, stdout=None) -> None:
        stdin = stdin or sys.stdin.buffer
        stdout = stdout or sys.stdout.buffer

        def send(payload: Any) -> None:
            stdout.write(json.dumps(payload).encode("utf-8") + b"\n")
            stdout.flush()

        for raw in stdin:
            line = raw.strip()
            if not line:
                continue
            try:
                msg = json.loads(line.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                send(_error(None, -32700, "Parse error"))
                continue
            if isinstance(msg, list):
                replies = [r for r in (self.handle(m) for m in msg) if r is not None]
                if replies:
                    send(replies)
            else:
                reply = self.handle(msg)
                if reply is not None:
                    send(reply)


def _error(msg_id: Any, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


def main() -> int:
    parser = argparse.ArgumentParser(description="factory-session-hub stdio MCP server (see module docstring).")
    parser.add_argument("--repo", type=Path, help="repository to manage (default: auto-detect)")
    parser.add_argument("--version", action="version", version=f"{SERVER_NAME} {SERVER_VERSION}")
    args = parser.parse_args()
    if sys.version_info < (3, 9):
        log("Python 3.9+ is required.")
        return 1
    try:
        McpServer(args.repo.resolve() if args.repo else None).serve()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
