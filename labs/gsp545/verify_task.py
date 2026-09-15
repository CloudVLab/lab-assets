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
import shutil
try:
    from google.cloud import logging as cloud_logging
    HAS_LOGGING = True
except ImportError:
    HAS_LOGGING = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_project_id(cli_project=None):
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
    if not HAS_LOGGING:
        return False
    try:
        resolved_project = get_project_id(project_id)
        if not resolved_project:
            print("[ERROR] Cloud Logging skipped: Could not resolve Google Cloud Project ID.")
            print("Please run 'gcloud config set project <PROJECT_ID>' or re-run with '--project <PROJECT_ID>'.")
            return False

        client = cloud_logging.Client(project=resolved_project)
        logger = client.logger("gsp545-validation")
        payload = {
            "task": f"task{task_num}",
            f"step_{task_num}": status,
            "details": details
        }
        logger.log_struct(payload, severity="INFO")
        logger.log_text(f"TASK_{task_num}_PASSED", severity="INFO")
        print(f"[Activity Tracking Logged] Task {task_num}: {status} (Project: {resolved_project})")
        print("[Tip] Wait up to 1 minute before clicking Check my progress in the lab console to allow Cloud Logging events to index.")
        return True
    except Exception as e:
        print(f"[ERROR] Cloud Logging emission failed: {e}")
        return False

def verify_task_1(project_id=None):
    print("Checking Antigravity Workspace, MCP Configuration, and Extension Hooks...")
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
        print(f"FAILED: No Antigravity configuration found at ~/.gemini/antigravity.json.")
        return False

    # 1. MCP Server Check
    mcp_servers = cfg.get("mcpServers", {})
    if "telemetry-db-mcp" not in mcp_servers:
        print("FAILED: Server 'telemetry-db-mcp' not registered in mcpServers.")
        return False

    server_cfg = mcp_servers["telemetry-db-mcp"]
    if "command" not in server_cfg:
        print("FAILED: 'command' field not specified for telemetry-db-mcp.")
        return False

    args = server_cfg.get("args", [])
    if not args or not isinstance(args, list):
        print("FAILED: 'args' field not specified as a list for telemetry-db-mcp.")
        return False

    server_script = None
    for a in args:
        expanded = os.path.expandvars(os.path.expanduser(a))
        if os.path.isfile(expanded) and expanded.endswith("mcp_server.py"):
            server_script = expanded
            break

    if not server_script:
        print(f"FAILED: 'args' does not contain a valid path to an existing mcp_server.py file. Given: {args}")
        return False

    # Test tool discovery via stdio JSON-RPC
    try:
        resolved_cmd = [server_cfg["command"]] + [os.path.expandvars(os.path.expanduser(a)) for a in args]
        proc = subprocess.run(
            resolved_cmd,
            input=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}).encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10
        )
        if proc.returncode != 0:
            print(f"FAILED: MCP server execution failed with return code {proc.returncode}: {proc.stderr.decode()}")
            return False
        response = json.loads(proc.stdout.decode())
        tools = [t.get("name") for t in response.get("result", {}).get("tools", [])]
        if "query_telemetry_schema" not in tools or "inspect_error_logs" not in tools:
            print(f"FAILED: MCP server does not expose required tools. Found: {tools}")
            return False
    except Exception as e:
        print(f"FAILED: Could not test MCP server tools/list: {e}")
        return False

    # 2. Extension Hook Check
    hooks = cfg.get("hooks", {})
    hook_path = hooks.get("pre_tool_call")
    if not hook_path:
        print("FAILED: Missing 'pre_tool_call' extension hook configuration under 'hooks' in antigravity.json.")
        return False

    expanded_hook = os.path.expandvars(os.path.expanduser(hook_path))
    if not os.path.exists(expanded_hook):
        print(f"FAILED: Extension hook script not found at {expanded_hook}.")
        return False

    if os.path.getsize(expanded_hook) < 20:
        print(f"FAILED: Extension hook script at {expanded_hook} appears empty.")
        return False

    # Test sandbox extension hook interception behavior
    try:
        unsafe_payload = "SELECT * FROM error_logs WHERE device_id = 'test' OR '1'='1'"
        hook_res = subprocess.run(
            [sys.executable, expanded_hook, unsafe_payload],
            capture_output=True,
            text=True,
            timeout=5
        )
        if hook_res.returncode == 0:
            print("FAILED: Extension hook query_guard.py did not block unsafe SQL injection pattern (expected non-zero exit code).")
            return False

        safe_payload = "SELECT * FROM error_logs WHERE device_id = ?"
        safe_res = subprocess.run(
            [sys.executable, expanded_hook, safe_payload],
            capture_output=True,
            text=True,
            timeout=5
        )
        if safe_res.returncode != 0:
            print("FAILED: Extension hook query_guard.py blocked safe parameterized query (expected exit code 0).")
            return False
    except Exception as e:
        print(f"FAILED: Error testing extension hook execution: {e}")
        return False

    print(f"SUCCESS: Task 1 verified ({matched_path} with MCP server and extension hook).")
    log_event(1, "PASSED", "Antigravity MCP server and extension hook registered successfully.", project_id=project_id)
    return True


def verify_task_2(project_id=None):
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
    log_event(2, "PASSED", "Custom skill and rules.md verified.", project_id=project_id)
    return True

def verify_task_3(project_id=None):
    print("Verifying Antigravity Subagent Execution and Automated Tests...")

    # 1. Verify Subagent Execution Trace
    trace_path = os.path.expanduser("~/.gemini/agent_trace.json")
    if not os.path.exists(trace_path):
        print("FAILED: Subagent execution trace not found at ~/.gemini/agent_trace.json.")
        print("Ensure you executed: agents-cli subagent run --skill audit-telemetry-fix --rules ~/.gemini/rules.md ...")
        return False

    try:
        with open(trace_path, "r", encoding="utf-8") as f:
            trace = json.load(f)
        if trace.get("skill") != "audit-telemetry-fix":
            print(f"FAILED: Trace indicates unexpected skill '{trace.get('skill')}'. Expected 'audit-telemetry-fix'.")
            return False
        if trace.get("test_verification", {}).get("status") != "PASSED":
            print(f"FAILED: Subagent execution trace indicates test failures: {trace.get('test_verification')}")
            return False
    except Exception as e:
        print(f"FAILED: Could not parse ~/.gemini/agent_trace.json: {e}")
        return False

    # 2. Run Automated Pytest
    print("Running Automated Performance & Security Tests (pytest)...")
    pytest_bin = "pytest"
    venv_pytest = os.path.join(BASE_DIR, "venv", "bin", "pytest")
    if not shutil.which("pytest") and os.path.exists(venv_pytest):
        pytest_bin = venv_pytest

    if shutil.which(pytest_bin):
        res = subprocess.run([pytest_bin, os.path.join(BASE_DIR, "tests")], cwd=BASE_DIR, capture_output=True, text=True)
        print(res.stdout)
        if res.stderr:
            print(res.stderr)
        if res.returncode != 0:
            print("FAILED: One or more pytest assertions failed. Ensure performance and security regressions are resolved.")
            return False
    else:
        print("  [Notice] pytest not on PATH; running in-process test verification fallback...")
        try:
            import pytest
        except ImportError:
            class MockPytest:
                @staticmethod
                def fixture(*args, **kwargs):
                    def decorator(fn):
                        return fn
                    return decorator
                @staticmethod
                def fail(msg):
                    raise AssertionError(msg)
            sys.modules["pytest"] = MockPytest()
        sys.path.insert(0, BASE_DIR)
        try:
            from tests.test_performance import test_telemetry_batch_performance
            from tests.test_security import setup_test_db, test_sql_injection_defense, test_log_error_event_injection_defense
            setup_test_db()
            test_telemetry_batch_performance()
            test_sql_injection_defense()
            test_log_error_event_injection_defense()
            print("  [PASS] All 3 performance and security assertions passed in-process.")
        except Exception as e:
            print(f"FAILED: In-process test verification failed: {e}")
            return False

    print("SUCCESS: Task 3 verified (Subagent execution trace and all pytest assertions passed).")
    log_event(3, "PASSED", "Subagent execution trace verified and all pytest assertions passed.", project_id=project_id)
    return True

def verify_task_4(project_id=None):
    print("Checking Agents CLI Validation, Evaluation Report, and Package Bundle...")
    manifest_path = os.path.join(BASE_DIR, "dist", "skill-manifest.json")
    archive_path = os.path.join(BASE_DIR, "dist", "audit-telemetry-fix.tar.gz")
    eval_report_path = os.path.join(BASE_DIR, "dist", "eval_report.json")
    benchmark_path = os.path.join(BASE_DIR, "tests", "eval_benchmark.json")

    # 1. Benchmark Configuration Check
    if not os.path.exists(benchmark_path):
        print(f"FAILED: Benchmark configuration not found at {benchmark_path}.")
        return False

    try:
        with open(benchmark_path, "r", encoding="utf-8") as f:
            b_cfg = json.load(f)
        lat_thresh = b_cfg.get("benchmarks", {}).get("latency", {}).get("max_threshold_seconds")
        sec_param = b_cfg.get("benchmarks", {}).get("security", {}).get("required_parameterization")
        sec_vulns = b_cfg.get("benchmarks", {}).get("security", {}).get("max_vulnerabilities")
        hook_guard = b_cfg.get("benchmarks", {}).get("extension_hooks", {}).get("guard_active")

        if lat_thresh is None or lat_thresh > 0.25:
            print(f"FAILED: tests/eval_benchmark.json latency threshold must be <= 0.25s (found: {lat_thresh}).")
            return False
        if sec_param is not True or sec_vulns != 0:
            print("FAILED: tests/eval_benchmark.json security benchmark must specify required_parameterization: true and max_vulnerabilities: 0.")
            return False
        if hook_guard is not True:
            print("FAILED: tests/eval_benchmark.json extension_hooks benchmark must specify guard_active: true.")
            return False
    except Exception as e:
        print(f"FAILED: Could not parse tests/eval_benchmark.json: {e}")
        return False

    # 2. Evaluation Report Check
    if not os.path.exists(eval_report_path) or os.path.getsize(eval_report_path) == 0:
        print("FAILED: Evaluation report not found at dist/eval_report.json. Run 'agents-cli eval run'.")
        return False

    try:
        with open(eval_report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
        if report.get("status") != "PASSED":
            print(f"FAILED: Evaluation report status is '{report.get('status')}'. Expected 'PASSED'.")
            return False
        if report.get("score") != 100.0:
            print(f"FAILED: Evaluation report score is {report.get('score')}. Expected 100.0.")
            return False
    except Exception as e:
        print(f"FAILED: Could not parse eval_report.json: {e}")
        return False

    # 3. Distribution Bundle Check
    has_manifest = os.path.exists(manifest_path) and os.path.getsize(manifest_path) > 0
    has_archive = os.path.exists(archive_path) and os.path.getsize(archive_path) > 0

    if not has_manifest and not has_archive:
        print("FAILED: Packaged skill distribution bundle not found in dist/. Run 'agents-cli package'.")
        return False

    print("SUCCESS: Task 4 verified (Agents CLI evaluation report and distribution package verified).")
    log_event(4, "PASSED", "Agents CLI evaluation report and distribution package verified.", project_id=project_id)
    return True

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=int, required=True, choices=[1, 2, 3, 4])
    parser.add_argument("--project", help="Google Cloud project ID (optional override)")
    args = parser.parse_args()

    if args.task == 1:
        success = verify_task_1(project_id=args.project)
    elif args.task == 2:
        success = verify_task_2(project_id=args.project)
    elif args.task == 3:
        success = verify_task_3(project_id=args.project)
    elif args.task == 4:
        success = verify_task_4(project_id=args.project)

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
