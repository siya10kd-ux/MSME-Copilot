"""MSME Copilot — AI operations agent for small manufacturers."""

import argparse
import json
import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from graph.state import create_initial_state
from graph.workflow import compile_workflow


def run_workflow(question: str = "", documents: list | None = None) -> dict:
    """Run the full agent workflow and return final state."""
    from db.sqlite_store import init_db

    init_db()
    app = compile_workflow()
    initial = create_initial_state(question=question, raw_documents=documents)
    result = app.invoke(initial)
    return dict(result)


def main():
    parser = argparse.ArgumentParser(description="MSME Copilot")
    parser.add_argument(
        "--question",
        default="Which products are profitable but frequently delayed?",
        help="Business question to ask",
    )
    parser.add_argument(
        "--check-ollama",
        action="store_true",
        help="Check Ollama connection and exit",
    )
    args = parser.parse_args()

    if args.check_ollama:
        from config.llm import check_ollama_connection

        ok = check_ollama_connection()
        print("Ollama connection:", "OK" if ok else "FAILED")
        sys.exit(0 if ok else 1)

    result = run_workflow(question=args.question)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
