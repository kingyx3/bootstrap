"""Tests for the PreToolUse guard — the code-enforced boundaries."""
import asyncio

import guards


def decide(command: str) -> str:
    result = asyncio.run(
        guards.block_dangerous_bash({"tool_input": {"command": command}}, "tid", None)
    )
    return "deny" if result else "allow"


def test_engineers_may_push_their_own_branch():
    assert decide("git push -u origin engineer-1") == "allow"
    assert decide("git push -u origin maintenance-fix") == "allow"  # 'main' substring must not trip


def test_pushes_to_default_branch_blocked():
    assert decide("git push origin main") == "deny"
    assert decide("git push origin HEAD:master") == "deny"


def test_force_push_blocked():
    assert decide("git push --force origin engineer-2") == "deny"
    assert decide("git push --force-with-lease origin engineer-2") == "deny"


def test_pr_create_and_merge_blocked_for_engineers():
    assert decide("gh pr create --fill") == "deny"
    assert decide("gh   pr   create --title x") == "deny"
    assert decide("gh pr merge 12 --squash") == "deny"


def test_reading_prs_is_allowed():
    assert decide("gh pr list") == "allow"
    assert decide("gh pr view 3") == "allow"


def test_production_release_blocked():
    assert decide("gh release create v1.2.0") == "deny"


def test_catastrophic_rm_blocked_but_subdirs_allowed():
    assert decide("rm -rf /") == "deny"
    assert decide("rm -rf .") == "deny"
    assert decide("rm -fr ~") == "deny"
    assert decide("rm -rf ./build") == "allow"          # the key false-positive fix
    assert decide("rm -rf ./node_modules") == "allow"
    assert decide("rm file.txt") == "allow"


def test_other_destructive_commands_blocked():
    assert decide("mkfs.ext4 /dev/sdb") == "deny"
    assert decide("dd if=/dev/zero of=/dev/sda") == "deny"


def test_ordinary_commands_allowed():
    assert decide("pytest -q") == "allow"
    assert decide("git commit -am 'wip' && npm test") == "allow"
    assert decide("ls -la && cat README.md") == "allow"
