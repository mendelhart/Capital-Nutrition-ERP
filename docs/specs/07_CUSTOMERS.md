# CAPITAL NUTRITION ERP — CUSTOMERS / PARTIES SPECIFICATION

## Objective

Create a canonical customer/party model usable by ERP sales, accounting, reporting, and Magento.

One ERP party is the single financial and legal identity. Storefront identities attach to it; they do not replace it.

## Ownership boundary

ERP owns:
- the canonical party
- legal/customer name
- billing address
- tax information
- payment terms
- credit status/limit
- customer pricing group
- active/inactive state
- receivable account assignment

Magento owns:
- Magento customer ID
- Magento account identity (email/login)
- storefront-specific identity data
- storefront address book entries

Neither system silently overwrites the other's fields. The mapping between them is explicit, stored, and auditable.

Conflicts are resolved by owner: an inbound Magento payload never mutates an ERP-owned field. Divergence is recorded, not applied.

## Functional scope

### Party model

Base on the Tryton `party` module. Extend rather than replace.

Define:
- party name (legal/customer name)
- party code and its sequence
- company vs individual distinction if required
- active/inactive flag
- party categories

Do not fork `party.party`. Storefront concerns belong in the Magento mapping model, not on the core party.

### Addresses

Support:
- one billing address per party at any given time
- multiple shipping addresses
- address purpose/usage flags
- country and subdivision required for tax determination
- address validity/active state

Historical documents must retain the address as posted. Editing a party address must not retroactively alter a posted invoice or a shipped order.

### Contact information

Support:
- email
- phone
- mobile
- other contact mechanisms as required

Contact mechanisms are attached to the party and optionally scoped to an address or a role.

### Tax information

Support:
- tax identifiers (registration numbers)
- customer tax rule / exemption status
- exemption certificate reference and expiry if applicable
- jurisdiction relevant to the shipping address

Tax calculation itself is delegated to the provider/adaptor defined in `03_ACCOUNTING.md`. This specification defines only the customer-side inputs.

### Payment terms

Support:
- default customer payment term
- override at order/invoice level
- term inheritance rules

### Credit status and limit

Support:
- credit limit amount
- current exposure calculation
- credit hold state
- behavior when a new order exceeds the limit

Whether an over-limit order is blocked, warned, or routed for approval is a policy decision. See Open questions.

### Customer pricing group

Support:
- assignment of a party to a pricing group
- resolution of the applicable price list at order time
- a defined default for parties with no explicit group

Pricing group semantics are shared with the Sales and Magento domains. The resolution order must be identical in ERP and storefront, or storefront-quoted prices will not match invoiced prices.

### External identifiers

Support:
- Magento customer ID(s)
- legacy Odoo party ID (required for migration reconciliation)
- other external identifiers as required

Each identifier records its source system, the external value, and the date the link was established.

### Lifecycle and state

Support:
- active/inactive state
- inactivation without deletion
- refusal to delete a party with financial history

A party referenced by any posted accounting document is never deleted. It is deactivated.

## Deduplication and matching

Customer creation from Magento must:
- identify existing matches before creating a new party
- avoid accidental duplicate parties
- preserve multiple Magento identities where legitimate
- record the mapping explicitly

### Matching

Define an ordered, deterministic match strategy. Candidate signals include:
- exact match on an already-mapped Magento customer ID
- tax identifier
- normalized email
- normalized name plus normalized billing address

The strategy must produce three outcomes:
1. Confident match — link to the existing party.
2. No match — create a new party.
3. Ambiguous — queue for human review; do not guess.

Ambiguous cases must never be auto-resolved into either a link or a new party.

Normalization rules (case, whitespace, punctuation, address abbreviations) must be defined once and applied identically on both sides.

### Legitimate multiplicity

Multiple Magento accounts mapping to one ERP party is a supported, expected state — not an error. Examples: a business with several buyers, or a customer who registered twice.

The reverse — one Magento account mapping to multiple ERP parties — is invalid and must be rejected by constraint.

### Review queue

Provide a reviewable queue of ambiguous and rejected matches with:
- the inbound payload
- the candidate parties considered
- the reason for the outcome
- an operator action to link, create, or reject

## Merge

Duplicates will occur. A merge path is mandatory.

Merging must:
- transfer or re-point Magento mappings
- preserve accounting history on the surviving party
- leave posted documents intact and traceable
- record the merge (who, when, source, target)
- prevent the merged-away party from being reused for new transactions

Tryton's party replace/erase wizards are the intended starting point. Their behavior must be verified against 8.0.x and against every custom model that references a party before merge is offered to operators.

Merges are not silently reversible. If unmerge is required, it must be specified explicitly.

## Sales and accounting dependencies

Customer records must support:
- quotations/orders
- invoices
- payments
- refunds/credit notes
- AR aging
- reporting

Concretely this requires, per party:
- a receivable account
- a payment term
- a tax rule
- a price list resolution
- a currency

These must be resolvable at document creation time, or document creation must fail with a clear reason rather than silently defaulting.

Consistency with `03_ACCOUNTING.md`: AR aging, partial payments, and credit notes are specified there. This document must not restate or contradict those rules.

## Integration contract obligations

The following must be defined in `12_INTEGRATION_CONTRACTS.md` and are named here as dependencies, not resolved here:
- inbound customer payload schema from Magento
- outbound party payload to Magento, if any
- idempotency and retry semantics
- ordering guarantees for customer-before-order events
- error and rejection channel
- handling of a Magento order whose customer failed to match

An order must never be created against a party that was invented to satisfy the order.

## Required scenarios

1. New Magento customer, no existing party → new party created, mapping recorded.
2. New Magento customer, matches existing party → linked, no duplicate created.
3. Second Magento account for an existing party → both mappings coexist on one party.
4. Ambiguous match → queued for review, no party created, no order lost.
5. Magento address change → storefront data updated, ERP-owned billing address unchanged.
6. ERP billing address change → posted invoices unchanged.
7. Order → invoice → payment → AR aging, all resolving to one party.
8. Credit note against a party with multiple Magento accounts.
9. Party exceeds credit limit on a new order → defined behavior triggered.
10. Duplicate parties merged → accounting history preserved, mappings re-pointed.
11. Attempted deletion of a party with posted documents → refused.
12. Party deactivated → excluded from new orders, still present in reporting and aging.
13. Migration: Odoo party loaded, legacy ID retained, reconciles to source.

## Acceptance

One ERP party can correctly map to multiple Magento accounts without corrupting sales or accounting history.

Demonstrated by:
- AR aging for that party is complete and correct across all its Magento accounts.
- No duplicate party was created across the scenario set.
- Every ambiguous case surfaced for review rather than resolving itself.
- A merge of two duplicates leaves the trial balance unchanged.
- Migrated parties reconcile to the Odoo source by count and by AR balance.

## Open questions

Do not invent:
- the exact match strategy thresholds and field precedence
- whether email is a sufficient match signal on its own
- credit limit policy: block, warn, or approval-route
- who owns the ambiguous-match review queue operationally
- the default pricing group for unassigned parties
- whether B2B and B2C parties require distinct handling
- exemption certificate storage and expiry enforcement
- whether outbound ERP→Magento party sync is in scope at all
- unmerge requirements
- the final Magento mapping model naming, which belongs to the Magento domain

Mark them as open until source documentation and business approval exist.
