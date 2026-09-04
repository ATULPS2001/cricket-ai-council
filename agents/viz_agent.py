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
import altair as alt


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
        h2h = h2h.copy()
        h2h['team1_won'] = h2h['winner'] == team1
        
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
    
    def create_venue_comparison_chart(self, team1: str, team2: str, venue: Optional[str] = None) -> alt.Chart:
        """Create bar chart comparing win% at venue."""
        stats1 = self.get_team_venue_stats(team1, venue)
        stats2 = self.get_team_venue_stats(team2, venue)
        
        data = pd.DataFrame({
            'team': [team1, team2],
            'win_pct': [stats1['win_pct'], stats2['win_pct']],
            'wins': [stats1['wins'], stats2['wins']],
            'losses': [stats1['losses'], stats2['losses']]
        })
        
        chart = alt.Chart(data).mark_bar().encode(
            x=alt.X('team:N', title='Team'),
            y=alt.Y('win_pct:Q', title='Win %', scale=alt.Scale(domain=[0, 100])),
            color='team:N',
            tooltip=['team', 'win_pct', 'wins', 'losses']
        ).properties(
            title=f'Win % at {venue}' if venue else 'Overall Win %',
            width=400,
            height=300
        )
        
        return chart
    
    def create_h2h_chart(self, team1: str, team2: str) -> alt.Chart:
        """Create pie chart showing H2H record."""
        h2h = self.get_h2h_data(team1, team2)
        
        if len(h2h) == 0:
            return alt.Chart(pd.DataFrame()).mark_text().encode(text='value:N')
        
        team1_wins = (h2h['winner'] == team1).sum()
        team2_wins = (h2h['winner'] == team2).sum()
        
        data = pd.DataFrame({
            'winner': [team1, team2],
            'wins': [int(team1_wins), int(team2_wins)]
        })
        
        chart = alt.Chart(data).mark_arc().encode(
            theta=alt.Theta('wins:Q'),
            color='winner:N',
            tooltip=['winner', 'wins']
        ).properties(
            title=f'H2H Record ({len(h2h)} matches)',
            width=400,
            height=300
        )
        
        return chart
    
    def create_form_chart(self, team: str) -> alt.Chart:
        """Create line chart showing recent form trend."""
        form = self.get_form_data(team, n=5)
        
        if len(form) == 0:
            return alt.Chart(pd.DataFrame()).mark_text().encode(text='value:N')
        
        form = form.copy()
        form['match_num'] = range(1, len(form) + 1)
        form['cumulative_wins'] = form['won'].cumsum()
        
        chart = alt.Chart(form).mark_line(point=True).encode(
            x=alt.X('match_num:O', title='Match (Recent →)'),
            y=alt.Y('cumulative_wins:Q', title='Cumulative Wins'),
            color=alt.value('#1f77b4'),
            tooltip=['match_num', 'won', 'cumulative_wins']
        ).properties(
            title=f'{team} - Recent Form (Last {len(form)} matches)',
            width=400,
            height=300
        )
        
        return chart
    
    def create_full_analysis(self, team1: str, team2: str, venue: Optional[str] = None) -> Dict[str, alt.Chart]:
        """Create all charts for a match analysis."""
        return {
            'venue_comparison': self.create_venue_comparison_chart(team1, team2, venue),
            'h2h': self.create_h2h_chart(team1, team2),
            'form_team1': self.create_form_chart(team1),
            'form_team2': self.create_form_chart(team2)
        }
