# ADR-0013: One working architecture document

- **Status:** Accepted
- **Date:** 2026-08-19
- **Deciders:** ERP Architect chat (`FND-002`), Morris Hart

## Context

ADR-0010 (*One working specification directory*) made `docs/specs/` the single
working set for the domain specifications, and left `docs/spec-package/` as the
pristine, read-only package. It did not settle the four documents that are not
domain specifications: `00_MASTER_BUILD.md`, `01_ARCHITECTURE.md`,
`02_BUSINESS_RULES.md` and `15_CLAUDE_CHAT_PROTOCOL.md`.

The architecture in particular existed twice — `docs/ARCHITECTURE.md` and
`docs/spec-package/01_ARCHITECTURE.md` — byte for byte identical, both 3,597
bytes, with `CLAUDE.md` pointing chats at the first and `docs/specs/README.md`
§ Start with pointing at the second. Two paths to one document is the same shape
of trap ADR-0010 closed: it stays harmless exactly as long as nobody edits
either copy.

## Decision

**`docs/ARCHITECTURE.md` is the one working architecture document.** It is the
path named in `00_MASTER_BUILD.md` § Repository memory and in `CLAUDE.md`.

- `docs/spec-package/01_ARCHITECTURE.md` stays as pristine history, read-only,
  like the rest of that directory. Where the two differ, `docs/ARCHITECTURE.md`
  governs.
- **No `01_ARCHITECTURE.md` is to be created in `docs/specs/`.** A chat reading
  `docs/specs/README.md` § Start with, item 2, follows it to `docs/ARCHITECTURE.md`.
- The same rule applies to `docs/BUSINESS_RULES.md`, which is the working copy of
  `02_BUSINESS_RULES.md`.

## Consequences

### Accepted costs

- The working set is split across two locations by document type: domain
  specifications in `docs/specs/`, cross-cutting documents at `docs/` top level.
  That is a rule every chat must know, which is exactly the kind of thing
  ADR-0010 rejected in its "keep both and add a precedence rule" alternative.
  It is accepted here only because both `00_MASTER_BUILD.md` and `CLAUDE.md`
  already name the top-level paths, so moving them would break the documents that
  every chat reads first.
- `docs/spec-package/01_ARCHITECTURE.md` will drift further from
  `docs/ARCHITECTURE.md` with every architecture change. That is intended: the
  package records what was originally specified.

### Rejected alternatives

- **Move the architecture into `docs/specs/01_ARCHITECTURE.md`.** Rejected: it
  contradicts `00_MASTER_BUILD.md` § Repository memory and `CLAUDE.md`, both of
  which name `docs/ARCHITECTURE.md`, and it would leave the old path as a stale
  file or a broken reference in every task document.
- **Keep both copies in sync.** Rejected for the reason ADR-0010 gives: a
  synchronisation rule is a thing that must be remembered correctly forever.
- **Delete the pristine copy.** Rejected: the value of the package is that it is
  pristine.

## Verification

Wrong if a chat is found designing against `docs/spec-package/01_ARCHITECTURE.md`
after this date, which would mean the pointer in `docs/specs/README.md` needs a
correction rather than an ADR.

Check: `docs/specs/01_ARCHITECTURE.md` does not exist, and `docs/ARCHITECTURE.md`
is the only architecture file outside `docs/spec-package/`.
