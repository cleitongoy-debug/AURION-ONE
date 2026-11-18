# Public Exposure Remediation Rule

Status: DIRECTIVE_COMMITTED — execution requires each runtime's own readback/ACK.

## Objective
Reduce public exposure of only the compromised fragments while preserving repositories, projects, files, history, authorized access, and running systems.

## Required method
1. Inventory only content already identified as potentially exposed.
2. For personal identifiers (email, phone, address, tokens or account identifiers), replace the exposed value in public-facing copies with a non-reversible mask or neutral placeholder. Never publish a lightly altered real credential as a substitute.
3. For internal operational details, rewrite only the sensitive passage into a minimal, non-sensitive description. Preserve surrounding useful documentation.
4. If a whole passage cannot be safely separated, restrict public visibility of that specific artifact or location while retaining the authorized original.
5. Verify the public-facing result by reading it back from the public branch/location.
6. Record exact paths, changed fragments (without reproducing secrets), commit IDs, verification time, and status.

## Preservation constraints
- DO NOT delete repositories, projects, branches, unrelated files, or useful history.
- DO NOT stop, restart, disable, or reconfigure running AURION systems.
- DO NOT change repository visibility or access permissions without explicit authorization.
- DO NOT rewrite Git history, force-push, purge caches, or remove forks as part of this directive.
- DO NOT copy sensitive values into logs, issues, commits, reports, or agent messages.
- Keep authorized originals intact; make the smallest safe change to public-facing copies.
- If a target, ownership, or exposure is uncertain, mark BLOCKED_NEEDS_OPERATOR_SCOPE and do not modify it.

## Evidence states
Use only: IDENTIFIED, CHANGE_COMMITTED, READBACK_VERIFIED, BLOCKED_NEEDS_OPERATOR_SCOPE, ACK_PENDING.
A commit is not proof that another agent/runtime received or executed this directive. Each runtime must return its own ACK and readback evidence.

## Completion report
Report repository/path, minimal change summary, commit SHA, public readback result, and remaining exposure. Never claim complete cleanup while historical copies or unverified destinations remain.
