# CAPITAL NUTRITION ERP — PRODUCTION / CUTOVER

## Objective

Deploy and transition to the ERP safely.

## Production stack

Define and document:
- application containers
- PostgreSQL
- reverse proxy
- TLS
- network isolation
- Magento connectivity
- background workers
- scheduled jobs

## Backup

Required:
- regular full backups
- WAL/archive strategy where appropriate
- encrypted offsite backup
- documented retention
- restore procedure

## Restore testing

A backup is not considered valid until it has been restored into a clean environment successfully.

Perform recurring restore drills.

## Monitoring

Monitor:
- application health
- PostgreSQL
- queue depth
- synchronization lag
- dead-letter queue
- failed jobs
- disk
- backup status
- replication where applicable

Alerts must be actionable.

## Cutover

Create an hour-by-hour runbook covering:
- final Odoo freeze
- final extraction
- migration
- physical inventory count
- reconciliation
- Magento synchronization state
- ERP activation
- verification
- rollback decision points

## Parallel run

Before final approval, compare Odoo and ERP for agreed consecutive clean days.

Compare:
- inventory
- AR
- AP
- P&L
- sales
- operational orders

## Rollback

Define explicit rollback triggers and procedures before cutover.

## Approval

Final cutover requires approval from:
- owner
- accountant
- responsible technical operator

No production cutover based solely on "it appears to work."
