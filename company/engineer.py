"""The Engineer — the individual contributor that does the actual building.

There is one `run_engineer` coroutine; the Engineering Manager scales it to many
concurrent engineers by calling it once per task under asyncio.gather.

When a project repo is configured (config.PROJECT_REPO), each engineer works in
its own isolated git worktree + branch of that repo and has GitHub in its
toolset (git/gh via Bash, plus the GitHub MCP server if enabled). Otherwise it
builds greenfield in ./workspace.
"""
from claude_agent_sdk import query, ClaudeAgentOptions, HookMatcher, ResultMessage

import config
from prompts import (
    ENGINEER_PROMPT,
    ENGINEER_WORK_CONTEXT_REPO,
    ENGINEER_WORK_CONTEXT_GREENFIELD,
)
from guards import block_dangerous_bash
import repo as repo_mod


async def run_engineer(engineer_id: str, task: str) -> str:
    """Run a single engineer on one self-contained task; return its report."""
    mcp_servers: dict = {}
    extra_tools: list[str] = []

    if repo_mod.repo_configured():
        workdir = await repo_mod.make_engineer_worktree(engineer_id)
        work_context = ENGINEER_WORK_CONTEXT_REPO.format(
            repo=repo_mod.repo_name(), branch=engineer_id
        )
        gh = repo_mod.github_mcp_server()
        if gh:
            mcp_servers["github"] = gh
            extra_tools.append("mcp__github__*")
    else:
        workdir = config.WORKSPACE_DIR
        work_context = ENGINEER_WORK_CONTEXT_GREENFIELD

    options = ClaudeAgentOptions(
        system_prompt=ENGINEER_PROMPT.format(
            engineer_id=engineer_id, work_context=work_context
        ),
        model=config.ENGINEER_MODEL,
        allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep", *extra_tools],
        permission_mode="acceptEdits",
        cwd=str(workdir),
        setting_sources=["project"],  # loads the target repo's CLAUDE.md/.claude, if any
        mcp_servers=mcp_servers,
        hooks={
            "PreToolUse": [HookMatcher(matcher="Bash", hooks=[block_dangerous_bash])],
        },
    )

    report = ""
    async for message in query(prompt=task, options=options):
        if isinstance(message, ResultMessage):
            report = message.result or ""
    return f"[{engineer_id}]\n{report}"
