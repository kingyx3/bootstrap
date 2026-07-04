"""The Engineer — the individual contributor that does the actual building.

There is one `run_engineer` coroutine; the Engineering Manager scales it to many
concurrent engineers by calling it once per task under asyncio.gather.

When a project repo is configured, each engineer works in its own isolated git
worktree + branch and pushes that branch. Engineers do NOT open pull requests —
that authority belongs to the Engineering Manager alone.
"""
from claude_agent_sdk import query, ClaudeAgentOptions, HookMatcher, ResultMessage

import config
from engineer.prompt import (
    ENGINEER_PROMPT,
    ENGINEER_WORK_CONTEXT_REPO,
    ENGINEER_WORK_CONTEXT_GREENFIELD,
)
from guards import block_dangerous_bash
import repo as repo_mod


async def run_engineer(engineer_id: str, task: str) -> str:
    """Run a single engineer on one self-contained task; return its report."""
    if repo_mod.repo_configured():
        workdir = await repo_mod.make_engineer_worktree(engineer_id)
        work_context = ENGINEER_WORK_CONTEXT_REPO.format(
            repo=repo_mod.repo_name(), branch=engineer_id
        )
    else:
        workdir = config.WORKSPACE_DIR
        work_context = ENGINEER_WORK_CONTEXT_GREENFIELD

    options = ClaudeAgentOptions(
        system_prompt=ENGINEER_PROMPT.format(
            engineer_id=engineer_id, work_context=work_context
        ),
        model=config.ENGINEER_MODEL,
        # Engineers get coding tools + Bash (git). No PR-creating tools: they push
        # branches; the guard blocks `gh pr create/merge` and pushes to main.
        allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
        permission_mode="acceptEdits",
        cwd=str(workdir),
        setting_sources=["project"],  # loads the target repo's CLAUDE.md/.claude, if any
        hooks={
            "PreToolUse": [HookMatcher(matcher="Bash", hooks=[block_dangerous_bash])],
        },
    )

    report = ""
    async for message in query(prompt=task, options=options):
        if isinstance(message, ResultMessage):
            report = message.result or ""
    return f"[{engineer_id}]\n{report}"
