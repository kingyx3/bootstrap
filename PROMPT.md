# The Improved Prompt

This document takes the original rough prompt and turns it into a reusable, high-leverage prompt you can paste into Claude (or any capable AI) whenever you want a serious plan for building a one-person company run by AI employees.

---

## Before → After

### Original prompt

> how can i create and use a one man company effectively using AI today

**Why it underperforms:** it's a single vague question. It doesn't say who you are, what constraints you have, what kind of answer you want, or how deep to go. The model has to guess at all of it, so you get a generic listicle of AI tools.

### Improved prompt

Copy everything in the block below. Fill in the `[bracketed]` slots before sending.

```text
You are a solo-founder strategist and AI operations architect. Your specialty is
designing one-person companies where the founder gives direction to a single AI
"CEO" orchestrator agent, and that orchestrator manages a staff of AI employees
(built on the Claude Agent SDK) that run the business day to day.

MY CONTEXT
- Skills/background: [e.g. 10 years in finance, decent Python, no design skills]
- Industry/niche: [e.g. financial analytics for family offices]
- Business model: [e.g. productized service / SaaS / content / consulting / e-commerce]
- Budget for tooling & API costs: [e.g. USD 300/month]
- Time available: [e.g. 15 hours/week alongside a day job]
- Income target: [e.g. USD 10k/month within 12 months]
- Jurisdiction: [e.g. Singapore]
- Risk tolerance: [e.g. conservative — no borrowed money, keep day job for now]

WHAT I WANT FROM YOU
Design my one-person company as an AI-run organization, with detailed build
steps — not just tool recommendations. Specifically:

1. BUSINESS DESIGN — Given my context, recommend ONE business model to start
   with and why. Define the offer, the target customer, and how I validate
   demand in under 30 days with concrete steps.

2. THE AI ORG CHART — Design the company as: me (owner) → one CEO/orchestrator
   agent that I give directions to → specialized AI employees (one per business
   function: marketing/content, sales, customer support, delivery/operations,
   finance/research). For each AI employee specify: its job description, its
   inputs and outputs, its KPIs, and what it must never do without my approval.

3. BUILD INSTRUCTIONS — For each AI employee, give me step-by-step build
   instructions on the Claude Agent SDK: the agent definition (system prompt
   built from a written SOP), the tools and permissions it needs, and how the
   orchestrator delegates work to it. Include the review/quality loop (work is
   checked before it's accepted), the escalation rules (when a human must be
   pulled in), and how the system runs on a schedule without me babysitting it.

4. AUTONOMY PLAN — For each job, state where it starts on the autonomy ladder
   (human-triggered → supervised → autonomous) and what evidence is required
   before promoting it one level up.

5. OPERATING RHYTHM — Define my weekly role as the human owner: the directions
   I give the CEO agent, the approvals I handle, the metrics I review (max 8
   numbers), and the total hours this should take.

6. 90-DAY EXECUTION PLAN — Week-by-week: what gets validated, built, launched,
   and automated, with kill/pivot/continue checkpoints at days 30, 60, and 90.

CONSTRAINTS ON YOUR ANSWER
- Use tools and APIs that actually exist today; state rough monthly costs.
- Be realistic about what AI cannot do: flag every place where human judgment,
  relationships, or licensed professionals (legal, tax, audit) are required.
- Prefer concrete artifacts (templates, file structures, prompts, checklists)
  over general advice.
- If any part of my context makes a recommendation risky, say so directly.
```

---

## Why each part works

| Element | What it does |
|---|---|
| **Role framing** ("solo-founder strategist and AI operations architect") | Anchors the response in operator-level advice instead of generic content. Naming the orchestrator-plus-employees architecture in the role means the whole answer is shaped around that design rather than a flat tool list. |
| **Context slots** (skills, budget, hours, jurisdiction…) | The eight slots cover every variable that changes the right answer. A plan for a coder with $50/month and a plan for a consultant with $500/month are different plans — without these, the model averages across all founders. |
| **Numbered deliverables** | Converts "how can I…" into six concrete artifacts. The model can't skip the hard parts (build steps, escalation rules) because they're explicitly itemized. |
| **Architecture fixed in the prompt** (owner → CEO agent → AI employees, Claude Agent SDK) | Removes the biggest source of drift. Instead of surveying twenty automation platforms, the answer goes deep on one buildable design. |
| **Autonomy plan requirement** | Forces the answer to treat automation as *earned*, not assumed — the difference between a system that quietly ships mistakes and one that gets promoted level by level as it proves itself. |
| **Constraints section** | "Tools that exist today", "state costs", "flag what AI can't do" are quality bars. They suppress hallucinated tools and force honesty about human-only work. |
| **"Concrete artifacts over general advice"** | The single highest-leverage line. It changes the output from prose *about* the business into templates, prompts, and checklists you can use the same day. |

## How to use it

1. Fill the slots honestly — especially budget and hours. Understating them produces a plan you can't execute.
2. Run it, then interrogate the answer: "expand deliverable 3 for the support employee", "rewrite the 90-day plan assuming 5 hours/week".
3. Re-run it quarterly with updated context; the plan should change as the business does.

The full generic answer to this prompt — the reusable framework and build manual — is in [`PLAYBOOK.md`](./PLAYBOOK.md).
