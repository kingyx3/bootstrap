"""PreToolUse guard hooks — boundaries enforced in code, not just in prompts.

A prompt that says "never run destructive commands" is a request. A hook that
denies the tool call is a rule. Engineers run Bash (including git), so we gate it.
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

# Push targets that engineers must never write to directly — they use branches + PRs.
_PROTECTED_BRANCHES = ("main", "master")


def _pushes_to_protected_branch(command: str) -> bool:
    tokens = command.split()
    if not ({"git", "push"} <= set(tokens)):
        return False
    for tok in tokens:
        if tok in _PROTECTED_BRANCHES:            # e.g. `git push origin main`
            return True
        if tok.endswith((":main", ":master")):    # e.g. `git push origin HEAD:main`
            return True
    return False


def _deny(command: str, reason: str) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


async def block_dangerous_bash(input_data, tool_use_id, context):
    """Deny destructive commands and direct pushes to the default branch.

    Returns {} to allow the command through.
    """
    command = input_data.get("tool_input", {}).get("command", "")
    lowered = command.lower()

    if any(bad in lowered for bad in _DANGEROUS):
        return _deny(command, f"Blocked by company policy — destructive command: {command!r}")

    if _pushes_to_protected_branch(lowered):
        return _deny(
            command,
            "Blocked by company policy — never push to the default branch. "
            "Push your own branch; the Engineering Manager opens the pull request.",
        )

    normalized = " ".join(lowered.split())
    if "gh pr create" in normalized or "gh pr merge" in normalized:
        return _deny(
            command,
            "Blocked by company policy — only the Engineering Manager opens or "
            "merges pull requests. Push your branch and report it instead.",
        )

    # Production releases are the owner's decision alone — no AI employee cuts them.
    if "gh release create" in normalized:
        return _deny(
            command,
            "Blocked by company policy — production releases are the owner's "
            "decision. Merging to the default branch (staging) is as far as the "
            "org goes; report readiness and let the owner release.",
        )

    return {}
