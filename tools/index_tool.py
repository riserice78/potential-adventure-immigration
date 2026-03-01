"""
tools/index_tool.py
-------------------
Two CrewAI tools that work with the pre-built transactions_index.json:

  TransactionSearchTool  — keyword search across ALL charters' transaction names;
                           used by MatcherCrew to narrow down candidates.
                           Each result shows its charter edition so the agent
                           can surface the right version to the user.

  TransactionDetailTool  — retrieves the full Citizen's Charter text for
                           one specific transaction; used by CharterCrew
                           to format the requirements response.
                           Uses the per-transaction source_pdf field so the
                           correct charter PDF is referenced.
"""

import json
import re
from pathlib import Path

from crewai.tools import BaseTool

INDEX_PATH = Path(__file__).parent.parent / "transactions_index.json"

# Words that carry no search signal and should be ignored when scoring
_STOPWORDS = {
    "i", "want", "need", "to", "for", "a", "an", "the", "how", "do",
    "get", "my", "me", "about", "please", "help", "apply", "avail",
    "process", "what", "where", "is", "are", "can", "make", "have",
    "with", "from", "that", "this", "will", "been", "they",
}

# Citizen-friendly words → official BI terminology expansions.
# These cover two cases:
#   (a) verb forms that don't substring-match their noun:
#       "extend" is not a substring of "extension" (diverge at char 6)
#   (b) everyday words that map to different official terms:
#       "spouse" → the charter says "marriage" / "married"
_SYNONYMS: dict[str, list[str]] = {
    # verb → BI noun form
    "extend":      ["extension"],
    "convert":     ["conversion"],
    "register":    ["registration"],
    "downgrade":   ["downgrading"],
    "revalidate":  ["revalidation"],
    "reissue":     ["reissuance", "re-issuance"],
    "accredit":    ["accreditation"],
    "certify":     ["certification", "certificate"],
    "stamp":       ["re-stamping", "stamping"],
    # everyday citizen words → BI official terms
    "foreigner":   ["alien", "foreign national"],
    "foreign":     ["alien"],
    "stay":        ["authorized stay", "overstaying"],
    "leave":       ["emigration", "departure"],
    "exit":        ["emigration clearance", "departure"],
    "spouse":      ["marriage", "married"],
    "husband":     ["marriage", "married"],
    "wife":        ["marriage", "married"],
    "child":       ["minor", "dependent"],
    "school":      ["student"],
    "job":         ["employment"],
    "retire":      ["retiree", "srrv"],
    "pension":     ["retiree", "srrv"],
    "business":    ["commercial", "investor"],
    "id":          ["identification", "i-card"],
    "lost":        ["lost", "replacement", "reissuance", "re-issuance"],
    "replacement": ["reissuance", "re-issuance", "lost"],
}

# Category substrings that identify a regional/field/satellite office.
# Transactions whose category does NOT match any of these are considered
# "central office" and receive a priority bonus in search ranking.
_REGIONAL_KEYWORDS = (
    "district office",
    "field office",
    "extension office",
    "satellite office",
    "border crossing",
    "one-stop shop",
    " oss",          # e.g. "BI Clark OSS"
)

# Edition order used for tie-breaking (higher index = more recent = preferred)
_EDITION_PRIORITY = {
    "1st": 1, "2nd": 2, "3rd": 3, "4th": 4,
    "2024": 5, "2025": 6,
}


def _is_regional(category: str) -> bool:
    """Return True if the transaction belongs to a regional/field office."""
    lower = category.lower()
    return any(kw in lower for kw in _REGIONAL_KEYWORDS)


def _edition_rank(charter_name: str) -> int:
    """Higher = more recent edition (used for tie-breaking deduplication)."""
    lower = charter_name.lower()
    for key, rank in _EDITION_PRIORITY.items():
        if key in lower:
            return rank
    return 0


def _normalize_query(query: str) -> str:
    """
    Normalize common notations before tokenizing so variants match each other.

    • 13A  ↔  13(A)   — section numbers with/without parentheses
    • 9(f) ↔  9f      — same pattern for any digit+letter combos
    Produces both forms so either notation in the charter text is found.
    """
    # Collapse "13(A)" → "13a" and "13A" → "13a" so they tokenize identically,
    # then re-expand into both forms inside the keyword group below.
    normalized = re.sub(r"(\d+)\(([a-zA-Z])\)", r"\1\2", query)   # 13(A) → 13A
    return normalized


class TransactionSearchTool(BaseTool):
    """
    Keyword search across all transaction names in the combined index.
    Used by MatcherCrew to pre-filter transactions across all charter editions
    down to a short list of plausible candidates before the LLM makes its
    final pick.
    """

    name: str = "search_transactions"
    description: str = (
        "Searches the combined Citizen's Charter index (all editions) for "
        "transactions matching the citizen's description. "
        "Input: the citizen's plain-language query "
        "(e.g. 'I need to get an ACR I-Card'). Returns up to 20 candidate "
        "transactions with their IDs, names, categories, and charter edition."
    )

    def _run(self, query: str) -> str:  # type: ignore[override]
        if not INDEX_PATH.exists():
            return (
                "Error: transactions_index.json not found. "
                "Run scripts/build_index.py then scripts/merge_indexes.py first."
            )

        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            index = json.load(f)

        transactions: list[dict] = index.get("transactions", [])

        # ── Step 1: Deduplicate by name across editions ──────────────────────
        # When the same transaction appears in multiple charter editions, keep
        # only the entry from the most recent edition so it doesn't unfairly
        # dominate the result list and block older-edition-only transactions.
        best_by_name: dict[str, dict] = {}
        for txn in transactions:
            key = txn["name"].strip().lower()
            existing = best_by_name.get(key)
            if existing is None:
                best_by_name[key] = txn
            else:
                # Prefer the more recent edition
                if _edition_rank(txn.get("charter_name", "")) > _edition_rank(
                    existing.get("charter_name", "")
                ):
                    best_by_name[key] = txn
        unique_txns = list(best_by_name.values())

        # ── Step 2: Keyword extraction + synonym expansion ───────────────────
        # Normalize first so "13(A)" and "13A" produce the same token
        normalized_query = _normalize_query(query)
        raw_keywords = [
            w.lower()
            for w in re.split(r"[\s\-/,]+", normalized_query)
            if len(w) > 1 and w.lower() not in _STOPWORDS
        ]

        if not raw_keywords:
            sample = "\n".join(_format_search_row(t) for t in unique_txns[:50])
            return f"No specific keywords found. Showing first 50 transactions:\n\n{sample}"

        # Build a per-keyword list of terms to search for:
        #   • the keyword itself
        #   • any synonym expansions
        #   • a 5-char stem prefix for keywords ≥ 6 chars (catches extend→extension,
        #     convert→conversion, register→registration, downgrade→downgrading, etc.)
        #   • both "13a" and "13(a)" forms for section-number tokens (digit+letter)
        keyword_groups: list[list[str]] = []
        for kw in raw_keywords:
            group = [kw]
            group.extend(_SYNONYMS.get(kw, []))
            if len(kw) >= 6:
                group.append(kw[:5])   # e.g. "exten" matches "extension"
            # Section-number normalization: "13a" ↔ "13(a)"
            sec_match = re.fullmatch(r"(\d+)([a-z])", kw)
            if sec_match:
                num, letter = sec_match.groups()
                group.append(f"{num}({letter})")   # 13a → 13(a)
            sec_match2 = re.fullmatch(r"(\d+)\(([a-z])\)", kw)
            if sec_match2:
                num, letter = sec_match2.groups()
                group.append(f"{num}{letter}")      # 13(a) → 13a
            keyword_groups.append(group)

        # ── Step 3: Score + central-office priority boost ────────────────────
        # Base score  = number of query keyword GROUPS that match (each group
        #               counts as 1 regardless of how many synonyms hit).
        # +1 bonus    = central/main office transaction (not a regional one).
        scored: list[tuple[float, dict]] = []
        for txn in unique_txns:
            haystack = f"{txn['name']} {txn.get('category', '')}".lower()
            base = sum(
                1 for group in keyword_groups
                if any(term in haystack for term in group)
            )
            if base == 0:
                continue
            bonus = 0 if _is_regional(txn.get("category", "")) else 1
            scored.append((base + bonus, txn))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = [txn for _, txn in scored[:20]]

        if not top:
            # Keyword match found nothing — fall back to unique list
            sample = "\n".join(_format_search_row(t) for t in unique_txns[:50])
            return (
                f"No keyword matches for '{query}'. "
                f"Showing first 50 transactions:\n\n{sample}"
            )

        formatted = "\n".join(_format_search_row(t) for t in top)
        return (
            f"Top {len(top)} candidate transaction(s) "
            f"(central-office results prioritised, deduplicated across editions):"
            f"\n\n{formatted}"
        )


def _format_search_row(t: dict) -> str:
    """One-line summary shown in search results."""
    edition = _short_edition(t.get("charter_name", ""))
    edition_tag = f" [{edition}]" if edition else ""
    return (
        f"ID {t['id']}: {t['name']} "
        f"[{t.get('category', 'N/A')}]"
        f"{edition_tag}"
    )


def _short_edition(charter_name: str) -> str:
    """Convert a full charter name to a short display tag."""
    if not charter_name:
        return ""
    lower = charter_name.lower()
    if "2025" in lower:
        return "2025 Ed."
    if "4th" in lower:
        return "4th Ed."
    if "3rd" in lower:
        return "3rd Ed."
    if "2nd" in lower:
        return "2nd Ed."
    if "1st" in lower:
        return "1st Ed."
    return charter_name  # fallback: full name


class TransactionDetailTool(BaseTool):
    name: str = "get_transaction_detail"
    description: str = (
        "Retrieves the full Citizen's Charter text for a specific transaction, "
        "including requirements, fees, processing time, and procedures. "
        "Input: the transaction name (e.g. 'Application for ACR I-Card') or "
        "its ID number from the transaction list (e.g. '5'). "
        "If multiple transactions match across different charter editions, "
        "a list of candidates is returned so you can call the tool again with "
        "the exact name or ID."
    )

    def _run(self, transaction: str) -> str:  # type: ignore[override]
        if not INDEX_PATH.exists():
            return (
                "Error: transactions_index.json not found. "
                "Run scripts/build_index.py then scripts/merge_indexes.py first."
            )

        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            index = json.load(f)

        transactions: list[dict] = index.get("transactions", [])
        stripped = transaction.strip()
        matched: dict | None = None

        # 1. Numeric ID
        if stripped.isdigit():
            tid = int(stripped)
            matched = next((t for t in transactions if t["id"] == tid), None)

        # 2. Exact name (case-insensitive)
        if not matched:
            lower = stripped.lower()
            matched = next(
                (t for t in transactions if t["name"].lower() == lower), None
            )

        # 3. Partial name (case-insensitive substring)
        if not matched:
            lower = stripped.lower()
            candidates = [t for t in transactions if lower in t["name"].lower()]
            if len(candidates) == 1:
                matched = candidates[0]
            elif len(candidates) > 1:
                names = "\n".join(
                    f"  {c['id']}. {c['name']}  [{_short_edition(c.get('charter_name', ''))}]"
                    for c in candidates
                )
                return (
                    f"Multiple transactions match '{transaction}':\n{names}\n\n"
                    "Please call this tool again with the exact transaction name "
                    "or its ID number."
                )

        # 4. No match — return a partial list so the agent can guide the user
        if not matched:
            sample = "\n".join(
                f"  {t['id']}. {t['name']}  [{_short_edition(t.get('charter_name', ''))}]"
                for t in transactions[:30]
            )
            return (
                f"No transaction found matching '{transaction}'.\n\n"
                f"Here are the first 30 available transactions:\n{sample}\n\n"
                "Call this tool again with the exact name or ID number."
            )

        edition = _short_edition(matched.get("charter_name", ""))
        return (
            f"TRANSACTION: {matched['name']}\n"
            f"CATEGORY: {matched.get('category', 'N/A')}\n"
            f"CHARTER EDITION: {matched.get('charter_name', 'N/A')}\n\n"
            f"CHARTER TEXT:\n{matched['text']}"
        )
