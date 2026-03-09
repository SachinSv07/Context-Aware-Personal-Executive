"""Quick local test loop for the agent.

Run:
    python agent/test_agent.py
"""

import sys
from pathlib import Path

# Add project root to path so imports work
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agent import process_query


print("Agent Test Loop")
print("=" * 50)
print("Try these queries:")
print("  - 'What emails are about the meeting?'")
print("  - 'Show me PDF documents'")
print("  - 'What notes do I have about budget?'")
print("Type 'quit' to exit.\n")

while True:
    query = input("Ask something: ").strip()
    if query.lower() in {"exit", "quit", "q"}:
        print("Exiting test loop.")
        break

    if not query:
        continue

    response = process_query(query)
    print(response)
    print("-" * 50)
