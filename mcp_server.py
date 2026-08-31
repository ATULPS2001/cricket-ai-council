"""MCP Server - Cricket data tools for the AI Council."""
from __future__ import annotations

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).parent / "data" / "processed"


class MCPCricketTools:
    """MCP-compatible tools for cricket data access."""

    def __init__(self):
        self.matches = None
        self.deliveries = None
        self._load_data()

    def _load_data(self):
        """Lazy-load data files."""
        if self.matches is None:
            matches_path = DATA_DIR / "matches.csv"
            if matches_path.exists():
                self.matches = pd.read_csv(matches_path)
            else:
                self.matches = pd.DataFrame()

        if self.deliveries is None:
            deliveries_path = DATA_DIR / "deliveries.csv"
            if deliveries_path.exists():
                self.deliveries = pd.read_csv(deliveries_path)
            else:
                self.deliveries = pd.DataFrame()

    def get_team_stats(self, team: str, phase: str = "all") -> str:
        """Get team statistics for a specific phase (powerplay, death, or all)."""
        if self.deliveries.empty:
            return "⚠️ No deliveries data available"

        deliveries = self.deliveries.copy()
        if "bowling_team" not in deliveries.columns:
            matches_teams = self.matches[["match_id", "team1", "team2"]].drop_duplicates() if not self.matches.empty else pd.DataFrame()
            if not matches_teams.empty:
                deliveries = deliveries.merge(matches_teams, on="match_id", how="left")
                deliveries["bowling_team"] = np.where(
                    deliveries["batting_team"] == deliveries["team1"],
                    deliveries["team2"],
                    deliveries["team1"],
                )

        team_batting = deliveries[deliveries["batting_team"] == team]

        if phase == "powerplay":
            team_batting = team_batting[team_batting["over"].between(0, 5)]
        elif phase == "death":
            team_batting = team_batting[team_batting["over"].between(15, 19)]

        if team_batting.empty:
            return f"No data found for {team} in {phase} phase"

        total_runs = team_batting["runs_total"].sum()
        total_balls = team_batting["actual_delivery"].sum()
        total_wickets = team_batting["is_wicket"].sum()
        run_rate = (total_runs / total_balls * 6) if total_balls > 0 else 0

        return f"""**{team} - {phase.upper()} Phase**
- Total Runs: {total_runs}
- Total Balls: {total_balls}
- Total Wickets: {total_wickets}
- Run Rate: {run_rate:.2f} runs/over ({total_runs/max(total_balls,1):.2f} runs/ball)
- Matches: {team_batting['match_id'].nunique()}"""

    def get_venue_record(self, team: str, venue: str) -> str:
        """Get team's win record at a specific venue."""
        if self.matches.empty:
            return "⚠️ No matches data available"

        venue_matches = self.matches[self.matches["venue"].str.contains(venue, case=False, na=False)]

        if venue_matches.empty:
            return f"No matches found at venue: {venue}"

        team_wins = venue_matches[venue_matches["winner"] == team]
        total_matches = len(venue_matches)
        wins = len(team_wins)
        win_pct = (wins / total_matches * 100) if total_matches > 0 else 0

        return f"""**{team} at {venue}**
- Total Matches: {total_matches}
- Wins: {wins}
- Losses: {total_matches - wins}
- Win Percentage: {win_pct:.1f}%"""

    def get_h2h(self, team1: str, team2: str, recent_n: Optional[int] = None) -> str:
        """Get head-to-head record between two teams."""
        if self.matches.empty:
            return "⚠️ No matches data available"

        h2h = self.matches[
            ((self.matches["team1"] == team1) & (self.matches["team2"] == team2)) |
            ((self.matches["team1"] == team2) & (self.matches["team2"] == team1))
        ]

        if h2h.empty:
            return f"No matches found between {team1} and {team2}"

        if "dates" in h2h.columns:
            h2h = h2h.sort_values("dates")
        if recent_n:
            h2h = h2h.tail(recent_n)

        team1_wins = len(h2h[h2h["winner"] == team1])
        team2_wins = len(h2h[h2h["winner"] == team2])
        total = len(h2h)

        return f"""**H2H: {team1} vs {team2}** (last {len(h2h)} matches)
- {team1} wins: {team1_wins} ({team1_wins/total*100:.1f}%)
- {team2} wins: {team2_wins} ({team2_wins/total*100:.1f}%)
- Total matches: {total}"""

    def get_toss_conversion(self, venue: str) -> str:
        """Get toss winner's match conversion rate at a venue."""
        if self.matches.empty:
            return "⚠️ No matches data available"

        venue_matches = self.matches[self.matches["venue"].str.contains(venue, case=False, na=False)]

        if venue_matches.empty:
            return f"No matches found at venue: {venue}"

        venue_matches = venue_matches.copy()
        venue_matches["toss_winner_won"] = venue_matches["toss_winner"] == venue_matches["winner"]

        total = len(venue_matches)
        toss_wins = venue_matches["toss_winner_won"].sum()
        conversion_pct = (toss_wins / total * 100) if total > 0 else 0

        field_first = venue_matches[venue_matches["toss_decision"] == "field"]
        field_conversion = (field_first["toss_winner_won"].mean() * 100) if not field_first.empty else 0

        bat_first = venue_matches[venue_matches["toss_decision"] == "bat"]
        bat_conversion = (bat_first["toss_winner_won"].mean() * 100) if not bat_first.empty else 0

        return f"""**Toss Conversion at {venue}**
- Total matches: {total}
- Toss winner won: {toss_wins} ({conversion_pct:.1f}%)
- Field first conversion: {field_conversion:.1f}% ({len(field_first)} matches)
- Bat first conversion: {bat_conversion:.1f}% ({len(bat_first)} matches)"""


if __name__ == "__main__":
    tools = MCPCricketTools()

    print("="*70)
    print("TEST: Team Stats (MI, death)")
    print("="*70)
    print(tools.get_team_stats("Mumbai Indians", "death"))

    print("\n" + "="*70)
    print("TEST: Venue Record (CSK at Chepauk)")
    print("="*70)
    print(tools.get_venue_record("Chennai Super Kings", "Chepauk"))

    print("\n" + "="*70)
    print("TEST: H2H (MI vs CSK)")
    print("="*70)
    print(tools.get_h2h("Mumbai Indians", "Chennai Super Kings", recent_n=10))

    print("\n" + "="*70)
    print("TEST: Toss Conversion (Wankhede)")
    print("="*70)
    print(tools.get_toss_conversion("Wankhede"))
