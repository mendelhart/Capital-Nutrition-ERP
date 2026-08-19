"""Reconciliation report rendering."""

from __future__ import annotations

import datetime as _dt
from typing import Sequence

from .checks import CheckResult, Status

_ICON = {
    Status.PASS: "PASS",
    Status.FAIL: "FAIL",
    Status.SKIPPED: "SKIP",
    Status.ERROR: "ERR ",
}


def render_summary(results: Sequence[CheckResult]) -> str:
    """One line per check, for the terminal."""
    width = max((len(r.title) for r in results), default=10)
    lines = []
    for r in results:
        diff = "" if r.status is Status.SKIPPED else f"  diff {r.difference:>14}"
        lines.append(f"  {_ICON[r.status]}  {r.title.ljust(width)}{diff}")
    return "\n".join(lines)


def render_markdown(results: Sequence[CheckResult], config, *, extra: dict | None = None) -> str:
    blocking = [r for r in results if r.blocks_cutover]
    verdict = (
        "**CUTOVER BLOCKED** — "
        f"{len(blocking)} check(s) failed. Every difference must be explained and corrected "
        "through an approved process before cutover."
        if blocking else
        "**No blocking differences.** All blocking checks tie."
    )
    now = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")

    out: list[str] = [
        "# Migration reconciliation",
        "",
        "| | |",
        "|---|---|",
        f"| Run label | `{config.run.label}` |",
        f"| Cutover date | {config.run.cutover_date.isoformat()} |",
        f"| Balances as of | {config.run.as_of.isoformat()} |",
        f"| Source | `{config.source.adapter}` |",
        f"| Target | `{config.target.adapter}` |",
        f"| Money tolerance | {config.reconcile.tolerance} |",
        f"| Generated | {now} |",
        "",
        verdict,
        "",
        "## Checks",
        "",
        "| Check | Status | Source | Target | Difference | Variances |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for r in results:
        diff = "—" if r.status is Status.SKIPPED else f"`{r.difference}`"
        target = "—" if r.status is Status.SKIPPED else f"{r.target_total}"
        out.append(
            f"| {r.title} | {r.status.value} | {r.source_total} | {target} | {diff} "
            f"| {len(r.variances) or '—'} |"
        )
    out.append("")

    for r in results:
        if r.status is Status.PASS and not r.note:
            continue
        out += [f"### {r.title} — {r.status.value}", ""]
        if r.note:
            out += [r.note, ""]
        if r.variances:
            shown = r.variances[: config.reconcile.detail_rows]
            out += [
                f"Largest {len(shown)} of {len(r.variances)} differences:",
                "",
                "| Key | Source | Target | Difference |",
                "|---|---:|---:|---:|",
            ]
            out += [f"| `{v.key}` | {v.source} | {v.target} | **{v.difference}** |" for v in shown]
            out.append("")
            unmapped = [v for v in r.variances if v.key.startswith("UNMAPPED:")]
            if unmapped:
                out += [
                    f"{len(unmapped)} difference(s) are on unmapped source values. Fix the "
                    "mapping tables first — these are not accounting differences.",
                    "",
                ]

    if extra:
        out += ["## Run detail", ""]
        for key, value in extra.items():
            out.append(f"- **{key}**: {value}")
        out.append("")

    out += [
        "## Sign-off",
        "",
        "| Role | Name | Date | Verdict |",
        "|---|---|---|---|",
        "| Operator | | | |",
        "| Accountant | | | |",
        "",
        "Acceptance (13_MIGRATION.md): the opening trial balance ties exactly. Any discrepancy "
        "must be explained, corrected through an approved process, or block cutover.",
        "",
    ]
    return "\n".join(out)
