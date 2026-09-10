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
    try:
        res = subprocess.check_output(cmd, shell=True).decode().strip()
        return res
    except Exception:
        return os.environ.get("GOOGLE_CLOUD_PROJECT", "test-project")

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
        logger.log_text(f"TASK_{task_num}_PASSED", severity="INFO")
        print(f"[Activity Tracking Logged] Task {task_num}: {status}")
    except Exception as e:
        print(f"[Notice] Cloud Logging emission: {e}")

def verify_task_1():
    print("Checking Antigravity MCP Configuration...")
    config_paths = [
        os.path.expanduser("~/.gemini/antigravity.json"),
        os.path.expanduser("~/.gemini/mcp_config.json"),
        os.path.expanduser("~/.config/antigravity/mcp_config.json")
    ]
    cfg = None
    matched_path = None
    for cp in config_paths:
        if os.path.exists(cp):
            try:
                with open(cp) as f:
                    cfg = json.load(f)
                matched_path = cp
                break
            except Exception as e:
                print(f"Error reading {cp}: {e}")

    if not cfg:
        print(f"FAILED: No Antigravity MCP configuration found at ~/.gemini/antigravity.json.")
        return False

    mcp_servers = cfg.get("mcpServers", {})
    if "telemetry-db-mcp" not in mcp_servers:
        print("FAILED: Server 'telemetry-db-mcp' not registered in mcpServers.")
        return False

    server_cfg = mcp_servers["telemetry-db-mcp"]
    if "command" not in server_cfg:
        print("FAILED: 'command' field not specified for telemetry-db-mcp.")
        return False

    print(f"SUCCESS: Task 1 verified ({matched_path}).")
    log_event(1, "PASSED", "Antigravity MCP server registered successfully.")
    return True

def verify_task_2():
    print("Checking Custom Skills and Governance Rules...")
    skill_path = os.path.expanduser("~/.gemini/skills/audit-telemetry-fix/SKILL.md")
    rules_path = os.path.expanduser("~/.gemini/rules.md")

    if not os.path.exists(skill_path):
        print(f"FAILED: Custom skill not found at {skill_path}.")
        return False

    if not os.path.exists(rules_path):
        print(f"FAILED: Enterprise rules not found at {rules_path}.")
        return False

    with open(skill_path) as f:
        skill_content = f.read()

    if "name:" not in skill_content or "audit-telemetry-fix" not in skill_content:
        print("FAILED: SKILL.md missing valid YAML frontmatter with 'name: audit-telemetry-fix'.")
        return False

    if "description:" not in skill_content:
        print("FAILED: SKILL.md missing frontmatter 'description'.")
        return False

    with open(rules_path) as f:
        rules_content = f.read()

    if len(rules_content.strip()) < 20:
        print("FAILED: rules.md appears to be empty or insufficient.")
        return False

    print("SUCCESS: Task 2 verified (Custom skill and governance rules created).")
    log_event(2, "PASSED", "Custom skill and rules.md verified.")
    return True

def verify_task_3():
    print("Running Automated Performance & Security Tests (pytest)...")
    res = subprocess.run(["pytest", "tests/"], capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print(res.stderr)

    if res.returncode != 0:
        print("FAILED: One or more pytest assertions failed. Ensure performance and security regressions are resolved.")
        return False

    print("SUCCESS: Task 3 verified (All performance and security tests passed).")
    log_event(3, "PASSED", "All pytest assertions passed.")
    return True

def verify_task_4():
    print("Checking Agents CLI Validation and Package Bundle...")
    manifest_path = "dist/skill-manifest.json"
    archive_path = "dist/audit-telemetry-fix.tar.gz"

    has_manifest = os.path.exists(manifest_path) and os.path.getsize(manifest_path) > 0
    has_archive = os.path.exists(archive_path) and os.path.getsize(archive_path) > 0

    if not has_manifest and not has_archive:
        print("FAILED: Packaged skill distribution bundle not found in dist/. Run 'agents-cli package'.")
        return False

    print("SUCCESS: Task 4 verified (Agents CLI validation and distribution package verified).")
    log_event(4, "PASSED", "Agents CLI validation and distribution package verified.")
    return True

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=int, required=True, choices=[1, 2, 3, 4])
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
