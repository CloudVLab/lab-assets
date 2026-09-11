#!/usr/bin/env python3
"""
Cymbal Solar - Human-in-the-Loop (HITL) Execution Guardrail Module.

Enforces deterministic safety controls, policy gates, and human approval
requirements for high-risk grid operations and emergency cutoffs.
"""

import uuid
from typing import Dict, Any, Optional

# High-risk actions that cannot be executed autonomously without human sign-off
HIGH_RISK_ACTIONS = {
    "grid_disconnect",
    "emergency_power_cutoff",
    "emergency_shutdown",
    "firmware_override"
}

# Operational thresholds requiring human intervention
MAX_AUTONOMOUS_VOLTAGE = 1000  # Volts
MAX_AUTONOMOUS_TEMP_CELSIUS = 50.0  # Celsius

VALID_APPROVAL_PREFIXES = ("CYMBAL-SUPERVISOR-", "AUTH-HUMAN-")

def evaluate_action_safety(action_name: str, parameters: Optional[Dict[str, Any]] = None, approval_token: Optional[str] = None) -> Dict[str, Any]:
    """
    Evaluates whether an agent action is safe for autonomous execution or
    requires Human-in-the-Loop (HITL) supervisor authorization.

    Args:
        action_name: Name of the operational command/tool.
        parameters: Command parameters (e.g., voltage, temperature).
        approval_token: Optional supervisor approval token string.

    Returns:
        Dict detailing the safety evaluation and authorization status.
    """
    params = parameters or {}

    # -------------------------------------------------------------------------
    # TODO (Candidate Task 4): Implement HITL Safety Guardrails
    # 1. Determine if the requested action is high-risk:
    #    - action_name is in HIGH_RISK_ACTIONS
    #    - action_name == "voltage_boost" and params.get("voltage", 0) > MAX_AUTONOMOUS_VOLTAGE
    #    - params.get("inverter_temp_celsius", 0) > MAX_AUTONOMOUS_TEMP_CELSIUS
    #    - params.get("temperature", 0) > MAX_AUTONOMOUS_TEMP_CELSIUS
    # 2. If high-risk:
    #    - Verify if 'approval_token' is present and starts with any of VALID_APPROVAL_PREFIXES.
    #    - If valid, return status "APPROVED" with decision "EXECUTE_APPROVED".
    #    - If invalid or missing, HALT execution and return status "REQUIRES_HUMAN_APPROVAL".
    # 3. If NOT high-risk:
    #    - Return status "ALLOWED" with decision "EXECUTE_AUTONOMOUS".
    # -------------------------------------------------------------------------

    # === START CANDIDATE IMPLEMENTATION STUB ===
    is_high_risk = False
    reasons = []

    if action_name in HIGH_RISK_ACTIONS:
        is_high_risk = True
        reasons.append(f"Action '{action_name}' is classified as HIGH_RISK")

    voltage = params.get("voltage", 0)
    if action_name == "voltage_boost" and voltage > MAX_AUTONOMOUS_VOLTAGE:
        is_high_risk = True
        reasons.append(f"Requested voltage {voltage}V exceeds autonomous threshold of {MAX_AUTONOMOUS_VOLTAGE}V")

    temp = params.get("inverter_temp_celsius", params.get("temperature", 0))
    if temp > MAX_AUTONOMOUS_TEMP_CELSIUS:
        is_high_risk = True
        reasons.append(f"Inverter temperature {temp}°C exceeds safety threshold of {MAX_AUTONOMOUS_TEMP_CELSIUS}°C")

    if is_high_risk:
        if approval_token and any(approval_token.startswith(p) for p in VALID_APPROVAL_PREFIXES):
            return {
                "status": "APPROVED",
                "decision": "EXECUTE_APPROVED",
                "action": action_name,
                "approval_token": approval_token,
                "authorized_by": "GRID_OPERATIONS_SUPERVISOR",
                "reasons": reasons
            }
        else:
            pending_token = f"PENDING-APPROVAL-{uuid.uuid4().hex[:8].upper()}"
            return {
                "status": "REQUIRES_HUMAN_APPROVAL",
                "decision": "BLOCKED_PENDING_APPROVAL",
                "action": action_name,
                "reasons": reasons,
                "approval_pending": True,
                "required_role": "GRID_OPERATIONS_SUPERVISOR",
                "pending_approval_token": pending_token
            }

    return {
        "status": "ALLOWED",
        "decision": "EXECUTE_AUTONOMOUS",
        "action": action_name,
        "parameters": params
    }
    # === END CANDIDATE IMPLEMENTATION STUB ===

if __name__ == "__main__":
    print("Testing HITL Guardrail...")
    # Test 1: Read telemetry (should pass autonomously)
    t1 = evaluate_action_safety("read_telemetry", {"inverter_id": "INV-101"})
    print("Test 1 (Read Telemetry):", t1["status"])

    # Test 2: Grid disconnect without token (should require approval)
    t2 = evaluate_action_safety("grid_disconnect", {"inverter_id": "INV-101"})
    print("Test 2 (Grid Disconnect, No Token):", t2["status"], "-", t2.get("decision"))

    # Test 3: Grid disconnect with supervisor token (should be approved)
    t3 = evaluate_action_safety("grid_disconnect", {"inverter_id": "INV-101"}, approval_token="CYMBAL-SUPERVISOR-98765")
    print("Test 3 (Grid Disconnect, Supervisor Token):", t3["status"], "-", t3.get("decision"))
