# This file is part of the Capital Nutrition ERP.
"""Let the external-event ledger point at a sale.

ADR-0002: domain modules extend ``_get_origin()`` to declare which of their
models an inbound event may have produced. They do not extend the keying
scheme, and they do not grow their own de-duplication columns.
"""

from trytond.pool import PoolMeta


class ExternalEvent(metaclass=PoolMeta):
    __name__ = 'capital_nutrition.external.event'

    @classmethod
    def _get_origin(cls):
        return super()._get_origin() + ['sale.sale']
