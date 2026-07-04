"""Entry point — give the CEO a directive.

    python run.py "Add a /health endpoint to the API and open a PR."

If a project repo is configured (PROJECT_REPO), it is cloned into the workspace
on first run and engineers work in worktrees of it. Requires ANTHROPIC_API_KEY.
See README.md.
"""
import asyncio
import sys

from ceo.agent import run_ceo
from repo import repo_configured, ensure_base_clone


async def main() -> None:
    if len(sys.argv) < 2:
        print('Usage: python run.py "your directive to the CEO"')
        raise SystemExit(2)

    if repo_configured():
        try:
            dest = await asyncio.to_thread(ensure_base_clone)
        except Exception as e:
            print(f"[bootstrap] ERROR preparing project repo: {e}")
            print("Check PROJECT_REPO and GITHUB_TOKEN, and that git is installed.")
            raise SystemExit(1)
        print(f"[bootstrap] project repo ready at {dest}\n")

    directive = " ".join(sys.argv[1:])
    await run_ceo(directive)


if __name__ == "__main__":
    asyncio.run(main())
