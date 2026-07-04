# `company/` — a runnable AI engineering org

A working scaffold of the three core AI employees from [`../PLAYBOOK.md`](../PLAYBOOK.md),
built on the [Claude Agent SDK](https://code.claude.com/docs/en/agent-sdk):

```
             You (owner)  ──directive──▶  ceo.py
                                            │  delegate_to_engineering(brief)
                                            ▼
                                  engineering_manager.py
                                            │  assign_to_engineers([task, task, …])
                          ┌─────────────────┼─────────────────┐   (parallel)
                          ▼                 ▼                 ▼
                     engineer.py       engineer.py       engineer.py
                   (engineer-1)       (engineer-2)       (engineer-3)   …up to MAX_ENGINEERS
```

Each arrow is a **nested agent**: a role delegates by calling a custom in-process
tool whose handler runs the level below as its own `query()` loop. Engineers are
spawned concurrently with `asyncio.gather`, so "the Engineer" scales to as many
engineers as the Engineering Manager assigns tasks for (capped by `MAX_ENGINEERS`).

## Files

| File | Role |
|---|---|
| `run.py` | Entry point — give the CEO a directive |
| `ceo.py` | CEO orchestrator + `delegate_to_engineering` tool |
| `engineering_manager.py` | Engineering Manager + `assign_to_engineers` tool (the parallel fan-out) |
| `engineer.py` | A single engineer agent (`run_engineer`), scaled to many |
| `prompts.py` | The three system prompts (job descriptions) |
| `guards.py` | `PreToolUse` hook that blocks destructive shell commands |
| `config.py` | Models per role, `MAX_ENGINEERS`, paths |
| `CLAUDE.md` | Company memory, auto-loaded for every role |
| `workspace/` | Where engineers build product code |

## Setup

```bash
cd company
python -m venv .venv && source .venv/bin/activate   # Python 3.10+
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...                  # or cp .env.example .env
```

## Run

```bash
python run.py "Build a small CLI to-do app in workspace/todo: add, list, and
complete tasks, persisted to a JSON file, with a couple of pytest tests."
```

What happens: the **CEO** turns your directive into a brief and calls
`delegate_to_engineering` → the **Engineering Manager** inspects `workspace/`,
splits the work into independent tasks, and calls `assign_to_engineers` → several
**Engineers** build in parallel and report back → the EM reviews and consolidates
→ the CEO reports to you. Product code appears under `workspace/`.

### Smoke test (cheap)

```bash
python run.py "Create workspace/hello/hello.py that prints 'hello from the AI org' and run it to confirm."
```

You should see the CEO report success and a new file under `workspace/hello/`.

## Scaling & tuning

- **More engineers:** raise `MAX_ENGINEERS` (env var). The EM assigns one task per
  engineer per round and can run multiple rounds for sequential work.
- **Cost:** engineers default to a fast model (`ENGINEER_MODEL`); the CEO and EM
  use the strong model. Override any of them via env vars — see `.env.example`.
- **True file isolation:** parallel engineers share `workspace/`. The EM is
  instructed to hand out non-overlapping tasks; for heavy parallel editing, give
  each engineer its own git worktree or subdirectory (extend `run_engineer`).

## Safety

- Boundaries are enforced in **code**, not just prompts: `guards.py` denies
  destructive Bash via a `PreToolUse` hook, and roles run with a scoped
  `allowed_tools` list.
- Employees are told (in `CLAUDE.md` and their prompts) to work only under
  `workspace/` and never touch the org's own runtime files.
- The CEO escalates anything irreversible or outward-facing to you rather than
  acting. Add more hooks in `guards.py` as you grant more powerful tools.

## Extending the org

Add a new employee (e.g. a **QA** or **Designer**) the same way the engineer is
wired: write a `run_<role>` coroutine, expose a delegation `@tool` on the manager
above it, and add its model to `config.py`. The hierarchy is just nested `query()`
calls bridged by custom tools.
