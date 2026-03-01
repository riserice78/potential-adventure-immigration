"""
migrate_2025_index.py
---------------------
One-time migration: patch the existing transactions_index.json (2025 edition)
to add charter_name and source_pdf fields to every transaction entry, then
save it as transactions_2025_index.json ready for merging.

Run:
    python scripts/migrate_2025_index.py
"""

import json
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
SRC_PATH = ROOT_DIR / "transactions_index.json"
DST_PATH = ROOT_DIR / "transactions_2025_index.json"

CHARTER_NAME = "Bureau of Immigration Citizen's Charter 2025, 1st Edition"
SOURCE_PDF   = "BureauOfImmigration_2025.pdf"


def migrate() -> None:
    if not SRC_PATH.exists():
        print(f"Error: {SRC_PATH} not found.")
        return

    with open(SRC_PATH, "r", encoding="utf-8") as f:
        index = json.load(f)

    transactions = index.get("transactions", [])
    patched = 0

    for txn in transactions:
        # Add fields if missing (idempotent)
        if "charter_name" not in txn:
            txn["charter_name"] = CHARTER_NAME
            patched += 1
        if "source_pdf" not in txn:
            txn["source_pdf"] = SOURCE_PDF

    # Update/normalise metadata
    index["metadata"]["charter_name"] = CHARTER_NAME
    index["metadata"]["source_pdf"]   = SOURCE_PDF
    index["metadata"]["migrated_at"]  = datetime.now().isoformat()

    with open(DST_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"✓ Migrated {patched} transaction(s) → {DST_PATH.name}")
    print(f"  Total transactions : {len(transactions)}")
    print(f"  Charter            : {CHARTER_NAME}")
    print(f"  Source PDF         : {SOURCE_PDF}")


if __name__ == "__main__":
    migrate()
