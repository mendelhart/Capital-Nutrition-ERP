"""Live Odoo XML-RPC extraction — NOT IMPLEMENTED.

Deliberately left as a stub. The source decision is still open, and a live
adapter has a property the spec cares about: the data can move underneath a
rehearsal. If this adapter is ever enabled it must first materialise a frozen
snapshot (write every dataset to disk, record a snapshot id, then read only
from that), so downstream stages keep the "controlled source snapshot"
guarantee.

To implement:
    1. authenticate via /xmlrpc/2/common -> uid
    2. execute_kw(db, uid, pwd, model, 'search_read', [domain], {'fields': [...]})
       once per dataset, paginating with offset/limit
    3. map Odoo field names to the aliases declared in base.DATASETS
    4. write raw pages to config.extract_dir before yielding, then re-read
"""

from __future__ import annotations

from typing import Any, Iterator

from .base import SourceAdapter, SourceUnavailable

_MESSAGE = (
    "The odoo_rpc source adapter is not implemented yet.\n"
    "Set [source] adapter = \"odoo_sql\" and point dsn at a restored snapshot, "
    "or implement capnut_migration/sources/odoo_rpc.py."
)


class OdooRpcSource(SourceAdapter):
    name = "odoo_rpc"

    def snapshot_info(self) -> dict[str, Any]:
        raise SourceUnavailable(_MESSAGE)

    def fetch(self, dataset_name: str) -> Iterator[dict[str, Any]]:
        raise SourceUnavailable(_MESSAGE)
