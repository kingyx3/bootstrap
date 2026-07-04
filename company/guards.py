"""PreToolUse guard hooks — boundaries enforced in code, not just in prompts.

A prompt that says "never run destructive commands" is a request. A hook that
denies the tool call is a rule. Engineers run Bash, so we gate it.
"""

# Substrings that should never appear in a Bash command engineers run.
_DANGEROUS = (
    "rm -rf /",
    "rm -rf ~",
    "rm -rf .",
    "git push --force",
    "git push -f",
    "mkfs",
    "dd if=",
    ":(){",          # fork bomb
    "> /dev/sda",
    "chmod -r 777 /",
)


async def block_dangerous_bash(input_data, tool_use_id, context):
    """Deny obviously destructive shell commands. Returns {} to allow."""
    command = input_data.get("tool_input", {}).get("command", "")
    lowered = command.lower()
    if any(bad in lowered for bad in _DANGEROUS):
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    f"Blocked by company policy — destructive command: {command!r}"
                ),
            }
        }
    return {}
