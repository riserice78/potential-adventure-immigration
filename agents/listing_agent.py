"""
Listing Agent — returns all available transactions from the pre-built index.

No API call is made here; the index already contains everything needed.
"""


def list_transactions(index: dict) -> str:
    """
    Format the transaction list from the index for display to the user.

    Args:
        index: The loaded transactions_index.json as a dict.

    Returns:
        A formatted string grouping transactions by category.
    """
    transactions = index.get("transactions", [])
    if not transactions:
        return "No transactions found in the index."

    lines: list[str] = []
    current_category: str | None = None

    for txn in transactions:
        category = txn.get("category") or "General"
        if category != current_category:
            current_category = category
            lines.append(f"\n{category}")
            lines.append("─" * len(category))
        lines.append(f"  {txn['id']}. {txn['name']}")

    return "\n".join(lines)
