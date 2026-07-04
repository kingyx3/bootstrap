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

WORKSPACE_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
