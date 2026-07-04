# The One-Person Company Playbook
### How to think about, build, and run a company staffed by AI employees

This is a business-agnostic framework. It works whether you sell consulting, software, content, or physical products, because it operates at the level of *business functions* (marketing, sales, support, delivery, finance) — and every business has the same functions.

**The architecture is fixed and simple:**

- **You** are the owner. Your job is to give direction, approve the few things that need approving, and do the human-only work (relationships, judgment, selling).
- **One CEO/orchestrator agent** is your single point of contact. You talk to it; it decomposes your directions into tasks, delegates to the AI employees, reviews their work, and reports back.
- **AI employees** — one per business function — do the actual work. Every employee's "body" is the **Claude Agent SDK**: a defined agent with a job description, an SOP-derived system prompt, scoped tools, and hard permission limits.
- **Loops** keep it running smoothly: a delegation loop, a quality loop, an escalation loop, and an improvement loop. These are what separate a reliable AI company from a demo.

```
                    ┌─────────────────────────────┐
                    │           YOU (Owner)        │
                    │  direction · approvals ·     │
                    │  relationships · judgment    │
                    └──────────────┬──────────────┘
                          directions │ ▲ reports & escalations
                                   ▼ │
                    ┌─────────────────────────────┐
                    │      CEO / ORCHESTRATOR      │
                    │  decompose → delegate →      │
                    │  review → synthesize         │
                    └───┬──────┬──────┬──────┬────┘
                        ▼      ▼      ▼      ▼
                 ┌────────┐┌────────┐┌────────┐┌────────┐
                 │Marketing││Support ││  Ops/  ││Finance/│
                 │/Content ││/Inbox  ││Delivery││Research│
                 └────┬───┘└────┬───┘└────┬───┘└────┬───┘
                      └─────────┴────┬────┴─────────┘
                                     ▼
                 ┌──────────────────────────────────────┐
                 │  Shared context: CLAUDE.md · SOPs ·   │
                 │  logs · files  +  Tools (MCP: email,  │
                 │  calendar, CRM, sheets, web)          │
                 └──────────────────────────────────────┘
```

---

# Part I — Mental models: how to think about it

## 1. You are not "using AI tools." You are hiring AI employees.

The single most important reframe. A tool is something you operate; an employee is someone you *manage*. Every AI employee, in any business, is defined by the same five things a human hire is:

| Component | Human hire | AI employee |
|---|---|---|
| **Job description** | Offer letter, role scope | A written spec: outcome, inputs, outputs, KPIs, boundaries |
| **Training/SOP** | Onboarding, shadowing | Your process, written down, becomes its system prompt |
| **Tools & access** | Laptop, email, CRM login | Scoped tool permissions (file access, MCP integrations) |
| **Memory/context** | Institutional knowledge | `CLAUDE.md` company memory + files it reads and writes |
| **Manager review** | 1:1s, performance reviews | Quality loop + error log → SOP updates |

If any of the five is missing, the "employee" is just a chatbot. Most people who say "AI didn't work for my business" skipped the SOP and the review loop.

## 2. The autonomy ladder

No job starts autonomous. Every job climbs this ladder one rung at a time, and only after proving reliable at the current rung:

| Level | Name | What it looks like | Human involvement |
|---|---|---|---|
| **L1** | Assistant | You drive every task in a chat | Everything |
| **L2** | Repeatable task | A written prompt/SOP you trigger for a known task | You trigger and check each run |
| **L3** | Triggered job | The task runs on an event or schedule; output queued for you | You approve outputs in batches |
| **L4** | Supervised agent | The agent runs a multi-step job end to end; a reviewer pass checks it; you approve only flagged items | Exceptions only |
| **L5** | Autonomous job | The agent runs the job; you audit samples weekly | Auditing |

**Promotion rule:** a job moves up one rung only after N consecutive clean runs at the current rung (start with N=10). Demotion is instant: one serious error sends the job back a rung until the SOP is fixed.

**What decides the ceiling** — three questions per task:

1. **Error cost** — what does a mistake cost? (An off-brand tweet ≈ nothing. A wrong invoice ≈ money and trust.)
2. **Reversibility** — can you undo it? (A draft: yes. A sent email: no.)
3. **Verifiability** — can correctness be checked cheaply, ideally by another agent? (Code with tests: yes. Strategic advice: no.)

Low cost + reversible + verifiable → can reach L5. High cost or irreversible → capped at L4 with a human approval gate, forever. That's not a limitation; it's the design.

## 3. The loops — what makes it run smoothly

Your job is *not* to manage each employee. You direct the CEO agent; the loops manage the employees. There are four, and you will build all four in Part II:

**Delegation loop** (the CEO's main loop)
```
owner directive → CEO decomposes into tasks → assigns each task to the right
employee → collects results → synthesizes → reports back to owner
```

**Quality loop** (nothing ships unreviewed)
```
employee produces work → a reviewer pass (separate critic agent, or the CEO
checking against the SOP's acceptance checklist) → PASS: accepted
→ FAIL: bounced back with specific feedback → employee revises (max 2 retries)
→ still failing: escalate to owner
```
The generator/critic split matters: the same context that produced a mistake will defend it. A fresh reviewer with only the SOP and the output catches what self-review misses.

**Escalation loop** (the only moments you're pulled in)
Hard rules, enforced in code (not just in prompts — see Part II step 4):
- anything **irreversible or outward-facing** (sending email to a customer, publishing, payments) above the job's autonomy level
- **spend** above a threshold you set
- **confidence below threshold** — the SOP tells every employee: "when unsure, stop and ask; never guess on X"
- anything touching **legal, tax, or commitments** on your behalf

**Improvement loop** (performance reviews for agents)
```
every run appends to a run log → errors get a one-line entry: what happened,
why, SOP fix → weekly, the CEO summarizes the error log → you approve SOP /
system-prompt updates → agents get better every week
```
Plus a **heartbeat**: a scheduled run (daily, via cron) where the CEO works the standing job list — check the inbox job, the content pipeline, the metrics — and reports *exceptions only*.

## 4. Why this is business-agnostic

Functions are universal. A solo consultancy, a niche SaaS, and an e-commerce brand all need marketing, sales, support, delivery, and finance done — only the *content* of each SOP differs. The framework, the ladder, and the loops are identical. When you apply this playbook, you change the SOPs, not the architecture.

---

# Part II — The build: your AI company on the Claude Agent SDK

Everything lives in **one Agent SDK project**. The Agent SDK is the same engine that powers Claude Code, as a library: agents get built-in tools (read/write files, run commands, search the web), you define employees as agents, and the orchestrator delegates to them. Docs: https://code.claude.com/docs/en/agent-sdk

This part is a generic recipe. Part III applies it end to end.

## Step 0 — Project skeleton

```bash
mkdir my-company && cd my-company
pip install claude-agent-sdk        # Python 3.10+  (or: npm i @anthropic-ai/claude-agent-sdk)
export ANTHROPIC_API_KEY=sk-ant-...
```

Repository layout — this *is* your company:

```
my-company/
├── CLAUDE.md                  # Company memory: what the business is, voice,
│                              #   policies, escalation thresholds. Every agent
│                              #   reads this automatically.
├── .claude/
│   └── agents/                # One file per AI employee (see Step 2)
│       ├── content-marketer.md
│       ├── support-rep.md
│       ├── ops-researcher.md
│       └── reviewer.md        # the critic used by the quality loop
├── docs/
│   ├── sops/                  # Written SOPs — the source of each system prompt
│   │   ├── support.md
│   │   └── content.md
│   └── offer.md               # What you sell, pricing, positioning
├── inbox/                     # Work queued FOR you (approvals, escalations)
├── outbox/                    # Approved work waiting to be executed/sent
├── logs/                      # Append-only run logs the loops read/write
│   ├── runs.jsonl
│   └── errors.md
├── evals/                     # Test cases per employee (Step 6)
└── ceo.py                     # The orchestrator entry point (Step 3)
```

Write `CLAUDE.md` first. Keep it under a page: what the company sells, who the customer is, the brand voice in three adjectives with one example, the hard policies ("never discount past 10%", "never send anything external without approval"), and where things live in the repo. This file is the institutional knowledge every employee inherits for free.

## Step 1 — Write the job description (per employee)

Before any code. One page, this template:

```markdown
# Job: Support/Inbox Rep
Outcome owned:   Every customer email gets an accurate, on-voice reply draft
                 within 4 working hours.
Inputs:          Incoming emails; docs/sops/support.md; past-answers FAQ file.
Outputs:         Reply drafts in inbox/ awaiting approval (L3). KPIs: draft
                 turnaround, % drafts approved without edits, escalation rate.
Boundaries:      NEVER sends email directly. NEVER promises refunds, discounts,
                 or dates. NEVER answers legal/billing-dispute questions —
                 those escalate with a one-line summary.
Autonomy:        Starts L2. Promotion to L3 after 10 consecutive approved-
                 unedited drafts. Ceiling: L4 (external sends stay gated).
```

If you can't write this page, you don't understand the job well enough to delegate it — to an AI or a human.

## Step 2 — Do the job manually, then capture the SOP

Do the job yourself 5–10 times *while narrating*: what you look at first, what you decide, what good output looks like, what the traps are. Turn the narration into `docs/sops/<job>.md`:

```markdown
# SOP: Support replies
1. Read the email. Classify: question / complaint / billing / spam.
2. Spam → log and stop. Billing dispute → escalate immediately.
3. For questions: check the FAQ file first; reuse approved language verbatim
   where it fits.
4. Structure: acknowledge in one sentence → answer in ≤3 short paragraphs →
   one concrete next step. Voice: warm, plain, no exclamation marks.
5. If the answer isn't in the FAQ or docs: do NOT improvise a policy.
   Draft what you can, mark the gap, escalate.

## Acceptance checklist (the reviewer uses this)
- [ ] Classification correct
- [ ] No promises about refunds/discounts/dates
- [ ] Voice matches CLAUDE.md examples
- [ ] Every factual claim traceable to FAQ/docs
- [ ] Gaps explicitly flagged, not papered over
```

**Automate the process only after you've done it manually and written it down.** The acceptance checklist at the bottom is load-bearing — it's what the quality loop reviews against.

## Step 3 — Define the employee as an agent

Each employee is a markdown file in `.claude/agents/`. Frontmatter declares identity, tool allowlist, and model; the body is the system prompt, built directly from the SOP:

```markdown
---
name: support-rep
description: Drafts replies to customer emails following the support SOP.
  Use for any incoming customer message.
tools: Read, Write, Grep, Glob
model: sonnet
---

You are the customer support rep for the company described in CLAUDE.md.

## Your job
Draft replies to customer emails. You write drafts to inbox/ — you NEVER send
anything yourself.

## Procedure
[paste the SOP steps from docs/sops/support.md]

## Output contract
For each email, write a file inbox/reply-<id>.md containing:
- CLASSIFICATION: question | complaint | billing | spam
- CONFIDENCE: high | medium | low
- DRAFT: the reply text
- FLAGS: anything the owner must know (gaps, risks), or "none"

## Escalation rules
Stop and flag (CONFIDENCE: low + FLAGS) instead of guessing when: the answer
isn't in the FAQ/docs; the customer is angry or mentions refunds, lawyers, or
disputes; or you'd need to promise anything about money or dates.
```

Notes on the frontmatter:
- `tools:` is the **least-privilege allowlist**. The support rep can read and write files and search the repo — it has no Bash, no web, no email. Add capabilities only when the job demands them.
- `model:` lets you tier costs — the orchestrator on your strongest model, high-volume drafting employees on a cheaper one. (Skip the field to inherit the project default.)
- Alternatively, define employees programmatically via the `agents={...}` option (an `AgentDefinition` per employee) in Step 4 — same fields, useful when you want them versioned in code. Files in `.claude/agents/` are the simpler default and are picked up automatically.

## Step 4 — Build the CEO orchestrator

The CEO is the main agent you converse with. Its system prompt makes it a **manager, not a doer** — its only real powers are delegating to employees (the `Agent` tool) and reading/writing the shared repo. `ceo.py`:

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, HookMatcher

CEO_SYSTEM_PROMPT = """
You are the CEO of the company described in CLAUDE.md. The owner gives you
directions; you run the company. You do not do the work yourself.

For every owner directive:
1. DECOMPOSE it into tasks and decide which employee owns each
   (see .claude/agents/ for the roster and docs/sops/ for their procedures).
2. DELEGATE each task to that employee with full context: the goal, the
   relevant files, and what "done" looks like per the SOP's checklist.
3. REVIEW every result by delegating it to the `reviewer` agent together with
   the relevant SOP's acceptance checklist. If REJECTED, send it back to the
   employee with the reviewer's specific feedback. Max 2 revision cycles,
   then escalate to the owner.
4. LOG every task to logs/runs.jsonl (task, employee, result, review verdict).
   Log failures to logs/errors.md with a one-line proposed SOP fix.
5. REPORT back: outcomes first, exceptions second, at most one question.
   Never narrate routine work.

Escalate to the owner (write to inbox/ and say so in your report) anything
irreversible, outward-facing, above spend limits in CLAUDE.md, or that an
employee flagged low-confidence. Never work around a blocked action.
"""

# Hard enforcement: prompts ask nicely, hooks enforce. This hook blocks any
# command that could send/publish, regardless of what any agent decides.
async def block_external_sends(input_data, tool_use_id, context):
    cmd = input_data.get("tool_input", {}).get("command", "")
    banned = ("mail", "sendmail", "curl -X POST", "gh pr create", "npx wrangler")
    if any(b in cmd for b in banned):
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason":
                    "External sends require owner approval: write to outbox/ instead.",
            }
        }
    return {}

async def run_directive(directive: str, session_id: str | None = None):
    options = ClaudeAgentOptions(
        system_prompt=CEO_SYSTEM_PROMPT,
        model="claude-opus-4-8",          # the CEO gets the strong model
        allowed_tools=["Read", "Write", "Edit", "Grep", "Glob", "Bash", "Agent"],
        permission_mode="acceptEdits",     # file edits auto-approved; hooks gate the rest
        hooks={"PreToolUse": [HookMatcher(matcher="Bash", hooks=[block_external_sends])]},
        resume=session_id,                 # continue the same CEO across days
    )
    async for message in query(prompt=directive, options=options):
        if hasattr(message, "result"):
            print(message.result)          # the CEO's report to you

if __name__ == "__main__":
    import sys
    asyncio.run(run_directive(sys.argv[1]))
```

Usage — this is your entire management interface:

```bash
python ceo.py "Draft this week's newsletter and process anything new in the support inbox."
```

Key mechanics:
- **Delegation** happens through the `Agent` tool: because `Agent` is in `allowed_tools` and your employees are defined in `.claude/agents/`, the CEO can invoke `support-rep`, `content-marketer`, etc. by name. Each employee runs in its own context with its own tools and reports its result back to the CEO.
- **Continuity**: capture the `session_id` from the init message and pass `resume=` so tomorrow's directive continues the same CEO with yesterday's context intact.
- **The quality loop is just another delegation**: the `reviewer` agent (next) is invoked by the CEO exactly like any employee.

## Step 5 — Build the reviewer (the quality loop)

`.claude/agents/reviewer.md` — deliberately blind to the producing agent's reasoning; it sees only the work and the checklist:

```markdown
---
name: reviewer
description: Adversarial quality reviewer. Checks a piece of work against an
  SOP acceptance checklist and returns APPROVED or REJECTED with reasons.
tools: Read, Grep, Glob
model: opus
---

You are a skeptical quality reviewer. You are given a piece of work and the
acceptance checklist from the relevant SOP. Your default stance is REJECTED —
approve only if every checklist item demonstrably passes.

Return exactly:
VERDICT: APPROVED | REJECTED
CHECKLIST: each item with pass/fail and one-line evidence
FEEDBACK: (if rejected) the specific, minimal changes needed — no rewrites
```

Read-only tools, strongest model, adversarial stance. This one agent raises the floor of everything the company ships.

## Step 6 — Wire external tools with MCP (as jobs earn them)

Employees reach the outside world through MCP servers — email, calendar, CRM, sheets, browsers — declared on the options and allowlisted per employee:

```python
options = ClaudeAgentOptions(
    # ...
    mcp_servers={
        "gmail":  {"command": "npx", "args": ["@your-choice/gmail-mcp"]},
        "sheets": {"command": "npx", "args": ["@your-choice/sheets-mcp"]},
    },
)
```

Then in an employee's `tools:` list, allow only the specific MCP tools it needs (e.g. the inbox-reader tool but *not* the send tool). Two rules:

1. **Least privilege, per employee.** The support rep can read the inbox; only the *owner-approval step* triggers a send. The finance employee can read the bank feed; nothing can move money.
2. **Read access is cheap to grant; write access is earned** — it follows the autonomy ladder, and irreversible writes (send, publish, pay) stay behind the hook + `outbox/` approval gate at any level.

## Step 7 — Schedule the heartbeat

The company should run without you triggering it. A cron job invokes the CEO headlessly with the standing directive:

```bash
# crontab: weekdays at 8:00 — the daily heartbeat
0 8 * * 1-5  cd /path/to/my-company && python ceo.py \
  "Daily heartbeat: process new support emails, advance the content pipeline, \
   update metrics in logs/metrics.md. Exceptions and approvals to inbox/; \
   end with a 5-line report." >> logs/heartbeat.log 2>&1
```

Your morning routine becomes: read the 5-line report, clear `inbox/` (approve/reject drafts and escalations), give the CEO at most one new directive. That's the company operating.

## Step 8 — Test like onboarding a hire

Before any employee is trusted at L3+, build an eval set in `evals/<employee>/`: 10–20 real historical cases (real emails you answered, real posts you wrote) with your actual output as the reference. Then:

1. Run the employee on every case (a small script that calls `query()` with the case as input).
2. Have the **reviewer** grade each output against the checklist *and* against your reference answer.
3. Define the bar before you run it (e.g. ≥90% APPROVED, zero boundary violations).
4. Keep the evals forever — rerun them after every SOP or prompt change, exactly like a regression test suite. A "small prompt tweak" that fails three evals just saved you from finding out via a customer.

## Step 9 — Run the improvement loop

Weekly, as part of the Friday review (Part IV): the CEO summarizes `logs/errors.md`, proposes SOP/prompt edits, you approve them, evals rerun. Agents don't get better by magic; they get better because errors become SOP lines. This loop is the compounding asset of the whole company — after a year, your `docs/sops/` directory is a fully documented, machine-executable operations manual that no competitor can copy.

---

# Part III — Worked example, end to end

A concrete miniature: a solo productized-consulting business ("market-research reports for e-commerce brands, $1.5k each") — but notice that *nothing below except the SOP contents* would change for a SaaS or an agency.

**The roster** (`.claude/agents/`):

| Agent | Model | Tools | Job |
|---|---|---|---|
| `ops-researcher` | opus | Read, Write, Bash, WebSearch, WebFetch, Grep, Glob | Produces the client deliverable: gathers data, builds the report draft |
| `content-marketer` | sonnet | Read, Write, Grep, Glob | Turns finished (anonymized) research into newsletter issues and posts → `outbox/` |
| `support-rep` | sonnet | Read, Write, Grep, Glob | Drafts replies to client/prospect emails → `inbox/` |
| `reviewer` | opus | Read, Grep, Glob | Quality gate for all of the above |

**A directive traced through the loops.** Monday, you run:

```bash
python ceo.py "Client Acme signed for the Q3 report (brief in docs/clients/acme.md).
Kick off the research, and this week's newsletter should go out Thursday."
```

1. **Delegation loop** — the CEO decomposes: (a) research report for Acme → `ops-researcher`, with the brief and the report SOP; (b) newsletter draft → `content-marketer`, with last week's approved issue as a style reference. Both run; the CEO collects results.
2. **Quality loop** — the CEO hands the report draft plus the report SOP's checklist to `reviewer`. Verdict: REJECTED — "competitor pricing section cites no sources." Bounced back to `ops-researcher` with that exact feedback; revision passes on the second review. The newsletter passes first time.
3. **Escalation loop** — the newsletter is outward-facing, so no agent can send it: it lands in `outbox/newsletter-2026-07-09.md`. The report is a client deliverable: it lands in `inbox/` for your approval. Meanwhile `support-rep` (running on the heartbeat) hit a prospect email asking for a discount — boundary rule — so a draft-plus-flag is in `inbox/` too.
4. **You**, Tuesday morning, 20 minutes: approve the report (send it yourself — client relationships stay human), approve the newsletter (one command or click sends what's in `outbox/`), decide the discount question, give the CEO one line of feedback ("newsletters: shorter intros"). 
5. **Improvement loop** — Friday, the CEO's weekly summary notes the missing-sources rejection; you approve one new SOP line ("every pricing claim needs a linked source"). The report evals rerun clean. The company is better than it was on Monday.

Steady state for this business: you sell (calls, relationships) and approve; the roster produces. Owner time: roughly 6–8 hours/week.

---

# Part IV — Operating the company (the human's job)

## What only you do

1. **Direction** — what to build, sell, and stop doing. Strategy stays human.
2. **Relationships** — sales conversations, partnerships, anything where trust is the product. People buy from people, especially from one-person companies.
3. **Approvals** — the escalation loop's endpoint: external sends, money, commitments.
4. **Judgment calls** — pricing, positioning, when to fire a client.
5. **Licensed work** — lawyers, tax agents, auditors. AI drafts questions *for* them, never replaces them.

Everything else is a candidate for the roster.

## The operating rhythm

| Cadence | Ritual | Time |
|---|---|---|
| **Daily** | Read the heartbeat report; clear `inbox/` (approve / reject / decide); ≤1 new directive to the CEO | 15–30 min |
| **Weekly (Fri)** | CEO's weekly review: metrics vs targets, error-log summary, proposed SOP changes, promotion/demotion decisions on the autonomy ladder | 60 min |
| **Monthly** | Strategy: what to productize next, pricing, which function gets the next AI employee | 2–3 hrs |

## The dashboard — 8 numbers, any business

Maintained by the CEO in `logs/metrics.md`, reviewed weekly:

1. Revenue (month to date) · 2. Leads/inquiries this week · 3. Conversion rate · 4. Delivery queue (open work + oldest item age) · 5. Support: median response time & open threads · 6. **% of agent outputs approved without edits** (the health of the roster) · 7. Escalations this week (rising = SOP gaps) · 8. Total cost: API + tools + contractors.

Number 6 is the one unique to an AI-run company — it's how you *feel* the roster getting better or worse.

## Build order and the 90-day rollout

Automate your biggest time sink first, one employee at a time. A new employee only starts once the previous one is at L3+.

| Phase | Weeks | What happens |
|---|---|---|
| **Foundation** | 1–2 | Validate the offer with real prospects (human work!). Write `CLAUDE.md`, the offer doc, and the SOP for your single biggest time sink. Stand up the skeleton + CEO + reviewer. |
| **First hire** | 3–4 | Build employee #1 per Part II. Run evals. Operate at L2 → promote to L3. |
| **Checkpoint — day 30** | | Kill/pivot/continue on the *offer* (demand evidence?), and on the *build* (is #1 saving ≥3 hrs/week?). |
| **Second & third hires** | 5–8 | Add the next two functions. Heartbeat goes live. Daily rhythm starts. |
| **Checkpoint — day 60** | | Revenue in? Roster approval-rate ≥80%? If not: fix SOPs before adding anyone. |
| **Compound** | 9–12 | Promote proven jobs to L4. Add the finance/research employee. Weekly improvement loop running without prompting. |
| **Checkpoint — day 90** | | You should be at: ≤10 hrs/week of operations, a documented ops manual in `docs/sops/`, and a clear answer on whether the business scales. |

## Costs

| Tier | Monthly | What it looks like |
|---|---|---|
| **Lean** | ~US$30–80 | API usage for a small roster on the heartbeat (drafting employees on Sonnet-class models), one email/domain stack |
| **Standard** | ~US$150–400 | Full roster running daily, Opus-class orchestrator + reviewer, MCP-connected email/CRM/sheets, modest research volume |
| **Heavy** | US$500+ | High-volume production (content at scale, many client deliverables), heavier research/browse workloads |

Compare against the alternative: the *cheapest* human doing any one of these functions part-time costs 10–50× the entire heavy tier. Watch cost per function in the dashboard and tier models accordingly (strong model for CEO/reviewer, cheaper models for volume work).

## Legal setup (brief, and get real advice)

Generic sequence for any jurisdiction: register the entity → separate business bank account → basic terms of service / engagement letter template → invoicing → understand your tax filing obligations. **Singapore note** (adjust for your jurisdiction): a sole proprietorship or private limited company (Pte Ltd) is registered through ACRA via BizFile+; a Pte Ltd gives limited liability and credibility with corporate clients at the cost of annual filing obligations, and corporate tax exemptions for new start-up companies can make it attractive early. This paragraph is orientation, not advice — a one-hour session with a corporate services firm or accountant is a rounding error against getting it wrong. This is a permanent human-only box on the org chart.

## Failure modes to avoid

- **Automating before doing.** If you never did the job manually, the SOP is fiction and the employee inherits the fiction.
- **Skipping the reviewer.** Unreviewed AI output is fine until the one time it isn't — and that time is public.
- **Prompt-only guardrails.** "Never send email" in a prompt is a request; a `PreToolUse` hook is a rule. Enforce boundaries in code.
- **Promoting on vibes.** The ladder runs on counted clean runs and eval scores, not on "it seems good lately."
- **Hiring AI for the human jobs.** Automating relationship-building is how one-person companies lose the only advantage they have.

---

*Companion document: [`PROMPT.md`](./PROMPT.md) — a reusable prompt that generates a tailored version of this plan for your specific skills, niche, budget, and jurisdiction.*
