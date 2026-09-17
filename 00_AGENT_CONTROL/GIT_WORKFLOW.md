# Git Workflow

## Branch policy

`main` is never a working branch.

Recommended branch hierarchy:

- `phase/01-foundation`
- `phase/02-data-ingestion`
- `phase/03-profiling-visualization`
- `phase/04-ml-engine`
- `phase/05-ai-analytics`
- `phase/06-api-frontend-integration`
- `phase/07-3d-universe-ui`
- `phase/08-testing-docker-deployment`

For deeper work, use child branches:

- `backend/<phase>-<task>`
- `frontend/<phase>-<task>`
- `integration/<phase>-<task>`
- `chore/<phase>-<task>`

## Important

The agent may push phase/task branches if GitHub authorization is already available.

The agent must NOT:
- push commits to `main`;
- force push;
- delete remote branches;
- merge into `main`;
- rewrite shared history.

## Phase completion

A completed phase should have:
- passing checks;
- updated docs;
- a phase report;
- updated project state;
- one or more meaningful commits;
- remote branch pushed.

Then STOP.

The human decides when/how branches are merged.

## Suggested commit style

- `feat: ...`
- `fix: ...`
- `test: ...`
- `docs: ...`
- `refactor: ...`
- `chore: ...`

Avoid giant commits such as `finished phase`.

## Pre-push checklist

Before pushing a phase (or task) branch, verify — don't assume:

1. `git remote -v` — confirms `origin` is the expected GitHub remote.
2. `git branch --show-current` — confirms you are on the correct phase/task branch,
   **never** `main`.
3. `git status` — confirms a clean working tree (nothing stray, nothing missing that
   should have been included).
4. `git log` — confirms the commit(s) exist with accurate, meaningful messages.
5. Confirm — not assume — that `DEFINITION_OF_DONE.md`'s applicable checklist actually
   passed for this phase (tests, lint/type/build checks, docs, phase report, state update).

**Push, then verify:**

6. `git push origin <branch-name>` (never `origin main`).
7. Verify the push succeeded (e.g. `git ls-remote origin <branch-name>` matches the local
   commit hash).
8. Report the commit hash(es) and branch name in the phase completion report
   (`AGENT_MASTER_INSTRUCTIONS.md`).

The agent never pushes "because code exists" — pushing is the last step of a fully passed
phase gate, and always targets the phase branch, never `main`.

## History preservation

- Never force-push, ever, on any branch that has already been pushed.
- Never rewrite published history (`rebase -i` on a pushed branch, `commit --amend` after a
  push, `reset --hard` on a pushed commit).
- To undo a pushed change, use `git revert`, which preserves the record of what happened
  and why, rather than erasing it.
- The only destructive git operations permitted without a fresh explicit human confirmation
  are ones that touch **uncommitted, unpushed, local-only** state (e.g. discarding a bad
  local edit before it's ever committed).

## Tagging

Not required phase-by-phase. At the end of Phase 08 (Testing, Docker & Deployment), once
the release checklist in that phase's prompt passes, a version tag (`v1.0.0`, semantic
versioning) on the branch the human merges is the natural release marker — created by, or
with explicit sign-off from, the human, consistent with "human controls merges."

## .gitignore ownership

The root `.gitignore` is the single source of truth for excluded paths across the whole
repository (frontend, backend, uploaded data, tooling caches). Phase-specific additions are
added there, not in scattered per-directory ignore files, unless a specific tool requires
its own (document it if so).

---
*Related: [AGENT_MASTER_INSTRUCTIONS.md](AGENT_MASTER_INSTRUCTIONS.md) ·
[DEFINITION_OF_DONE.md](DEFINITION_OF_DONE.md) · [PROJECT_STATE.md](PROJECT_STATE.md)*
