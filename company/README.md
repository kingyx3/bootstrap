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

## Layout

Each employee lives in its own directory (package): its agent and its system
prompt. Shared infrastructure sits at the root.

```
company/
├── run.py                       # entry point — give the CEO a directive
├── config.py                    # models per role, MAX_ENGINEERS, PROJECT_REPO, paths
├── guards.py                    # PreToolUse hook (destructive cmds, main pushes, PR creation)
├── repo.py                      # clone, per-engineer worktrees, open_pull_request, GitHub MCP
├── CLAUDE.md                    # company memory, auto-loaded for every role
├── ceo/
│   ├── agent.py                 #   CEO orchestrator + delegate_to_engineering tool
│   └── prompt.py
├── engineering_manager/
│   ├── agent.py                 #   assign_to_engineers (fan-out) + open_pull_request (EM-only)
│   └── prompt.py
├── engineer/
│   ├── agent.py                 #   run_engineer, scaled to many
│   └── prompt.py
└── workspace/                   # cloned project repo + per-engineer worktrees (or greenfield)
```

## Who can do what with the repo

| Role | Git / GitHub capability |
|---|---|
| **Engineer** | Commits and pushes **its own branch**. Cannot push to the default branch, force-push, or open/merge PRs (blocked in code by the Bash guard). |
| **Engineering Manager** | Reviews branches and, once a change is complete, **opens the pull request** into the default branch via the `open_pull_request` tool — the only role that can. Does not merge. |
| **CEO / Owner** | The CEO escalates; **merging to the default branch is the owner's decision.** |

## Name your GitHub repo at inception

Set `PROJECT_REPO` when you first use this template — this is what makes the
GitHub repo part of the engineers' toolset:

```bash
export PROJECT_REPO=your-org/your-product     # owner/name, or a full URL
export GITHUB_TOKEN=ghp_...                    # access to that repo
# optional, needs Docker: export ENABLE_GITHUB_MCP=1
```

On first run the repo is cloned into `workspace/<repo>`. Each engineer then gets
its **own git worktree + branch** of that clone (so parallel engineers never
collide), builds there, commits, and pushes its branch. The **Engineering
Manager** reviews the branches and opens the pull request into the default
branch. Auth uses a git credential helper that reads `$GITHUB_TOKEN` at run time
— the token is never written into `.git/config`.

Leave `PROJECT_REPO` empty to fall back to greenfield builds in `workspace/`.

**Prerequisites for repo mode:** `git` (required), `gh` (recommended, for PRs),
Docker (only if `ENABLE_GITHUB_MCP=1`).

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
  destructive Bash *and* direct pushes to the default branch via a `PreToolUse`
  hook, and roles run with a scoped `allowed_tools` list. Engineers reach the
  codebase only through pull requests.
- Employees are told (in `CLAUDE.md` and their prompts) to work only in their
  assigned directory and never touch the org's own runtime files.
- The CEO escalates anything irreversible or outward-facing to you rather than
  acting. Add more hooks in `guards.py` as you grant more powerful tools.
- **Token exposure:** `GITHUB_TOKEN` is available to the engineers' Bash
  environment (that's how `git`/`gh` authenticate). Scope the PAT to just this
  repo, as you would a CI token, and prefer a fine-grained PAT.

## Extending the org

Add a new employee (e.g. a **QA** or **Designer**) the same way the engineer is
wired: write a `run_<role>` coroutine, expose a delegation `@tool` on the manager
above it, and add its model to `config.py`. The hierarchy is just nested `query()`
calls bridged by custom tools.
