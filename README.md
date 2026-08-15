# Cricket AI Council

A multi-agent AI system for structured match outcome prediction with backtested evaluation.

## Overview

This project tests a hypothesis: **Does recent form matter more than historical performance in predicting IPL match outcomes?**

The system decomposes prediction into orthogonal signals (historical aggregates, recent form), evaluates each independently via train/test backtesting, and will fuse them via a Formulator Agent.

## Key Results

| Agent | Signal Type | Test Set | Accuracy | Interpretation |
|-------|-------------|----------|----------|----------------|
| **Stats Agent** | Historical aggregates (H2H, venue, toss) | 144 matches (2023-24) | **55.6%** | Baseline random = 50% |
| **Form Agent** | Last 5 matches (win%, batting RR, death bowling) | 144 matches (2023-24) | **43.7%** | Negative signal — form alone underperforms |

**Key insight:** Recent form is a *negative predictor*. Historical patterns outperform "hot team" narratives in IPL.

## Architecture

```
cricket-ai-council/
├── agents/
│   ├── stats_agent.py      # Historical aggregate-based predictions
│   ├── form_agent.py       # Recent form & momentum analysis
│   └── formulator_agent.py # Signal fusion (planned)
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

## Quick Start

```bash
# Clone and setup
git clone https://github.com/ATULPS2001/cricket-ai-council.git
cd cricket-ai-council
pip install pandas

# Run backtests
python evaluation/backtest_stats_agent.py
python evaluation/backtest_form_agent.py
```

## Agents

### Stats Agent

Predicts match winners using historical aggregates:
- Head-to-head records
- Venue-specific performance
- Toss and batting-first patterns

**Example:**
```python
from agents.stats_agent import StatsAgent
import pandas as pd

matches = pd.read_csv("data/processed/matches.csv")
deliveries = pd.read_csv("data/processed/deliveries.csv")

agent = StatsAgent(matches, deliveries)
verdict = agent.analyze({
    "type": "toss_bat_gamble",
    "teams": ["Mumbai Indians", "Chennai Super Kings"],
    "venue": "Wankhede Stadium, Mumbai"
})

print(verdict.prediction)   # "Mumbai Indians"
print(verdict.confidence)   # 0.72
print(verdict.reasoning)    # "..."
```

### Form Agent

Analyzes recent form signals:
- Last 5 matches: win%, batting run rate, death-over bowling economy
- Recent H2H record (last 5 meetings)
- Composite form score with weighted components

**Example:**
```python
from agents.form_agent import FormAgent

agent = FormAgent(matches, deliveries)
verdict = agent.analyze({
    "type": "form_check",
    "teams": ["Mumbai Indians", "Chennai Super Kings"],
    "match_id": 1234567  # For time-aware form
})
```

## Methodology

### Train/Test Split
- **Train:** 874 matches (2008-2022 seasons)
- **Test:** 144 matches (2023-2024 seasons)
- Excluded ties and no-results from evaluation

### Evaluation Metrics
- Accuracy (primary)
- Per-team breakdown
- Confidence calibration (noted as uncalibrated)

## Data

Uses ball-by-ball IPL match data:
- `matches.csv` — Match-level metadata (teams, venue, toss, winner)
- `deliveries.csv` — Ball-by-ball delivery data

Place processed data in `data/processed/`.

## Design Document

See [`docs/council_design.md`](docs/council_design.md) for full system architecture and agent specifications.

## License

MIT

---

> **⚠️ Vibe Coding Alert:** This project was built with AI assistance. The code works, the backtests are real, but the form agent's 43.7% accuracy is a feature, not a bug — it taught us that "hot team" narratives are noise. [Inspired by karpathy's llm-council](https://github.com/karpathy/llm-council).
