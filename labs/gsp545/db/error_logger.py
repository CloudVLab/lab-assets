#!/usr/bin/env python3
"""
Cymbal Solar Error Logger Handler.
VULNERABILITY: Raw string concatenation in SQL queries (CWE-89 SQL Injection).
Candidate must use Antigravity to patch using parameterized queries (? placeholders).
"""

import sqlite3
import os

DB_PATH = os.path.expanduser("~/cymbal-telemetry.db")

def log_error_event(device_id, error_code, message, severity):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # VULNERABLE TO SQL INJECTION:
    query = f"INSERT INTO error_logs (device_id, error_code, message, severity) VALUES ('{device_id}', '{error_code}', '{message}', '{severity}')"
    cursor.execute(query)
    conn.commit()
    conn.close()

def search_errors_by_device(device_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # VULNERABLE TO SQL INJECTION:
    query = f"SELECT device_id, error_code, message, severity FROM error_logs WHERE device_id = '{device_id}'"
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    return [{"device_id": r[0], "error_code": r[1], "message": r[2], "severity": r[3]} for r in rows]
