"""MCP Server for Cricket AI Council - exposes cricket data tools."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

import pandas as pd

# ─── Config ───────────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).parent / "data" / "processed"


# ─── MCP Client ───────────────────────────────────────────────────────────────


class CricketMCPClient:
    """Client for cricket data tools (MCP-style interface)."""

    def __init__(self):
        self.matches = None
        self.deliveries = None
        self._load_data()

    def _load_data(self):
        """Lazy-load CSVs."""
        if self.matches is None:
            matches_path = DATA_DIR / "matches.csv"
            deliveries_path = DATA_DIR / "deliveries.csv"
            if matches_path.exists():
                self.matches = pd.read_csv(matches_path)
            if deliveries_path.exists():
                self.deliveries = pd.read_csv(deliveries_path)

    def get_team_stats(self, team: str, phase: str = "death") -> dict[str, Any]:
        """
        Get team batting/bowling stats for a phase.
        
        Args:
            team: Team name (e.g., "Mumbai Indians")
            phase: "powerplay" (0-5) or "death" (15-19)
        
        Returns:
            Dict with batting_rr, bowling_economy, matches
        """
        if self.deliveries is None:
            return {"error": "Data not loaded"}

        # Derive bowling_team
        deliveries = self.deliveries.copy()
        if "bowling_team" not in deliveries.columns:
            matches_teams = self.matches[["match_id", "team1", "team2"]].drop_duplicates()
            deliveries = deliveries.merge(matches_teams, on="match_id", how="left")
            deliveries["bowling_team"] = deliveries.apply(
                lambda row: row["team2"] if row["batting_team"] == row["team1"] else row["team1"],
                axis=1,
            )

        # Filter by phase
        over_col = "over" if "over" in deliveries.columns else "over_number"
        if phase == "powerplay":
            phase_mask = deliveries[over_col].between(0, 5)
        elif phase == "death":
            phase_mask = deliveries[over_col].between(15, 19)
        else:
            return {"error": f"Unknown phase: {phase}"}

        phase_balls = deliveries[phase_mask]

        # Batting stats
        team_batting = phase_balls[phase_balls["batting_team"] == team]
        if len(team_batting) == 0:
            return {"error": f"No data for {team}"}

        batting_runs = team_batting["runs_total"].sum()
        batting_balls = team_batting["actual_delivery"].sum()
        batting_rr = (batting_runs / batting_balls * 6) if batting_balls > 0 else 0

        # Bowling stats
        team_bowling = phase_balls[phase_balls["bowling_team"] == team]
        bowling_runs = team_bowling["runs_total"].sum()
        bowling_balls = team_bowling["actual_delivery"].sum()
        bowling_econ = (bowling_runs / bowling_balls * 6) if bowling_balls > 0 else 0

        return {
            "team": team,
            "phase": phase,
            "batting_runs": batting_runs,
            "batting_balls": batting_balls,
            "batting_rr": round(batting_rr, 3),
            "bowling_runs": bowling_runs,
            "bowling_balls": bowling_balls,
            "bowling_economy": round(bowling_econ, 3),
            "matches": phase_balls["match_id"].nunique(),
        }

    def get_venue_record(self, team: str, venue_keyword: str) -> dict[str, Any]:
        """
        Get team's win record at a venue (partial match).
        
        Args:
            team: Team name
            venue_keyword: Venue keyword (e.g., "Chepauk", "Wankhede")
        
        Returns:
            Dict with matches, wins, win_pct
        """
        if self.matches is None:
            return {"error": "Data not loaded"}

        matches = self.matches[self.matches["venue"].str.contains(venue_keyword, case=False, na=False)]
        team_matches = matches[(matches["team1"] == team) | (matches["team2"] == team)]

        if len(team_matches) == 0:
            return {"error": f"No matches found for {team} at {venue_keyword}"}

        wins = team_matches[team_matches["winner"] == team]
        win_pct = len(wins) / len(team_matches) if len(team_matches) > 0 else 0

        return {
            "team": team,
            "venue_keyword": venue_keyword,
            "matches": len(team_matches),
            "wins": len(wins),
            "win_pct": round(win_pct, 3),
            "venue_name": team_matches["venue"].iloc[0] if len(team_matches) > 0 else None,
        }

    def get_h2h(self, team1: str, team2: str, recent_n: Optional[int] = None) -> dict[str, Any]:
        """
        Get head-to-head record between two teams.
        
        Args:
            team1: First team
            team2: Second team
            recent_n: If specified, only last N matches
        
        Returns:
            Dict with matches, team1_wins, team2_wins, team1_win_pct
        """
        if self.matches is None:
            return {"error": "Data not loaded"}

        h2h = self.matches[
            ((self.matches["team1"] == team1) & (self.matches["team2"] == team2)) |
            ((self.matches["team1"] == team2) & (self.matches["team2"] == team1))
        ].copy()

        if len(h2h) == 0:
            return {"error": f"No matches found between {team1} and {team2}"}

        # Sort by date
        if "dates" in h2h.columns:
            h2h = h2h.sort_values("dates")

        if recent_n:
            h2h = h2h.tail(recent_n)

        # Exclude ties/no-results
        decisive = h2h[h2h["winner"].isin([team1, team2])]

        team1_wins = decisive[decisive["winner"] == team1]
        team2_wins = decisive[decisive["winner"] == team2]

        return {
            "team1": team1,
            "team2": team2,
            "matches": len(decisive),
            "team1_wins": len(team1_wins),
            "team2_wins": len(team2_wins),
            "team1_win_pct": round(len(team1_wins) / len(decisive), 3) if len(decisive) > 0 else 0,
            "recent_n": recent_n,
        }


# ─── CLI Test ─────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    mcp = CricketMCPClient()

    print("=== Test: Team Stats ===")
    stats = mcp.get_team_stats("Chennai Super Kings", phase="death")
    print(stats)

    print("\n=== Test: Venue Record ===")
    venue = mcp.get_venue_record("Chennai Super Kings", "Chepauk")
    print(venue)

    print("\n=== Test: H2H ===")
    h2h = mcp.get_h2h("Mumbai Indians", "Chennai Super Kings", recent_n=10)
    print(h2h)
