# Cricket AI Council

A multi-agent cricket prediction system built for IPL match analysis.

## Overview

The Cricket AI Council is a prototype system that combines statistical analysis with structured reasoning to predict IPL match outcomes. It consists of three specialized agents:

1. **Stats Agent** - Analyzes historical match data to generate predictions
2. **Form Agent** - Evaluates recent team form and momentum (TODO)
3. **Formulator Agent** - Synthesizes inputs into final verdicts (TODO)

## Architecture

```
cricket-ai-council/
├── agents/
│   ├── stats_agent.py      # Statistical prediction engine
│   ├── form_agent.py       # Recent form analysis (TODO)
│   └── formulator_agent.py # Decision synthesis (TODO)
├── data/
│   ├── raw/                # Raw CSV data
│   └── processed/          # Cleaned matches.csv, deliveries.csv
├── evaluation/
│   ├── backtest_stats_agent.py  # Backtest harness
│   └── results/            # Backtest output CSVs
└── docs/
    └── council_design.md   # System design document
```

## Stats Agent

The Stats Agent predicts match winners based on:
- Historical head-to-head records
- Venue-specific performance
- Toss and batting-first patterns

### Query Format

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

### Backtested performance

The Stats Agent was evaluated on held-out IPL matches from 2023-2024:

| Metric | Value |
|--------|-------|
| Test set size | 144 matches |
| Accuracy | **55.6%** |
| Baseline (random) | 50% |
| Average confidence | 0.78 |

**Note:** Confidence scores are currently uncalibrated — average confidence (0.78) exceeds actual accuracy (55.6%). Calibration is planned for a future release.

Per-team accuracy varies (e.g., 76.9% on Mumbai Indians, 56.3% on Rajasthan Royals), suggesting venue and team-specific biases in the underlying data.

## Setup

```bash
# Clone the repository
git clone https://github.com/ATULPS2001/cricket-ai-council.git
cd cricket-ai-council

# Install dependencies
pip install pandas

# Run the backtest
python evaluation/backtest_stats_agent.py
```

## Data

The system uses ball-by-ball IPL match data in CSV format:
- `matches.csv` - Match-level metadata (teams, venue, toss, winner)
- `deliveries.csv` - Ball-by-ball delivery data

Data should be placed in `data/processed/` directory.

## License

MIT
