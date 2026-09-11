#!/usr/bin/env python3
"""
Cymbal Solar - Agent Identity & 2-Legged OAuth (2LO) Token Injection Module.

Handles token generation and secure tool execution headers using Google Cloud
Agent Identity service accounts and IAM Credentials token exchange.
"""

import os
import subprocess
from typing import Dict, List, Optional
import google.auth
from google.auth import impersonated_credentials
from google.auth.transport.requests import Request

DEFAULT_SA_ID = "solarops-agent-sa"
REQUIRED_OAUTH_SCOPE = "https://www.googleapis.com/auth/cloud-platform"

def get_project_id() -> str:
    """Retrieve active Google Cloud Project ID."""
    try:
        res = subprocess.check_output("gcloud config get-value project 2>/dev/null", shell=True).decode().strip()
        if res and res != "(unset)":
            return res
    except Exception:
        pass
    return os.environ.get("GOOGLE_CLOUD_PROJECT", "test-project")

def get_agent_service_account_email(project_id: Optional[str] = None) -> str:
    """Returns the fully qualified email of the SolarOps Agent service account."""
    proj = project_id or get_project_id()
    return f"{DEFAULT_SA_ID}@{proj}.iam.gserviceaccount.com"

def generate_2lo_token(target_service_account: str, scopes: Optional[List[str]] = None, lifetime_seconds: int = 3600) -> Dict[str, any]:
    """
    Generate a short-lived OAuth 2.0 access token via 2-legged OAuth (2LO)
    service account token exchange.

    Args:
        target_service_account: Email of the service account to impersonate.
        scopes: List of OAuth scopes. Must include 'https://www.googleapis.com/auth/cloud-platform'.
        lifetime_seconds: Desired token lifetime in seconds (default: 3600).

    Returns:
        Dict containing access_token, token_type, and scopes.

    Raises:
        ValueError: If scopes are missing or invalid.
    """
    # -------------------------------------------------------------------------
    # TODO (Candidate Task 3): Implement 2LO Token Exchange
    # 1. Validate that 'scopes' is provided and contains REQUIRED_OAUTH_SCOPE.
    #    If not, raise ValueError(f"Required scope missing: {REQUIRED_OAUTH_SCOPE}").
    # 2. Obtain base credentials using google.auth.default().
    # 3. Create impersonated credentials using:
    #      impersonated_credentials.Credentials(
    #          source_credentials=source_credentials,
    #          target_principal=target_service_account,
    #          target_scopes=scopes,
    #          lifetime=lifetime_seconds
    #      )
    # 4. Refresh credentials to obtain access token:
    #      creds.refresh(Request())
    # 5. Return dict with keys: 'access_token', 'token_type' ('Bearer'), 'scopes'.
    # -------------------------------------------------------------------------
    
    # === START CANDIDATE IMPLEMENTATION STUB ===
    if not scopes or REQUIRED_OAUTH_SCOPE not in scopes:
        raise ValueError(f"Required scope missing: {REQUIRED_OAUTH_SCOPE}")

    source_credentials, _ = google.auth.default()
    creds = impersonated_credentials.Credentials(
        source_credentials=source_credentials,
        target_principal=target_service_account,
        target_scopes=scopes,
        lifetime=lifetime_seconds
    )
    creds.refresh(Request())

    return {
        "access_token": creds.token,
        "token_type": "Bearer",
        "expires_in": lifetime_seconds,
        "scopes": scopes,
        "target_principal": target_service_account
    }
    # === END CANDIDATE IMPLEMENTATION STUB ===

def create_authorized_tool_headers(project_id: Optional[str] = None, scopes: Optional[List[str]] = None) -> Dict[str, str]:
    """
    Constructs HTTP headers with injected 2LO Bearer token for secure backend tool invocation.
    """
    proj = project_id or get_project_id()
    sa_email = get_agent_service_account_email(proj)
    target_scopes = scopes or [REQUIRED_OAUTH_SCOPE]

    token_data = generate_2lo_token(
        target_service_account=sa_email,
        scopes=target_scopes
    )

    return {
        "Authorization": f"Bearer {token_data['access_token']}",
        "Content-Type": "application/json",
        "X-Agent-Identity": sa_email
    }

def invoke_firmware_override(endpoint_url: str, payload: dict, auth_headers: dict) -> dict:
    """
    Simulated backend tool execution verifying authorization headers.
    Enforces that incoming requests have valid Bearer token and Agent Identity.
    """
    auth_header = auth_headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return {
            "status_code": 401,
            "error": "Unauthorized: Missing or malformed Bearer token."
        }

    token = auth_header.split("Bearer ")[1].strip()
    if not token or len(token) < 10:
        return {
            "status_code": 401,
            "error": "Unauthorized: Invalid access token."
        }

    return {
        "status_code": 200,
        "message": "Firmware override executed successfully.",
        "payload_received": payload,
        "authenticated_principal": auth_headers.get("X-Agent-Identity", "unknown")
    }

if __name__ == "__main__":
    import json
    proj = get_project_id()
    print(f"Testing 2LO Token Exchange for project: {proj}...")
    try:
        headers = create_authorized_tool_headers(proj)
        print(f"Successfully generated 2LO auth headers for: {headers.get('X-Agent-Identity')}")
        print("Authorization Header:", headers.get("Authorization")[:25] + "...")
    except Exception as ex:
        print(f"Token generation error: {ex}")
