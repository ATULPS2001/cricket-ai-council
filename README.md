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

| Agent | Data it reasons over | Role |
|---|---|---|
| Stats Agent | Historical aggregates (averages, strike rates, head-to-head) | Long-run baseline |
| Form Agent | Last 5-10 innings | Recent-form weighting |
| Conditions Agent | Pitch report, weather, venue history, toss | Context adjustment |
| Momentum Agent | Ball-by-ball game state | In-match win probability |
| Arbitrator | All agent outputs + confidence scores | Conflict resolution |

## Data sources

- [Cricsheet](https://cricsheet.org/) — free historical ball-by-ball data (primary, for backtesting)
- CricketData / Roanuz APIs — live match data (planned, for real-time demos)

## Tech stack

- Python 3.11+
- LLM APIs (agent reasoning)
- pandas / scikit-learn (baseline ML models for backtesting)

## Status

🚧 Early prototype. Currently building: agent base class + Stats Agent + backtesting harness against Cricsheet historical matches.

## Roadmap

- [ ] `base_agent.py` shared interface
- [ ] Stats Agent + backtest on historical data
- [ ] Form Agent
- [ ] Conditions Agent
- [ ] Momentum Agent (ball-by-ball, sequential — not parallel fan-out)
- [ ] Arbitrator + Synthesizer
- [ ] Backtested accuracy report
- [ ] Live API integration
- [ ] Simple web UI

## Setup

```bash
git clone https://github.com/ATULPS2001/cricket-ai-council.git
cd cricket-ai-council
pip install -r requirements.txt
cp .env.example .env  # add your LLM API keys
```

## License

MIT
