#!/usr/bin/env python3
"""
Mock Model Context Protocol (MCP) Server for Cymbal Solar Telemetry Database.
Provides JSON-RPC stdio interface with tools:
- query_telemetry_schema
- inspect_error_logs
"""

import sys
import json
import sqlite3
import os

DB_PATH = os.path.expanduser("~/cymbal-telemetry.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inverter_telemetry (
            device_id TEXT PRIMARY KEY,
            voltage REAL,
            temperature REAL,
            efficiency REAL,
            status TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
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
    # Seed sample telemetry
    cursor.execute("INSERT OR REPLACE INTO inverter_telemetry VALUES ('INV-HG-101', 480.2, 58.4, 0.98, 'NORMAL', datetime('now'))")
    cursor.execute("INSERT OR REPLACE INTO inverter_telemetry VALUES ('INV-HG-204', 380.1, 74.2, 0.81, 'DEGRADED', datetime('now'))")
    cursor.execute("INSERT OR REPLACE INTO error_logs (device_id, error_code, message, severity) VALUES ('INV-HG-204', 'E-101', 'High operating temperature on DC bus', 'WARNING')")
    conn.commit()
    conn.close()

def handle_query_telemetry_schema(args):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table'")
    schemas = [row[0] for row in cursor.fetchall()]
    conn.close()
    return {"status": "success", "tables": schemas}

def handle_inspect_error_logs(args):
    severity = args.get("severity", "WARNING")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT device_id, error_code, message, severity FROM error_logs WHERE severity = ?", (severity,))
    rows = cursor.fetchall()
    conn.close()
    results = [{"device_id": r[0], "error_code": r[1], "message": r[2], "severity": r[3]} for r in rows]
    return {"status": "success", "errors": results}

TOOLS = {
    "query_telemetry_schema": handle_query_telemetry_schema,
    "inspect_error_logs": handle_inspect_error_logs
}

def main():
    init_db()
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            req = json.loads(line)
            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})

            if method == "tools/list":
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "tools": [
                            {
                                "name": "query_telemetry_schema",
                                "description": "Returns the SQLite database schemas for inverter telemetry and error logs."
                            },
                            {
                                "name": "inspect_error_logs",
                                "description": "Queries error logs by severity level (INFO, WARNING, CRITICAL).",
                                "parameters": {"severity": {"type": "string"}}
                            }
                        ]
                    }
                }
            elif method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                if tool_name in TOOLS:
                    result = TOOLS[tool_name](tool_args)
                    resp = {"jsonrpc": "2.0", "id": req_id, "result": result}
                else:
                    resp = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Tool not found: {tool_name}"}}
            else:
                resp = {"jsonrpc": "2.0", "id": req_id, "result": {"status": "ok"}}

            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
        except Exception as e:
            err_resp = {"jsonrpc": "2.0", "error": {"code": -32000, "message": str(e)}}
            sys.stdout.write(json.dumps(err_resp) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    main()
