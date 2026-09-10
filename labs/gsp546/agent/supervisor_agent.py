#!/usr/bin/env python3
"""
Supervisor Agent implementation for Cymbal Solar GridCare.
Orchestrates worker agents (Diagnostic, Inventory, Dispatch) via Agent-to-Agent (A2A) protocol.
"""

from typing import Dict, Any, Optional
from agent.diagnostic_agent import DiagnosticAgent
from agent.tools import query_hardware_manuals, check_parts_inventory

class InventoryAgent:
    def check_stock(self, part_number: str) -> Dict[str, Any]:
        stock_info = check_parts_inventory(part_number)
        return {"agent": "InventoryAgent", "part_number": part_number, "status": stock_info}

class DispatchAgent:
    def schedule_service(self, device_id: str, depot: str) -> Dict[str, Any]:
        return {
            "agent": "DispatchAgent",
            "device_id": device_id,
            "dispatch_status": "CONFIRMED",
            "depot": depot,
            "assigned_slot": "Next Day Morning"
        }

class GridCareSupervisorAgent:
    def __init__(self):
        self.diagnostic_agent = DiagnosticAgent(tools=[query_hardware_manuals])
        self.inventory_agent = InventoryAgent()
        self.dispatch_agent = DispatchAgent()

    def route_request(self, session_id: str, query: str) -> Dict[str, Any]:
        """
        Hierarchical multi-agent router using A2A handoffs.
        1. Triage with DiagnosticAgent
        2. If part replacement is identified, call InventoryAgent
        3. If part in stock, call DispatchAgent
        """
        # Step 1: Diagnostic handoff
        diag_resp = self.diagnostic_agent.process_query(session_id, query)
        
        inventory_result: Optional[Dict[str, Any]] = None
        dispatch_result: Optional[Dict[str, Any]] = None

        # Step 2: Handoff to inventory if replacement indicated
        if "replace" in query.lower() or "hg-pm-480" in diag_resp.get("response", "").lower():
            inventory_result = self.inventory_agent.check_stock("HG-PM-480")
            
            # Step 3: Handoff to dispatch if part in stock
            if inventory_result.get("status", {}).get("in_stock", False):
                depot = inventory_result["status"].get("depot", "Central-Denver")
                # BUG (Troubleshooting Milestone): The supervisor assumes device_id is a top-level key
                # in diag_resp, causing a KeyError because DiagnosticAgent stores it under diag_resp["context"]["device_id"].
                device_id = diag_resp["device_id"]
                dispatch_result = self.dispatch_agent.schedule_service(device_id, depot)

        return {
            "session_id": session_id,
            "supervisor_status": "COMPLETED",
            "diagnostic": diag_resp,
            "inventory": inventory_result,
            "dispatch": dispatch_result
        }
