# This file is part of the Capital Nutrition ERP.
"""Exceptions raised by the Capital Nutrition sales module."""

from trytond.model.exceptions import ValidationError


class SaleChannelError(ValidationError):
    "A sale's channel is inconsistent with its external references."
