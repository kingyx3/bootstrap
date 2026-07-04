"""PreToolUse guard hooks — boundaries enforced in code, not just in prompts.

A prompt that says "never run destructive commands" is a request. A hook that
denies the tool call is a rule. Engineers run Bash (including git), so we gate it.
"""

# Destructive patterns matched as substrings. These have no safe subdirectory
# form, so a substring match won't create false positives (unlike a bare `rm`).
_DANGEROUS = (
    "git push --force",
    "git push -f",
    "mkfs",
    "dd if=",
    ":(){",          # fork bomb
    "> /dev/sda",
    "chmod -r 777 /",
)

# A recursive rm is catastrophic only when aimed at one of these whole tokens.
# Token matching means `rm -rf ./build` is allowed while `rm -rf .` is blocked.
_RM_DANGER_TARGETS = {"/", "/*", "~", "~/", ".", "./", "*"}

# Push targets that engineers must never write to directly — they use branches + PRs.
_PROTECTED_BRANCHES = ("main", "master")


def _is_catastrophic_rm(tokens: list[str]) -> bool:
    if "rm" not in tokens:
        return False
    recursive = (
        any(t.startswith("-") and not t.startswith("--") and "r" in t and "f" in t for t in tokens)
        or ("-r" in tokens and "-f" in tokens)
        or ("--recursive" in tokens and "--force" in tokens)
    )
    if not recursive:
        return False
    return any(t in _RM_DANGER_TARGETS for t in tokens)


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
    tokens = lowered.split()

    if any(bad in lowered for bad in _DANGEROUS) or _is_catastrophic_rm(tokens):
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
