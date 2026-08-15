# Council Member Design Specifications

This document defines the role, data sources, and reasoning strategy for each agent in the Cricket AI Council. Each agent is designed to have a distinct analytical lens so that disagreements are meaningful, not just prompt noise.

---

## 1. Stats Agent (✅ Implemented)

**Role:** Long-run historical baseline — answers "what usually happens" based on career aggregates and head-to-head records.

**Data sources:**
- `matches.csv`: team-level win/loss records, venue history
- `deliveries.csv`: career batting averages, strike rates, bowling economy, wicket tallies

**Reasoning strategy:**
- Computes career-level aggregates for all players (batting average, strike rate, bowling average, economy)
- Computes team-level win percentages at specific venues and overall
- For toss-bat gamble questions: filters to historical matches between the two teams at the specified venue (or all venues if unspecified), computes win percentages, predicts the team with higher win %, confidence = max(win%, 1-win%)
- For top-scorer questions: ranks candidate batters by career average (not total runs — avoids bias toward players with more innings), returns top candidate with fixed confidence 0.6
- For head-to-head questions: compares two players' career averages at a venue (or overall), predicts the higher-average player, confidence scaled by the magnitude of the difference

**Known limitations:**
- Ignores recent form entirely (a player's 2024 performance is weighted the same as their 2008 performance)
- No context adjustment (pitch conditions, weather, toss impact, injuries)
- Cannot handle in-match state (e.g., "Team A needs 12 runs off 8 balls, 3 wickets in hand")

---

## 2. Form Agent (🚧 Planned)

**Role:** Recent-form weighting — answers "who's hot right now" by prioritizing the last 5-10 innings over career aggregates.

**Data sources:**
- `deliveries.csv`: filtered to most recent N innings per player
- `matches.csv`: filtered to most recent N matches per team

**Reasoning strategy:**
- For each player, computes rolling averages over last 5/10 innings (batting average, strike rate, bowling economy)
- For teams, computes win percentage in last 10 matches
- For toss-bat gamble: weights recent team form (last 10 matches) at 70%, overall historical record at 30%
- For top-scorer: ranks candidates by last-10-innings average, not career average
- Confidence scaled by sample size (e.g., if a player has only 2 recent innings, confidence is downweighted)

**Key design decisions:**
- Window size: 10 innings for batters, 10 matches for teams (tunable hyperparameter)
- Recency weighting: exponential decay (most recent innings weighted 2x the 10th-most recent) vs. simple rolling average — TBD which performs better in backtest
- Handles players with <5 recent innings by falling back to career average with reduced confidence

**Expected to disagree with Stats Agent when:**
- A veteran player with strong career stats is in a prolonged slump
- A young player with limited career data is on a hot streak
- A team's recent form diverges sharply from their historical record (e.g., a traditionally weak team that just signed star players)

---

## 3. Conditions Agent (🚧 Planned)

**Role:** Context adjustment — answers "how do pitch, weather, toss, and venue characteristics affect this specific match?"

**Data sources:**
- `matches.csv`: venue-level statistics (average first-innings score, win % batting first vs. chasing, day/night split)
- External APIs (planned): pitch report, weather forecast, dew probability
- Toss decision and match type (league vs. knockout)

**Reasoning strategy:**
- For each venue, computes:
  - Average first-innings score
  - Win percentage batting first vs. chasing
  - Day match vs. night match win splits (dew factor)
  - Boundary size / ground dimensions (if available in metadata)
- For toss-bat gamble:
  - If venue strongly favors chasing (e.g., >60% win rate chasing), predicts team that won toss and chose to field
  - If venue strongly favors batting first, predicts team that won toss and chose to bat
  - Adjusts prediction based on dew probability (night matches in certain venues)
- For player-specific questions:
  - Adjusts batter projections based on venue characteristics (e.g., spin-friendly pitches favor certain batters)
  - Adjusts bowler projections based on pitch type (pace vs. spin)

**Key design decisions:**
- Venue-level stats computed from all historical matches at that venue (no recency weighting — ground characteristics are stable)
- Toss decision treated as a strong signal (teams don't choose bat/field randomly)
- Weather/dew data: initially hardcoded heuristics (e.g., "night matches in Mumbai/Chennai = dew factor"), later integrated from live API

**Expected to disagree with Stats/Form Agents when:**
- A strong team's historical record is at a venue that strongly favors the opposition's style (e.g., a spin-heavy team at a pace-friendly venue)
- Toss winner makes an unconventional decision (e.g., batting first at a venue where chasing usually wins)
- Weather conditions deviate from normal (e.g., rain-affected match, unusual dew)

---

## 4. Momentum Agent (🚧 Planned)

**Role:** In-match state tracking — answers "given the current game state (score, wickets, overs remaining), which team is favored to win?"

**Data sources:**
- `deliveries.csv`: ball-by-ball sequence for live state updates
- Real-time match feed (planned): live score API for in-progress matches

**Reasoning strategy:**
- Maintains running match state: current score, wickets fallen, overs bowled, required run rate (if chasing)
- Computes win probability after each ball using:
  - Historical win rates for similar game states (e.g., "120/3 after 15 overs, chasing 160" → X% win rate historically)
  - Required run rate vs. current run rate
  - Wickets in hand vs. overs remaining
- For toss-bat gamble (pre-match): not applicable — this agent only activates once the match starts
- For in-match questions: updates win probability ball-by-ball, accounts for momentum shifts (e.g., quick wickets, rapid scoring)

**Key design decisions:**
- Sequential processing: unlike other agents, this agent cannot run in parallel fan-out — it must process deliveries in order to maintain correct state
- State representation: discrete buckets (e.g., "100-120 runs, 2-4 wickets, 12-15 overs") vs. continuous features — TBD which generalizes better
- Cold-start problem: for novel game states with no historical precedent, falls back to simple run-rate comparison

**Expected to disagree with other agents when:**
- A team with weak historical stats is winning comfortably in a specific match
- A strong team is in trouble (e.g., early wickets, high required run rate)
- Momentum swings rapidly (e.g., 3 wickets in 10 balls, or 30 runs in 2 overs)

---

## 5. Arbitrator (🚧 Planned)

**Role:** Conflict resolution — receives predictions from all active agents, resolves disagreements, assigns final confidence.

**Data sources:**
- All agent verdicts (prediction + confidence + reasoning text)
- Match context (venue, toss, match type, weather if available)

**Reasoning strategy:**
- Receives 3-4 agent verdicts (Stats, Form, Conditions, optionally Momentum)
- If all agents agree: synthesizes into single verdict with high confidence (max of individual confidences + bonus for unanimity)
- If agents disagree:
  - Weights agents by domain relevance (e.g., Conditions Agent weighted higher for toss-bat gamble, Momentum Agent weighted higher for in-match questions)
  - Applies domain-specific rules (e.g., "if Conditions Agent predicts toss-bat winner with >0.7 confidence and venue has strong historical bias, override Stats/Form")
  - Computes final confidence as weighted average of individual confidences, adjusted for agreement level
- Outputs final verdict + confidence + explanation of which agents were overruled and why

**Key design decisions:**
- Hardcoded weighting rules for v1 (e.g., Conditions 0.4, Stats 0.3, Form 0.3 for toss-bat gamble), later replaced with learned weights from backtest
- No LLM-based judge for v1 — keeps it simple, interpretable, and fast
- Handles missing agents gracefully (e.g., if Momentum Agent isn't implemented yet, re-normalizes weights among remaining agents)

**Expected to overrule agents when:**
- Stats Agent predicts based on career averages but Conditions Agent identifies a strong venue bias that historically overrides career stats
- Form Agent is overconfident based on small sample size (e.g., player with 3 recent innings)
- Agents are evenly split (e.g., 2-2) and a tiebreaker rule applies (e.g., home team advantage, toss decision)

---

## 6. Synthesizer (🚧 Planned)

**Role:** Final output generation — formats the Arbitrator's verdict into human-readable explanation with confidence score.

**Data sources:**
- Arbitrator's final verdict + confidence + reasoning
- Individual agent verdicts (for attribution: "Stats Agent predicted X, Conditions Agent predicted Y, final decision: X because...")

**Reasoning strategy:**
- Generates structured output:
  - Final prediction (team/player name)
  - Confidence score (0.0-1.0)
  - One-paragraph explanation summarizing key factors
  - Optional: breakdown of which agents agreed/disagreed
- For UI integration: outputs JSON with fields for frontend display (prediction, confidence, reasoning, agent breakdown)

**Key design decisions:**
- No additional reasoning — purely formatting, not a second arbitration layer
- Keeps explanation concise (2-3 sentences) for UI readability
- Includes confidence calibration note if confidence is low (<0.5) or high (>0.9)

---

## Agent Interaction Pattern

```
Question → Router → [Stats, Form, Conditions, Momentum] → Arbitrator → Synthesizer → Final Verdict
```

- **Parallel fan-out:** Stats, Form, Conditions run in parallel (independent data sources)
- **Sequential exception:** Momentum runs last, consuming other agents' outputs if in-match question
- **Arbitration:** Weighted voting with domain-specific rules, not simple majority
- **Synthesis:** Formatting only, no additional reasoning
