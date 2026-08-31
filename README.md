# Cricket AI Council 🏏

**An AI-powered strategic decision support system for cricket** — featuring a council of three specialized agents (Tactical, Data, Evaluator) orchestrated with LangGraph, grounded in real match data via RAG, and deployable with Docker.

![CI](https://github.com/ATULPS2001/cricket-ai-council/actions/workflows/ci.yml/badge.svg)
![License](https://img.shields.io/github/license/ATULPS2001/cricket-ai-council)

---

## 🚀 Quick Start

```bash
# 1. Clone and install
git clone https://github.com/ATULPS2001/cricket-ai-council.git
cd cricket-ai-council
pip3 install -r requirements.txt

# 2. Set API key
export GOOGLE_API_KEY="your-gemini-api-key"

# 3. Run workflow locally (test)
python3 workflow.py

# 4. Or deploy with Docker
docker-compose up --build
```

**Access the UI:** http://localhost:8501  
**API Docs:** http://localhost:8000/docs

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Query                              │
│  "Playing CSK at Chepauk, what's our batting strategy?"     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              LangGraph Workflow                             │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Research    │ →  │  Strategy    │ →  │   Critic     │  │
│  │    Node      │    │    Node      │    │    Node      │  │
│  │              │    │              │    │              │  │
│  │ - MCP Tools  │    │ - LLM Gen    │    │ - Validate   │  │
│  │ - Stats      │    │ - Role-based │    │ - Citations  │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
         │                      │
         ▼                      ▼
┌──────────────────┐  ┌──────────────────┐
│   MCP Server     │  │   RAG (Chroma)   │
│                  │  │                  │
│ - get_team_stats │  │ - Match reports  │
│ - get_venue_rec  │  │ - Scorecards     │
│ - get_h2h        │  │ - Tactics notes  │
└──────────────────┘  └──────────────────┘
```

---

## 🎯 The Council

| Agent | Role | Example Output |
|-------|------|----------------|
| **Tactical** | Head Coach | "Target 45-50 in powerplay. Use left-right combo vs their new ball." |
| **Data** | Analyst | "CSK concedes 0.57 runs/ball in death overs. Chase success at 180+ is 38%." |
| **Evaluator** | Strategist | "High-risk strategy: 65% confidence. Alternative: preserve wickets, target 160." |

---

## 📁 Project Structure

```
cricket-ai-council/
├── workflow.py              # LangGraph orchestration (3 nodes)
├── mcp_server.py            # Cricket data tools (MCP-style)
├── config.py                # Shared configuration
├── rag/
│   ├── index.py            # Chroma indexing script
│   └── retrieve.py         # RAG retrieval
├── app/
│   └── main.py             # FastAPI backend
├── ui/
│   └── streamlit_app.py    # Streamlit UI
├── analysis/
│   └── insights.py         # Data analytics engine
├── data/
│   ├── processed/          # CSVs (matches, deliveries)
│   ├── json_scorecards/    # JSON scorecards for RAG
│   └── chroma_db/          # Vector database
├── Dockerfile
├── docker-compose.yml
├── .github/workflows/ci.yml
├── requirements.txt
└── README.md
```

---

## 🛠️ Features

### ✅ LangGraph Orchestration
- **Research Node**: Queries MCP tools for stats
- **Strategy Node**: Generates role-based responses
- **Critic Node**: Validates, adds citations, flags hallucinations

### ✅ MCP Server (3 Tools)
- `get_team_stats(team, phase)` — Powerplay/death batting & bowling
- `get_venue_record(team, venue)` — Win% at specific grounds
- `get_h2h(team1, team2)` — Head-to-head records

### ✅ RAG Pipeline (Chroma)
- Indexes JSON scorecards and match reports
- Retrieves top-2 docs per query
- Citations: `[source: match_1426261.json]`

### ✅ FastAPI + Streamlit
- REST API: `POST /query` with role selection
- Interactive UI with chat history and citations

### ✅ Docker + CI
- One-command deploy: `docker-compose up`
- GitHub Actions: lint, test, build

---

## 📊 Sample Query

**Input:**
```json
{
  "query": "We're playing CSK at Chepauk. They've won 76% of home games. What's our batting strategy?",
  "role": "tactical"
}
```

**Output:**
```
Given CSK's 76% home win rate at Chepauk:

1. Powerplay (Overs 1-6): Target 45-50 runs
   - CSK's new ball bowlers: 0.54 runs/ball
   - Use aggressive left-right combinations

2. Middle Overs (7-15): Preserve wickets
   - CSK spin duo: 0.48 runs/ball economy
   - Rotate strike, avoid mid-wicket risks

3. Death Overs (16-20): If 2+ wickets in hand
   - Target 10-12 runs/over
   - CSK concedes 0.57 runs/ball in death

Key Matchup: Your right-handers vs their off-spinner (SR 145)

[source: match_1426261.json] [source: venue_stats_chepauk]
```

---

## 🔧 Configuration

### Environment Variables

```bash
# Required
export GOOGLE_API_KEY="your-gemini-api-key"

# Optional
export API_URL="http://localhost:8000"  # For Streamlit
```

### Config File (`config.py`)

```python
LLM_MODEL = "gemini-2.0-flash"
RAG_N_RESULTS = 2
CONFIDENCE_THRESHOLD = 0.7
```

---

## 🧪 Testing

```bash
# Run workflow locally
python3 workflow.py

# Test MCP tools
python3 mcp_server.py

# Test RAG retrieval
python3 rag/retrieve.py

# Run API server
python3 -m uvicorn app.main:app --reload

# Run Streamlit UI
streamlit run ui/streamlit_app.py
```

---

## 🚢 Deployment

### Local (Docker)

```bash
docker-compose up --build
```

### Production (Railway/Render)

1. Connect GitHub repo
2. Set `GOOGLE_API_KEY` env var
3. Deploy command: `docker-compose up`

---

## 📈 Roadmap

- [ ] Guardrails (human approval gate)
- [ ] Observability (LangSmith integration)
- [ ] More MCP tools (player stats, live scores)
- [ ] Multi-turn conversation memory
- [ ] Evaluation dashboard

---

## 📄 License

MIT License

---

## 🙏 Acknowledgments

- Match data: IPL T20 ball-by-ball datasets
- LLM: Google Gemini 2.0 Flash
- Orchestration: LangGraph
- Vector DB: Chroma
