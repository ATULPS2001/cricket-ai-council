# Cricket AI Council

Multi-agent system for IPL match prediction. Tests whether recent form or historical stats matter more.

## Results

Backtested on 144 held-out matches (2023-24 IPL):

| Agent | Signal | Accuracy |
|-------|--------|----------|
| Stats Agent | Historical aggregates (H2H, venue, toss) | 55.6% |
| Form Agent | Last 5 matches (win%, batting RR, death bowling) | 43.7% |
| **Formulator Agent** | Weighted fusion (70% stats + 30% form) | **58.3%** |

Finding: Recent form alone is noise (43.7%), but fused with stats at ~30% weight, it adds signal. Ensemble beats either signal alone.

## Structure

```
cricket-ai-council/
├── agents/
│   ├── stats_agent.py      # Historical stats
│   ├── form_agent.py       # Recent form
│   └── formulator_agent.py # Fusion (weighted ensemble)
├── data/processed/         # matches.csv, deliveries.csv
├── evaluation/             # Backtest harnesses + results
└── docs/council_design.md  # Design notes
```

## Usage

```bash
git clone https://github.com/ATULPS2001/cricket-ai-council.git
cd cricket-ai-council
pip install pandas

# Run backtests
python evaluation/backtest_stats_agent.py
python evaluation/backtest_form_agent.py
python evaluation/backtest_formulator_agent.py
```

## Agents

### Stats Agent

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
print(verdict.prediction, verdict.confidence, verdict.reasoning)
```

### Form Agent

```python
from agents.form_agent import FormAgent
agent = FormAgent(matches, deliveries)

verdict = agent.analyze({
    "type": "form_check",
    "teams": ["Mumbai Indians", "Chennai Super Kings"],
    "match_id": 1234567
})
print(verdict.prediction, verdict.confidence, verdict.reasoning)
```

### Formulator Agent

```python
from agents.formulator_agent import FormulatorAgent
agent = FormulatorAgent(matches, deliveries, w_stats=0.7, w_form=0.3)

verdict = agent.analyze({
    "type": "toss_bat_gamble",
    "teams": ["Mumbai Indians", "Chennai Super Kings"],
    "venue": "Wankhede Stadium, Mumbai"
})
print(verdict.prediction, verdict.confidence, verdict.reasoning)
```

## Methodology

- Train: 874 matches (2008-2022)
- Test: 144 matches (2023-24)
- Excluded ties/no-results

## Notes

Built with AI assistance. Code works, backtests are real. The 43.7% form failure taught us: decompose signals first, fuse second. Ensemble methods win.

See [docs/council_design.md](docs/council_design.md) for full design.

License: MIT
