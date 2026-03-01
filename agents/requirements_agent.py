"""
Requirements Agent — retrieves requirements for a specific transaction
using the pre-built index, then asks Claude to format a clean response.

Matching priority:
  1. Numeric input  → direct lookup by transaction ID
  2. Exact name     → case-insensitive exact match
  3. Partial name   → case-insensitive substring match (unique result only)
  4. Claude-assisted → Claude Haiku picks the best match from the name list
"""

import anthropic


SYSTEM_PROMPT = """You are a government services assistant that specializes in reading
Citizen's Charter documents. Your job is to provide citizens with detailed, accurate
information about a specific transaction they want to avail.

When presenting transaction details, structure your response clearly with these sections:

**Transaction:** [Full transaction name]

**Requirements:**
List every documentary requirement needed, exactly as stated in the document.
For each requirement, indicate:
- The document name
- Number of copies required (if specified)
- Whether it must be an original or photocopy (if specified)
- Any other conditions (e.g., certified true copy, notarized)

**Where to Secure the Requirements:**
For each requirement, state where the citizen can obtain it (e.g., issuing office/agency).
If the charter specifies this, use the exact information from the document.
If not explicitly stated, use your general knowledge of Philippine government agencies.

**Processing Time:** [If stated in the document]

**Fees:** [If stated in the document, otherwise state "None" or "Free"]

**Where to File/Apply:** [Office/counter to submit to, if stated]

**Steps/Procedure:** [Brief numbered steps if provided in the document]

Be thorough but concise. Use plain language that any citizen can understand."""


def _find_best_match(
    client: anthropic.Anthropic,
    transactions: list[dict],
    user_input: str,
) -> dict | None:
    """
    Ask Claude Haiku to identify the transaction the user most likely means.
    Returns the matched transaction dict, or None if no good match is found.
    """
    names_list = "\n".join(
        f"{t['id']}. {t['name']}" for t in transactions
    )
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=16,
        messages=[
            {
                "role": "user",
                "content": (
                    f'A citizen is looking for: "{user_input}"\n\n'
                    "From the list below, which transaction ID best matches "
                    "what they are looking for?\n\n"
                    f"{names_list}\n\n"
                    "Reply with ONLY the transaction ID number (e.g. 5). "
                    "If nothing matches, reply with 0."
                ),
            }
        ],
    )
    try:
        tid = int(response.content[0].text.strip())
        if tid == 0:
            return None
        return next((t for t in transactions if t["id"] == tid), None)
    except (ValueError, StopIteration):
        return None


def get_transaction_requirements(
    client: anthropic.Anthropic,
    index: dict,
    transaction_name: str,
) -> str:
    """
    Look up a transaction in the index and return formatted requirements.

    Args:
        client:           Initialized Anthropic client.
        index:            The loaded transactions_index.json as a dict.
        transaction_name: User input — either a number or a transaction name.

    Returns:
        A formatted string with full details of the transaction requirements.
    """
    transactions = index.get("transactions", [])
    stripped = transaction_name.strip()
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

    # 3. Partial name (case-insensitive substring, unique result only)
    if not matched:
        lower = stripped.lower()
        candidates = [t for t in transactions if lower in t["name"].lower()]
        if len(candidates) == 1:
            matched = candidates[0]

    # 4. Claude-assisted matching
    if not matched:
        matched = _find_best_match(client, transactions, stripped)

    if not matched:
        return (
            f'Could not find a transaction matching "{transaction_name}".\n'
            "Please check the transaction list and try again."
        )

    # Pass only this transaction's text to Claude for formatting
    with client.beta.messages.stream(
        model="claude-opus-4-6",
        max_tokens=4096,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f'The citizen wants to avail: "{matched["name"]}"\n\n'
                    "Here is the relevant section from the Citizen's Charter:\n\n"
                    f"{matched['text']}"
                ),
            }
        ],
    ) as stream:
        return stream.get_final_message().content[-1].text
