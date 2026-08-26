# ADR-0014: Tryton's own queue for asynchronous integration work

- **Status:** Accepted
- **Date:** 2026-08-19
- **Deciders:** ERP Architect chat (`FND-002`), Morris Hart

## Context

`docs/specs/09_MAGENTO.md` § Integration architecture requires a queue that is
"ordered, durable, worker-consumed", plus retry, dead-lettering and replay.
Nothing states what provides it. An implementer reaching for the familiar answer
would add Celery and Redis — a second datastore, a second process supervisor and
a second failure mode, for an ERP with three users.

What Tryton 8.0.9 actually provides was verified against the installed package
rather than assumed:

- `ir.queue` (`trytond/ir/queue_.py`) with `Model.__queue__` as the caller,
  `push`/`pull`, `scheduled_at` and `expected_at` fields, and PostgreSQL
  `LISTEN`/`NOTIFY` wake-up.
- `trytond-worker` and `trytond-cron` as installed console scripts;
  `trytond-worker --processes` for concurrency.
- Failure handling that is deliberately thin: the worker reschedules only on
  `DatabaseOperationalError`; a `UserError`/`UserWarning` is recorded to
  `ir.error` and **not** retried; any other exception is logged and the task ends.

## Decision

Use `ir.queue` with `trytond-worker` for asynchronous work, and `trytond-cron`
for scheduled work. No external broker — no Celery, Redis, RabbitMQ or
equivalent — without a superseding ADR.

**The queue is transport only.** The integration's state machine — attempt count,
error classification, backoff, dead-letter, parked-for-review, replay — lives in
the integration's own durable records: the external-event ledger of ADR-0002
(*A single external-event ledger for integration idempotency*) and the Magento
event model of `docs/specs/09_MAGENTO.md`. A design that expects `ir.queue` to
remember a failure is wrong and will lose events.

## Consequences

### Accepted costs

- Retry, backoff and dead-lettering are ours to implement in the event model.
  They are not free with the platform. This is work the specification already
  required, but it must not be assumed to be already done by the queue.
- Queue throughput is bounded by PostgreSQL and by `--processes`. At Capital
  Nutrition's volume this is not a constraint; if it becomes one, that is the
  observation that reopens this decision.
- `ir.queue` rows accumulate until cleaned (`clean_days`, default 30). Retention
  is an operations setting to be recorded, not left at the default by accident.
- Ordering is by `scheduled_at`/`expected_at`, not strict FIFO per stream. A flow
  that needs per-order sequencing enforces it in its own event model — for
  example by parking an order whose customer has not yet matched, which
  `07_CUSTOMERS.md` and `09_MAGENTO.md` already require.

### Rejected alternatives

- **Celery + Redis (or RabbitMQ).** Rejected: a second datastore to back up,
  monitor, secure and restore, and a second place for a money event to disappear,
  in a system whose whole premise is that its owner can maintain it. It also puts
  the queue outside the database transaction, so "committed but not enqueued"
  becomes possible.
- **A polling table written by hand.** Rejected: that is `ir.queue`, without the
  `LISTEN`/`NOTIFY` wake-up, the worker, or the upstream maintenance.
- **In-process threads.** Rejected: work is lost on restart, silently, on the
  money path.
- **Rely on `ir.queue` for retry and dead-lettering.** Rejected on the evidence
  above: it retries only database operational errors, and a `UserError` ends the
  task with no retry and no dead-letter state that an operator can act on.

## Verification

Wrong if observed Magento volume exceeds what a PostgreSQL-backed queue serves
comfortably, or if a required flow needs strict cross-event ordering that
`ir.queue` cannot express. Watch synchronisation lag (`docs/runbooks/MONITORING.md`)
and the dead-letter arrival rate during the parallel run.

Evidence for the platform claims: `trytond` 8.0.9 as published —
`trytond/ir/queue_.py`, `trytond/worker.py`, `trytond/cli/worker.py`, and the
`console_scripts` entry points. Re-check on any move off the 8.0 series.
