"""
Citizen's Charter Assistant
============================
A multi-agent system that reads a pre-built index of a government agency's
Citizen's Charter and helps citizens understand available transactions and
their requirements.

Agents:
  1. Listing Agent     — returns all available transactions from the index
  2. Requirements Agent — retrieves requirements for a chosen transaction

Build the index first (run once):
    python scripts/build_index.py --pdf citizenscharters/BureauOfImmigration_4thEdition.pdf

Then run the assistant:
    python main.py
    python main.py --index path/to/transactions_index.json
"""

import argparse
import json
import os
import sys

import anthropic
from dotenv import load_dotenv

from agents.listing_agent import list_transactions
from agents.requirements_agent import get_transaction_requirements

load_dotenv()

SEPARATOR = "─" * 60
DEFAULT_INDEX = os.path.join(os.path.dirname(__file__), "transactions_index.json")


def load_index(index_path: str) -> dict:
    """Load the pre-built transactions index from disk."""
    if not os.path.isfile(index_path):
        print(
            f"Error: Index file not found: {index_path}\n\n"
            "Build it first by running:\n"
            "  python scripts/build_index.py "
            "--pdf citizenscharters/BureauOfImmigration_4thEdition.pdf"
        )
        sys.exit(1)

    with open(index_path, "r", encoding="utf-8") as f:
        return json.load(f)


def print_header(index: dict) -> None:
    meta = index.get("metadata", {})
    print(SEPARATOR)
    print("  Citizen's Charter Assistant")
    print(SEPARATOR)
    if meta:
        print(f"  Source : {meta.get('source_pdf', 'unknown')}")
        print(f"  Index  : {meta.get('total_transactions', '?')} transactions")
        print(f"  Built  : {meta.get('built_at', 'unknown')[:10]}")
    print(SEPARATOR)


def run(index_path: str) -> None:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable is not set.")
        print("Create a .env file with ANTHROPIC_API_KEY=your-key or export it.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    # ── Step 1: Load index ───────────────────────────────────────────────────
    print(f"\nLoading index from: {index_path} ...")
    index = load_index(index_path)
    print("   ✓ Index loaded.\n")

    print_header(index)

    # ── Step 2: Agent 1 — List transactions ─────────────────────────────────
    transactions_text = list_transactions(index)

    print(SEPARATOR)
    print("  Available Transactions")
    print(SEPARATOR)
    print(transactions_text)
    print(SEPARATOR)

    # ── Step 3: Interaction loop ─────────────────────────────────────────────
    try:
        while True:
            print("\nEnter the transaction name or number you are interested in.")
            print('(Type "quit" or "exit" to close the assistant.)\n')
            user_input = input("Your choice: ").strip()

            if not user_input:
                print("  ⚠  Please enter a transaction name or number.")
                continue

            if user_input.lower() in ("quit", "exit", "q"):
                print("\nThank you for using the Citizen's Charter Assistant. Goodbye!")
                break

            # ── Step 4: Agent 2 — Get requirements ──────────────────────────
            print(
                f'\n🤖 Agent 2 is looking up requirements for: "{user_input}" ...\n'
            )
            requirements_text = get_transaction_requirements(
                client, index, user_input
            )

            print(SEPARATOR)
            print("  Transaction Requirements")
            print(SEPARATOR)
            print(requirements_text)
            print(SEPARATOR)

            # ── Step 5: Continue? ────────────────────────────────────────────
            print("\nWould you like to check another transaction? (yes/no)")
            again = input("Your answer: ").strip().lower()
            if again not in ("yes", "y"):
                print("\nThank you for using the Citizen's Charter Assistant. Goodbye!")
                break

    except KeyboardInterrupt:
        print("\n\nInterrupted. Goodbye!")
    except anthropic.AuthenticationError:
        print("\nError: Invalid API key. Check your ANTHROPIC_API_KEY.")
        sys.exit(1)
    except anthropic.APIConnectionError:
        print("\nError: Could not connect to Anthropic API. Check your internet connection.")
        sys.exit(1)
    except anthropic.APIStatusError as e:
        print(f"\nAPI Error ({e.status_code}): {e.message}")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Citizen's Charter Assistant — powered by Claude multi-agent system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Build the index first (run once):\n"
            "  python scripts/build_index.py "
            "--pdf citizenscharters/BureauOfImmigration_4thEdition.pdf\n\n"
            "Then start the assistant:\n"
            "  python main.py\n"
        ),
    )
    parser.add_argument(
        "--index",
        default=DEFAULT_INDEX,
        metavar="PATH",
        help="Path to transactions_index.json (default: ./transactions_index.json)",
    )

    args = parser.parse_args()
    run(index_path=args.index)


if __name__ == "__main__":
    main()
