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
import json
import subprocess
import argparse
from google.cloud import logging as cloud_logging

def get_project_id(cli_project=None):
    """Resolve active Google Cloud Project ID with comprehensive fallbacks."""
    if cli_project and cli_project.strip() and cli_project != "(unset)":
        return cli_project.strip()

    # 1. Check environment variables (DEVSHELL_PROJECT_ID is default in Cloud Shell)
    for env_var in ["DEVSHELL_PROJECT_ID", "GOOGLE_CLOUD_PROJECT", "GCP_PROJECT", "PROJECT_ID"]:
        val = os.environ.get(env_var, "").strip()
        if val and val != "(unset)":
            return val

    # 2. Check gcloud CLI configuration
    for cmd in ["gcloud config get-value project 2>/dev/null", "gcloud config get project 2>/dev/null"]:
        try:
            res = subprocess.check_output(cmd, shell=True).decode().strip()
            if res and res != "(unset)":
                return res
        except Exception:
            pass

    # 3. Auto-discover via gcloud projects list (standard in Cloud Shell / Qwiklabs)
    try:
        res = subprocess.check_output("gcloud projects list --format='value(projectId)' --limit=1 2>/dev/null", shell=True).decode().strip()
        if res and res != "(unset)":
            os.environ["GOOGLE_CLOUD_PROJECT"] = res
            subprocess.run(f"gcloud config set project {res} 2>/dev/null", shell=True)
            return res
    except Exception:
        pass

    # 4. Check Google Auth default credentials
    try:
        import google.auth
        _, auth_project = google.auth.default()
        if auth_project and auth_project != "(unset)":
            return auth_project
    except Exception:
        pass

    return None

def log_event(task_num, status, details, project_id=None):
    """Emit dual-channel verification telemetry to Google Cloud Logging."""
    try:
        resolved_project = get_project_id(project_id)
        if not resolved_project:
            print("[ERROR] Cloud Logging skipped: Could not resolve Google Cloud Project ID.")
            print("Please run 'gcloud config set project <PROJECT_ID>' or pass '--project <PROJECT_ID>'.")
            return False

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

        # 1. Primary: Python Google Cloud Logging SDK
        try:
            client = cloud_logging.Client(project=resolved_project)
            logger = client.logger("gsp546-validation")
            logger.log_struct(payload, severity="INFO")
            logger.log_text(f"TASK_{task_num}_{status}", severity="INFO")
        except Exception as sdk_err:
            print(f"[Warning] Python Logging SDK emission error: {sdk_err}")

        # 2. Synchronous fallback: gcloud logging write CLI
        try:
            json_payload_str = json.dumps(payload).replace("'", "'\\''")
            subprocess.run(
                f"gcloud logging write gsp546-validation '{json_payload_str}' --payload-type=json --project={resolved_project} 2>/dev/null",
                shell=True
            )
            subprocess.run(
                f"gcloud logging write gsp546-validation 'TASK_{task_num}_{status}' --payload-type=text --project={resolved_project} 2>/dev/null",
                shell=True
            )
        except Exception:
            pass

        print(f"[Activity Tracking Logged] Task {task_num} ({task_id}): {status} (Project: {resolved_project})")
        print("[Tip] Allow 30-60 seconds for Cloud Logging events to index before clicking Check my progress.")
        return True
    except Exception as e:
        print(f"[ERROR] Could not emit Cloud Logging entry: {e}")
        return False

def verify_task_1(project_id=None):
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
    log_event(1, "PASSED", "DiagnosticAgent with session memory verified.", project_id=project_id)
    return True

def verify_task_2(project_id=None):
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
    log_event(2, "PASSED", "Vector Search RAG tool verified.", project_id=project_id)
    return True

def verify_task_3(project_id=None):
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
    log_event(3, "PASSED", "Multi-Agent A2A routing verified.", project_id=project_id)
    return True

def verify_task_4(project_id=None):
    print("Verifying Cloud Run Deployment...")
    resolved_proj = get_project_id(project_id)
    proj_flag = f"--project {resolved_proj}" if resolved_proj else ""
    cmd = f"gcloud run services describe gridcare-agent-service --platform managed --region us-central1 {proj_flag} --format='value(status.url)' 2>/dev/null"
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
        log_event(4, "PASSED", f"Cloud Run service deployed and healthy at {url}.", project_id=project_id)
        return True
    except Exception as e:
        print(f"FAILED: Could not verify Cloud Run service: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="GSP546 Verification Script")
    parser.add_argument("--task", type=int, required=True, choices=[1, 2, 3, 4], help="Task number to verify")
    parser.add_argument("--project", type=str, help="GCP Project ID (optional, auto-detected)")
    args = parser.parse_args()

    if args.task == 1:
        verify_task_1(project_id=args.project)
    elif args.task == 2:
        verify_task_2(project_id=args.project)
    elif args.task == 3:
        verify_task_3(project_id=args.project)
    elif args.task == 4:
        verify_task_4(project_id=args.project)

if __name__ == "__main__":
    main()
