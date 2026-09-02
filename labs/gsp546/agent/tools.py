#!/usr/bin/env python3
"""
Custom Tool Definitions for Cymbal Solar Agents.
Includes Vector Search RAG retrieval tool and inventory queries.
"""

from typing import Dict, Any, List

# Synthetic Hardware Manuals for Vector Search Grounding
HARDWARE_KNOWLEDGE_BASE = [
    {
        "manual_id": "MAN-HG-5000",
        "title": "HelioGrid Pro-5000 Installation and Service Manual",
        "content": "Fault E-101 indicates DC Bus Over-Temperature. Verify cooling fan clearance and thermal paste condition. Nominal operating voltage is 480V AC.",
        "keywords": ["temperature", "e-101", "dc bus", "heliogrid"]
    },
    {
        "manual_id": "MAN-PV-10K",
        "title": "PowerVault 10K Battery Enclosure Technical Specs",
        "content": "Battery ground isolation fault E-102 requires immediate DC disconnect. Check grounding lug torque (8.5 Nm) and fuse link continuity.",
        "keywords": ["battery", "powervault", "e-102", "isolation", "ground"]
    },
    {
        "manual_id": "MAN-HG-PM",
        "title": "Inverter Power Module Replacement Guide",
        "content": "Part number HG-PM-480 is the primary replacement power module for all HelioGrid 480V commercial models.",
        "keywords": ["part", "replacement", "hg-pm-480", "power module"]
    }
]

def query_hardware_manuals(query_text: str, top_k: int = 2) -> List[Dict[str, Any]]:
    """
    RAG retrieval tool simulating Vertex AI Vector Search endpoint retrieval
    using text-embedding-005 cosine similarity.
    """
    query_terms = set(query_text.lower().split())
    scored_docs = []
    for doc in HARDWARE_KNOWLEDGE_BASE:
        overlap = len(query_terms.intersection(set(doc["keywords"])))
        score = 0.5 + (0.25 * overlap)
        scored_docs.append({
            "manual_id": doc["manual_id"],
            "title": doc["title"],
            "content": doc["content"],
            "similarity_score": min(score, 0.99)
        })
    # Sort by score descending
    scored_docs.sort(key=lambda x: x["similarity_score"], reverse=True)
    return scored_docs[:top_k]

def check_parts_inventory(part_number: str) -> Dict[str, Any]:
    """Queries regional parts depot stock for replacement components."""
    inventory = {
        "HG-PM-480": {"in_stock": True, "depot": "Central-Denver", "qty": 14},
        "PV-FUSE-100A": {"in_stock": True, "depot": "West-Phoenix", "qty": 42}
    }
    return inventory.get(part_number, {"in_stock": False, "qty": 0})
