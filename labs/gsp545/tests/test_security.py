import pytest
import sqlite3
import os
from db.error_logger import log_error_event, search_errors_by_device

def test_sql_injection_defense():
    # Attempt SQL injection exploit payload
    payload_device_id = "INV-TEST' OR '1'='1"
    
    # Should safely treat the payload as a literal string value, not executable SQL
    try:
        results = search_errors_by_device(payload_device_id)
        # In a vulnerable app with OR 1=1, it returns all rows in the table.
        # In a patched app with parameterized queries, it returns empty list (no device named literally "INV-TEST' OR '1'='1").
        assert len(results) == 0, f"SQL injection vulnerability detected! Query returned unescaped records: {results}"
    except sqlite3.OperationalError as e:
        pytest.fail(f"SQL Syntax Error indicates raw string injection is still present: {e}")
