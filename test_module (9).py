# This file is part of the Capital Nutrition ERP.
"""Tests for the Capital Nutrition sales module."""

from trytond.model.exceptions import ValidationError
from trytond.pool import Pool
from trytond.tests.test_tryton import (
    ModuleTestCase, activate_module, with_transaction)


class CapitalNutritionSaleTestCase(ModuleTestCase):
    "Test Capital Nutrition Sale module"
    module = 'capital_nutrition_sale'
    extras = ['sale', 'capital_nutrition_base']

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        activate_module(['capital_nutrition_sale'])

    @with_transaction()
    def test_default_channel_is_erp(self):
        "A sale created without a stated channel is an ERP order."
        pool = Pool()
        Sale = pool.get('sale.sale')
        self.assertEqual(Sale.default_channel(), 'erp')

    @with_transaction()
    def test_channel_selection_values(self):
        "Both approved channels are offered, ERP first."
        pool = Pool()
        Sale = pool.get('sale.sale')
        values = [v for v, _ in Sale.channel.selection]
        self.assertEqual(values, ['erp', 'magento'])

    @with_transaction()
    def test_sale_is_a_valid_event_origin(self):
        "ADR-0002: the ledger can point at a sale."
        pool = Pool()
        Event = pool.get('capital_nutrition.external.event')
        self.assertIn('sale.sale', Event._get_origin())

    @with_transaction()
    def test_external_line_id_field_exists(self):
        "External line identity is retained per line."
        pool = Pool()
        Line = pool.get('sale.line')
        self.assertIn('external_line_id', Line._fields)

    @with_transaction()
    def test_sale_has_no_external_order_id_column(self):
        """ADR-0002 rejects per-integration de-duplication columns.

        Order-level external identity belongs to the event ledger's origin
        reference, not to a column on the sale. If this test starts failing,
        the decision recorded in 08_SALES.md has been changed without the ADR
        being revisited.
        """
        pool = Pool()
        Sale = pool.get('sale.sale')
        self.assertNotIn('external_order_id', Sale._fields)


del ModuleTestCase
