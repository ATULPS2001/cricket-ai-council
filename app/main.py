"""FastAPI backend for Cricket AI Council."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Literal, Optional
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.stats_agent import StatsAgent
from agents.form_agent import FormAgent
from agents.formulator_agent import FormulatorAgent
from config import validate_config, API_HOST, API_PORT, DATA_DIR

validate_config()

# Load data once at startup
matches_df = pd.read_csv(DATA_DIR / "matches.csv")
deliveries_df = pd.read_csv(DATA_DIR / "deliveries.csv")

stats_agent = StatsAgent(matches_df, deliveries_df)
form_agent = FormAgent(matches_df, deliveries_df)
formulator_agent = FormulatorAgent(matches_df, deliveries_df)

app = FastAPI(
    title="Cricket AI Council API",
    description="Multi-agent cricket analytics system",
    version="1.0.0"
)


class QueryRequest(BaseModel):
    query: str
    role: Literal["stats", "form", "formulator"] = "stats"
    teams: Optional[list] = None
    venue: Optional[str] = None


class QueryResponse(BaseModel):
    query: str
    role: str
    prediction: Optional[str] = None
    confidence: Optional[float] = None
    reasoning: Optional[str] = None
    success: bool = True


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "cricket-ai-council"}


@app.post("/query", response_model=QueryResponse)
def query_council(request: QueryRequest):
    try:
        # Build structured question for agents
        question = {
            "type": "toss_bat_gamble" if "toss" in request.query.lower() or "bat" in request.query.lower() else "form_check",
            "teams": request.teams or [],
            "venue": request.venue,
        }
        
        if request.role == "stats":
            verdict = stats_agent.analyze(question)
        elif request.role == "form":
            verdict = form_agent.analyze(question)
        elif request.role == "formulator":
            verdict = formulator_agent.analyze(question)
        else:
            raise ValueError(f"Unknown role: {request.role}")

        return QueryResponse(
            query=request.query,
            role=request.role,
            prediction=verdict.prediction,
            confidence=verdict.confidence,
            reasoning=verdict.reasoning,
            success=True
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent execution failed: {str(e)}"
        )


@app.get("/")
def root():
    return {
        "service": "Cricket AI Council",
        "version": "1.0.0",
        "agents": ["stats", "form", "formulator"],
        "endpoints": {
            "health": "/health",
            "query": "/query (POST)"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)
