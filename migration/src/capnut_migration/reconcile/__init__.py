"""Automatic reconciliation.

Spec: "Reconcile automatically" and "Opening trial balance ties exactly. Any
discrepancy must be explained, corrected through an approved process, or block
cutover."

So reconciliation here is a gate with an exit code, not a report someone reads.
"""

from .checks import CheckResult, Status, compare, run_all, sum_by
from .report import render_markdown, render_summary

__all__ = [
    "CheckResult",
    "Status",
    "compare",
    "run_all",
    "sum_by",
    "render_markdown",
    "render_summary",
]
