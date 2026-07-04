"""Project repository integration.

The target GitHub repo is named at inception via PROJECT_REPO (see config.py).
When set, this module:
  - clones the repo into the workspace once (ensure_base_clone),
  - gives each engineer its own isolated git worktree + branch
    (make_engineer_worktree), so parallel engineers never clobber each other,
  - optionally builds the GitHub MCP server config for richer GitHub tools.

Auth uses a git credential helper that reads $GITHUB_TOKEN from the environment
at run time, so the token is never written into .git/config or a remote URL.
"""
import asyncio
import re
import subprocess
from pathlib import Path

import config

# A credential helper that supplies the token from the environment on demand.
# The literal string is stored in git config; $GITHUB_TOKEN expands at auth time.
_CRED_HELPER = '!f() { echo username=x-access-token; echo "password=$GITHUB_TOKEN"; }; f'

_worktree_lock = asyncio.Lock()


def repo_configured() -> bool:
    return bool(config.PROJECT_REPO)


def repo_name() -> str:
    """Bare repo name, e.g. 'your-product' from 'your-org/your-product(.git)'."""
    tail = config.PROJECT_REPO.rstrip("/").split("/")[-1]
    return re.sub(r"\.git$", "", tail) or "repo"


def clone_url() -> str:
    """Normalise PROJECT_REPO (owner/name, https URL, or git@ URL) to a clone URL."""
    spec = config.PROJECT_REPO
    if spec.startswith(("http://", "https://", "git@")):
        return spec
    return f"https://github.com/{spec}.git"


def base_repo_dir() -> Path:
    return config.WORKSPACE_DIR / repo_name()


def _run(args: list[str], cwd: str | None = None) -> subprocess.CompletedProcess:
    """Run a command, raising a RuntimeError with the real stderr on failure.

    subprocess's CalledProcessError stringifies to just the exit code, which
    hides the git/gh error text from the agent. We surface stderr instead so the
    Engineering Manager (and logs) see why something failed.
    """
    try:
        proc = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    except FileNotFoundError as e:
        raise RuntimeError(f"'{args[0]}' is not installed or not on PATH") from e
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(detail or f"`{' '.join(args)}` failed (exit {proc.returncode})")
    return proc


def ensure_base_clone() -> Path | None:
    """Clone PROJECT_REPO into the workspace once. Returns the local path (or None)."""
    if not repo_configured():
        return None

    dest = base_repo_dir()
    if dest.exists():
        return dest

    url = clone_url()
    args = ["git"]
    use_helper = config.GITHUB_TOKEN and url.startswith("https://")
    if use_helper:
        args += ["-c", f"credential.helper={_CRED_HELPER}"]
    args += ["clone", url, str(dest)]
    _run(args)

    if use_helper:
        # Persist the (token-less) helper so future pushes on this clone authenticate.
        _run(["git", "-C", str(dest), "config", "credential.helper", _CRED_HELPER])
    return dest


async def make_engineer_worktree(engineer_id: str) -> Path:
    """Create (or reuse) an isolated worktree + branch for one engineer."""
    base = base_repo_dir()
    worktree = config.WORKSPACE_DIR / "engineers" / engineer_id
    branch = engineer_id  # e.g. "engineer-1"

    async with _worktree_lock:  # serialise worktree creation; execution stays parallel
        if not worktree.exists():
            worktree.parent.mkdir(parents=True, exist_ok=True)
            await asyncio.to_thread(
                _run,
                ["git", "-C", str(base), "worktree", "add", "-B", branch, str(worktree)],
            )
    return worktree


def open_pull_request(head_branch: str, title: str, body: str = "", base: str | None = None) -> str:
    """Open a PR from head_branch into base (default: repo default branch).

    Runs `gh pr create` in the base clone; authenticates via GITHUB_TOKEN in the
    environment. Raises on failure (missing gh, auth, or unknown branch) — the
    caller turns that into a tool error. Returns the PR URL on success.
    """
    args = ["gh", "pr", "create", "--head", head_branch,
            "--title", title, "--body", body or title]
    if base:
        args += ["--base", base]
    proc = _run(args, cwd=str(base_repo_dir()))
    return (proc.stdout or "").strip() or "Pull request created."


def merge_pull_request(pull_request: str, method: str = "squash") -> str:
    """Merge a PR into the default branch (which deploys to staging).

    `pull_request` is a PR number, URL, or branch. `method` is squash|merge|rebase.
    Runs `gh pr merge` in the base clone; raises on failure (not mergeable, checks
    failing, auth) so the caller can surface it as a tool error. This merges to
    STAGING only — production releases are the owner's decision and are not wired
    into the org.
    """
    flag = {"squash": "--squash", "merge": "--merge", "rebase": "--rebase"}.get(
        method, "--squash"
    )
    proc = _run(["gh", "pr", "merge", pull_request, flag], cwd=str(base_repo_dir()))
    return (proc.stdout or "").strip() or f"Merged {pull_request} into the default branch."


def github_mcp_server() -> dict | None:
    """Config for the official GitHub MCP server, or None if not enabled/possible."""
    if not (config.ENABLE_GITHUB_MCP and config.GITHUB_TOKEN):
        return None
    return {
        "command": "docker",
        "args": [
            "run", "-i", "--rm",
            "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
            "ghcr.io/github/github-mcp-server",
        ],
        "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": config.GITHUB_TOKEN},
    }
