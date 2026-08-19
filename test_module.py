# This file is part of the Capital Nutrition ERP.
"""Tests for capital_nutrition_base.

Per MASTER_BUILD: tests must cover failure paths, not only happy paths.
"""

import datetime as dt
from unittest.mock import patch

from trytond.model.exceptions import SQLConstraintError
from trytond.modules.capital_nutrition_base.exceptions import (
    ExternalEventPayloadMismatch,
)
from trytond.pool import Pool
from trytond.tests.test_tryton import ModuleTestCase, with_transaction
from trytond.transaction import Transaction


class CapitalNutritionBaseTestCase(ModuleTestCase):
    "Test Capital Nutrition Base module"
    module = 'capital_nutrition_base'

    @staticmethod
    def _model():
        return Pool().get('capital_nutrition.external.event')

    # -- happy paths ---------------------------------------------------

    @with_transaction()
    def test_register_creates_event(self):
        "A new key is recorded once and reported as new"
        Event = self._model()

        event, is_new = Event.register(
            'magento', 'sales_order', '100000123', {'grand_total': '42.00'})

        self.assertTrue(is_new)
        self.assertEqual(event.source, 'magento')
        self.assertEqual(event.event_type, 'sales_order')
        self.assertEqual(event.external_id, '100000123')
        self.assertEqual(event.state, 'received')
        self.assertEqual(event.attempts, 0)
        self.assertIsNotNone(event.received_at)
        self.assertIsNotNone(event.payload_digest)

    @with_transaction()
    def test_register_is_idempotent(self):
        "Replaying the same key returns the same row and is_new=False"
        Event = self._model()
        payload = {'grand_total': '42.00'}

        first, first_new = Event.register(
            'magento', 'sales_order', '100000123', payload)
        second, second_new = Event.register(
            'magento', 'sales_order', '100000123', payload)

        self.assertTrue(first_new)
        self.assertFalse(second_new)
        self.assertEqual(first.id, second.id)
        self.assertEqual(Event.search_count([]), 1)

    @with_transaction()
    def test_register_strips_whitespace(self):
        "Keys are normalised so ' 123 ' and '123' are the same event"
        Event = self._model()

        first, _ = Event.register('magento', 'sales_order', '100000123')
        second, is_new = Event.register(
            ' magento ', ' sales_order ', ' 100000123 ')

        self.assertFalse(is_new)
        self.assertEqual(first.id, second.id)

    @with_transaction()
    def test_digest_is_key_order_independent(self):
        "The digest depends on content, not on dict ordering"
        Event = self._model()

        self.assertEqual(
            Event.digest({'a': 1, 'b': 2}),
            Event.digest({'b': 2, 'a': 1}))
        self.assertNotEqual(
            Event.digest({'a': 1}), Event.digest({'a': 2}))
        self.assertIsNone(Event.digest(None))

    @with_transaction()
    def test_different_sources_are_distinct(self):
        "The same external id from two sources is two events"
        Event = self._model()

        Event.register('magento', 'sales_order', '1')
        _, is_new = Event.register('odoo', 'sales_order', '1')

        self.assertTrue(is_new)
        self.assertEqual(Event.search_count([]), 2)

    @with_transaction()
    def test_process_marks_processed(self):
        "Processing records the outcome"
        Event = self._model()

        event, _ = Event.register('magento', 'sales_order', '1')
        Event.process([event])

        self.assertEqual(event.state, 'processed')
        self.assertIsNotNone(event.processed_at)
        self.assertEqual(event.attempts, 1)

    @with_transaction()
    def test_process_records_origin(self):
        "Processing links the event to the ERP record it produced"
        pool = Pool()
        Event = self._model()
        User = pool.get('res.user')
        origin = User(Transaction().user)

        with patch.object(
                Event, '_get_origin', classmethod(lambda cls: ['res.user'])):
            event, _ = Event.register('magento', 'sales_order', '1')
            Event.process([event], origin=origin)

            self.assertEqual(event.state, 'processed')
            self.assertEqual(event.origin, origin)

    @with_transaction()
    def test_process_is_idempotent(self):
        "Processing twice does not double-count attempts"
        Event = self._model()

        event, _ = Event.register('magento', 'sales_order', '1')
        Event.process([event])
        first_processed_at = event.processed_at
        Event.process([event])

        self.assertEqual(event.attempts, 1)
        self.assertEqual(event.processed_at, first_processed_at)

    @with_transaction()
    def test_pending_excludes_processed(self):
        "pending() returns work still to do, including failures"
        Event = self._model()

        done, _ = Event.register('magento', 'sales_order', '1')
        failed, _ = Event.register('magento', 'sales_order', '2')
        fresh, _ = Event.register('magento', 'sales_order', '3')
        Event.process([done])
        Event.fail([failed], "boom")

        pending = Event.pending(source='magento')

        self.assertEqual(
            {e.id for e in pending}, {failed.id, fresh.id})

    @with_transaction()
    def test_get_rec_name(self):
        "rec_name identifies the event across systems"
        Event = self._model()

        event, _ = Event.register('magento', 'sales_order', '100000123')

        self.assertEqual(
            event.rec_name, 'magento/sales_order/100000123')
        self.assertEqual(
            Event.search_count([('rec_name', '=', '100000123')]), 1)

    # -- failure paths -------------------------------------------------

    @with_transaction()
    def test_replay_with_different_payload_is_reported(self):
        "A changed payload behind a known key raises, it is not absorbed"
        Event = self._model()

        Event.register('magento', 'sales_order', '1', {'grand_total': '42.00'})

        with self.assertRaises(ExternalEventPayloadMismatch):
            Event.register(
                'magento', 'sales_order', '1', {'grand_total': '43.00'})

    @with_transaction()
    def test_replay_with_different_payload_does_not_mutate(self):
        "The stored digest is left untouched when a mismatch is detected"
        Event = self._model()

        event, _ = Event.register(
            'magento', 'sales_order', '1', {'grand_total': '42.00'})
        original_digest = event.payload_digest

        with self.assertRaises(ExternalEventPayloadMismatch):
            Event.register(
                'magento', 'sales_order', '1', {'grand_total': '43.00'})

        self.assertEqual(event.payload_digest, original_digest)
        self.assertEqual(Event.search_count([]), 1)

    @with_transaction()
    def test_duplicate_key_violates_database_constraint(self):
        "The invariant is enforced by the database, not only by register()"
        Event = self._model()

        Event.register('magento', 'sales_order', '1')

        with self.assertRaises(SQLConstraintError):
            Event.create([{
                        'source': 'magento',
                        'event_type': 'sales_order',
                        'external_id': '1',
                        'state': 'received',
                        'attempts': 0,
                        'received_at': dt.datetime.now(),
                        }])

    @with_transaction()
    def test_fail_keeps_event_retryable(self):
        "A failure is recorded and counted, and the event stays pending"
        Event = self._model()

        event, _ = Event.register('magento', 'sales_order', '1')
        Event.fail([event], "connection reset")
        Event.fail([event], "connection reset")

        self.assertEqual(event.state, 'failed')
        self.assertEqual(event.attempts, 2)
        self.assertEqual(event.error_message, "connection reset")
        self.assertIn(event, Event.pending())

    @with_transaction()
    def test_process_after_failure_clears_error(self):
        "A retry that succeeds leaves no stale error behind"
        Event = self._model()

        event, _ = Event.register('magento', 'sales_order', '1')
        Event.fail([event], "connection reset")
        Event.process([event])

        self.assertEqual(event.state, 'processed')
        self.assertIsNone(event.error_message)
        self.assertEqual(event.attempts, 2)

    @with_transaction()
    def test_register_rejects_empty_key_parts(self):
        "An event without a full key is a programming error, not a record"
        Event = self._model()

        for args in [
                ('', 'sales_order', '1'),
                ('magento', '', '1'),
                ('magento', 'sales_order', ''),
                ('magento', 'sales_order', None),
                ]:
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    Event.register(*args)

    @with_transaction()
    def test_copy_resets_processing_state(self):
        "A copied event never carries another event's outcome"
        Event = self._model()

        event, _ = Event.register('magento', 'sales_order', '1')
        Event.fail([event], "boom")

        copy, = Event.copy([event], default={'external_id': '2'})

        self.assertEqual(copy.state, 'received')
        self.assertEqual(copy.attempts, 0)
        self.assertIsNone(copy.error_message)
        self.assertIsNone(copy.processed_at)


del ModuleTestCase
