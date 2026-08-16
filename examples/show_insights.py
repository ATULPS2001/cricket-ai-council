"""Demo: showcase the new innings-aware insights module."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis.insights import CricketInsights

DATA_DIR = ROOT / "data" / "processed"


def fmt_table(df: pd.DataFrame, title: str, head: int = 12) -> None:
    print(f"\n{'='*70}")
    print(title)
    print('='*70)
    print(df.head(head).to_string(index=False))


def main() -> None:
    print("Loading matches and deliveries...")
    matches = pd.read_csv(DATA_DIR / "matches.csv")
    deliveries = pd.read_csv(DATA_DIR / "deliveries.csv")

    insights = CricketInsights(matches, deliveries)

    # 1. Phase performance (powerplay & death)
    phase = insights.phase_performance()
    fmt_table(phase, "Phase Performance (Powerplay & Death) – All Teams")

    # 2. Chase success by target bracket
    chase = insights.chase_success_by_target()
    fmt_table(chase, "Chase Success by Target Bracket")

    # 3. Toss conversion by venue
    toss = insights.toss_conversion_by_venue(minimum_matches=10)
    fmt_table(toss, "Toss-Winner Match Conversion by Venue (min 10 matches)")

    # 4. Team-venue dominance
    dominance = insights.team_venue_dominance(minimum_matches=5)
    fmt_table(dominance, "Team–Venue Dominance (min 5 matches)")

    # 5. Collapse & recovery
    collapse = insights.collapse_and_recovery()
    fmt_table(collapse, "Collapse & Recovery by Team")

    # 6. Margin trends (close games)
    margins = insights.margin_trends()
    fmt_table(margins, "Close-Game Trends by Season")

    # 7. Example H2H
    h2h = insights.h2h_analysis("Mumbai Indians", "Chennai Super Kings", recent_n=10)
    print(f"\n{'='*70}")
    print("Example H2H (last 10 decisive MI vs CSK)")
    print('='*70)
    print(f"Matches: {h2h['matches']}")
    print(f"Mumbai Indians wins: {h2h['team1_wins']} ({h2h['team1_win_pct']:.1%})")
    csk_win_pct = 1 - h2h['team1_win_pct'] if not pd.isna(h2h['team1_win_pct']) else float('nan')
    print(f"Chennai Super Kings wins: {h2h['team2_wins']} ({csk_win_pct:.1%})")


if __name__ == "__main__":
    main()
