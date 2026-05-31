"""
Export all Questions and Dashboards to portable JSON files,
then sync SQL into docs/03-questions.md and config/metabase/questions.yaml.

Output:
  metabase-config/exports/questions/{collection_slug}__{question_slug}.json
  metabase-config/exports/dashboards/{collection_slug}__{dashboard_slug}.json

Run: python scripts/04_export_config.py
"""
import io
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv()

from scripts.metabase_client import client_from_env

EXPORTS_ROOT = Path(__file__).parent.parent / "metabase-config" / "exports"
DOCS_PATH    = Path(__file__).parent.parent / "docs" / "03-questions.md"
YAML_PATH    = Path(__file__).parent.parent / "config" / "metabase" / "questions.yaml"


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "_", text)
    return text.strip("_")


def get_collection_path(client, collection_id: int | None, cache: dict) -> str:
    """Resolve collection_id → 'Northwind/Sales' style path."""
    if collection_id is None:
        return "Our analytics"
    if collection_id in cache:
        return cache[collection_id]

    resp = client.session.get(f"{client.base_url}/api/collection/{collection_id}", timeout=30)
    resp.raise_for_status()
    col = resp.json()
    name = col["name"]
    parent_id = col.get("parent_id")

    if parent_id:
        parent_path = get_collection_path(client, parent_id, cache)
        path = f"{parent_path}/{name}"
    else:
        path = name

    cache[collection_id] = path
    return path


def export_questions(client, db_name: str) -> list[dict]:
    """Pull all native SQL questions from Metabase and write to JSON files.

    Returns the list of exported question dicts for downstream sync steps.
    """
    out_dir = EXPORTS_ROOT / "questions"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("\n── Exporting Questions ──")
    all_cards = client.list_all_questions()
    col_cache: dict = {}
    exported: list[dict] = []

    for name, card_id in all_cards.items():
        if name.startswith("__"):
            continue

        resp = client.session.get(f"{client.base_url}/api/card/{card_id}", timeout=30)
        resp.raise_for_status()
        card = resp.json()

        if card.get("query_type") != "native":
            continue

        col_id   = card.get("collection_id")
        col_path = get_collection_path(client, col_id, col_cache)
        col_slug = slugify(col_path.split("/")[-1])
        q_slug   = slugify(name)
        sql      = card.get("dataset_query", {}).get("native", {}).get("query", "")

        payload = {
            "name":            name,
            "collection_path": col_path,
            "database_name":   db_name,
            "sql":             sql,
            "display":         card.get("display", "table"),
            "description":     card.get("description") or "",
        }

        filename = out_dir / f"{col_slug}__{q_slug}.json"
        filename.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  [OK] {filename.name}")
        exported.append(payload)

    return exported


def export_dashboards(client) -> int:
    out_dir = EXPORTS_ROOT / "dashboards"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("\n── Exporting Dashboards ──")
    col_cache: dict = {}

    resp = client.session.get(f"{client.base_url}/api/dashboard", timeout=30)
    resp.raise_for_status()
    body = resp.json()
    all_dashes = body if isinstance(body, list) else body.get("data", [])
    count = 0

    for item in all_dashes:
        dash_id = item["id"]
        resp2 = client.session.get(f"{client.base_url}/api/dashboard/{dash_id}", timeout=30)
        resp2.raise_for_status()
        dash = resp2.json()

        col_id   = dash.get("collection_id")
        col_path = get_collection_path(client, col_id, col_cache)
        col_slug = slugify(col_path.split("/")[-1])
        d_slug   = slugify(dash["name"])

        cards = []
        for dc in dash.get("dashcards", []):
            card = dc.get("card") or {}
            if not card:
                continue
            cards.append({
                "question_name": card.get("name", ""),
                "row":    dc["row"],
                "col":    dc["col"],
                "size_x": dc["size_x"],
                "size_y": dc["size_y"],
            })

        payload = {
            "name":            dash["name"],
            "collection_path": col_path,
            "description":     dash.get("description") or "",
            "cards":           cards,
        }

        filename = out_dir / f"{col_slug}__{d_slug}.json"
        filename.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  [OK] {filename.name}  ({len(cards)} cards)")
        count += 1

    return count


# ---------------------------------------------------------------------------
# Sync helpers
# ---------------------------------------------------------------------------

def _normalize_name(name: str) -> str:
    """Strip known prefixes ('Q1:', 'Sales —') and return lowercase for fuzzy matching."""
    name = re.sub(r"^Q\d+:\s*", "", name)          # strip "Q1: "
    name = re.sub(r"^[^—\-]*[—\-]\s*", "", name)   # strip "Sales — " or "Sales - "
    return name.lower().strip()


def _name_similarity(a: str, b: str) -> float:
    """Word-overlap ratio between two normalized names (0.0–1.0)."""
    words_a = set(re.findall(r"\w+", a.lower()))
    words_b = set(re.findall(r"\w+", b.lower()))
    if not words_a or not words_b:
        return 0.0
    return len(words_a & words_b) / max(len(words_a), len(words_b))


# ---------------------------------------------------------------------------
# Sync docs/03-questions.md
# ---------------------------------------------------------------------------

def _replace_sql_in_docs(content: str, heading_name: str, new_sql: str) -> tuple[str, bool]:
    """Find a heading containing heading_name and replace the next ```sql block."""
    lines = content.split("\n")
    result: list[str] = []
    i = 0
    updated = False

    while i < len(lines):
        line = lines[i]
        is_target_heading = (
            bool(re.match(r"^#{1,4}\s+", line))
            and heading_name in line
            and not updated
        )

        if is_target_heading:
            result.append(line)
            i += 1
            # Scan forward for the next ```sql block; stop at next heading
            while i < len(lines):
                if lines[i].strip() == "```sql":
                    result.append(lines[i])   # opening ```sql
                    i += 1
                    # Skip old SQL content
                    while i < len(lines) and lines[i].strip() != "```":
                        i += 1
                    # Insert new SQL lines
                    result.extend(new_sql.split("\n"))
                    result.append("```")
                    if i < len(lines):
                        i += 1  # skip the closing ```
                    updated = True
                    break
                elif re.match(r"^#{1,4}\s+", lines[i]):
                    # Reached next heading with no SQL block found
                    break
                else:
                    result.append(lines[i])
                    i += 1
        else:
            result.append(line)
            i += 1

    return "\n".join(result), updated


def sync_docs(questions: list[dict]) -> int:
    """Update SQL blocks in docs/03-questions.md to match current Metabase state."""
    if not DOCS_PATH.exists():
        print("  [SKIP] docs/03-questions.md not found")
        return 0

    content = DOCS_PATH.read_text(encoding="utf-8")
    updated_count = 0

    for q in questions:
        name    = q["name"]
        new_sql = q["sql"].strip()
        content, ok = _replace_sql_in_docs(content, name, new_sql)
        if ok:
            updated_count += 1
            print(f"  [OK] {name}")
        else:
            print(f"  [--] No heading match for '{name}'")

    DOCS_PATH.write_text(content, encoding="utf-8")
    return updated_count


# ---------------------------------------------------------------------------
# Sync config/metabase/questions.yaml  (raw string replacement — preserves comments)
# ---------------------------------------------------------------------------

def _replace_yaml_sql(raw: str, yaml_name: str, new_sql: str) -> tuple[str, bool]:
    """Replace the sql: | block for yaml_name in raw YAML text without reparsing."""
    name_escaped = re.escape(yaml_name)

    # Match: list entry with this name, then any fields (non-greedy), then sql: | + indented block
    pattern = (
        r"((?:^|\n)([ \t]*)- *name: *['\"]?" + name_escaped + r"['\"]?"
        r"(?:\n(?!\s*- )[\s\S])*?"   # fields before sql (doesn't cross another list item)
        r"\2  sql: \|\n)"            # sql: | header (same indent level + 2)
        r"((?:\2    [^\n]*\n?)*)"    # indented SQL content (indent + 4 spaces)
    )

    # Detect existing indent from the name line; default to 4-space indent for SQL content
    match = re.search(pattern, raw, flags=re.MULTILINE)
    if not match:
        return raw, False

    # Determine base indentation (the list item's indent) and build SQL indent
    base_indent = match.group(2)          # e.g. "" or "  "
    sql_indent  = base_indent + "    "    # 4 more spaces for sql body

    indented_sql = "\n".join(sql_indent + line for line in new_sql.split("\n"))
    if not indented_sql.endswith("\n"):
        indented_sql += "\n"

    new_raw, count = re.subn(pattern, r"\g<1>" + indented_sql, raw, count=1, flags=re.MULTILINE)
    return new_raw, count > 0


def sync_yaml(questions: list[dict]) -> int:
    """Update sql fields in config/metabase/questions.yaml to match Metabase state.

    Matches YAML entries to Metabase questions by normalized name similarity
    (word overlap), so mismatched prefixes like 'Q1:' vs 'Sales —' are tolerated.
    """
    if not YAML_PATH.exists():
        print("  [SKIP] questions.yaml not found")
        return 0

    raw = YAML_PATH.read_text(encoding="utf-8")

    # Build a quick lookup: normalized_metabase_name → question dict
    mb_index: dict[str, dict] = {_normalize_name(q["name"]): q for q in questions}

    # Parse YAML only to get the list of names (not to rewrite — we use raw replacement)
    import yaml  # local import; pyyaml is in requirements.txt
    data = yaml.safe_load(raw)
    updated_count = 0

    for entry in data.get("questions", []):
        yaml_name = entry["name"]
        yaml_norm = _normalize_name(yaml_name)

        # Find best matching Metabase question
        best_name, best_score = max(
            ((mb_norm, _name_similarity(yaml_norm, mb_norm)) for mb_norm in mb_index),
            key=lambda t: t[1],
            default=(None, 0.0),
        )

        if best_score < 0.6 or best_name is None:
            print(f"  [--] No match for '{yaml_name}' (best score={best_score:.2f})")
            continue

        mb_q    = mb_index[best_name]
        new_sql = mb_q["sql"].strip()

        raw, ok = _replace_yaml_sql(raw, yaml_name, new_sql)
        if ok:
            updated_count += 1
            print(f"  [OK] '{yaml_name}' ← '{mb_q['name']}'")
        else:
            print(f"  [ERR] Regex replacement failed for '{yaml_name}'")

    YAML_PATH.write_text(raw, encoding="utf-8")
    return updated_count


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    client  = client_from_env()
    db_name = "Northwind DW"

    questions = export_questions(client, db_name)
    d_count   = export_dashboards(client)

    print(f"\n── Syncing docs/03-questions.md ──")
    docs_updated = sync_docs(questions)

    print(f"\n── Syncing config/metabase/questions.yaml ──")
    yaml_updated = sync_yaml(questions)

    print(f"\n{'='*55}")
    print(f"Exported   {len(questions)} questions  →  metabase-config/exports/questions/")
    print(f"Exported   {d_count} dashboards →  metabase-config/exports/dashboards/")
    print(f"Synced     {docs_updated} SQL blocks  →  docs/03-questions.md")
    print(f"Synced     {yaml_updated} SQL blocks  →  config/metabase/questions.yaml")


if __name__ == "__main__":
    main()
