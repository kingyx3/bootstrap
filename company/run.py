"""Entry point — give the CEO a directive.

    python run.py "Build a CLI to-do app in workspace/todo with add/list/done commands and tests."

Requires ANTHROPIC_API_KEY in the environment. See README.md.
"""
import asyncio
import sys

from ceo import run_ceo


async def main() -> None:
    if len(sys.argv) < 2:
        print('Usage: python run.py "your directive to the CEO"')
        raise SystemExit(2)

    directive = " ".join(sys.argv[1:])
    await run_ceo(directive)


if __name__ == "__main__":
    asyncio.run(main())
