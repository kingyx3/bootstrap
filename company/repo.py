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
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True)


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
