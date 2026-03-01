"""
merge_indexes.py
----------------
Combines all per-charter index files into a single transactions_index.json
that the runtime app loads.

Auto-discovers any file matching transactions_*_index.json in the project root,
or you can specify them explicitly with --indexes.

Run:
    python scripts/merge_indexes.py

    # or specify files explicitly:
    python scripts/merge_indexes.py \\
        --indexes transactions_2025_index.json transactions_4th_index.json

Output: transactions_index.json  (overwrites any existing file)
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
OUTPUT_PATH = ROOT_DIR / "transactions_index.json"


def merge(index_paths: list[Path]) -> None:
    all_transactions: list[dict] = []
    charters_meta: list[dict] = []
    seen_ids: set[int] = set()

    for path in index_paths:
        if not path.exists():
            print(f"  ⚠  Skipping (not found): {path.name}")
            continue

        with open(path, "r", encoding="utf-8") as f:
            index = json.load(f)

        meta = index.get("metadata", {})
        transactions = index.get("transactions", [])

        # Detect ID collisions early
        for txn in transactions:
            tid = txn.get("id")
            if tid in seen_ids:
                print(
                    f"  ⚠  ID collision: transaction id={tid} already exists. "
                    f"Re-run build_index.py for '{path.name}' with a different --id-offset."
                )
            else:
                seen_ids.add(tid)

        all_transactions.extend(transactions)
        charters_meta.append(
            {
                "charter_name":       meta.get("charter_name", path.stem),
                "source_pdf":         meta.get("source_pdf", ""),
                "built_at":           meta.get("built_at", ""),
                "total_transactions": len(transactions),
                "total_pages":        meta.get("total_pages", 0),
                "id_range": (
                    f"{transactions[0]['id']}–{transactions[-1]['id']}"
                    if transactions else "N/A"
                ),
            }
        )
        print(f"  ✓ {path.name}: {len(transactions)} transactions loaded")

    # Sort combined list by id
    all_transactions.sort(key=lambda t: t.get("id", 0))

    combined = {
        "metadata": {
            "merged_at": datetime.now().isoformat(),
            "total_transactions": len(all_transactions),
            "charters": charters_meta,
        },
        "transactions": all_transactions,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)

    print(f"\n✓ Combined index saved → {OUTPUT_PATH.name}")
    print(f"  Total transactions : {len(all_transactions)}")
    print(f"  Charters merged    : {len(charters_meta)}")
    for c in charters_meta:
        print(f"    • {c['charter_name']}  (IDs {c['id_range']})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Merge per-charter index files into combined transactions_index.json.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python scripts/merge_indexes.py\n"
            "  python scripts/merge_indexes.py \\\n"
            "      --indexes transactions_2025_index.json transactions_4th_index.json\n"
        ),
    )
    parser.add_argument(
        "--indexes",
        nargs="+",
        metavar="FILE",
        default=None,
        help=(
            "Per-charter index files to merge (relative to project root). "
            "If omitted, auto-discovers transactions_*_index.json files."
        ),
    )
    args = parser.parse_args()

    if args.indexes:
        paths = [ROOT_DIR / f for f in args.indexes]
    else:
        # Auto-discover: any transactions_*_index.json, sorted alphabetically
        # Exclude the combined output file itself
        paths = sorted(
            p for p in ROOT_DIR.glob("transactions_*_index.json")
            if p.name != OUTPUT_PATH.name
        )

    if not paths:
        print("No per-charter index files found. Run build_index.py first.")
        raise SystemExit(1)

    print(f"Merging {len(paths)} index file(s):")
    merge(paths)
