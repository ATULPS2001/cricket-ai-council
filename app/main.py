"""FastAPI backend for Cricket AI Council."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Literal
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from workflow import CricketWorkflow
from config import validate_config, API_HOST, API_PORT

validate_config()

app = FastAPI(
    title="Cricket AI Council API",
    description="Multi-agent cricket analytics system",
    version="1.0.0"
)


class QueryRequest(BaseModel):
    query: str
    role: Literal["tactical", "data", "evaluator"] = "tactical"


class QueryResponse(BaseModel):
    query: str
    role: str
    response: str
    success: bool = True


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "cricket-ai-council"}


@app.post("/query", response_model=QueryResponse)
def query_council(request: QueryRequest):
    try:
        workflow = CricketWorkflow()
        response = workflow.run(request.query, request.role)

        return QueryResponse(
            query=request.query,
            role=request.role,
            response=response,
            success=True
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Workflow execution failed: {str(e)}"
        )


@app.get("/")
def root():
    return {
        "service": "Cricket AI Council",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "query": "/query (POST)"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)
