"""The CEO / orchestrator — the human owner's single point of contact.

You talk to the CEO; the CEO delegates engineering work to the Engineering
Manager (who delegates to engineers). The `delegate_to_engineering` tool is the
bridge from this level to the one below.
"""
from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    ResultMessage,
    SystemMessage,
    AssistantMessage,
    tool,
    create_sdk_mcp_server,
)

import config
from prompts import CEO_PROMPT
from engineering_manager import run_engineering_manager


@tool(
    "delegate_to_engineering",
    "Hand a project brief to the Engineering Manager. The EM breaks it into tasks, "
    "assigns them to engineers, reviews their work, and returns one consolidated "
    "report. Use this for anything that requires building or changing code.",
    {
        "type": "object",
        "properties": {
            "brief": {
                "type": "string",
                "description": (
                    "A clear brief: the goal, constraints, and what 'done' looks like."
                ),
            }
        },
        "required": ["brief"],
    },
)
async def delegate_to_engineering(args):
    report = await run_engineering_manager(args["brief"])
    return {"content": [{"type": "text", "text": report}]}


_org_server = create_sdk_mcp_server(
    name="org", version="1.0.0", tools=[delegate_to_engineering]
)


async def run_ceo(directive: str, session_id: str | None = None) -> str | None:
    """Run the CEO on one owner directive. Returns the session id so the owner can
    resume the same CEO (with full context) on the next directive."""
    options = ClaudeAgentOptions(
        system_prompt=CEO_PROMPT,
        model=config.CEO_MODEL,
        mcp_servers={"org": _org_server},
        allowed_tools=[
            "Read",
            "Glob",
            "Grep",
            "Write",
            "mcp__org__delegate_to_engineering",
        ],
        permission_mode="acceptEdits",
        cwd=str(config.COMPANY_ROOT),
        setting_sources=["project"],
        resume=session_id,
    )

    new_session_id = session_id
    async for message in query(prompt=directive, options=options):
        if isinstance(message, SystemMessage) and message.subtype == "init":
            new_session_id = message.data.get("session_id", new_session_id)
        elif isinstance(message, AssistantMessage):
            for block in message.content:
                # Print streamed text from the CEO (duck-typed: text blocks
                # expose type == "text" and a .text string).
                if getattr(block, "type", None) == "text":
                    print(getattr(block, "text", ""))
        elif isinstance(message, ResultMessage):
            print("\n=== CEO report ===")
            if message.result:
                print(message.result)
            print(
                f"\n(session {message.session_id} · {message.num_turns} turns · "
                f"cost ${message.total_cost_usd})"
            )
    return new_session_id
