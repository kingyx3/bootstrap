"""Company configuration: models per role, team size, and paths.

Everything is overridable via environment variables so you can tune cost and
scale without touching code.
"""
import os
from pathlib import Path

# --- Paths -----------------------------------------------------------------
COMPANY_ROOT = Path(__file__).resolve().parent      # the org's own runtime code
WORKSPACE_DIR = COMPANY_ROOT / "workspace"          # where engineers build product code
LOGS_DIR = COMPANY_ROOT / "logs"                    # run logs


def _load_dotenv(path: Path) -> None:
    """Load KEY=VALUE lines from a .env file into the environment (no dependency).

    Real exported environment variables win — we only set defaults for keys that
    are not already present. Lines that are blank, comments, or malformed are
    skipped; surrounding quotes on values are stripped.
    """
    if not path.exists():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


_load_dotenv(COMPANY_ROOT / ".env")

# --- Models per role -------------------------------------------------------
# The orchestrator and manager get the strong model; engineers run on a
# cheaper, fast model since there are many of them. See the model catalogue in
# ../PLAYBOOK.md and the repo docs for current IDs.
CEO_MODEL = os.environ.get("CEO_MODEL", "claude-opus-4-8")
MANAGER_MODEL = os.environ.get("MANAGER_MODEL", "claude-opus-4-8")
ENGINEER_MODEL = os.environ.get("ENGINEER_MODEL", "claude-sonnet-5")

# --- Team scale ------------------------------------------------------------
# How many engineers the Engineering Manager may run in parallel per round.
# This is the "scale the engineer to multiple engineers" knob.
MAX_ENGINEERS = int(os.environ.get("MAX_ENGINEERS", "3"))

# --- Project repository (named at inception) -------------------------------
# The GitHub repo this company works on. Set it once, when you start using this
# bootstrap template, e.g. PROJECT_REPO=your-org/your-product (or a full URL).
# When set, the repo is cloned into the workspace at startup and each engineer
# works in its own git worktree + branch of it. When empty, engineers build
# greenfield in ./workspace with no GitHub integration.
PROJECT_REPO = os.environ.get("PROJECT_REPO", "").strip()

# Token with access to PROJECT_REPO (used for clone/push and, if enabled, the
# GitHub MCP server). A fine-grained PAT scoped to just this repo is ideal.
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()

# Also expose the official GitHub MCP server to engineers (issues, PRs, etc.).
# Requires Docker + GITHUB_TOKEN. Git/gh over Bash works without this.
ENABLE_GITHUB_MCP = os.environ.get("ENABLE_GITHUB_MCP", "").lower() in ("1", "true", "yes")

WORKSPACE_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
