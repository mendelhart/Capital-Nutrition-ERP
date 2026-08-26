# CAPITAL NUTRITION ERP — MIGRATION SPECIFICATION

## Objective

Move from Odoo to the new ERP with zero unexplained financial differences.

## Principles

- Never migrate blindly.
- Extract from a controlled source snapshot.
- Preserve source identifiers.
- Use explicit mappings.
- Make loads idempotent.
- Rehearse repeatedly.
- Reconcile automatically.

## Extraction

Use read-only extraction into staging structures.

Credentials must remain with the user/operator and must never be committed.

## Mapping

Maintain reviewable mapping tables for:
- accounts
- products
- customers/parties
- vendors
- taxes
- other required master data

Accountant reviews accounting mappings.

## Inventory

Physical inventory is counted at cutover.

Historical inventory records may be migrated for reference where useful, but opening operational inventory must come from an approved physical count/reconciliation process.

## Financial opening

Load:
- opening balances
- open AR
- open AP
- approved open POs
- required historical/reference data

## Reconciliation

Compare:
- trial balance
- AR aging
- AP aging
- open POs
- inventory value
- order counts by month
- sales totals
- payments/refunds where applicable

## Rehearsals

Perform at least three complete migration rehearsals.

The third should be routine and repeatable.

## Acceptance

Opening trial balance ties exactly.

Any discrepancy must be explained, corrected through an approved process, or block cutover.
