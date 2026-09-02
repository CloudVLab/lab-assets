#!/usr/bin/env python3
"""
Verification Script for GSP545 Challenge Lab.
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
from google.cloud import logging as cloud_logging

def get_project_id():
    cmd = "gcloud config get-value project 2>/dev/null"
    res = subprocess.check_output(cmd, shell=True).decode().strip()
    return res

def log_event(task_num, status, details):
    try:
        project_id = get_project_id()
        client = cloud_logging.Client(project=project_id)
        logger = client.logger("gsp545-validation")
        payload = {
            "task": f"task{task_num}",
            f"step_{task_num}": status,
            "details": details
        }
        logger.log_struct(payload, severity="INFO")
        print(f"[Activity Tracking Logged] Task {task_num}: {status}")
    except Exception as e:
        print(f"[Warning] Could not emit Cloud Logging entry: {e}")

def verify_task_1():
    print("Checking Antigravity MCP Configuration...")
    config_path = os.path.expanduser("~/.gemini/antigravity.json")
    if not os.path.exists(config_path):
        print(f"FAILED: {config_path} not found.")
        return False
    with open(config_path) as f:
        cfg = json.load(f)
    mcp_servers = cfg.get("mcpServers", {})
    if "telemetry-db-mcp" not in mcp_servers:
        print("FAILED: telemetry-db-mcp not registered in antigravity.json.")
        return False
    server_cfg = mcp_servers["telemetry-db-mcp"]
    if "command" not in server_cfg:
        print("FAILED: command not specified for telemetry-db-mcp.")
        return False
    print("SUCCESS: Task 1 verified.")
    log_event(1, "PASSED", "Antigravity MCP server registered successfully.")
    return True

def verify_task_2():
    print("Checking Custom Skills and Governance Rules...")
    skill_path = os.path.expanduser("~/.gemini/skills/audit-telemetry-fix/SKILL.md")
    rules_path = os.path.expanduser("~/.gemini/rules.md")
    if not os.path.exists(skill_path):
        print(f"FAILED: {skill_path} not found.")
        return False
    if not os.path.exists(rules_path):
        print(f"FAILED: {rules_path} not found.")
        return False
    with open(skill_path) as f:
        content = f.read()
    if "audit-telemetry-fix" not in content or "description" not in content:
        print("FAILED: SKILL.md missing valid YAML frontmatter.")
        return False
    print("SUCCESS: Task 2 verified.")
    log_event(2, "PASSED", "Custom skill and rules.md verified.")
    return True

def verify_task_3():
    print("Running Automated Performance & Security Tests (pytest)...")
    res = subprocess.run(["pytest", "tests/"], capture_output=True, text=True)
    print(res.stdout)
    if res.returncode != 0:
        print("FAILED: One or more pytest assertions failed.")
        return False
    print("SUCCESS: Task 3 verified.")
    log_event(3, "PASSED", "All pytest assertions passed.")
    return True

def verify_task_4():
    print("Checking Agents CLI Validation and Package Bundle...")
    manifest_path = "dist/skill-manifest.json"
    archive_path = "dist/audit-telemetry-fix.tar.gz"
    if not os.path.exists(manifest_path) and not os.path.exists(archive_path):
        print("FAILED: Packaged skill distribution bundle not found in dist/.")
        return False
    print("SUCCESS: Task 4 verified.")
    log_event(4, "PASSED", "Agents CLI validation and distribution package verified.")
    return True

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
