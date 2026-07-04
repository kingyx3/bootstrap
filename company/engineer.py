"""The Engineer — the individual contributor that does the actual building.

There is one `run_engineer` coroutine; the Engineering Manager scales it to many
concurrent engineers by calling it once per task under asyncio.gather.
"""
from claude_agent_sdk import query, ClaudeAgentOptions, HookMatcher, ResultMessage

import config
from prompts import ENGINEER_PROMPT
from guards import block_dangerous_bash


async def run_engineer(engineer_id: str, task: str) -> str:
    """Run a single engineer on one self-contained task; return its report.

    Each engineer is its own agent loop with real coding tools, scoped to the
    workspace and guarded against destructive shell commands.
    """
    options = ClaudeAgentOptions(
        system_prompt=ENGINEER_PROMPT.format(engineer_id=engineer_id),
        model=config.ENGINEER_MODEL,
        allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
        permission_mode="acceptEdits",
        cwd=str(config.COMPANY_ROOT),
        setting_sources=["project"],  # load CLAUDE.md company memory
        hooks={
            "PreToolUse": [HookMatcher(matcher="Bash", hooks=[block_dangerous_bash])],
        },
    )

    report = ""
    async for message in query(prompt=task, options=options):
        if isinstance(message, ResultMessage):
            report = message.result or ""
    return f"[{engineer_id}]\n{report}"
