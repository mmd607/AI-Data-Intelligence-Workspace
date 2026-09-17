# START HERE — Give this repository to your coding agent

Paste the following as the first instruction:

> Read `README.md` and every file under `00_AGENT_CONTROL/` before coding.
> Do not start implementation until you understand the branch and phase rules.
> Inspect the repository and Git status.
> Read `PROJECT_STATE.md`.
> Start only the current phase.
> Ask me only when a permission, credential, destructive action, architectural
> decision, or other explicit human approval is required.
> At the end of the phase, run the Definition of Done, update the state and phase
> report, commit, push the non-main branch, and STOP. Never push to main and never
> merge automatically.

## GitHub authorization

If GitHub access is not already authenticated in the agent environment, the agent
must ask you to authenticate. Do not paste tokens into project files or chat.

## After authentication

The agent should verify:
- remote URL;
- current branch;
- push permission;
- repository status.

Then begin Phase 01.

---
*Source of truth: [AGENT_MASTER_INSTRUCTIONS.md](AGENT_MASTER_INSTRUCTIONS.md) ·
[PROJECT_STATE.md](PROJECT_STATE.md) · [GIT_WORKFLOW.md](GIT_WORKFLOW.md) ·
[DEFINITION_OF_DONE.md](DEFINITION_OF_DONE.md)*
