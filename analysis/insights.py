"""Cricket trend analytics built from innings-aware ball-by-ball data."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).parent.parent / "data" / "processed"


class CricketInsights:
    """Coach-facing historical insights derived from matches and deliveries data."""

    def __init__(self, matches: pd.DataFrame, deliveries: pd.DataFrame):
        self.matches = matches.copy()
        self.deliveries = deliveries.copy()
        self._normalise_inputs()
        self.innings = self._build_innings_table()

    def _normalise_inputs(self) -> None:
        self.matches["match_id"] = self.matches["match_id"].astype(str)
        self.deliveries["match_id"] = self.deliveries["match_id"].astype(str)

        # Derive is_wicket from player_out
        if "is_wicket" not in self.deliveries:
            self.deliveries["is_wicket"] = self.deliveries["player_out"].notna().astype(int)

        # Derive bowling_team from team1/team2 vs batting_team
        matches_teams = self.matches[["match_id", "team1", "team2"]].drop_duplicates()
        self.deliveries = self.deliveries.merge(matches_teams, on="match_id", how="left")
        self.deliveries["bowling_team"] = np.where(
            self.deliveries["batting_team"] == self.deliveries["team1"],
            self.deliveries["team2"],
            self.deliveries["team1"],
        )

    def _build_innings_table(self) -> pd.DataFrame:
        """Build per-innings aggregates from deliveries."""
        required = ["match_id", "innings", "batting_team", "runs_total", "is_wicket", "actual_delivery"]
        missing = [c for c in required if c not in self.deliveries]
        if missing:
            raise ValueError(f"deliveries missing: {missing}")

        innings = self.deliveries.groupby(["match_id", "innings", "batting_team"], as_index=False).agg(
            runs=("runs_total", "sum"),
            wickets=("is_wicket", "sum"),
            legal_balls=("actual_delivery", "sum"),
        )
        innings["run_rate"] = np.where(
            innings["legal_balls"] > 0,
            innings["runs"] / innings["legal_balls"] * 6,
            np.nan,
        )
        innings = innings.merge(self.matches, on="match_id", how="left", suffixes=("", "_match"))
        innings["innings_rank"] = innings.groupby("match_id")["innings"].rank(method="first")
        innings["is_first_innings"] = innings["innings_rank"].eq(1)
        innings["is_chase"] = ~innings["is_first_innings"]

        first = innings[innings["is_first_innings"]][["match_id", "runs"]].rename(columns={"runs": "target_base"})
        innings = innings.merge(first, on="match_id", how="left")
        innings["target"] = np.where(innings["is_chase"], innings["target_base"] + 1, np.nan)
        innings["won"] = innings["batting_team"].eq(innings["winner"])
        return innings

    def phase_performance(self, team: Optional[str] = None) -> pd.DataFrame:
        """Batting and bowling impact in the powerplay (overs 0-5) and death (15-19)."""
        balls = self.deliveries.copy()
        balls["phase"] = np.select(
            [balls["over"].between(0, 5), balls["over"].between(15, 19)],
            ["powerplay", "death"],
            default="middle",
        )
        balls = balls[balls["phase"].isin(["powerplay", "death"])]
        if team:
            balls = balls[(balls["batting_team"] == team) | (balls["bowling_team"] == team)]

        batting = balls.groupby(["batting_team", "phase"], as_index=False).agg(
            batting_runs=("runs_total", "sum"),
            legal_balls=("actual_delivery", "sum"),
            wickets_lost=("is_wicket", "sum"),
            matches=("match_id", "nunique"),
        )
        batting["batting_rr"] = batting["batting_runs"] / batting["legal_balls"].replace(0, np.nan) * 6

        bowling = balls.groupby(["bowling_team", "phase"], as_index=False).agg(
            bowling_runs=("runs_total", "sum"),
            bowling_balls=("actual_delivery", "sum"),
            wickets_taken=("is_wicket", "sum"),
        ).rename(columns={"bowling_team": "team"})
        bowling["bowling_economy"] = bowling["bowling_runs"] / bowling["bowling_balls"].replace(0, np.nan) * 6

        result = batting.rename(columns={"batting_team": "team"}).merge(bowling, on=["team", "phase"], how="left")
        return result.sort_values(["phase", "batting_rr"], ascending=[True, False]).reset_index(drop=True)

    def chase_success_by_target(self) -> pd.DataFrame:
        """Chase success and finish profile by target bracket."""
        chases = self.innings[self.innings["is_chase"] & self.innings["target"].notna()].copy()
        bins = [0, 140, 160, 180, 200, np.inf]
        labels = ["<=140", "141-160", "161-180", "181-200", "201+"]
        chases["target_bracket"] = pd.cut(chases["target"], bins=bins, labels=labels, include_lowest=True)
        return chases.groupby("target_bracket", observed=False).agg(
            chases=("match_id", "nunique"),
            successful_chases=("won", "sum"),
            chase_win_pct=("won", "mean"),
            avg_target=("target", "mean"),
            avg_wickets_lost=("wickets", "mean"),
            avg_chase_rr=("run_rate", "mean"),
        ).reset_index()

    def toss_conversion_by_venue(self, minimum_matches: int = 10) -> pd.DataFrame:
        """Toss winner's match conversion by venue and decision."""
        m = self.matches.copy()
        m["toss_winner_won"] = m["toss_winner"].eq(m["winner"])
        result = m.groupby(["venue", "toss_decision"], as_index=False).agg(
            matches=("match_id", "nunique"),
            toss_winner_wins=("toss_winner_won", "sum"),
            toss_winner_win_pct=("toss_winner_won", "mean"),
        )
        return result[result["matches"] >= minimum_matches].sort_values(
            ["toss_winner_win_pct", "matches"], ascending=[False, False]
        )

    def team_venue_dominance(self, minimum_matches: int = 5) -> pd.DataFrame:
        """Team-venue win% (historical dominance)."""
        played = self.innings[["match_id", "venue", "batting_team", "won"]].drop_duplicates("match_id")
        result = played.groupby(["batting_team", "venue"], as_index=False).agg(
            matches=("match_id", "nunique"),
            wins=("won", "sum"),
            win_pct=("won", "mean"),
        ).rename(columns={"batting_team": "team"})
        return result[result["matches"] >= minimum_matches].sort_values(
            ["win_pct", "matches"], ascending=[False, False]
        )

    def collapse_and_recovery(self) -> pd.DataFrame:
        """3+ wickets in any 2-over window; did the side still win?"""
        balls = self.deliveries.sort_values(["match_id", "innings", "over"]).copy()
        over_wickets = balls.groupby(["match_id", "innings", "batting_team", "over"], as_index=False)["is_wicket"].sum()
        over_wickets["two_over_wickets"] = over_wickets.groupby(["match_id", "innings"])["is_wicket"].transform(
            lambda s: s.rolling(2, min_periods=2).sum()
        )
        collapses = over_wickets[over_wickets["two_over_wickets"] >= 3][["match_id", "innings", "batting_team"]].drop_duplicates()
        collapses = collapses.merge(
            self.innings[["match_id", "innings", "batting_team", "won"]],
            on=["match_id", "innings", "batting_team"],
            how="left",
        )
        return collapses.groupby("batting_team", as_index=False).agg(
            collapse_innings=("match_id", "nunique"),
            recovered_to_win=("won", "sum"),
            recovery_win_pct=("won", "mean"),
        ).rename(columns={"batting_team": "team"}).sort_values("collapse_innings", ascending=False)

    def margin_trends(self) -> pd.DataFrame:
        """Close-game frequency by season using win_by_runs / win_by_wickets."""
        m = self.matches.copy()
        m["is_close_run_win"] = m["win_by_runs"].fillna(0).le(10) & m["win_by_runs"].notna()
        m["is_close_wicket_win"] = m["win_by_wickets"].fillna(0).le(2) & m["win_by_wickets"].notna()
        return m.groupby("season", as_index=False).agg(
            matches=("match_id", "nunique"),
            close_run_games=("is_close_run_win", "sum"),
            close_wicket_games=("is_close_wicket_win", "sum"),
        )

    def h2h_analysis(self, team1: str, team2: str, recent_n: Optional[int] = None) -> dict[str, Any]:
        """Head-to-head between two teams."""
        h2h = self.matches[
            ((self.matches["team1"] == team1) & (self.matches["team2"] == team2)) |
            ((self.matches["team1"] == team2) & (self.matches["team2"] == team1))
        ].copy()
        if "dates" in h2h:
            h2h = h2h.sort_values("dates")
        if recent_n:
            h2h = h2h.tail(recent_n)
        decisive = h2h[h2h["winner"].isin([team1, team2])]
        return {
            "team1": team1,
            "team2": team2,
            "matches": len(decisive),
            "team1_wins": int(decisive["winner"].eq(team1).sum()),
            "team2_wins": int(decisive["winner"].eq(team2).sum()),
            "team1_win_pct": float(decisive["winner"].eq(team1).mean()) if len(decisive) else np.nan,
        }


if __name__ == "__main__":
    matches = pd.read_csv(DATA_DIR / "matches.csv")
    deliveries = pd.read_csv(DATA_DIR / "deliveries.csv")
    insights = CricketInsights(matches, deliveries)
    print("Powerplay & death-over performance")
    print(insights.phase_performance().head(12).to_string(index=False))
    print("\nChase success by target")
    print(insights.chase_success_by_target().to_string(index=False))
    print("\nToss conversion by venue")
    print(insights.toss_conversion_by_venue().head(15).to_string(index=False))
