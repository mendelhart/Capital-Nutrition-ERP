# This file is part of the Capital Nutrition ERP.
"""Order origin and external line identity for the sales domain.

Implements the parts of ``docs/specs/08_SALES.md`` that standard ``sale`` does
not cover:

* "Every order must identify its origin", recorded in an explicit ``channel``
  field rather than inferred from side effects.
* "external line IDs" retained per line, so a replayed or amended external
  order event can be reconciled line by line rather than by position or
  description matching (``docs/specs/09_MAGENTO.md``, Inbound / Orders).

Order-level external identity is deliberately NOT a column here. ADR-0002
rejects per-integration de-duplication columns: the link between a Magento
order and its ERP sale is the ``origin`` reference on
``capital_nutrition.external.event``. See ``external_event.py``.
"""

from trytond.i18n import gettext
from trytond.model import Index, fields
from trytond.pool import PoolMeta
from trytond.pyson import Bool, Eval

from .exceptions import SaleChannelError

#: Order origins. Extend deliberately when a channel is approved; never infer
#: an origin from a side effect.
CHANNELS = [
    ('erp', "ERP / Phone / Manual"),
    ('magento', "Magento"),
    ]

#: Channels whose orders originate in an external system.
EXTERNAL_CHANNELS = {'magento'}


class Sale(metaclass=PoolMeta):
    __name__ = 'sale.sale'

    channel = fields.Selection(
        CHANNELS, "Channel", required=True, sort=False,
        states={'readonly': Eval('state') != 'draft'},
        help="Where this order came from. Set at creation and never inferred "
        "from downstream side effects.")

    @classmethod
    def default_channel(cls):
        # An order created through the ERP is an ERP order unless an
        # integration says otherwise.
        return 'erp'

    @property
    def is_external(self):
        return self.channel in EXTERNAL_CHANNELS

    @classmethod
    def validate(cls, sales):
        super().validate(sales)
        for sale in sales:
            sale.check_external_lines()

    def check_external_lines(self):
        "An internal order has no external line identities to carry."
        if self.is_external:
            return
        for line in self.lines or ():
            if getattr(line, 'external_line_id', None):
                raise SaleChannelError(
                    gettext(
                        'capital_nutrition_sale'
                        '.msg_sale_external_line_on_internal_channel',
                        sale=self.rec_name,
                        channel=self.channel))


class SaleLine(metaclass=PoolMeta):
    __name__ = 'sale.line'

    external_line_id = fields.Char(
        "External Line ID",
        states={
            'readonly': Eval('sale_state') != 'draft',
            'invisible': ~Bool(Eval('external_line_id')),
            },
        help="Identifier of this line in the originating external system. "
        "Retained so external order events reconcile line by line.")

    @classmethod
    def __setup__(cls):
        super().__setup__()
        t = cls.__table__()
        cls._sql_indexes.add(
            Index(t, (t.external_line_id, Index.Equality())))
