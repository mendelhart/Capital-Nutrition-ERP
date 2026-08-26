# CAPITAL NUTRITION ERP — UI / UX SPECIFICATION

## Objective

Make the ERP fast, clear, consistent, and practical for approximately three ERP users.

This domain has its own dedicated development stream. UI quality is not left to whichever developer happens to build a feature.

## UX principles

1. Optimize for frequent workflows.
2. Minimize unnecessary clicks.
3. Keep important information visible.
4. Make errors understandable and actionable.
5. Use consistent terminology.
6. Never sacrifice accounting or inventory correctness for visual convenience.
7. Prefer familiar ERP patterns over novelty.
8. Preserve keyboard efficiency where practical.

## Global standards

Define and consistently apply:
- navigation
- page hierarchy
- forms
- tables
- filters
- search
- sorting
- pagination
- dialogs
- confirmation behavior
- notifications
- error states
- empty states
- loading states
- permissions
- audit visibility

## Core screens

Prioritize:

### Dashboard
Show operational exceptions and high-value metrics rather than decorative charts.

### Sales
- order list
- order detail
- customer history
- fulfillment state
- payment state

### Purchasing
- PO list
- PO detail
- vendor history
- receiving
- discrepancies

### Inventory
- stock lookup
- warehouse/location view
- lot information
- movement history
- availability

### Accounting
- invoices
- bills
- payments
- reconciliation
- period status
- reporting

### Integration
- queue
- failures
- dead letters
- replay
- reconciliation

## UI consistency contract

No domain chat may invent a conflicting navigation pattern, terminology, button hierarchy, table convention, or status representation.

If a new pattern is needed:
1. document it
2. evaluate reuse
3. update this specification
4. apply it consistently.

## Acceptance

A user can complete the most common sales, purchasing, inventory, and accounting workflows without unnecessary navigation or confusing states.
