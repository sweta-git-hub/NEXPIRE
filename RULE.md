# RULE.md — ResQ-Chain Development Working Rules

This file governs how **any** developer or coding agent (Claude Code, another AI agent, or a human
contributor) works on this repository. It must be read before writing the first line of code, and
followed for the entire life of the project. If a new agent picks up this repo mid-project, this file
plus `STATUS.md` and `DECISIONS.md` should be enough to get productive with minimal extra context.

---

## 1. Phase Discipline (Rule A)

- The project is broken into numbered **Phases** (see the Implementation Roadmap in the project
  playbook — currently Phase 0 through Phase 7).
- The agent works on **exactly one phase at a time** and must not implement functionality that
  belongs to a later phase, even if it seems convenient or "while I'm in here."
- If, while working, the agent identifies necessary work that falls outside the current phase's
  defined scope (a blocker, a missing dependency, a design gap), it must **stop and flag it** in
  `STATUS.md` under "Blockers / Scope Questions" and ask the user before proceeding — it does not
  silently expand scope to route around the problem.
- A phase is not "done" until its stated deliverable (per the roadmap) is met, documented, and
  explicitly approved by the user.

## 2. Branching &amp; Commits (Rule B)

- Each phase gets its **own branch**, named `phase-<n>-<short-slug>` (e.g. `phase-0-setup`,
  `phase-2-markdown-engine`, `phase-4-comms`).
- No direct commits to `main`. `main` only receives approved, completed phase branches via merge.
- Within a phase branch, commit **early and often** — one commit per meaningful, working increment
  (a new endpoint, a passing test, a schema migration), not one giant commit at the end of the
  phase. This keeps history reviewable and makes it possible to bisect if something breaks.
- Commit message format: `[phase-<n>] <type>: <short description>`
  where `<type>` is one of `feat`, `fix`, `refactor`, `docs`, `test`, `chore`.
  Example: `[phase-2] feat: add gradient boosting markdown scorer behind scoring interface`

## 3. Permission Gates (Rule C)

The agent must **explicitly ask for permission** before doing any of the following, and must wait
for an affirmative response before proceeding:

- Pushing any commit to the remote repository.
- Opening or merging a pull request.
- Beginning a new phase (even if the current phase feels complete — the user confirms completion
  first).
- Installing a new dependency that was not already agreed upon in the current phase's plan.
- Modifying code that belongs to a previously completed (merged) phase.

When asking, the agent should state clearly *what* it wants to do and *why*, in one or two
sentences — not a long justification. A short confirmation from the user is sufficient to proceed.

## 4. Documentation Requirements (Rule D)

Three living documents live at the repo root and are updated continuously, not just at the end:

### `STATUS.md`
Updated after **every commit or phase boundary**. Structure:

```markdown
## Current Phase
Phase <n> — <name> (branch: phase-<n>-<slug>)

## Built
- <feature> — done, tested
- <feature> — done, needs review

## In Progress
- <feature> — <what's left>

## Not Started
- <feature/phase> — planned for Phase <n+1>

## Blockers / Scope Questions
- <anything that needs user input before continuing>
```

### `DECISIONS.md`
An append-only log of technical decisions and their rationale, one entry per decision, added at the
time the decision is made (not reconstructed later from memory). Structure:

```markdown
## [Phase <n>] <short decision title>
**Date:** <date>
**Decision:** <what was decided>
**Rationale:** <why, including alternatives considered and rejected>
**Reversible?** <yes/no — and what it would take to reverse it>
```

Example entries this project should expect early on: choice of rule-based vs. ML pricing for the
Phase 2 MVP, PostGIS vs. a simpler bounding-box radius query, Twilio sandbox vs. full WhatsApp
Business verification, synthetic vs. partial-real training data.

### Per-phase README section
Each phase branch should update a `## Phase <n>` section in the root `README.md` summarizing what
was built in plain language, so a judge, teammate, or new agent can understand the state of the
product without reading code.

## 5. Testing &amp; Definition of Done

- A phase is only "done" when: the stated deliverable works end-to-end locally, `STATUS.md` reflects
  it under "Built," and any non-obvious decision made along the way is logged in `DECISIONS.md`.
- Prefer a small number of meaningful tests (core business logic: reservation locking, price
  optimization, claim state transitions) over broad low-value coverage — time is limited.

## 6. Communication Cadence

- At the start of each phase: a one-line plan restating the phase's scope and deliverable, for the
  user to confirm before work begins.
- At the end of each phase: a short summary of what was built, what was cut/deferred, and any
  decisions logged — then wait for explicit go-ahead before branching into the next phase.

## 7. What NOT to do

- Do not merge to `main` without approval.
- Do not silently skip a phase's stated deliverable to "save time" — flag the tradeoff instead and
  let the user decide (see Chapter 8.2 of the playbook for the agreed priority order if time runs
  short).
- Do not leave `STATUS.md` or `DECISIONS.md` stale — an out-of-date status file is worse than none,
  because it actively misleads the next contributor.
