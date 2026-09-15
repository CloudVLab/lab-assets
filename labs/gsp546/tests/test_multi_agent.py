import os
import sys
import pytest

# Ensure repository root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent.diagnostic_agent import DiagnosticAgent
from agent.supervisor_agent import GridCareSupervisorAgent
from agent.tools import query_hardware_manuals


def test_diagnostic_agent_memory_persistence():
    agent = DiagnosticAgent()
    session_id = "test-session-001"
    
    # Turn 1: Establish device context
    r1 = agent.process_query(session_id, "Inverter INV-HG-101 is reporting intermittent power cuts.")
    assert r1["context"].get("device_id") == "INV-HG-101"
    
    # Turn 2: Ask follow up without repeating device_id
    r2 = agent.process_query(session_id, "What is the current operating temperature status?")
    assert "INV-HG-101" in r2["response"]
    assert "74.2C" in r2["response"]

def test_vector_search_rag_grounding():
    results = query_hardware_manuals("fault E-101 high temperature", top_k=2)
    assert len(results) > 0
    top_result = results[0]
    assert "E-101" in top_result["content"]
    assert top_result["similarity_score"] > 0.5

def test_supervisor_multi_agent_a2a_orchestration():
    supervisor = GridCareSupervisorAgent()
    session_id = "test-session-002"
    
    # Multi-agent handoff trigger
    query = "Inverter INV-HG-101 needs power module replace"
    res = supervisor.route_request(session_id, query)
    
    assert res["supervisor_status"] == "COMPLETED"
    assert res["diagnostic"] is not None
    assert res["inventory"] is not None
    assert res["inventory"]["status"]["in_stock"] is True
    assert res["dispatch"] is not None
    assert res["dispatch"]["dispatch_status"] == "CONFIRMED"
