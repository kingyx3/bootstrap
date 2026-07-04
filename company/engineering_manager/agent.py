"""The Engineering Manager — decomposes a brief, assigns tasks to a scalable pool
of engineers (in parallel), reviews their work, and — uniquely — opens the pull
request into the default branch once a change is complete.

`assign_to_engineers` fans out to real engineer agents. `open_pull_request` is
the EM's exclusive shipping tool; engineers are not given it, and the Bash guard
blocks `gh pr create/merge`, so PR creation can happen only here.
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
from engineering_manager.prompt import ENGINEERING_MANAGER_PROMPT
from engineer.agent import run_engineer
import repo as repo_mod


@tool(
    "assign_to_engineers",
    "Assign independent, self-contained engineering tasks to engineers. Each task "
    "is executed by its own engineer working in parallel on its own branch; they "
    "report back with what they built and their branch name. Split the work so no "
    "two tasks edit the same files.",
    {
        "type": "object",
        "properties": {
            "tasks": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "One self-contained task per engineer, including what to build, "
                    "paths in the repo, and acceptance criteria."
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


@tool(
    "open_pull_request",
    "Open a pull request from a completed engineer branch into the default branch. "
    "Only the Engineering Manager may open PRs; call this once a change is reviewed "
    "and complete.",
    {
        "type": "object",
        "properties": {
            "head_branch": {
                "type": "string",
                "description": "The engineer branch to open the PR from, e.g. engineer-1.",
            },
            "title": {"type": "string", "description": "Pull request title."},
            "body": {"type": "string", "description": "Pull request description (optional)."},
            "base": {
                "type": "string",
                "description": "Target branch (optional; defaults to the repo's default branch).",
            },
        },
        "required": ["head_branch", "title"],
    },
)
async def open_pull_request(args):
    if not repo_mod.repo_configured():
        return {
            "content": [{"type": "text", "text": "No project repo configured; nothing to PR into."}],
            "is_error": True,
        }
    try:
        url = await asyncio.to_thread(
            repo_mod.open_pull_request,
            args["head_branch"],
            args["title"],
            args.get("body", ""),
            args.get("base"),
        )
        return {"content": [{"type": "text", "text": f"Opened pull request: {url}"}]}
    except Exception as e:  # gh missing/auth/branch errors surface to the EM, not a crash
        return {
            "content": [{"type": "text", "text": f"Failed to open pull request: {e}"}],
            "is_error": True,
        }


@tool(
    "merge_pull_request",
    "Merge a reviewed, complete pull request into the default branch. Merging the "
    "default branch deploys to STAGING. Only the Engineering Manager may merge. Do "
    "NOT use this for production releases — those are the owner's decision.",
    {
        "type": "object",
        "properties": {
            "pull_request": {
                "type": "string",
                "description": "PR number, URL, or branch to merge, e.g. 42 or engineer-1.",
            },
            "method": {
                "type": "string",
                "description": "Merge method: squash (default), merge, or rebase.",
            },
        },
        "required": ["pull_request"],
    },
)
async def merge_pull_request(args):
    if not repo_mod.repo_configured():
        return {
            "content": [{"type": "text", "text": "No project repo configured; nothing to merge."}],
            "is_error": True,
        }
    try:
        result = await asyncio.to_thread(
            repo_mod.merge_pull_request, args["pull_request"], args.get("method", "squash")
        )
        return {"content": [{"type": "text", "text": result}]}
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Failed to merge pull request: {e}"}],
            "is_error": True,
        }


_eng_server = create_sdk_mcp_server(
    name="eng",
    version="1.0.0",
    tools=[assign_to_engineers, open_pull_request, merge_pull_request],
)


async def run_engineering_manager(brief: str) -> str:
    """Run the Engineering Manager on one project brief; return its report to the CEO."""
    planning_dir = (
        repo_mod.base_repo_dir() if repo_mod.repo_configured() else config.COMPANY_ROOT
    )

    allowed_tools = ["Read", "Glob", "Grep", "mcp__eng__assign_to_engineers"]
    mcp_servers = {"eng": _eng_server}
    if repo_mod.repo_configured():
        allowed_tools.append("mcp__eng__open_pull_request")
        allowed_tools.append("mcp__eng__merge_pull_request")
        gh = repo_mod.github_mcp_server()  # optional richer GitHub tools for the EM
        if gh:
            mcp_servers["github"] = gh
            allowed_tools.append("mcp__github__*")

    options = ClaudeAgentOptions(
        system_prompt=ENGINEERING_MANAGER_PROMPT,
        model=config.MANAGER_MODEL,
        mcp_servers=mcp_servers,
        allowed_tools=allowed_tools,
        permission_mode="acceptEdits",
        cwd=str(planning_dir),
        setting_sources=["project"],
    )

    report = ""
    async for message in query(prompt=brief, options=options):
        if isinstance(message, ResultMessage):
            report = message.result or ""
    return report
