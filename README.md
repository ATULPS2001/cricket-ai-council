# 🏏 Cricket AI Council

**Multi-agent AI system for cricket match predictions and analytics.**

Built with:
- **Stats Agent** - Career statistics and historical records
- **Form Agent** - Recent form and momentum analysis
- **Formulator Agent** - Fuses predictions from both agents
- **FastAPI** - Backend API
- **Streamlit** - Interactive UI

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Streamlit UI                            │
│  (Select agent: Stats / Form / Formulator)                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                         │
│  /query endpoint → routes to selected agent                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      Agent Layer                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐              │
│  │  Stats   │  │   Form   │  │  Formulator  │              │
│  │  Agent   │  │  Agent   │  │    Agent     │              │
│  └──────────┘  └──────────┘  └──────────────┘              │
│       ↓              ↓              ↑                       │
│  Career stats   Recent form   Fuses both                   │
│  H2H records    Last 5 games  (80% Stats + 20% Form)       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     Data Layer                              │
│  data/processed/matches.csv  (match-level aggregates)       │
│  data/processed/deliveries.csv (ball-by-ball data)          │
└─────────────────────────────────────────────────────────────┘
```

## Agents

### 📊 Stats Agent

Analyzes **career statistics and historical records**:

- Career batting averages and strike rates
- Bowling economy rates and averages
- Head-to-head records between teams/players
- Venue-based win percentages

**Best for:** Questions about long-term performance, career comparisons, historical matchups.

### 📈 Form Agent

Evaluates **recent form and momentum**:

- Last 5 matches: win%, batting run rate, death-over bowling economy
- Recent H2H record (last 5 meetings)
- Form differential between two teams

**Best for:** Questions about current momentum, recent performance trends, "hot/cold" teams.

### 🧠 Formulator Agent

**Fuses predictions from Stats and Form agents** using weighted ensemble:

- Default weights: 80% Stats + 20% Form
- Balances long-term statistics with recent momentum
- More robust than either agent alone (since Form Agent underperforms at ~44% accuracy)

**Best for:** General predictions where you want both historical context and recent form considered.

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/ATULPS2001/cricket-ai-council.git
cd cricket-ai-council
pip install -r requirements.txt
```

### 2. Set up environment

```bash
# Set your Google API key (for future LLM features)
export GOOGLE_API_KEY='your-key-here'

# Optional: customize config in config.py
# - API_HOST, API_PORT
# - DATA_DIR
```

### 3. Prepare data

```bash
# Download IPL data from Cricsheet (if not already done)
# Place in data/raw/ folder

# Process into matches.csv and deliveries.csv
python data/load_cricsheet.py
```

### 4. Run the system

**Terminal 1 - Start FastAPI backend:**
```bash
python app/main.py
# Runs on http://localhost:8000
```

**Terminal 2 - Start Streamlit UI:**
```bash
streamlit run ui/streamlit_app.py
# Opens at http://localhost:8501
```

## API Endpoints

### `GET /`
Health check and service info.

### `GET /health`
Returns `{"status": "healthy"}`.

### `POST /query`
Query an agent for a prediction.

**Request:**
```json
{
  "query": "CSK vs MI at Wankhede, who wins?",
  "role": "stats",  // or "form" or "formulator"
  "teams": ["Chennai Super Kings", "Mumbai Indians"],
  "venue": "Wankhede"
}
```

**Response:**
```json
{
  "query": "CSK vs MI at Wankhede, who wins?",
  "role": "stats",
  "prediction": "Mumbai Indians",
  "confidence": 0.65,
  "reasoning": "At Wankhede, Chennai Super Kings won 3/8 (37.5%) vs Mumbai Indians won 5/8. Prediction: Mumbai Indians.",
  "success": true
}
```

## Project Structure

```
cricket-ai-council/
├── agents/              # Agent implementations
│   ├── base_agent.py    # Abstract base class
│   ├── stats_agent.py   # Career stats agent
│   ├── form_agent.py    # Recent form agent
│   └── formulator_agent.py  # Fusion agent
├── app/                 # FastAPI backend
│   └── main.py
├── ui/                  # Streamlit frontend
│   └── streamlit_app.py
├── data/                # Data pipeline
│   ├── raw/             # Raw Cricsheet JSON files
│   └── processed/       # CSV files (matches.csv, deliveries.csv)
├── config.py            # Configuration
├── requirements.txt     # Python dependencies
└── README.md
```

## Future Work

- [ ] Add Coach/Analyst/Strategist agent roles (LLM-powered)
- [ ] Integrate real-time match data
- [ ] Add player matchup analysis
- [ ] Build prediction tracking and backtesting
- [ ] Deploy to cloud (Render/Railway)

## License

MIT
