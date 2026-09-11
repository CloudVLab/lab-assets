# GSP548: Secure Agent Tool Execution, Identity, and Workload Guardrails

This directory contains starter application code, security harnesses, tests, and verification tooling for **GSP548: Secure Agent Tool Execution, Identity, and Workload Guardrails: Challenge Lab**.

## Contents

- `agent/`: Security and guardrail modules:
  - `security.py`: Agent Identity and 2-legged OAuth (2LO) client credentials token exchange module.
  - `control_guard.py`: Human-in-the-Loop (HITL) safety interceptor gating destructive grid actions and thermal cutoffs.
  - `dlp_masker.py`: Cloud DLP / Sensitive Data Protection (SDP) PII de-identification masking utility.
- `scripts/`:
  - `red_team_exploit.py`: Automated red-team penetration harness evaluating Model Armor prompt injection protection.
- `tests/`:
  - `test_security.py`: Comprehensive test suite verifying Model Armor injection interception, DLP masking, 2LO OAuth token exchange, and HITL safety gates.
- `verify_task.py`: Candidate verification CLI emitting dual-mode Cloud Logging telemetry to `gsp548-validation`.
- `requirements.txt`: Python package dependencies.
