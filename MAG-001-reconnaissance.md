# CAPITAL NUTRITION ERP — MAG-001

## Task ID

`MAG-001`

## Domain

`MAGENTO`

## Objective

Produce an approved reconnaissance map of the live Magento 1 installation, so
that connector design rests on observed facts rather than assumptions about what
Magento 1 typically does.

This task writes documentation only. It writes no connector code.

## Context

Reference:
- `docs/spec-package/00_MASTER_BUILD.md` — principle 7, every external integration must be idempotent
- `docs/specs/09_MAGENTO.md` — "Phase 0 — reconnaissance"
- `docs/integration/12_INTEGRATION_CONTRACTS.md` — Magento ↔ Sales, ↔ Customers, ↔ Inventory
- `docs/specs/07_CUSTOMERS.md` — party mapping obligations
- `docs/STATUS.md`

## Scope

### In scope
- Inspecting the live Magento installation and its admin configuration
- Inspecting the Magento codebase for overridden core classes and installed extensions
- Exercising each candidate API endpoint against a non-production copy where one exists
- Recording observed request/response shapes, limits, and failures
- Identifying gaps that require a custom Magento module
- Writing the map to `docs/specs/09_MAGENTO_RECON.md`

### Out of scope
- Any ERP model, connector, queue, or worker code
- Any change to the Magento installation, including installing a module
- Any decision that closes an open question in `09_MAGENTO.md` without business approval

## Existing code

None. `modules/`, `scripts/`, and `tests/` are empty.

## Functional requirements

The map must answer each question below with a stated fact and its source. Where
a fact cannot be established, record `UNKNOWN` and what would be needed to
establish it. Do not infer from Magento 1 general behavior.

### 1. Platform identity
1. Exact Magento version string, from the codebase and from the admin, noting
   which sources were available and whether they agree.
2. Edition: Community or Enterprise.
3. Magento or OpenMage, and if OpenMage, the fork version.
4. PHP version, MySQL version, web server.
5. Patch level and whether security patches are current.
6. Who maintains it, and what the change/deploy process is.

### 2. API surface
7. Which APIs are enabled: SOAP v1, SOAP v2 (WS-I), REST.
8. The API endpoint URLs.
9. Whether the API user, role, and resource ACLs exist, and what they grant.
10. For each flow in `09_MAGENTO.md`, the exact API call that serves it, or `NONE`.
11. For each such call, an observed sample request and response.
12. Fields present in each response, and fields required by the ERP that are absent.

### 3. Limits and behavior
13. Observed rate limits, or evidence that none are enforced.
14. Observed latency for a single call and for a batch call.
15. Maximum practical batch size before timeout.
16. Session/token lifetime and renewal behavior.
17. Fault codes returned for: bad credentials, unknown entity, invalid payload, concurrent write.
18. Behavior on a repeated identical write — does Magento deduplicate, or duplicate?

### 4. Customizations
19. Overridden core classes, by class and by module.
20. Installed third-party extensions, with version and purpose.
21. Custom order or customer attributes, and whether the API exposes them.
22. Custom order states or statuses beyond stock Magento.
23. Any existing integration already writing to Magento, and what it touches.

### 5. Events
24. Whether any webhook or outbound event capability exists.
25. If not, the polling strategy the connector will require, and what field supports incremental polling.
26. Whether order/customer records carry a reliable `updated_at` that changes on every write.

### 6. Money
27. Payment methods configured, with their Magento codes.
28. Whether payment capture happens in Magento, at the gateway, or elsewhere.
29. How refunds and credit memos are represented, and whether partials are supported.
30. Where tax is calculated, and which figure Magento treats as authoritative.
31. Currency configuration and rounding behavior.

### 7. Inventory
32. How stock is represented, including whether Magento manages stock per SKU or per store.
33. Which field the ERP would write to update availability.
34. Whether configurable/grouped/bundle products exist, and how their stock behaves.

### 8. Gaps
35. Each flow that cannot be served by the existing API.
36. For each gap, whether a custom Magento module is required, and roughly what it must do.
37. Any gap that changes the scope or feasibility of `09_MAGENTO.md`.

## Business rules

None applied by this task. The task records what exists; it does not change it.

## Integration requirements

Upstream dependencies: none.

Downstream consumers: every other MAG task. `MAG-002` through `MAG-026` are
blocked on this map being approved.

Failure behavior: if a question cannot be answered, it is recorded as `UNKNOWN`
with the blocker named. An unanswered question blocks only the tasks that depend
on it, not the whole map.

Idempotency: not applicable — read-only reconnaissance.

## Technical requirements

- Output document: `docs/specs/09_MAGENTO_RECON.md`
- One section per numbered area above, one entry per question.
- Each entry records: the answer, the source, and the date observed.
- Sample payloads are stored redacted. No credentials, no customer personal data,
  no payment instrument data enters the repository.
- Credentials used for reconnaissance are held outside the repository.
- Where an API was exercised, note whether it was against production or a copy.

## Tests

No automated tests. Verification is by review:

- Every question has an answer or an explicit `UNKNOWN`.
- Every answer names a source.
- No answer is phrased as an expectation ("should", "typically", "by default").
- Sample payloads are redacted.

## Acceptance criteria

The task is complete when:

- [ ] `docs/specs/09_MAGENTO_RECON.md` exists and covers all 37 questions.
- [ ] Every answer carries a source and an observation date.
- [ ] Gaps requiring a custom Magento module are listed explicitly.
- [ ] Any finding that contradicts `09_MAGENTO.md` is raised, not quietly absorbed.
- [ ] The ERP owner has approved the map.
- [ ] `docs/STATUS.md` records the Magento domain as reconnaissance-complete.

## Documentation

Update:
- `docs/STATUS.md`
- `docs/specs/09_MAGENTO.md` — close any open question the map resolves
- `docs/integration/12_INTEGRATION_CONTRACTS.md` — if the map changes a Magento contract
- ADR if the map forces an architectural decision, such as requiring a custom Magento module

## Commit

`MAG-001: Magento 1 reconnaissance map`

## Handoff

If incomplete, create:

`docs/tasks/MAGENTO/MAG-001-handoff.md`

recording which of the 37 questions are answered, which are blocked and on what,
and the exact next step.

## Note on current access

As of this task's writing, no API credentials or admin access have been provided
to the build. Until they are, this task cannot start and every MAG task remains
blocked. The first concrete action is obtaining:

- Magento admin access, read-only is sufficient for most questions
- SOAP/REST API credentials scoped for reconnaissance
- filesystem or repository access to the Magento codebase
- confirmation of whether a staging copy exists to exercise calls against
