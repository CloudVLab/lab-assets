#!/usr/bin/env python3
"""
FastAPI Server for Cymbal Solar GridCare Multi-Agent Service.
Exposes endpoints for Cloud Run deployment:
- GET /health
- POST /agent/query
"""

import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agent.supervisor_agent import GridCareSupervisorAgent

app = FastAPI(title="Cymbal Solar GridCare Multi-Agent Service")
supervisor = GridCareSupervisorAgent()

class QueryRequest(BaseModel):
    session_id: str
    query: str

@app.get("/")
def read_root():
    return {"status": "ONLINE", "service": "GridCare Multi-Agent Service", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "HEALTHY", "agents": ["Supervisor", "Diagnostic", "Inventory", "Dispatch"]}

@app.post("/agent/query")
def agent_query(req: QueryRequest):
    try:
        result = supervisor.route_request(req.session_id, req.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
