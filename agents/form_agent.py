"""
Form Agent - Recent form and momentum analysis for IPL teams.

Analyzes:
- Last 5 matches: win%, batting run rate, death-over bowling economy
- Recent H2H record (last 5 meetings)
- Form differential between two teams

Query format:
{
    "type": "form_check",
    "teams": ["Team A", "Team B"],
    "venue": "optional",
    "match_id": "optional - for time-aware form (matches before this one)"
}

Returns Verdict with prediction, confidence, reasoning.
"""
from dataclasses import dataclass
from typing import Optional, List
import pandas as pd
import numpy as np


@dataclass
class Verdict:
    prediction: str
    confidence: float
    reasoning: str


class FormAgent:
    def __init__(self, matches: pd.DataFrame, deliveries: pd.DataFrame):
        self.matches = matches.copy()
        self.deliveries = deliveries.copy()
        
        # Precompute match order within seasons for "last N matches" logic
        self.matches = self.matches.sort_values(['season_int', 'match_id']).reset_index(drop=True)
        
        # Precompute team-level aggregates per match
        self._precompute_team_stats()
    
    def _precompute_team_stats(self):
        """Precompute batting RR and death-over economy per team per match."""
        # Add bowling_team = the team not batting
        self.deliveries = self.deliveries.copy()
        
        # Get team1/team2 from matches for each match_id
        match_teams = self.matches[['match_id', 'team1', 'team2']].drop_duplicates()
        self.deliveries = self.deliveries.merge(match_teams, on='match_id', how='left')
        self.deliveries['bowling_team'] = self.deliveries.apply(
            lambda row: row['team2'] if row['batting_team'] == row['team1'] else row['team1'],
            axis=1
        )
        
        # Batting: runs per over per team per match
        batting = self.deliveries.groupby(['match_id', 'batting_team']).agg(
            total_runs=('runs_total', 'sum'),
            total_balls=('actual_delivery', 'count')
        ).reset_index()
        batting['run_rate'] = batting['total_runs'] / (batting['total_balls'] / 6)
        batting = batting[['match_id', 'batting_team', 'run_rate']]
        
        # Bowling: death-over economy (overs 15-19, i.e., 16th-20th over) per team per match
        death_overs = self.deliveries[(self.deliveries['over'] >= 15) & (self.deliveries['over'] <= 19)]
        bowling = death_overs.groupby(['match_id', 'bowling_team']).agg(
            death_runs=('runs_total', 'sum'),
            death_balls=('actual_delivery', 'count')
        ).reset_index()
        bowling['death_economy'] = bowling['death_runs'] / (bowling['death_balls'] / 6)
        bowling = bowling[['match_id', 'bowling_team', 'death_economy']]
        
        # Create lookup dicts for fast access
        self.batting_lookup = batting.set_index(['match_id', 'batting_team'])['run_rate'].to_dict()
        self.bowling_lookup = bowling.set_index(['match_id', 'bowling_team'])['death_economy'].to_dict()
    
    def _get_batting_rr(self, match_id: int, team: str) -> Optional[float]:
        """Get batting run rate for a team in a specific match."""
        return self.batting_lookup.get((match_id, team), None)
    
    def _get_bowling_economy(self, match_id: int, team: str) -> Optional[float]:
        """Get death-over bowling economy for a team in a specific match."""
        return self.bowling_lookup.get((match_id, team), None)
    
    def _get_last_n_matches(self, team: str, n: int = 5, before_match_id: Optional[int] = None) -> pd.DataFrame:
        """Get last N matches for a team, optionally before a specific match_id."""
        team_matches = self.matches[
            (self.matches['team1'] == team) | (self.matches['team2'] == team)
        ].copy()
        
        if before_match_id is not None:
            team_matches = team_matches[team_matches['match_id'] < before_match_id]
        
        # Drop ties/no-results
        team_matches = team_matches[team_matches['winner'].notna()]
        team_matches = team_matches[~team_matches['result'].isin(['tie', 'no result'])]
        
        # Sort by season_int, match_id and take last N
        team_matches = team_matches.sort_values(['season_int', 'match_id']).tail(n)
        
        return team_matches
    
    def _compute_form_score(self, team: str, before_match_id: Optional[int] = None) -> dict:
        """Compute form score components for a team."""
        last_matches = self._get_last_n_matches(team, n=5, before_match_id=before_match_id)
        
        if len(last_matches) == 0:
            return {'win_pct': 0.5, 'batting_rr': 8.0, 'death_economy': 9.0, 'n_matches': 0}
        
        # Win%
        wins = ((last_matches['winner'] == team)).sum()
        win_pct = wins / len(last_matches)
        
        # Batting RR and death economy for each match
        batting_rrs = []
        death_economies = []
        for _, m in last_matches.iterrows():
            mid = m['match_id']
            # Batting RR: team could be team1 or team2
            rr = self._get_batting_rr(mid, team)
            if rr is not None:
                batting_rrs.append(rr)
            
            # Bowling economy
            econ = self._get_bowling_economy(mid, team)
            if econ is not None:
                death_economies.append(econ)
        
        batting_rr = np.mean(batting_rrs) if batting_rrs else 8.0
        death_economy = np.mean(death_economies) if death_economies else 9.0
        
        return {
            'win_pct': win_pct,
            'batting_rr': batting_rr,
            'death_economy': death_economy,
            'n_matches': len(last_matches)
        }
    
    def _get_h2h_recent(self, team1: str, team2: str, n: int = 5, before_match_id: Optional[int] = None) -> float:
        """Get team1's win% in last N H2H matches vs team2."""
        h2h = self.matches[
            ((self.matches['team1'] == team1) & (self.matches['team2'] == team2)) |
            ((self.matches['team1'] == team2) & (self.matches['team2'] == team1))
        ].copy()
        
        if before_match_id is not None:
            h2h = h2h[h2h['match_id'] < before_match_id]
        
        # Drop ties/no-results
        h2h = h2h[h2h['winner'].notna()]
        h2h = h2h[~h2h['result'].isin(['tie', 'no result'])]
        
        h2h = h2h.sort_values(['season_int', 'match_id']).tail(n)
        
        if len(h2h) == 0:
            return 0.5  # Neutral
        
        team1_wins = ((h2h['winner'] == team1)).sum()
        return team1_wins / len(h2h)
    
    def analyze(self, query: dict) -> Verdict:
        """
        Analyze form for two teams.
        
        Query:
        {
            "type": "form_check",
            "teams": ["Team A", "Team B"],
            "venue": "optional",
            "match_id": "optional - for time-aware form"
        }
        """
        teams = query['teams']
        match_id = query.get('match_id', None)
        
        if len(teams) != 2:
            return Verdict(
                prediction=teams[0] if teams else "Unknown",
                confidence=0.0,
                reasoning="Need exactly 2 teams for form analysis"
            )
        
        team1, team2 = teams[0], teams[1]
        
        # Compute form scores
        form1 = self._compute_form_score(team1, before_match_id=match_id)
        form2 = self._compute_form_score(team2, before_match_id=match_id)
        
        # H2H recent edge
        h2h_edge = self._get_h2h_recent(team1, team2, n=5, before_match_id=match_id)
        
        # Composite form score
        # Weights: 40% win%, 30% batting RR, 20% bowling economy (inverted), 10% H2H
        # Normalize: batting RR ~8-10 (higher=better), death economy ~8-12 (lower=better)
        batting_rr_norm = (form1['batting_rr'] - 7) / 4  # ~0.25-0.75 range
        death_econ_inv = (12 - form1['death_economy']) / 4  # Invert: lower economy = higher score
        
        score1 = (
            0.4 * form1['win_pct'] +
            0.3 * batting_rr_norm +
            0.2 * death_econ_inv +
            0.1 * h2h_edge
        )
        
        batting_rr_norm_2 = (form2['batting_rr'] - 7) / 4
        death_econ_inv_2 = (12 - form2['death_economy']) / 4
        
        score2 = (
            0.4 * form2['win_pct'] +
            0.3 * batting_rr_norm_2 +
            0.2 * death_econ_inv_2 +
            0.1 * (1 - h2h_edge)  # H2H edge for team2 is inverse
        )
        
        # Decision
        score_diff = score1 - score2
        threshold = 0.05  # Need meaningful gap to make a prediction
        
        if abs(score_diff) < threshold:
            # Neutral - form too close
            return Verdict(
                prediction="neutral",
                confidence=0.5,
                reasoning=f"Form too close: {team1} ({score1:.2f}) vs {team2} ({score2:.2f}). Diff: {score_diff:.2f} < threshold {threshold}"
            )
        
        # Predict higher-score team
        if score_diff > 0:
            prediction = team1
            confidence = 0.5 + (score_diff * 1.5)  # Scale confidence by gap
        else:
            prediction = team2
            confidence = 0.5 + (abs(score_diff) * 1.5)
        
        confidence = min(0.95, max(0.55, confidence))  # Clamp to reasonable range
        
        reasoning = (
            f"{prediction} in better form: "
            f"win% {form1['win_pct']:.0%} vs {form2['win_pct']:.0%}, "
            f"batting RR {form1['batting_rr']:.1f} vs {form2['batting_rr']:.1f}, "
            f"death economy {form1['death_economy']:.1f} vs {form2['death_economy']:.1f}, "
            f"H2H edge {h2h_edge:.0%}"
        )
        
        return Verdict(
            prediction=prediction,
            confidence=round(confidence, 2),
            reasoning=reasoning
        )
