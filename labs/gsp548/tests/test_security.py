#!/usr/bin/env python3
"""
Cymbal Solar - Security, Governance, and Guardrail Test Suite.

Automated verification for:
1. Model Armor prompt injection protection
2. Cloud DLP / SDP PII de-identification
3. Agent Identity & 2LO OAuth token injection
4. Human-in-the-Loop (HITL) safety policy gates
"""

import os
import sys
import unittest

# Ensure starter is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent.security import (
    generate_2lo_token,
    create_authorized_tool_headers,
    invoke_firmware_override,
    REQUIRED_OAUTH_SCOPE
)
from agent.control_guard import (
    evaluate_action_safety,
    HIGH_RISK_ACTIONS,
    MAX_AUTONOMOUS_VOLTAGE,
    MAX_AUTONOMOUS_TEMP_CELSIUS
)
from agent.dlp_masker import mask_text_with_dlp_template
from scripts.red_team_exploit import ADVERSARIAL_PAYLOADS


class TestModelArmorPolicy(unittest.TestCase):
    """Verifies Model Armor adversarial testing harness structure."""

    def test_red_team_payload_registry(self):
        self.assertGreaterEqual(len(ADVERSARIAL_PAYLOADS), 3)
        ids = [p["id"] for p in ADVERSARIAL_PAYLOADS]
        self.assertIn("EXPLOIT-01-DIRECT-INJECTION", ids)
        self.assertIn("EXPLOIT-02-JAILBREAK-ROLEPLAY", ids)
        self.assertIn("EXPLOIT-03-CREDENTIAL-EXFILTRATION", ids)

    def test_red_team_payload_content(self):
        for payload in ADVERSARIAL_PAYLOADS:
            self.assertGreater(len(payload["prompt"]), 20)
            has_trigger = (
                "SYSTEM OVERRIDE" in payload["prompt"] or
                "DAN" in payload["prompt"] or
                "Ignore" in payload["prompt"]
            )
            self.assertTrue(has_trigger)


class TestSensitiveDataProtection(unittest.TestCase):
    """Verifies Cloud DLP PII masking and redaction."""

    def test_ssn_masking(self):
        input_text = "Customer profile: Alice Smith, SSN: 123-45-6789."
        masked = mask_text_with_dlp_template(input_text)
        self.assertNotIn("123-45-6789", masked)
        self.assertTrue("***-**-6789" in masked or "******6789" in masked or "*" in masked)

    def test_credit_card_masking(self):
        input_text = "Billing payment card: 4111 2222 3333 4444 on file."
        masked = mask_text_with_dlp_template(input_text)
        self.assertNotIn("4111 2222 3333 4444", masked)
        self.assertIn("4444", masked)

    def test_mixed_pii_masking(self):
        input_text = "Contact: tech-lead@cymbalsolar.internal, phone: 555-019-2834, ssn: 987-65-4321."
        masked = mask_text_with_dlp_template(input_text)
        self.assertNotIn("987-65-4321", masked)


class TestAgentIdentityAndOAuth(unittest.TestCase):
    """Verifies Agent Identity 2LO OAuth token exchange and security headers."""

    def test_missing_scope_raises_error(self):
        with self.assertRaises(ValueError) as ctx:
            generate_2lo_token("solarops-agent-sa@test-project.iam.gserviceaccount.com", scopes=[])
        self.assertIn("Required scope missing", str(ctx.exception))

    def test_invalid_scope_raises_error(self):
        with self.assertRaises(ValueError) as ctx:
            generate_2lo_token("solarops-agent-sa@test-project.iam.gserviceaccount.com", scopes=["https://www.googleapis.com/auth/userinfo.email"])
        self.assertIn("Required scope missing", str(ctx.exception))

    def test_backend_tool_rejects_missing_auth(self):
        res = invoke_firmware_override("https://firmware.internal/override", {"command": "reset"}, {})
        self.assertEqual(res["status_code"], 401)
        self.assertIn("Missing or malformed Bearer token", res["error"])

    def test_backend_tool_accepts_valid_auth(self):
        mock_headers = {
            "Authorization": "Bearer mock_valid_access_token_cymbal_solarops",
            "X-Agent-Identity": "solarops-agent-sa@test-project.iam.gserviceaccount.com"
        }
        res = invoke_firmware_override("https://firmware.internal/override", {"voltage": 800}, mock_headers)
        self.assertEqual(res["status_code"], 200)
        self.assertEqual(res["message"], "Firmware override executed successfully.")


class TestHumanInTheLoopSafetyGuardrails(unittest.TestCase):
    """Verifies HITL authorization policy gates for high-risk operations."""

    def test_autonomous_action_allowed(self):
        res = evaluate_action_safety("read_telemetry", {"inverter_id": "INV-A100"})
        self.assertEqual(res["status"], "ALLOWED")
        self.assertEqual(res["decision"], "EXECUTE_AUTONOMOUS")

    def test_grid_disconnect_blocks_without_token(self):
        res = evaluate_action_safety("grid_disconnect", {"inverter_id": "INV-A100"})
        self.assertEqual(res["status"], "REQUIRES_HUMAN_APPROVAL")
        self.assertEqual(res["decision"], "BLOCKED_PENDING_APPROVAL")
        self.assertTrue(res["approval_pending"])
        self.assertEqual(res["required_role"], "GRID_OPERATIONS_SUPERVISOR")
        self.assertIn("pending_approval_token", res)

    def test_high_voltage_blocks_without_token(self):
        res = evaluate_action_safety("voltage_boost", {"voltage": 1200})
        self.assertEqual(res["status"], "REQUIRES_HUMAN_APPROVAL")
        self.assertEqual(res["decision"], "BLOCKED_PENDING_APPROVAL")

    def test_high_temperature_cutoff_blocks_without_token(self):
        res = evaluate_action_safety("emergency_power_cutoff", {"temperature": 55.5})
        self.assertEqual(res["status"], "REQUIRES_HUMAN_APPROVAL")
        self.assertEqual(res["decision"], "BLOCKED_PENDING_APPROVAL")

    def test_grid_disconnect_approved_with_valid_token(self):
        token = "CYMBAL-SUPERVISOR-SEC-998811"
        res = evaluate_action_safety("grid_disconnect", {"inverter_id": "INV-A100"}, approval_token=token)
        self.assertEqual(res["status"], "APPROVED")
        self.assertEqual(res["decision"], "EXECUTE_APPROVED")
        self.assertEqual(res["authorized_by"], "GRID_OPERATIONS_SUPERVISOR")
        self.assertEqual(res["approval_token"], token)


if __name__ == "__main__":
    unittest.main()
