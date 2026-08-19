# ADR-0010: One working specification directory

- **Status:** Accepted
- **Date:** 2026-08-19
- **Deciders:** Morris Hart
- **Answers:** `STATUS.md` Q9 / next-action 5 — which repository directory is authoritative for specs

## Context

The repository held three overlapping copies of the specification set:

| Directory | Role | State when found |
|---|---|---|
| `docs/spec-package/` | pristine build package | complete, original, unmodified |
| `docs/specs/` | working specifications | complete after 04/05/10 were brought across; the expanded, current versions |
| `docs/domains/` | working specifications | partial duplicate, drifted |

`docs/domains/` had diverged. `08_SALES.md` was 1,537 bytes there against 12,072
bytes in `docs/specs/`; `09_MAGENTO.md` was 2,041 against 11,484. In both cases
`docs/domains/` still held the original stub while the worked specification lived
in `docs/specs/`.

`CLAUDE.md` instructed every chat to read `docs/domains/*.md`. A Sales or Magento
chat following that instruction would have designed against the stub and never
seen the real specification. This was not a latent risk; it was the documented
procedure.

## Decision

`docs/specs/` is the single working specification directory.

- `04_PRODUCTS.md`, `05_INVENTORY.md` and `10_REPORTING.md` existed only in
  `docs/domains/`. They were byte-identical to the pristine package versions and
  were copied into `docs/specs/` unchanged. They remain original stubs and have
  not been worked on — treat them accordingly.
- Every other file in `docs/domains/` was either identical to its `docs/specs/`
  counterpart or an older, shorter version of it. No content was lost.
- `docs/domains/` is retired. Its files were moved to
  `_to_delete/docs-domains-retired/` rather than deleted, because the workspace
  mount does not permit deletion; that directory is gitignored and can be removed
  by hand.
- `docs/spec-package/` stays as the read-only pristine package.
- `CLAUDE.md` now names `docs/specs/` as the one working set.

## Consequences

### Accepted costs

- Two directories still hold a copy of each specification — the working set and
  the pristine package. That duplication is deliberate and useful: it shows what
  the build package originally said versus what we decided. It is only a hazard
  when a third, undeclared copy appears, which is what this ADR removes.
- Anyone with an open branch or an in-flight chat referencing `docs/domains/`
  will get a missing path. That is the intended failure — loud, not silent.

### Rejected alternatives

- **Promote `docs/domains/` instead, as `CLAUDE.md` described.** Rejected: it
  held the older content for Sales and Magento, so promoting it would have meant
  copying the good versions in from `docs/specs/` first, arriving at the same
  place with more steps and more chance of losing work.
- **Keep both and add a precedence rule.** Rejected: a precedence rule is a
  thing every chat must read and remember correctly, forever. Deleting the
  duplicate is a thing that cannot be forgotten.
- **Merge everything back into `docs/spec-package/`.** Rejected: the value of the
  pristine package is that it is pristine. Editing it destroys the record of
  what was originally specified versus what we changed.

## Verification

Wrong if `docs/specs/` turns out to be missing worked content that existed only
in `docs/domains/`. Checked before retiring: every overlapping file was compared
byte for byte, and the three files unique to `docs/domains/` were carried across.
The retired copies remain in `_to_delete/docs-domains-retired/` until the tree is
confirmed good, so this is reversible.

Grep for `docs/domains` across the repository should return nothing outside this
ADR and the baseline commit message.
