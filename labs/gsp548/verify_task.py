#!/usr/bin/env python3
"""
Verification Script for GSP548 Challenge Lab:
Secure Agent Tool Execution, Identity, and Workload Guardrails.

Usage:
  python3 verify_task.py --task 1
  python3 verify_task.py --task 2
  python3 verify_task.py --task 3
  python3 verify_task.py --task 4
"""

import sys
import os
import json
import subprocess
import argparse

LOG_NAME = "gsp548-validation"

def get_project_id():
    """Retrieve active Google Cloud Project ID."""
    cmd = "gcloud config get-value project 2>/dev/null"
    try:
        res = subprocess.check_output(cmd, shell=True).decode().strip()
        if res and res != "(unset)":
            return res
    except Exception:
        pass
    return os.environ.get("GOOGLE_CLOUD_PROJECT", "test-project")

def log_event(task_num: int, status: str, details: str):
    """Emit dual-mode validation telemetry to Cloud Logging."""
    if os.environ.get("SKIP_CLOUD_LOGGING", "").lower() in ("true", "1", "yes"):
        print(f"[Activity Tracking Simulated] Task {task_num}: {status}")
        return

    try:
        from google.cloud import logging as cloud_logging
        project_id = get_project_id()
        client = cloud_logging.Client(project=project_id)
        logger = client.logger(LOG_NAME)
        payload = {
            "task": f"task{task_num}",
            f"step_{task_num}": status,
            "details": details
        }
        logger.log_struct(payload, severity="INFO")
        logger.log_text(f"TASK_{task_num}_PASSED", severity="INFO")
        print(f"[Activity Tracking Logged] Task {task_num}: {status}")
    except Exception as e:
        print(f"[Notice] Cloud Logging emission: {e}")

def run_cmd(cmd_list, timeout=20):
    """Helper to run a shell command and return stdout, stderr, and returncode."""
    try:
        res = subprocess.run(cmd_list, capture_output=True, text=True, timeout=timeout)
        return res.returncode, res.stdout, res.stderr
    except Exception as e:
        return 1, "", str(e)

def verify_task_1():
    print("Checking Model Armor and Cloud DLP Templates...")
    project_id = get_project_id()

    # 1. Check Model Armor template: cymbal-solar-agent-armor
    location = os.environ.get("REGION", "us-central1")
    print(f"Checking Model Armor template 'cymbal-solar-agent-armor' in project {project_id} (location: {location})...")
    cmd_ma = [
        "gcloud", "model-armor", "templates", "describe",
        "cymbal-solar-agent-armor",
        f"--location={location}",
        "--format=json"
    ]
    rc, stdout, stderr = run_cmd(cmd_ma)
    if rc != 0 and location != "us-central1":
        # Try us-central1 location fallback
        cmd_ma_uc1 = [
            "gcloud", "model-armor", "templates", "describe",
            "cymbal-solar-agent-armor",
            "--location=us-central1",
            "--format=json"
        ]
        rc, stdout, stderr = run_cmd(cmd_ma_uc1)

    if rc != 0:
        print("FAILED: Model Armor template 'cymbal-solar-agent-armor' not found.")
        print(f"Hint: Create the template using 'gcloud model-armor templates create cymbal-solar-agent-armor --location={location} ...'")
        return False

    print("Model Armor template 'cymbal-solar-agent-armor' verified.")

    # 2. Check Cloud DLP de-identification template: solarops-pii-mask-template
    print("Checking Cloud DLP de-identification template 'solarops-pii-mask-template'...")
    cmd_dlp = [
        "gcloud", "dlp", "deidentify-templates", "describe",
        "solarops-pii-mask-template",
        f"--location={location}",
        "--format=json"
    ]
    rc_dlp, stdout_dlp, stderr_dlp = run_cmd(cmd_dlp)
    if rc_dlp != 0:
        # Try global or default location
        cmd_dlp_global = [
            "gcloud", "dlp", "deidentify-templates", "describe",
            "solarops-pii-mask-template",
            "--format=json"
        ]
        rc_dlp, stdout_dlp, stderr_dlp = run_cmd(cmd_dlp_global)

    if rc_dlp != 0:
        print("FAILED: Cloud DLP de-identification template 'solarops-pii-mask-template' not found.")
        print("Hint: Create the template using 'gcloud dlp deidentify-templates create ...'")
        return False

    print("Cloud DLP de-identification template 'solarops-pii-mask-template' verified.")
    print("SUCCESS: Task 1 verified (Model Armor and Cloud DLP templates created).")
    log_event(1, "PASSED", "Model Armor and Cloud DLP templates successfully verified.")
    return True

def verify_task_2():
    print("Running Red-Team Adversarial Penetration Test against Model Armor...")
    script_path = os.path.join(os.path.dirname(__file__), "scripts", "red_team_exploit.py")
    if not os.path.exists(script_path):
        script_path = "scripts/red_team_exploit.py"

    if not os.path.exists(script_path):
        print(f"FAILED: Red-team exploit script not found at {script_path}.")
        return False

    rc, stdout, stderr = run_cmd(["python3", script_path], timeout=60)
    print(stdout)
    if stderr:
        print(stderr)

    if rc != 0:
        print("FAILED: Red-team exploit was NOT neutralized. One or more attacks bypassed Model Armor.")
        print("Hint: Update 'cymbal-solar-agent-armor' filter confidence threshold to LOW_AND_ABOVE.")
        return False

    print("SUCCESS: Task 2 verified (Model Armor filter threshold hardened and exploit neutralized).")
    log_event(2, "PASSED", "Model Armor filter threshold hardened and prompt injections blocked.")
    return True

def verify_task_3():
    print("Checking Agent Identity and 2LO OAuth Token Injection...")
    project_id = get_project_id()
    sa_email = f"solarops-agent-sa@{project_id}.iam.gserviceaccount.com"

    # Check SA exists
    cmd_sa = ["gcloud", "iam", "service-accounts", "describe", sa_email, "--format=json"]
    rc, stdout, stderr = run_cmd(cmd_sa)
    if rc != 0:
        print(f"FAILED: Service Account '{sa_email}' not found.")
        return False

    # Execute unit test for Agent Identity & 2LO OAuth
    test_file = os.path.join(os.path.dirname(__file__), "tests", "test_security.py")
    if not os.path.exists(test_file):
        test_file = "tests/test_security.py"

    rc_test, stdout_test, stderr_test = run_cmd([
        "python3", "-m", "unittest",
        "tests.test_security.TestAgentIdentityAndOAuth"
    ])
    if rc_test != 0:
        # Try direct invocation
        rc_test, stdout_test, stderr_test = run_cmd(["python3", test_file])

    if rc_test != 0:
        print(stdout_test)
        print(stderr_test)
        print("FAILED: 2-legged OAuth token generation tests failed. Check agent/security.py implementation.")
        return False

    print("SUCCESS: Task 3 verified (Agent Identity & 2LO OAuth token exchange verified).")
    log_event(3, "PASSED", "Agent Identity and 2LO OAuth token injection verified.")
    return True

def verify_task_4():
    print("Running Full Security, HITL Guardrails, and Governance Test Suite...")
    test_file = os.path.join(os.path.dirname(__file__), "tests", "test_security.py")
    if not os.path.exists(test_file):
        test_file = "tests/test_security.py"

    rc, stdout, stderr = run_cmd(["python3", test_file])
    print(stdout)
    if stderr:
        print(stderr)

    if rc != 0:
        print("FAILED: Security test suite failed. Ensure HITL guardrails in agent/control_guard.py are implemented.")
        return False

    print("SUCCESS: Task 4 verified (HITL safety guardrails and full security suite passed).")
    log_event(4, "PASSED", "Human-in-the-Loop safety controls and security suite verified.")
    return True

def main():
    parser = argparse.ArgumentParser(description="GSP548 Student Verification CLI")
    parser.add_argument("--task", type=int, required=True, choices=[1, 2, 3, 4], help="Task number to verify")
    args = parser.parse_args()

    if args.task == 1:
        success = verify_task_1()
    elif args.task == 2:
        success = verify_task_2()
    elif args.task == 3:
        success = verify_task_3()
    elif args.task == 4:
        success = verify_task_4()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
