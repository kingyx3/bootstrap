# bootstrap

Building and running a **one-person company with AI** — where you give direction to a single AI "CEO" orchestrator agent, and it manages a staff of AI employees (built on the Claude Agent SDK) that run the business.

- **[PROMPT.md](./PROMPT.md)** — a reusable, high-quality prompt (with fill-in slots for your skills, niche, budget, and jurisdiction) that generates a tailored version of the plan below. Includes a before/after of the original rough prompt and notes on why each part works.
- **[PLAYBOOK.md](./PLAYBOOK.md)** — the core deliverable: a business-agnostic framework and build manual. How to think about AI employees (the autonomy ladder, the four loops), step-by-step build instructions on the Claude Agent SDK (project skeleton, agent definitions, the CEO orchestrator, the quality/escalation/improvement loops, scheduled runs), a fully worked example, and a 90-day rollout plan.
- **[company/](./company/)** — a runnable scaffold of the three core AI employees on the Claude Agent SDK: a **CEO** orchestrator → an **Engineering Manager** → **Engineers** that scale to a parallel pool. Each level delegates to the one below via a nested-agent tool; boundaries are enforced with a permission hook. See [`company/README.md`](./company/README.md) to run it.
