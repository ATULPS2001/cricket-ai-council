# Cricket AI Council

An AI-powered decision support system for cricket match strategy, featuring a council of three specialized agents (Tactical, Data, Evaluator) that collaborate to provide data-driven insights for coaches and analysts.

## Problem

Cricket teams need to make dozens of strategic decisions before and during matches—toss calls, batting orders, bowling changes, and chase targets. These decisions are often based on intuition rather than historical evidence. The Cricket AI Council transforms raw match data into actionable strategic recommendations.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Query                              │
│  "We're playing CSK at Chepauk, what's our game plan?"      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Orchestrator                             │
│  - Parses query (team, venue, context)                      │
│  - Routes to appropriate agents                             │
│  - Synthesizes final response                               │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
    ┌────────────────┐ ┌──────────────┐ ┌──────────────┐
    │ Tactical Agent │ │  Data Agent  │ │ Evaluator    │
    │                │ │              │ │ Agent        │
    │ - Game plans   │ │ - Stats &    │ │ - Risk       │
    │ - Player       │ │   trends     │ │   assessment │
    │   matchups     │ │ - Historical │ │ - Confidence │
    │ - Phase        │ │   records    │ │   scoring    │
    │   strategies   │ │ - H2H data   │ │              │
    └────────────────┘ └──────────────┘ └──────────────┘
              │               │               │
              └───────────────┼───────────────┘
                              ▼
                  ┌───────────────────────┐
                  │   CricketInsights     │
                  │   (Data Engine)       │
                  │                       │
                  │ - Powerplay/Death     │
                  │ - Chase success by    │
                  │   target bracket      │
                  │ - Venue dominance     │
                  │ - Collapse/recovery   │
                  │ - Toss conversion     │
                  └───────────────────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │   Gemini LLM          │
                  │   (Response Gen)      │
                  └───────────────────────┘
```

## Agents

| Agent | Role | Output |
|-------|------|--------|
| **Tactical Agent** | Head Coach persona | Actionable game plans, player matchups, phase strategies |
| **Data Agent** | Analyst persona | Statistics, trends, historical comparisons, probabilities |
| **Evaluator Agent** | Strategist persona | Risk assessment, confidence scoring, alternative scenarios |

## Sample Input/Output

### Input
```
Role: Tactical Agent
Query: "We're playing CSK at Chepauk next week. They've won 76% of home games.
        What's our batting strategy?"
```

### Output
```
Tactical Agent Response:

"Given CSK's 76% home win rate at Chepauk, here's your batting strategy:

1. Powerplay (Overs 1-6): Target 45-50 runs. CSK's new ball bowlers 
   average 0.54 runs/ball in powerplay. Use aggressive left-right 
   combinations to disrupt their line.

2. Middle Overs (7-15): Preserve wickets. CSK's spin duo typically 
   bowls 8 overs in this phase with 0.48 runs/ball economy. 
   Rotate strike, avoid risky shots over mid-wicket.

3. Death Overs (16-20): If 2+ wickets in hand, target 10-12 runs/over. 
   CSK concedes 0.57 runs/ball in death overs. Pre-identify 
   finishers for specific bowler matchups.

Key Matchup: Your right-handers vs their off-spinner—historical SR 145.
             Use this advantage in overs 8-12."
```

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/ATULPS2001/cricket-ai-council.git
cd cricket-ai-council
pip3 install -r requirements.txt

# 2. Set API key
export GOOGLE_API_KEY="your-gemini-api-key"

# 3. Run the council
python3 cli_council.py
```

## Project Structure

```
cricket-ai-council/
├── agents/              # AI agent implementations
│   ├── base_agent.py
│   ├── tactical_agent.py
│   ├── data_agent.py
│   └── evaluator_agent.py
├── analysis/            # Data analytics engine
│   └── insights.py
├── orchestrator/        # Query routing & synthesis
├── data/processed/      # Match data (CSV)
├── examples/            # Demo scripts
├── docs/                # Architecture & design docs
├── requirements.txt
└── README.md
```

## Data Sources

- Ball-by-ball delivery data from IPL matches (2008-2024)
- Match results, toss decisions, venue statistics
- Processed into `matches.csv` and `deliveries.csv`

## License

MIT License
