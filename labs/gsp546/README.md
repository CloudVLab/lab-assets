# GSP546: Architect Code-First Custom Agents and Multi-Agent Orchestration with ADK

This directory contains starter application code, multi-agent frameworks, tests, and verification tooling for **GSP546: Architect Code-First Custom Agents and Multi-Agent Orchestration with ADK: Challenge Lab**.

## Contents

- `agent/`: Custom Python agent implementations:
  - `diagnostic_agent.py`: ADK agent with managed multi-turn session memory.
  - `tools.py`: Vector Search RAG retrieval tool and inventory lookup.
  - `supervisor_agent.py`: Multi-agent supervisor coordinating worker agents via A2A protocol.
- `app/`:
  - `main.py`: FastAPI server for Cloud Run deployment.
- `Dockerfile`: Container image build manifest for Google Cloud Build and Cloud Run.
- `tests/`: Automated test suite (`test_multi_agent.py`) verifying memory retention, vector similarity, and A2A routing handoffs.
- `verify_task.py`: Verification harness emitting Cloud Logging entries for Qwiklabs Activity Tracking.
- `requirements.txt`: Python package dependencies.
