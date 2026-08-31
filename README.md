# Cricket AI Council

A multi-agent AI system that answers cricket strategy and analytics questions by combining historical match data, tool-based retrieval, and LLM reasoning. Three specialized agents — Tactical (Head Coach), Data (Analyst), and Evaluator (Chief Strategist) — draw on a shared cricket dataset through an MCP-style tool layer, and every response is orchestrated through an explicit LangGraph workflow with a built-in critic step for citation and hallucination checks.

## Architecture

```
                    ┌─────────────────────┐
                    │   User Query + Role  │
                    │ (tactical/data/eval) │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │   FastAPI  /query     │
                    │   (app/main.py)       │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │  LangGraph Workflow   │
                    │   (workflow.py)       │
                    │                       │
                    │  ┌─────────────────┐  │
                    │  │  Research Node  │──┼──► MCP Tools (mcp_server.py)
                    │  └────────┬────────┘  │      - get_team_stats
                    │           │           │      - get_venue_record
                    │  ┌────────▼────────┐  │      - get_h2h
                    │  │  Strategy Node  │──┼──► Gemini LLM (role-specific
                    │  └────────┬────────┘  │      system prompt)
                    │           │           │
                    │  ┌────────▼────────┐  │
                    │  │   Critic Node   │  │  (adds citations,
                    │  └────────┬────────┘  │   flags missing data)
                    └───────────┼───────────┘
                                │
                    ┌───────────▼───────────┐
                    │   Final Response      │
                    │  (Streamlit UI /      │
                    │   API JSON response)  │
                    └───────────────────────┘
```

**Data layer:** `analysis/insights.py` computes venue trends, phase (powerplay/death) performance, chase-success brackets, toss conversion, and team-venue dominance from `data/processed/matches.csv` and `deliveries.csv`. `mcp_server.py` exposes these as callable tools for the agents.

## Sample Input / Output

**Input:**
```json
{
  "query": "Playing CSK at Chepauk, what's our batting strategy?",
  "role": "tactical"
}
```

**Output:**
```
Given CSK's strong home record at Chepauk:

- Powerplay: Rotate strike, avoid early risk against new-ball swing
- Middle overs: Preserve wickets, target spin matchups
- Death: CSK's death bowling economy is competitive — plan for 9-10 runs/over, not 12+

Sources:
[source: chepauk_record]
[source: csk_stats]
```

## Quick Start

```bash
git clone https://github.com/ATULPS2001/cricket-ai-council.git
cd cricket-ai-council
pip install -r requirements.txt
export GOOGLE_API_KEY="your-gemini-key"

# Run the workflow standalone
python3 workflow.py

# Run the API
uvicorn app.main:app --reload

# Run the UI (separate terminal)
streamlit run ui/streamlit_app.py
```

### Docker

```bash
echo "GOOGLE_API_KEY=your-key" > .env
docker compose up --build
```

- API: http://localhost:8000/docs
- UI: http://localhost:8501

See `QUICKSTART.md` for more detail.

## Project Structure

```
cricket-ai-council/
├── analysis/         # Core cricket analytics (venue, phase, chase, H2H trends)
├── mcp_server.py     # Tool layer exposing analytics to agents
├── workflow.py        # LangGraph orchestration (research → strategy → critic)
├── agents/            # Role-specific agent logic
├── app/main.py         # FastAPI backend
├── ui/streamlit_app.py # Streamlit chat interface
├── rag/               # Chroma-based retrieval (index.py, retrieve.py)
├── data/               # Processed matches/deliveries CSVs
├── Dockerfile
├── docker-compose.yml
└── .github/workflows/  # CI pipeline
```

## Tech Stack

- **Orchestration:** LangGraph
- **LLM:** Google Gemini
- **Tool layer:** Custom MCP-style server (`mcp_server.py`)
- **Retrieval:** Chroma (RAG over match reports/scorecards)
- **Backend:** FastAPI
- **Frontend:** Streamlit
- **Data:** pandas-based analytics over historical IPL ball-by-ball data
- **Deployment:** Docker + GitHub Actions CI
