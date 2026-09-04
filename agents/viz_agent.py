"""
Viz Agent - Creates visual charts to support predictions from Stats/Form/Formulator agents.

Generates:
- Team win% comparison bars
- Recent form trends (last 5 matches)
- H2H history
- Venue-based stats
"""
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any


class VizAgent:
    def __init__(self, matches: pd.DataFrame, deliveries: pd.DataFrame):
        self.matches = matches.copy()
        self.deliveries = deliveries.copy()
    
    def get_team_venue_stats(self, team: str, venue: Optional[str] = None) -> Dict[str, Any]:
        """Get win/loss stats for a team at a venue."""
        if venue:
            venue_matches = self.matches[self.matches['venue'].str.contains(venue, case=False, na=False)]
        else:
            venue_matches = self.matches
        
        team_matches = venue_matches[
            (venue_matches['team1'] == team) | (venue_matches['team2'] == team)
        ].dropna(subset=['winner'])
        
        if len(team_matches) == 0:
            return {'wins': 0, 'losses': 0, 'total': 0, 'win_pct': 0.0}
        
        wins = (team_matches['winner'] == team).sum()
        losses = len(team_matches) - wins
        
        return {
            'wins': int(wins),
            'losses': int(losses),
            'total': int(len(team_matches)),
            'win_pct': round(wins / len(team_matches) * 100, 1)
        }
    
    def get_h2h_data(self, team1: str, team2: str, n: int = 10) -> pd.DataFrame:
        """Get H2H match history between two teams."""
        h2h = self.matches[
            ((self.matches['team1'] == team1) & (self.matches['team2'] == team2)) |
            ((self.matches['team1'] == team2) & (self.matches['team2'] == team1))
        ].dropna(subset=['winner'])
        
        h2h = h2h.sort_values(['season', 'match_id']).tail(n)
        
        # Add winner indicator
        h2h = h2h.copy()
        h2h['team1_won'] = h2h['winner'] == h2h['team1']
        
        return h2h
    
    def get_form_data(self, team: str, n: int = 5) -> pd.DataFrame:
        """Get last N matches for a team with results."""
        team_matches = self.matches[
            (self.matches['team1'] == team) | (self.matches['team2'] == team)
        ].dropna(subset=['winner'])
        
        team_matches = team_matches.sort_values(['season', 'match_id']).tail(n)
        team_matches = team_matches.copy()
        team_matches['won'] = team_matches['winner'] == team
        
        return team_matches
    
    def create_venue_comparison(self, team1: str, team2: str, venue: Optional[str] = None) -> Dict:
        """Create venue comparison data for both teams."""
        stats1 = self.get_team_venue_stats(team1, venue)
        stats2 = self.get_team_venue_stats(team2, venue)
        
        return {
            'teams': [team1, team2],
            'win_pct': [stats1['win_pct'], stats2['win_pct']],
            'wins': [stats1['wins'], stats2['wins']],
            'losses': [stats1['losses'], stats2['losses']],
            'total_matches': [stats1['total'], stats2['total']]
        }
    
    def create_h2h_chart_data(self, team1: str, team2: str) -> Dict:
        """Create H2H chart data."""
        h2h = self.get_h2h_data(team1, team2)
        
        if len(h2h) == 0:
            return {'labels': [], 'team1_wins': [], 'team2_wins': []}
        
        # Count wins
        team1_wins = (h2h['winner'] == team1).sum()
        team2_wins = (h2h['winner'] == team2).sum()
        
        return {
            'labels': [team1, team2],
            'wins': [int(team1_wins), int(team2_wins)],
            'total_matches': len(h2h)
        }
    
    def create_form_chart_data(self, team: str) -> Dict:
        """Create form trend data for a team."""
        form = self.get_form_data(team, n=5)
        
        if len(form) == 0:
            return {'match_numbers': [], 'results': [], 'cumulative_wins': []}
        
        match_nums = range(1, len(form) + 1)
        results = form['won'].tolist()
        cumulative = np.cumsum(results)
        
        return {
            'match_numbers': list(match_nums),
            'results': results,
            'cumulative_wins': list(cumulative)
        }
