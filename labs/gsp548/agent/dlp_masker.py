#!/usr/bin/env python3
"""
Cymbal Solar - Sensitive Data Protection (Cloud DLP) Masking Utility.

Interacts with Google Cloud DLP API and the 'solarops-pii-mask-template'
de-identification template to sanitize customer logs and agent contexts.
"""

import re
import os
import subprocess
from typing import Optional

def get_project_id() -> str:
    """Retrieve active Google Cloud Project ID."""
    try:
        res = subprocess.check_output("gcloud config get-value project 2>/dev/null", shell=True).decode().strip()
        if res and res != "(unset)":
            return res
    except Exception:
        pass
    return os.environ.get("GOOGLE_CLOUD_PROJECT", "test-project")

def mask_text_with_dlp_template(text: str, project_id: Optional[str] = None, template_id: str = "solarops-pii-mask-template", location: Optional[str] = None) -> str:
    """
    De-identifies sensitive data in text using Cloud DLP de-identification template.
    Falls back to deterministic masking patterns if offline or testing locally.
    """
    proj = project_id or get_project_id()
    loc = location or os.environ.get("REGION", "us-central1")
    template_name = f"projects/{proj}/locations/{loc}/deidentifyTemplates/{template_id}"

    try:
        from google.cloud import dlp_v2
        client = dlp_v2.DlpServiceClient()
        parent = f"projects/{proj}/locations/{loc}"

        item = {"value": text}
        response = client.deidentify_content(
            request={
                "parent": parent,
                "deidentify_template_name": template_name,
                "item": item
            }
        )
        return response.item.value
    except Exception:
        # Fallback local regex masking for offline testing and validation
        # Mask SSN: 123-45-6789 -> ***-**-6789
        masked = re.sub(r'\b\d{3}-\d{2}-(\d{4})\b', r'***-**-\1', text)
        # Mask Credit Cards: 4111 2222 3333 4444 -> ************4444
        masked = re.sub(r'\b(?:\d[ -]*?){13,16}\b', lambda m: '*' * (len(re.sub(r'\D', '', m.group(0))) - 4) + re.sub(r'\D', '', m.group(0))[-4:], masked)
        # Mask Email: student@example.com -> s***t@example.com
        masked = re.sub(r'([a-zA-Z0-9_.+-])[a-zA-Z0-9_.+-]*([a-zA-Z0-9_.+-])@([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', r'\1***\2@\3', masked)
        # Mask Phone: 555-123-4567 -> ***-***-4567
        masked = re.sub(r'\b(?:\+?1[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?(\d{4})\b', r'***-***-\1', masked)
        return masked

if __name__ == "__main__":
    sample = "Customer John Doe: SSN 123-45-6789, Email jdoe@example.com, Phone 555-019-2834."
    print("Original:", sample)
    print("Masked:  ", mask_text_with_dlp_template(sample))
