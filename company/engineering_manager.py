"""The Engineering Manager — decomposes a brief, assigns tasks to a scalable pool
of engineers (in parallel), reviews their work, and reports up to the CEO.

The `assign_to_engineers` tool is the delegation bridge: when the manager agent
calls it, the handler fans out to N real engineer agents concurrently.
"""
import asyncio

from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    ResultMessage,
    tool,
    create_sdk_mcp_server,
)

import config
from prompts import ENGINEERING_MANAGER_PROMPT
from engineer import run_engineer
import repo as repo_mod


@tool(
    "assign_to_engineers",
    "Assign independent, self-contained engineering tasks to engineers. Each task "
    "is executed by its own engineer working in parallel; they report back with "
    "what they built. Split the work so no two tasks edit the same files.",
    {
        "type": "object",
        "properties": {
            "tasks": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "One self-contained task per engineer, including what to build, "
                    "paths under ./workspace, and acceptance criteria."
                ),
            }
        },
        "required": ["tasks"],
    },
)
async def assign_to_engineers(args):
    """Fan out tasks to concurrent engineers (this is where scaling happens)."""
    tasks = args.get("tasks", [])
    if not tasks:
        return {
            "content": [{"type": "text", "text": "No tasks provided."}],
            "is_error": True,
        }

    overflow = ""
    if len(tasks) > config.MAX_ENGINEERS:
        overflow = (
            f"\n\nNOTE: {len(tasks)} tasks requested but MAX_ENGINEERS="
            f"{config.MAX_ENGINEERS}. Only the first {config.MAX_ENGINEERS} ran this "
            f"round — assign the remaining {len(tasks) - config.MAX_ENGINEERS} in a "
            f"follow-up call."
        )
        tasks = tasks[: config.MAX_ENGINEERS]

    reports = await asyncio.gather(
        *[run_engineer(f"engineer-{i + 1}", task) for i, task in enumerate(tasks)]
    )

    body = "\n\n---\n\n".join(
        f"### Task {i + 1}: {task}\n{report}"
        for i, (task, report) in enumerate(zip(tasks, reports))
    )
    return {"content": [{"type": "text", "text": body + overflow}]}


_eng_server = create_sdk_mcp_server(
    name="eng", version="1.0.0", tools=[assign_to_engineers]
)


async def run_engineering_manager(brief: str) -> str:
    """Run the Engineering Manager on one project brief; return its report to the CEO."""
    # Plan against the project repo when one is configured, else the workspace.
    planning_dir = (
        repo_mod.base_repo_dir() if repo_mod.repo_configured() else config.COMPANY_ROOT
    )
    options = ClaudeAgentOptions(
        system_prompt=ENGINEERING_MANAGER_PROMPT,
        model=config.MANAGER_MODEL,
        mcp_servers={"eng": _eng_server},
        allowed_tools=["Read", "Glob", "Grep", "mcp__eng__assign_to_engineers"],
        permission_mode="acceptEdits",
        cwd=str(planning_dir),
        setting_sources=["project"],
    )

    report = ""
    async for message in query(prompt=brief, options=options):
        if isinstance(message, ResultMessage):
            report = message.result or ""
    return report
