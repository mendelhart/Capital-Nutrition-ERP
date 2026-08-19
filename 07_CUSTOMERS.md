# CAPITAL NUTRITION ERP — CUSTOMERS / PARTIES

## Objective

Create a canonical customer/party model usable by ERP sales, accounting, reporting, and Magento.

## Ownership

ERP owns the canonical party.

Magento owns:
- Magento customer ID
- Magento account identity
- storefront-specific identity data

Maintain explicit mapping between them.

## Customer data

Support as required:
- legal/customer name
- billing address
- shipping addresses
- contact information
- tax information
- payment terms
- credit status/limit if applicable
- customer pricing group
- external identifiers
- active/inactive state

## Deduplication

Customer creation from Magento must:
- identify existing matches
- avoid accidental duplicate parties
- preserve multiple Magento identities where legitimate
- record mapping explicitly

## Sales and accounting

Customer records must support:
- quotations/orders
- invoices
- payments
- refunds/credit notes
- AR aging
- reporting

## Acceptance

One ERP party can correctly map to multiple Magento accounts without corrupting sales or accounting history.
