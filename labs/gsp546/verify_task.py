#!/usr/bin/env python3
"""
Verification Script for GSP546 Challenge Lab.
Usage:
  python3 verify_task.py --task 1
  python3 verify_task.py --task 2
  python3 verify_task.py --task 3
  python3 verify_task.py --task 4
"""

import os
import sys
import subprocess
import argparse
from google.cloud import logging as cloud_logging

def get_project_id():
    try:
        cmd = "gcloud config get-value project 2>/dev/null"
        res = subprocess.check_output(cmd, shell=True).decode().strip()
        return res
    except Exception:
        return os.environ.get("PROJECT_ID", "")

def log_event(task_num, status, details):
    try:
        project_id = get_project_id()
        if not project_id:
            print("[Warning] No GCP project ID detected; skipping Cloud Logging.")
            return

        client = cloud_logging.Client(project=project_id)
        logger = client.logger("gsp546-validation")

        task_keys = {
            1: "task1_diagnostic_agent",
            2: "task2_vector_rag",
            3: "task3_a2a_orchestration",
            4: "task4_cloud_run"
        }

        task_id = task_keys.get(task_num, f"task{task_num}")
        payload = {
            "task": task_id,
            f"step_{task_num}": status,
            "details": details
        }
        # Emit structured JSON log
        logger.log_struct(payload, severity="INFO")
        # Emit text log for textPayload filters
        logger.log_text(f"TASK_{task_num}_{status}", severity="INFO")
        print(f"[Activity Tracking Logged] Task {task_num} ({task_id}): {status}")
    except Exception as e:
        print(f"[Warning] Could not emit Cloud Logging entry: {e}")

def verify_task_1():
    print("Verifying Diagnostic Agent & Memory Persistence...")
    cmd = [sys.executable, "-m", "pytest", "tests/test_multi_agent.py::test_diagnostic_agent_memory_persistence"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print(res.stderr)
    if res.returncode != 0:
        print("FAILED: DiagnosticAgent memory persistence assertion failed.")
        return False
    print("SUCCESS: Task 1 verified.")
    log_event(1, "PASSED", "DiagnosticAgent with session memory verified.")
    return True

def verify_task_2():
    print("Verifying Vector Search RAG Retrieval Tool...")
    cmd = [sys.executable, "-m", "pytest", "tests/test_multi_agent.py::test_vector_search_rag_grounding"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print(res.stderr)
    if res.returncode != 0:
        print("FAILED: Vector Search RAG tool assertion failed.")
        return False
    print("SUCCESS: Task 2 verified.")
    log_event(2, "PASSED", "Vector Search RAG tool verified.")
    return True

def verify_task_3():
    print("Verifying Multi-Agent A2A Orchestration...")
    cmd = [sys.executable, "-m", "pytest", "tests/test_multi_agent.py::test_supervisor_multi_agent_a2a_orchestration"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print(res.stderr)
    if res.returncode != 0:
        print("FAILED: Supervisor multi-agent A2A routing assertion failed.")
        return False
    print("SUCCESS: Task 3 verified.")
    log_event(3, "PASSED", "Multi-Agent A2A routing verified.")
    return True

def verify_task_4():
    print("Verifying Cloud Run Deployment...")
    project_id = get_project_id()
    cmd = "gcloud run services describe gridcare-agent-service --platform managed --region us-central1 --format='value(status.url)' 2>/dev/null"
    try:
        url = subprocess.check_output(cmd, shell=True).decode().strip()
        if not url:
            print("FAILED: Service 'gridcare-agent-service' not found on Cloud Run.")
            return False
        print(f"Service active at: {url}")
        # Test health endpoint
        curl_cmd = f"curl -s -f {url}/health"
        health_resp = subprocess.check_output(curl_cmd, shell=True).decode().strip()
        print(f"Health Response: {health_resp}")
        print("SUCCESS: Task 4 verified.")
        log_event(4, "PASSED", f"Cloud Run service deployed and healthy at {url}.")
        return True
    except Exception as e:
        print(f"FAILED: Could not verify Cloud Run service: {e}")
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=int, required=True, choices=[1, 2, 3, 4])
    args = parser.parse_args()

    if args.task == 1:
        verify_task_1()
    elif args.task == 2:
        verify_task_2()
    elif args.task == 3:
        verify_task_3()
    elif args.task == 4:
        verify_task_4()

if __name__ == "__main__":
    main()
