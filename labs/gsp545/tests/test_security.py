import pytest
import sqlite3
import os
from db.error_logger import log_error_event, search_errors_by_device, DB_PATH

@pytest.fixture(autouse=True)
def setup_test_db():
    """Ensure database and table exist with seed telemetry records."""
    db_path = os.path.expanduser(DB_PATH)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS error_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            error_code TEXT,
            message TEXT,
            severity TEXT,
            logged_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("DELETE FROM error_logs WHERE device_id = 'INV-HG-TEST'")
    cursor.execute("INSERT INTO error_logs (device_id, error_code, message, severity) VALUES ('INV-HG-TEST', 'E-101', 'Voltage surge', 'WARNING')")
    conn.commit()
    conn.close()

def test_sql_injection_defense():
    # Attempt SQL injection exploit payload
    payload_device_id = "INV-TEST' OR '1'='1"
    
    # Should safely treat the payload as a literal string value, not executable SQL
    try:
        results = search_errors_by_device(payload_device_id)
        # In a vulnerable app with OR '1'='1', it returns all rows in the table.
        # In a patched app with parameterized queries, it returns empty list (no device named literally "INV-TEST' OR '1'='1").
        assert len(results) == 0, f"SQL injection vulnerability detected! Query returned unescaped records: {results}"
    except sqlite3.OperationalError as e:
        pytest.fail(f"SQL Syntax Error indicates raw string injection is still present: {e}")

def test_log_error_event_injection_defense():
    # Test inserting an event with quotes and semicolons in fields
    malicious_device_id = "INV-TEST'); DROP TABLE error_logs; --"
    try:
        log_error_event(malicious_device_id, "E-999", "Exploit attempt", "CRITICAL")
    except sqlite3.OperationalError as e:
        pytest.fail(f"SQL Syntax Error during log_error_event indicates unescaped SQL: {e}")
