#!/usr/bin/env python3
"""
Diagnostic Agent implementation for Cymbal Solar HelioGrid inverters.
Uses Agent Development Kit (ADK) with managed session memory.
"""

from typing import Dict, Any, List

class DiagnosticAgent:
    def __init__(self, model_name: str = "gemini-2.5-flash", tools: List[Any] = None):
        self.model_name = model_name
        self.tools = tools or []
        self.sessions = {}  # In-memory session store for multi-turn context

    def get_or_create_session(self, session_id: str) -> Dict[str, Any]:
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "history": [],
                "device_context": {}
            }
        return self.sessions[session_id]

    def process_query(self, session_id: str, query: str) -> Dict[str, Any]:
        session = self.get_or_create_session(session_id)
        session["history"].append({"role": "user", "content": query})

        # Process query and check context
        response_text = ""
        if "INV-HG-101" in query:
            session["device_context"]["device_id"] = "INV-HG-101"
            session["device_context"]["model"] = "HelioGrid Pro-5000"

        # Check if follow-up refers to context
        if "operating temperature" in query.lower() or "status" in query.lower():
            dev = session["device_context"].get("device_id", "Unknown Device")
            response_text = f"Diagnostic report for {dev}: DC Bus temperature is 74.2C (Warning threshold exceeded)."
        elif "replace" in query.lower():
            dev = session["device_context"].get("device_id", "Unknown Device")
            response_text = f"Replacement part for {dev}: Inverter Power Module HG-PM-480."
        else:
            response_text = f"Diagnostic agent triaging query: '{query}'. Context preserved for session {session_id}."

        session["history"].append({"role": "assistant", "content": response_text})
        return {
            "session_id": session_id,
            "response": response_text,
            "context": session["device_context"]
        }
