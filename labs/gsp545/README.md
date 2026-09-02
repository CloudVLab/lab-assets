# GSP545: Customize Coding Agents and Enterprise Workflows with Antigravity

This directory contains starter application code, tests, and verification tooling for **GSP545: Customize Coding Agents and Enterprise Workflows with Antigravity: Challenge Lab**.

## Contents

- `telemetry-db-mcp/`: Mock Model Context Protocol (MCP) SQLite server (`query_telemetry_schema`, `inspect_error_logs`).
- `telemetry_processor.py`: Legacy synchronous telemetry processing pipeline to be refactored by coding subagents.
- `db/error_logger.py`: Error logging module containing SQL injection vulnerability to be patched.
- `tests/`: Automated test suites (`test_performance.py`, `test_security.py`) validating speedup and security.
- `verify_task.py`: Verification harness emitting Cloud Logging entries for Qwiklabs Activity Tracking.
- `requirements.txt`: Python package dependencies.
