# Cricket AI Council

> A multi-agent LLM system where specialized AI agents independently analyze a cricket question, debate their conclusions, and an arbitrator synthesizes a single verdict with a confidence score.

## Why this exists

Most cricket prediction tools produce a single black-box number. This project instead makes disagreement visible: a **Stats Agent**, **Form Agent**, **Conditions Agent**, and **Momentum Agent** each reason independently over the same question, and an **Arbitrator** resolves conflicts into a final, explainable verdict.

## Architecture

```
                 ┌─────────────┐
   Question ───► │   Router     │
                 └──────┬──────┘
                        │  fan-out
        ┌───────────────┼───────────────┬───────────────┐
        ▼               ▼               ▼               ▼
  Stats Agent      Form Agent    Conditions Agent   Momentum Agent
        │               │               │               │
        └───────────────┴───────┬───────┴───────────────┘
                                 ▼
                          Arbitrator
                                 │
                                 ▼
                           Synthesizer
                                 │
                                 ▼
                        Final verdict + confidence
```

## Council members

| Agent | Status | Data it reasons over | Role |
|---|---|---|---|
| **Stats Agent** | ✅ Implemented | Historical aggregates (averages, strike rates, head-to-head) | Long-run baseline |
| Form Agent | 🚧 Planned | Last 5-10 innings | Recent-form weighting |
| Conditions Agent | 🚧 Planned | Pitch report, weather, venue history, toss | Context adjustment |
| Momentum Agent | 🚧 Planned | Ball-by-ball game state | In-match win probability |
| Arbitrator | 🚧 Planned | All agent outputs + confidence scores | Conflict resolution |

## Data sources

- [Cricsheet](https://cricsheet.org/) — free historical ball-by-ball data (primary, for backtesting)
- CricketData / Roanuz APIs — live match data (planned, for real-time demos)

## Tech stack

- Python 3.9+
- pandas, scikit-learn (data processing + baseline ML)
- LLM APIs (agent reasoning — OpenAI, Anthropic, or local models)

## Quick start

```bash
# 1. Clone and install
git clone https://github.com/ATULPS2001/cricket-ai-council.git
cd cricket-ai-council
pip install -r requirements.txt

# 2. Download Cricsheet data
# Go to https://cricsheet.org/downloads/, grab the IPL JSON zip,
# unzip into data/raw/ (each match becomes one <id>.json file)

# 3. Parse the data
python data/load_cricsheet.py

# 4. Run the Stats Agent
python agents/stats_agent.py
```

## Stats Agent usage example

```python
import pandas as pd
from agents.stats_agent import StatsAgent

matches = pd.read_csv("data/processed/matches.csv")
deliveries = pd.read_csv("data/processed/deliveries.csv")
agent = StatsAgent(matches, deliveries)

# Example 1: Toss-and-bat gamble prediction
q1 = {
    "type": "toss_bat_gamble",
    "teams": ["Chennai Super Kings", "Mumbai Indians"],
    "venue": "Wankhede"
}
verdict1 = agent.analyze(q1)
print(verdict1.prediction, "— confidence:", verdict1.confidence)
print(verdict1.reasoning)

# Example 2: Top scorer among a list of players
q2 = {
    "type": "top_scorer",
    "players": ["V Kohli", "RG Sharma", "MS Dhoni"]
}
verdict2 = agent.analyze(q2)
print(verdict2.prediction, "— confidence:", verdict2.confidence)

# Example 3: Head-to-head comparison
q3 = {
    "type": "head_to_head",
    "players": ["V Kohli", "RG Sharma"],
    "venue": "M Chinnaswamy"
}
verdict3 = agent.analyze(q3)
print(verdict3.prediction, "— confidence:", verdict3.confidence)
```

## Progress tracker

- [x] `base_agent.py` shared interface
- [x] Stats Agent + backtest on historical data
- [ ] Form Agent
- [ ] Conditions Agent
- [ ] Momentum Agent (ball-by-ball, sequential — not parallel fan-out)
- [ ] Arbitrator + Synthesizer
- [ ] Backtested accuracy report
- [ ] Live API integration
- [ ] Simple web UI (Streamlit)

## License

MIT
