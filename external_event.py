# This file is part of the Capital Nutrition ERP.
"""Idempotency ledger for inbound external events.

Every external integration must be idempotent (MASTER_BUILD, core principle 7
and non-negotiable 4). Rather than re-implementing "have I seen this before?"
in each integration, all inbound events are recorded once here, keyed by
``(source, event_type, external_id)`` and protected by a database unique
constraint.

See ``docs/adr/0002-external-event-idempotency-ledger.md``.
"""

import datetime as dt
import hashlib
import json

from trytond.i18n import gettext
from trytond.model import Index, ModelSQL, ModelView, Unique, fields
from trytond.pool import Pool
from trytond.pyson import Eval

from .exceptions import ExternalEventPayloadMismatch, ExternalEventStateError

__all__ = ['ExternalEvent']

STATES = [
    ('received', "Received"),
    ('processed', "Processed"),
    ('failed', "Failed"),
    ('ignored', "Ignored"),
    ]


class ExternalEvent(ModelSQL, ModelView):
    "External Event"
    __name__ = 'capital_nutrition.external.event'
    _rec_name = 'external_id'

    source = fields.Char(
        "Source", required=True, readonly=True,
        help="System the event originated from, e.g. 'magento'.")
    event_type = fields.Char(
        "Event Type", required=True, readonly=True,
        help="Kind of event within the source, e.g. 'sales_order'.")
    external_id = fields.Char(
        "External Identifier", required=True, readonly=True,
        help="Identifier of the event in the source system.")
    payload_digest = fields.Char(
        "Payload Digest", readonly=True,
        help="SHA-256 of the canonical payload, used to detect a replay "
        "carrying different content.")
    state = fields.Selection(STATES, "State", required=True, readonly=True,
        sort=False)
    received_at = fields.Timestamp("Received at", required=True, readonly=True)
    processed_at = fields.Timestamp(
        "Processed at", readonly=True,
        states={'invisible': Eval('state') != 'processed'})
    attempts = fields.Integer("Attempts", required=True, readonly=True)
    error_message = fields.Text(
        "Error Message", readonly=True,
        states={'invisible': Eval('state') != 'failed'})
    origin = fields.Reference(
        "Origin", selection='get_origin', readonly=True,
        help="ERP record this event produced.")

    @classmethod
    def __setup__(cls):
        super().__setup__()
        table = cls.__table__()
        cls._sql_constraints += [
            ('key_unique',
                Unique(
                    table, table.source, table.event_type, table.external_id),
                'capital_nutrition_base.msg_external_event_key_unique'),
            ]
        cls._sql_indexes.add(
            Index(
                table,
                (table.state, Index.Equality()),
                (table.source, Index.Equality())))
        cls._order = [('received_at', 'DESC'), ('id', 'DESC')]

    @classmethod
    def default_state(cls):
        return 'received'

    @classmethod
    def default_attempts(cls):
        return 0

    @classmethod
    def default_received_at(cls):
        return dt.datetime.now()

    @classmethod
    def _get_origin(cls):
        "Model names an event may point at. Domain modules extend this."
        return []

    @classmethod
    def get_origin(cls):
        Model = Pool().get('ir.model')
        get_name = Model.get_name
        models = cls._get_origin()
        return [(None, '')] + [(m, get_name(m)) for m in models]

    # -- idempotency ---------------------------------------------------

    @staticmethod
    def digest(payload):
        "Stable SHA-256 digest of a JSON-serialisable payload."
        if payload is None:
            return None
        if isinstance(payload, bytes):
            data = payload
        elif isinstance(payload, str):
            data = payload.encode('utf-8')
        else:
            data = json.dumps(
                payload, sort_keys=True, separators=(',', ':'),
                default=str).encode('utf-8')
        return hashlib.sha256(data).hexdigest()

    @classmethod
    def register(cls, source, event_type, external_id, payload=None):
        """Idempotently record an inbound event.

        Returns ``(event, is_new)``. ``is_new`` is False when this exact key
        has already been seen, which is the caller's signal to skip the work
        rather than repeat it.

        Raises ``ExternalEventPayloadMismatch`` when a known key comes back
        with different content — that is reported, never silently accepted.

        Concurrency: two transactions registering the same key at the same
        time are serialised by the ``key_unique`` database constraint; the
        loser gets an integrity error and must retry the whole transaction.
        The constraint, not this method, is the invariant.
        """
        source = cls._normalise(source)
        event_type = cls._normalise(event_type)
        external_id = cls._normalise(external_id)
        if not (source and event_type and external_id):
            raise ValueError(
                "source, event_type and external_id are all required")

        digest = cls.digest(payload)
        events = cls.search([
                ('source', '=', source),
                ('event_type', '=', event_type),
                ('external_id', '=', external_id),
                ], limit=1)
        if events:
            event, = events
            if (digest and event.payload_digest
                    and digest != event.payload_digest):
                raise ExternalEventPayloadMismatch(
                    cls._message(
                        'msg_external_event_payload_mismatch',
                        source=source, event_type=event_type,
                        external_id=external_id))
            return event, False

        event = cls(
            source=source,
            event_type=event_type,
            external_id=external_id,
            payload_digest=digest,
            state='received',
            attempts=0,
            received_at=dt.datetime.now())
        event.save()
        return event, True

    @staticmethod
    def _normalise(value):
        return value.strip() if isinstance(value, str) else value

    @staticmethod
    def _message(name, **kwargs):
        return gettext(f'capital_nutrition_base.{name}', **kwargs)

    # -- lifecycle -----------------------------------------------------

    @classmethod
    def process(cls, events, origin=None):
        "Mark events as successfully processed."
        to_write = []
        for event in events:
            if event.state == 'processed':
                if origin is not None and event.origin != origin:
                    raise ExternalEventStateError(
                        cls._message(
                            'msg_external_event_already_processed',
                            external_id=event.external_id))
                continue
            values = {
                'state': 'processed',
                'processed_at': dt.datetime.now(),
                'error_message': None,
                'attempts': (event.attempts or 0) + 1,
                }
            if origin is not None:
                values['origin'] = str(origin)
            to_write.extend(([event], values))
        if to_write:
            cls.write(*to_write)

    @classmethod
    def fail(cls, events, message):
        "Record a processing failure. The event stays retryable."
        to_write = []
        for event in events:
            to_write.extend(([event], {
                        'state': 'failed',
                        'error_message': message,
                        'attempts': (event.attempts or 0) + 1,
                        }))
        if to_write:
            cls.write(*to_write)

    @classmethod
    def ignore(cls, events, reason=None):
        "Record that an event was deliberately not acted on."
        cls.write(list(events), {
                'state': 'ignored',
                'error_message': reason,
                'processed_at': dt.datetime.now(),
                })

    @classmethod
    def pending(cls, source=None, event_type=None):
        "Events that still need work: never processed, or failed."
        domain = [('state', 'in', ['received', 'failed'])]
        if source:
            domain.append(('source', '=', source))
        if event_type:
            domain.append(('event_type', '=', event_type))
        return cls.search(domain)

    @classmethod
    def copy(cls, records, default=None):
        # An idempotency record is a fact about something that happened once.
        # Duplicating one would create a second row for the same key.
        default = {} if default is None else default.copy()
        default.setdefault('state', 'received')
        default.setdefault('processed_at')
        default.setdefault('error_message')
        default.setdefault('origin')
        default.setdefault('attempts', 0)
        return super().copy(records, default=default)

    def get_rec_name(self, name):
        return f'{self.source}/{self.event_type}/{self.external_id}'

    @classmethod
    def search_rec_name(cls, name, clause):
        _, operator, value = clause[:3]
        return ['OR',
            ('external_id', operator, value, *clause[3:]),
            ('source', operator, value, *clause[3:]),
            ]
