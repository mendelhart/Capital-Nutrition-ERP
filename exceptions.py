# This file is part of the Capital Nutrition ERP.
"""Exceptions raised by the Capital Nutrition base module."""

from trytond.exceptions import UserError


class ExternalEventPayloadMismatch(UserError):
    """The same external event key was replayed with a different payload.

    This is never corrected silently: an integration that changes the content
    behind an identifier it already delivered is a data-integrity problem the
    operator has to see.
    """


class ExternalEventStateError(UserError):
    "An external event was transitioned into an invalid state."
