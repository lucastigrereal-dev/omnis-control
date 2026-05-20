"""
M4.4 — Static Schema Validation Tests
Validates CRM migration SQL without connecting to Supabase.
Parses 002_crm_supabase_schema.sql and checks structure.
"""
import re
import sys
import pytest
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"
SCHEMA_FILE = MIGRATIONS_DIR / "002_crm_supabase_schema.sql"


def read_schema():
    if not SCHEMA_FILE.exists():
        pytest.skip(f"Schema file not found: {SCHEMA_FILE}")
    return SCHEMA_FILE.read_text(encoding="utf-8")


# ============================================================
# TABLE EXISTENCE
# ============================================================

REQUIRED_TABLES = [
    "crm_leads",
    "crm_deals",
    "crm_followups",
    "crm_objections",
    "crm_commissions",
]


@pytest.mark.parametrize("table", REQUIRED_TABLES)
def test_table_has_create_statement(table):
    """Each required table must have CREATE TABLE IF NOT EXISTS."""
    sql = read_schema()
    assert f"CREATE TABLE IF NOT EXISTS {table}" in sql, f"Missing CREATE TABLE for {table}"


# ============================================================
# NO DESTRUCTIVE STATEMENTS
# ============================================================

DESTRUCTIVE_PATTERNS = [
    (r"\bDROP\s+TABLE\b", "DROP TABLE"),
    (r"\bDROP\s+INDEX\b", "DROP INDEX"),
    (r"\bDROP\s+VIEW\b", "DROP VIEW"),
    (r"\bDROP\s+TRIGGER\b", "DROP TRIGGER"),
    (r"\bTRUNCATE\b", "TRUNCATE"),
    (r"\bDELETE\s+FROM\b", "DELETE FROM"),
    (r"\bDROP\s+CASCADE\b", "DROP CASCADE"),
]


@pytest.mark.parametrize("pattern,label", DESTRUCTIVE_PATTERNS)
def test_no_destructive_statement(pattern, label):
    """Schema must not contain destructive SQL."""
    sql = read_schema()
    matches = re.findall(pattern, sql, re.IGNORECASE)
    assert len(matches) == 0, f"Destructive statement found: {label} — matches: {matches}"


# ============================================================
# FOREIGN KEYS
# ============================================================

REQUIRED_FKS = [
    ("crm_deals", "lead_id", "crm_leads"),
    ("crm_followups", "lead_id", "crm_leads"),
    ("crm_followups", "deal_id", "crm_deals"),
    ("crm_objections", "lead_id", "crm_leads"),
    ("crm_objections", "deal_id", "crm_deals"),
    ("crm_commissions", "deal_id", "crm_deals"),
]


@pytest.mark.parametrize("table,column,ref_table", REQUIRED_FKS)
def test_foreign_key_exists(table, column, ref_table):
    """Each FK relationship must be defined in the schema."""
    sql = read_schema()
    pattern = rf"REFERENCES\s+{ref_table}\s*\(\s*id\s*\)"
    # Find the FK in the correct table's CREATE block
    table_block = extract_create_table(sql, table)
    assert re.search(pattern, table_block, re.IGNORECASE), (
        f"FK {table}.{column} -> {ref_table}.id not found"
    )


def extract_create_table(sql, table_name):
    """Extract the CREATE TABLE block for a specific table."""
    pattern = rf"CREATE TABLE IF NOT EXISTS {table_name}\s*\(.*?\);"
    match = re.search(pattern, sql, re.DOTALL)
    return match.group(0) if match else ""


# ============================================================
# CHECK CONSTRAINTS
# ============================================================

REQUIRED_CONSTRAINTS = [
    "chk_leads_status",
    "chk_leads_source",
    "chk_leads_priority",
    "chk_deals_status",
    "chk_deals_product",
    "chk_deals_probability",
    "chk_deals_value",
    "chk_followups_status",
    "chk_followups_channel",
    "chk_followups_cadence",
    "chk_objections_type",
    "chk_objections_outcome",
    "chk_commissions_tier",
    "chk_commissions_role",
    "chk_commissions_payment",
    "chk_commissions_value",
]


@pytest.mark.parametrize("constraint", REQUIRED_CONSTRAINTS)
def test_check_constraint_exists(constraint):
    """Each required CHECK constraint must exist."""
    sql = read_schema()
    assert f"CONSTRAINT {constraint}" in sql, f"Missing CONSTRAINT {constraint}"


# ============================================================
# INDEXES
# ============================================================

REQUIRED_INDEXES = [
    "idx_leads_status",
    "idx_leads_created_at",
    "idx_deals_lead_id",
    "idx_deals_status",
    "idx_deals_created_at",
    "idx_followups_lead_id",
    "idx_followups_status",
    "idx_followups_scheduled_for",
    "idx_followups_created_at",
    "idx_objections_lead_id",
    "idx_objections_type",
    "idx_objections_created_at",
    "idx_commissions_deal_id",
    "idx_commissions_payment",
    "idx_commissions_created_at",
]


@pytest.mark.parametrize("index", REQUIRED_INDEXES)
def test_index_exists(index):
    """Each required index must exist."""
    sql = read_schema()
    assert f"CREATE INDEX IF NOT EXISTS {index}" in sql, f"Missing INDEX {index}"


# ============================================================
# VIEWS
# ============================================================

REQUIRED_VIEWS = [
    "vw_pipeline_summary",
    "vw_leads_qualificados",
    "vw_comissoes_mensal",
]


@pytest.mark.parametrize("view", REQUIRED_VIEWS)
def test_view_exists(view):
    """Each required view must exist."""
    sql = read_schema()
    assert f"CREATE OR REPLACE VIEW {view}" in sql, f"Missing VIEW {view}"


# ============================================================
# NO SQLITE SYNTAX IN POSTGRESQL MIGRATION
# ============================================================

SQLITE_PATTERNS = [
    (r"datetime\('now'\)", "SQLite datetime function"),
    (r"INTEGER\s+PRIMARY\s+KEY", "SQLite INTEGER PK (use UUID)"),
    (r"AUTOINCREMENT", "SQLite AUTOINCREMENT"),
    (r"PRAGMA\s+", "SQLite PRAGMA"),
]


@pytest.mark.parametrize("pattern,label", SQLITE_PATTERNS)
def test_no_sqlite_syntax(pattern, label):
    """Schema targets PostgreSQL — no SQLite-specific syntax."""
    sql = read_schema()
    matches = re.findall(pattern, sql, re.IGNORECASE)
    assert len(matches) == 0, f"SQLite syntax found: {label} — matches: {matches}"


# ============================================================
# RLS — DOCUMENTED, NOT ACTIVE
# ============================================================

def test_rls_is_commented_out():
    """RLS policies must be commented out (not active)."""
    sql = read_schema()
    # Find ENABLE ROW LEVEL SECURITY statements
    enabled = re.findall(r"^\s*ALTER\s+TABLE.*ENABLE\s+ROW\s+LEVEL\s+SECURITY", sql, re.MULTILINE)
    assert len(enabled) == 0, (
        f"RLS is ACTIVE — should be commented out. Found: {enabled}"
    )


# ============================================================
# IDEMPOTENCY
# ============================================================

def test_all_create_table_use_if_not_exists():
    """All CREATE TABLE must use IF NOT EXISTS."""
    sql = read_schema()
    creates = re.findall(r"CREATE\s+TABLE\s+(?!IF\s+NOT\s+EXISTS)(\w+)", sql, re.IGNORECASE)
    assert len(creates) == 0, f"CREATE TABLE without IF NOT EXISTS: {creates}"


def test_all_create_index_use_if_not_exists():
    """All CREATE INDEX must use IF NOT EXISTS."""
    sql = read_schema()
    creates = re.findall(r"CREATE\s+INDEX\s+(?!IF\s+NOT\s+EXISTS)(\w+)", sql, re.IGNORECASE)
    assert len(creates) == 0, f"CREATE INDEX without IF NOT EXISTS: {creates}"


# ============================================================
# COLUMN COUNT (sanity check)
# ============================================================

EXPECTED_COLUMNS = {
    "crm_leads": 32,
    "crm_deals": 26,
    "crm_followups": 22,
    "crm_objections": 14,
    "crm_commissions": 20,
}


@pytest.mark.parametrize("table,expected_count", EXPECTED_COLUMNS.items())
def test_column_count(table, expected_count):
    """Sanity check: each table has the expected number of columns."""
    sql = read_schema()
    block = extract_create_table(sql, table)
    if not block:
        pytest.skip(f"Table block not found for {table}")
    # Count column definitions (lines with a type that aren't CONSTRAINT or PK)
    # Strip the CREATE TABLE wrapper
    inner = block.split("(", 1)[1].rsplit(")", 1)[0]
    # Count lines that define columns (have a type keyword)
    columns = re.findall(
        r"^\s+(\w+)\s+(UUID|TEXT|INTEGER|DECIMAL|BOOLEAN|DATE|TIMESTAMPTZ|JSONB|TEXT\[\])",
        inner, re.MULTILINE
    )
    actual_count = len(columns)
    assert actual_count == expected_count, (
        f"{table}: expected {expected_count} columns, got {actual_count}: {[c[0] for c in columns]}"
    )


# ============================================================
# SEED FILE SAFETY
# ============================================================

def test_seed_file_exists():
    """Seed file must exist but be separate from schema."""
    seed = MIGRATIONS_DIR / "002_crm_seed.sql"
    assert seed.exists(), "Seed file 002_crm_seed.sql not found"


def test_seed_uses_on_conflict_do_nothing():
    """Seed INSERTs must use ON CONFLICT DO NOTHING for idempotency."""
    seed = (MIGRATIONS_DIR / "002_crm_seed.sql").read_text(encoding="utf-8")
    inserts = re.findall(r"INSERT\s+INTO\s+\w+", seed, re.IGNORECASE)
    on_conflicts = re.findall(r"ON\s+CONFLICT\s+\(id\)\s+DO\s+NOTHING", seed, re.IGNORECASE)
    assert len(inserts) == len(on_conflicts), (
        f"All INSERTs must have ON CONFLICT (id) DO NOTHING. "
        f"Found {len(inserts)} INSERTs, {len(on_conflicts)} ON CONFLICT clauses."
    )


def test_seed_no_destructive():
    """Seed file must not contain destructive statements."""
    seed = (MIGRATIONS_DIR / "002_crm_seed.sql").read_text(encoding="utf-8")
    for pattern, label in DESTRUCTIVE_PATTERNS:
        matches = re.findall(pattern, seed, re.IGNORECASE)
        assert len(matches) == 0, f"Seed contains {label}"
