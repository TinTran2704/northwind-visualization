"""
Quick smoke-test: authenticate → list databases → find 'Northwind DW'.
Run: python scripts/test_connection.py
"""
import sys
import io
from pathlib import Path

# Fix Windows console encoding for UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Allow running from repo root without installing the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from scripts.metabase_client import client_from_env

def main() -> None:
    client = client_from_env()
    print("✓ Authentication OK")

    db_id = client.get_database_id("Northwind DW")
    print(f"✓ Found 'Northwind DW' → database_id={db_id}")

    col_id = client.get_collection_id("Northwind")
    print(f"✓ Collection 'Northwind' → collection_id={col_id}")

    print("\nAll checks passed — Metabase API is reachable.")

if __name__ == "__main__":
    main()
