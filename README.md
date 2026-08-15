# Cricket AI Council

A multi-agent AI system for structured cricket match prediction, built with backtested evaluation.

## Overview

This project tests a hypothesis: **Does recent form matter more than historical performance in IPL match outcomes?**

The system decomposes prediction into separate signals (historical stats, recent form), evaluates each independently via backtesting, and will fuse them via a Formulator Agent.

## Backtested Results (2023-2024 IPL)

| Agent | Signal Type | Test Set | Accuracy | Notes |
|-------|-------------|----------|----------|-------|
| **Stats Agent** | Historical aggregates (H2H, venue, toss) | 144 matches | **55.6%** | Baseline random = 50% |
| **Form Agent** | Last 5 matches (win%, batting RR, death bowling) | 144 matches | **43.7%** | Negative signal — form alone underperforms |

**Key insight:** Recent form is a *negative predictor*. Historical patterns outperform "hot team" narratives.

## Architecture

```
cricket-ai-council/
├── agents/
│   ├── stats_agent.py      # Historical aggregate-based predictions
│   ├── form_agent.py       # Recent form & momentum analysis
│   └── formulator_agent.py # Signal fusion (TODO)
├── data/
│   ├── raw/                # Raw CSV data
│   └── processed/          # Cleaned matches.csv, deliveries.csv
├── evaluation/
│   ├── backtest_stats_agent.py  # Stats Agent backtest harness
│   ├── backtest_form_agent.py   # Form Agent backtest harness
│   └── results/            # Backtest output CSVs
└── docs/
    └── council_design.md   # System design document
```

## Agents

### Stats Agent

Predicts match winners based on:
- Historical head-to-head records
- Venue-specific performance
- Toss and batting-first patterns

**Usage:**
```python
from agents.stats_agent import StatsAgent
import pandas as pd

matches = pd.read_csv("data/processed/matches.csv")
deliveries = pd.read_csv("data/processed/deliveries.csv")

agent = StatsAgent(matches, deliveries)

query = {
    "type": "toss_bat_gamble",
    "teams": ["Mumbai Indians", "Chennai Super Kings"],
    "venue": "Wankhede Stadium, Mumbai"
}

verdict = agent.analyze(query)
print(verdict.prediction)   # "Mumbai Indians"
print(verdict.confidence)   # 0.72
print(verdict.reasoning)    # "..."
```

### Form Agent

Analyzes recent form signals:
- Last 5 matches: win%, batting run rate, death-over bowling economy
- Recent H2H record (last 5 meetings)
- Composite form score with weighted components

**Usage:**
```python
from agents.form_agent import FormAgent

agent = FormAgent(matches, deliveries)

query = {
    "type": "form_check",
    "teams": ["Mumbai Indians", "Chennai Super Kings"],
    "match_id": 1234567  # For time-aware form (matches before this one)
}

verdict = agent.analyze(query)
```

## Setup

```bash
# Clone the repository
git clone https://github.com/ATULPS2001/cricket-ai-council.git
cd cricket-ai-council

# Install dependencies
pip install pandas

# Run backtests
python evaluation/backtest_stats_agent.py
python evaluation/backtest_form_agent.py
```

## Data

The system uses ball-by-ball IPL match data in CSV format:
- `matches.csv` - Match-level metadata (teams, venue, toss, winner)
- `deliveries.csv` - Ball-by-ball delivery data

Data should be placed in `data/processed/` directory.

## Design Document

See [`docs/council_design.md`](docs/council_design.md) for full system architecture and agent specifications.

## License

MIT
