"""
build_index.py — One-time script to index a Citizen's Charter PDF.

Run this once per charter edition before merging:
    python scripts/build_index.py \\
        --pdf citizenscharters/BureauOfImmigration_2025.pdf \\
        --charter-name "Bureau of Immigration Citizen's Charter 2025, 1st Edition" \\
        --output transactions_2025_index.json

    python scripts/build_index.py \\
        --pdf citizenscharters/BureauOfImmigration_4thEdition.pdf \\
        --charter-name "Bureau of Immigration Citizen's Charter, 4th Edition" \\
        --output transactions_4th_index.json \\
        --id-offset 1000

Then merge all per-charter indexes into the combined runtime index:
    python scripts/merge_indexes.py

How it works:
  Phase 1 — pdfplumber extracts raw text from every page (no API calls).
  Phase 2 — Claude Haiku scans chunks of ~80 pages and returns the name,
             category, and start page of every transaction it finds.
  Phase 3 — pdfplumber slices the text between consecutive start pages to
             build each transaction's full content block.
  Save    — Results are written to the specified --output file.
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import anthropic
import pdfplumber
from dotenv import load_dotenv

load_dotenv()

# ── Configuration ────────────────────────────────────────────────────────────
CHUNK_SIZE = 80          # pages fed to Claude per discovery call
OVERLAP = 5              # overlap between chunks to avoid missing boundaries
MAX_PAGES_PER_TXN = 20  # safety cap: never store more than this many pages per transaction

ROOT_DIR = Path(__file__).parent.parent
CHECKPOINTS_DIR = ROOT_DIR / ".index_checkpoints"

SEPARATOR = "─" * 60


# ── Charter-name auto-detection ───────────────────────────────────────────────

_NAME_MAP = {
    r"2025":       "Bureau of Immigration Citizen's Charter 2025, 1st Edition",
    r"4th":        "Bureau of Immigration Citizen's Charter, 4th Edition",
    r"3rd":        "Bureau of Immigration Citizen's Charter, 3rd Edition",
    r"2nd":        "Bureau of Immigration Citizen's Charter, 2nd Edition",
    r"1st":        "Bureau of Immigration Citizen's Charter, 1st Edition",
}


def _auto_charter_name(filename: str) -> str:
    lower = filename.lower()
    for pattern, label in _NAME_MAP.items():
        if re.search(pattern, lower):
            return label
    # Generic fallback: strip extension and underscores
    stem = Path(filename).stem.replace("_", " ")
    return f"Bureau of Immigration Citizen's Charter — {stem}"


# ── Phase 1: Text extraction ─────────────────────────────────────────────────

def extract_page_texts(pdf_path: str) -> list[str]:
    """Return a list of raw text strings, one per page."""
    texts: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        total = len(pdf.pages)
        print(f"   Total pages: {total}")
        for i, page in enumerate(pdf.pages):
            texts.append(page.extract_text() or "")
            if (i + 1) % 100 == 0:
                print(f"   Extracted {i + 1}/{total} pages...")
    return texts


# ── Phase 2: Transaction discovery ───────────────────────────────────────────

def _parse_json_response(raw: str) -> list:
    """Robustly parse a JSON array from Claude's response."""
    text = raw.strip()
    # Strip markdown code fences if present
    if "```" in text:
        parts = text.split("```")
        # content is between the first pair of fences
        text = parts[1] if len(parts) >= 2 else parts[0]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def _checkpoint_path(output_path: Path) -> Path:
    CHECKPOINTS_DIR.mkdir(exist_ok=True)
    return CHECKPOINTS_DIR / (output_path.stem + "_phase2.json")


def _load_checkpoint(ckpt_path: Path) -> tuple[dict, int]:
    """Return (found_dict, last_completed_chunk_idx) or ({}, -1) if no checkpoint."""
    if not ckpt_path.exists():
        return {}, -1
    try:
        with open(ckpt_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"   ♻  Resuming from checkpoint: {ckpt_path.name}")
        print(f"      {len(data['found'])} transaction(s) already discovered.")
        print(f"      Last completed chunk: {data['last_chunk'] + 1}")
        return data["found"], data["last_chunk"]
    except Exception as exc:
        print(f"   ⚠  Checkpoint corrupt, starting fresh: {exc}")
        return {}, -1


def _save_checkpoint(ckpt_path: Path, found: dict, last_chunk: int) -> None:
    with open(ckpt_path, "w", encoding="utf-8") as f:
        json.dump({"found": found, "last_chunk": last_chunk}, f, ensure_ascii=False)


def discover_transactions(
    client: anthropic.Anthropic, page_texts: list[str], ckpt_path: Path
) -> list[dict]:
    """
    Phase 2: Ask Claude Haiku to find transaction names and start pages.

    Checkpoints progress after every chunk so the build can be resumed
    if it is interrupted (e.g. API credit exhaustion).

    Returns a deduplicated list of dicts:
        {"name": str, "category": str, "start_page": int}
    """
    total_pages = len(page_texts)

    # Load any existing checkpoint
    found, last_completed = _load_checkpoint(ckpt_path)

    starts = list(range(0, total_pages, CHUNK_SIZE - OVERLAP))
    total_chunks = len(starts)

    for chunk_idx, start in enumerate(starts):
        # Skip already-processed chunks
        if chunk_idx <= last_completed:
            print(
                f"   Skipping pages {start + 1}–{min(start + CHUNK_SIZE, total_pages)} "
                f"(chunk {chunk_idx + 1}/{total_chunks}) — already in checkpoint."
            )
            continue

        end = min(start + CHUNK_SIZE, total_pages)

        chunk_text = ""
        for p in range(start, end):
            chunk_text += f"\n=== PAGE {p + 1} ===\n{page_texts[p]}"

        print(
            f"   Scanning pages {start + 1}–{end} "
            f"(chunk {chunk_idx + 1}/{total_chunks})..."
        )

        prompt = (
            f"You are reading pages {start + 1} to {end} of a Philippine "
            "government Citizen's Charter document.\n\n"
            "Identify every transaction or service that STARTS in this page range. "
            "For each one, return the exact transaction name, its office/division "
            "(if shown), and the page number where it starts.\n\n"
            "Return ONLY a JSON array — no explanation, no markdown fences:\n"
            "[\n"
            '  {"name": "Full Transaction Name", "category": "Office or Division", "start_page": 45},\n'
            "  ...\n"
            "]\n\n"
            "If no transactions start in this range, return [].\n\n"
            f"Text:\n{chunk_text}"
        )

        try:
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )
            transactions_in_chunk = _parse_json_response(
                response.content[0].text
            )
            new_count = 0
            for txn in transactions_in_chunk:
                name = txn.get("name", "").strip()
                if name and name not in found:
                    found[name] = {
                        "category": txn.get("category", "").strip(),
                        "start_page": int(txn.get("start_page", start + 1)),
                    }
                    new_count += 1
            print(f"     → {new_count} new transaction(s) found.")
            # Persist progress after every successful chunk
            _save_checkpoint(ckpt_path, found, chunk_idx)
        except (json.JSONDecodeError, ValueError, KeyError) as exc:
            print(f"   ⚠  Warning: could not parse chunk {chunk_idx + 1}: {exc}")
            _save_checkpoint(ckpt_path, found, chunk_idx)

        time.sleep(0.2)  # be polite to the API

    return [
        {"name": name, "category": info["category"], "start_page": info["start_page"]}
        for name, info in found.items()
    ]


# ── Phase 3: Text extraction per transaction ──────────────────────────────────

def extract_transaction_texts(
    page_texts: list[str],
    transactions: list[dict],
    charter_name: str,
    source_pdf: str,
    id_offset: int = 0,
) -> list[dict]:
    """
    Phase 3: Slice raw text from start_page to the next transaction's start_page.

    Returns the final list of indexed transactions with full text content.
    Each entry includes charter_name and source_pdf for multi-charter support.
    """
    sorted_txns = sorted(transactions, key=lambda x: x["start_page"])
    total_pages = len(page_texts)
    indexed = []

    for i, txn in enumerate(sorted_txns):
        start = txn["start_page"] - 1  # 0-indexed

        # End at the next transaction's start page, or end of document
        if i + 1 < len(sorted_txns):
            end = sorted_txns[i + 1]["start_page"] - 1
        else:
            end = total_pages

        # Safety cap
        end = min(end, start + MAX_PAGES_PER_TXN)

        text_parts = []
        for p in range(start, end):
            page_text = page_texts[p].strip()
            if page_text:
                text_parts.append(f"--- Page {p + 1} ---\n{page_text}")

        indexed.append(
            {
                "id": id_offset + i + 1,
                "name": txn["name"],
                "category": txn["category"],
                "start_page": txn["start_page"],
                "charter_name": charter_name,
                "source_pdf": source_pdf,
                "text": "\n\n".join(text_parts),
            }
        )

    return indexed


# ── Main ──────────────────────────────────────────────────────────────────────

def build_index(pdf_path: str, charter_name: str, output_path: Path, id_offset: int) -> None:  # noqa: C901
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY is not set.")
        sys.exit(1)

    if not os.path.isfile(pdf_path):
        print(f"Error: PDF not found: {pdf_path}")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    pdf_name = os.path.basename(pdf_path)

    print(f"\n{SEPARATOR}")
    print(f"  Charter : {charter_name}")
    print(f"  PDF     : {pdf_name}")
    print(f"  Output  : {output_path.name}")
    print(f"  ID offset: {id_offset}")
    print(SEPARATOR)

    # Phase 1 ─ Extract text
    print("\n[1/3] Extracting text from PDF...")
    page_texts = extract_page_texts(pdf_path)

    # Phase 2 ─ Discover transactions
    print("\n[2/3] Discovering transactions (Claude Haiku)...")
    ckpt_path = _checkpoint_path(output_path)
    transactions = discover_transactions(client, page_texts, ckpt_path)
    print(f"\n   Found {len(transactions)} unique transaction(s).")

    # Phase 3 ─ Extract text per transaction
    print("\n[3/3] Extracting transaction content...")
    indexed = extract_transaction_texts(
        page_texts, transactions, charter_name, pdf_name, id_offset
    )

    # Save per-charter index
    index = {
        "metadata": {
            "charter_name": charter_name,
            "source_pdf": pdf_name,
            "built_at": datetime.now().isoformat(),
            "total_transactions": len(indexed),
            "total_pages": len(page_texts),
        },
        "transactions": indexed,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    # Remove checkpoint — build completed successfully
    if ckpt_path.exists():
        ckpt_path.unlink()

    print(f"\n{SEPARATOR}")
    print(f"  ✓ Index saved to: {output_path}")
    print(f"    {len(indexed)} transactions | {len(page_texts)} pages")
    print(f"    ID range: {id_offset + 1} – {id_offset + len(indexed)}")
    print(SEPARATOR)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build a per-charter transaction index from a Citizen's Charter PDF.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  # 2025 edition (primary)\n"
            "  python scripts/build_index.py \\\n"
            "      --pdf citizenscharters/BureauOfImmigration_2025.pdf \\\n"
            "      --charter-name \"Bureau of Immigration Citizen's Charter 2025, 1st Edition\" \\\n"
            "      --output transactions_2025_index.json\n\n"
            "  # 4th edition (legacy, IDs start at 1001)\n"
            "  python scripts/build_index.py \\\n"
            "      --pdf citizenscharters/BureauOfImmigration_4thEdition.pdf \\\n"
            "      --output transactions_4th_index.json \\\n"
            "      --id-offset 1000\n\n"
            "  # Merge all per-charter indexes\n"
            "  python scripts/merge_indexes.py\n"
        ),
    )
    parser.add_argument(
        "--pdf",
        required=True,
        metavar="PATH",
        help="Path to the Citizen's Charter PDF file",
    )
    parser.add_argument(
        "--charter-name",
        metavar="NAME",
        default=None,
        help=(
            "Human-readable charter edition name "
            "(auto-detected from filename if not provided)"
        ),
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        default=None,
        help=(
            "Output JSON filename in the project root "
            "(default: transactions_<stem>_index.json)"
        ),
    )
    parser.add_argument(
        "--id-offset",
        type=int,
        default=0,
        metavar="N",
        help=(
            "Add N to all transaction IDs so multiple charters don't share IDs. "
            "E.g. --id-offset 1000 for the 4th edition. (default: 0)"
        ),
    )
    args = parser.parse_args()

    pdf_name = os.path.basename(args.pdf)
    charter_name = args.charter_name or _auto_charter_name(pdf_name)

    if args.output:
        output_path = ROOT_DIR / args.output
    else:
        stem = Path(pdf_name).stem.lower().replace(" ", "_")
        output_path = ROOT_DIR / f"transactions_{stem}_index.json"

    build_index(args.pdf, charter_name, output_path, args.id_offset)
