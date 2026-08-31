"""FastAPI backend for Cricket AI Council."""
from __future__ import annotations

import os
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from workflow import build_workflow

# ─── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(title="Cricket AI Council API")

# ─── Models ───────────────────────────────────────────────────────────────────


class QueryRequest(BaseModel):
    query: str
    role: Literal["tactical", "data", "evaluator"] = "tactical"


class QueryResponse(BaseModel):
    response: str
    citations: list[str]
    stats_used: dict


# ─── Endpoints ────────────────────────────────────────────────────────────────


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/query", response_model=QueryResponse)
async def query_council(request: QueryRequest):
    """Query the Cricket AI Council."""
    try:
        # Build workflow
        app_workflow = build_workflow()

        # Prepare state
        state = {
            "messages": [],
            "query": request.query,
            "role": request.role,
            "retrieved_stats": {},
            "retrieved_docs": [],
            "citations": [],
            "final_response": "",
        }

        # Run workflow
        result = app_workflow.invoke(state)

        return QueryResponse(
            response=result["final_response"],
            citations=result.get("citations", []),
            stats_used=result.get("retrieved_stats", {}),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Run ──────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
