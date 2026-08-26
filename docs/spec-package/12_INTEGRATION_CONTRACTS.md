# CAPITAL NUTRITION ERP — INTEGRATION CONTRACTS

## Purpose

This document defines the boundaries between independently developed domains.

A domain is not allowed to invent behavior at an interface.

## Sales ↔ Inventory

### Inputs
- product
- requested quantity
- warehouse/location
- reservation/availability

### Outputs
- reserved quantity
- fulfillment state
- shipment
- backorder
- cancellation effects

### Required scenarios
- full fulfillment
- partial fulfillment
- insufficient stock
- cancellation
- return

## Sales ↔ Accounting

### Inputs
- customer
- lines
- prices
- discounts
- taxes
- currency
- payment

### Outputs
- invoice
- AR
- revenue
- tax
- credit/refund

## Purchasing ↔ Inventory

### Inputs
- PO
- product
- quantity
- expected receipt

### Outputs
- receipt
- stock quantity
- lot
- valuation

## Purchasing ↔ Accounting

### Inputs
- vendor bill
- receipt
- price
- tax
- landed cost

### Outputs
- AP
- inventory/accrual
- payment

## Products ↔ Sales/Purchasing/Inventory

The product master provides canonical product identity, units, SKU, categories, and required configuration.

Each domain must not maintain its own competing product identity.

## Magento ↔ Sales

Magento order identity must map deterministically to ERP order identity.

Required external references:
- Magento order ID
- order increment number where relevant
- external line identifiers

## Magento ↔ Customers

Magento customer ID maps to ERP party.

Multiple Magento identities may map to one ERP party when explicitly valid.

## Magento ↔ Inventory

ERP owns inventory availability.

Magento receives availability updates according to the approved batching/debounce policy.

## Reporting ↔ Transactional systems

Reporting reads approved transactional data and must not alter accounting or inventory.

## Contract change process

Any change to a contract requires:
1. update this document
2. assess affected domains
3. create ADR if architectural
4. update tests on both sides
5. update STATUS.md.
