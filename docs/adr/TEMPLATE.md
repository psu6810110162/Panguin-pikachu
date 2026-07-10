# ADR-NNN: <short title, verb phrase>

**Status:** Accepted <!-- or: Superseded by ADR-0XX / Deprecated -->

## Context

<What problem/question forced this decision? What constraints applied? Link to the
requirement, discussion, or prior ADR that led here.>

## Decision

<What we're doing, stated plainly. Include the concrete shape — file paths, config
values, library names — not just the abstract idea.>

## Consequences

<What we get, what we give up, and when to revisit. If this decision could be wrong
under different constraints, say what would change your mind.>

---

**Numbering:** `NNN-kebab-title.md`, zero-padded 3 digits, next free number after the
highest existing ADR.

**Rules (see "Changing or adding an ADR" in `docs/ENGINEERING_PLAN.md`):**
- ADRs are immutable records — don't edit an old ADR's Decision after the fact. If a
  decision changes, write a **new** ADR that supersedes it and cross-link both ways.
- Write one when: adding/removing a dependency, changing the data model/contract,
  changing the security model, or reversing a prior ADR.
- Same PR process as code: CI green + 1 review from the other person.
