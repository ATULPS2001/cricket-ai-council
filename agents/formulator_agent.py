"""
Formulator Agent — fuses Stats Agent and Form Agent predictions.

Uses weighted ensemble:
  final_score = w_stats * stats_confidence + w_form * form_confidence

Since Form Agent underperforms (43.7% vs 55.6%), form weight can be:
  - Zero (ignore form entirely)
  - Negative (invert form signal)
  - Small positive (discounted form)

Default weights: w_stats=0.8, w_form=0.2 (conservative fusion)

Query format (same as sub-agents):
{
    "type": "toss_bat_gamble" | "form_check",
    "teams": ["Team A", "Team B"],
    "venue": "optional",
    "match_id": "optional"
}

Returns Verdict with prediction, confidence, reasoning.
"""
from dataclasses import dataclass
from typing import Optional
import pandas as pd

from agents.stats_agent import StatsAgent
from agents.form_agent import FormAgent


@dataclass
class Verdict:
    prediction: str
    confidence: float
    reasoning: str


class FormulatorAgent:
    def __init__(
        self,
        matches: pd.DataFrame,
        deliveries: pd.DataFrame,
        w_stats: float = 0.8,
        w_form: float = 0.2
    ):
        """
        Initialize Formulator Agent.
        
        Args:
            matches: Match-level data
            deliveries: Ball-by-ball data
            w_stats: Weight for Stats Agent (0-1)
            w_form: Weight for Form Agent (can be negative to invert signal)
        """
        self.stats_agent = StatsAgent(matches, deliveries)
        self.form_agent = FormAgent(matches, deliveries)
        self.w_stats = w_stats
        self.w_form = w_form
    
    def _confidence_to_score(self, confidence: float, prediction: str, teams: list) -> tuple:
        """
        Convert agent confidence to a directional score.
        
        Returns (score_for_team1, score_for_team2)
        where higher score = more likely to win.
        """
        if prediction == teams[0]:
            return (confidence, 1 - confidence)
        elif prediction == teams[1]:
            return (1 - confidence, confidence)
        else:  # neutral or unknown
            return (0.5, 0.5)
    
    def analyze(self, query: dict) -> Verdict:
        """
        Fuse predictions from Stats and Form agents.
        
        Query format:
        {
            "type": "toss_bat_gamble" | "form_check",
            "teams": ["Team A", "Team B"],
            "venue": "optional",
            "match_id": "optional"
        }
        """
        teams = query["teams"]
        
        if len(teams) != 2:
            return Verdict(
                prediction=teams[0] if teams else "Unknown",
                confidence=0.0,
                reasoning="Need exactly 2 teams"
            )
        
        # Get predictions from both agents
        stats_verdict = self.stats_agent.analyze(query)
        form_verdict = self.form_agent.analyze(query)
        
        # Convert to directional scores
        stats_scores = self._confidence_to_score(stats_verdict.confidence, stats_verdict.prediction, teams)
        form_scores = self._confidence_to_score(form_verdict.confidence, form_verdict.prediction, teams)
        
        # Weighted fusion
        team1_score = self.w_stats * stats_scores[0] + self.w_form * form_scores[0]
        team2_score = self.w_stats * stats_scores[1] + self.w_form * form_scores[1]
        
        # Normalize to 0-1 confidence
        total_weight = self.w_stats + self.w_form
        if total_weight == 0:
            # Edge case: both weights zero, default to neutral
            return Verdict(
                prediction=teams[0],
                confidence=0.5,
                reasoning="Both agent weights are zero"
            )
        
        team1_final = team1_score / total_weight
        team2_final = team2_score / total_weight
        
        # Decision
        if team1_final > team2_final:
            prediction = teams[0]
            confidence = team1_final
        else:
            prediction = teams[1]
            confidence = team2_final
        
        # Reasoning
        reasoning = (
            f"Fused prediction: {prediction}\n"
            f"Stats Agent: {stats_verdict.prediction} ({stats_verdict.confidence:.2f})\n"
            f"Form Agent: {form_verdict.prediction} ({form_verdict.confidence:.2f})\n"
            f"Weights: stats={self.w_stats}, form={self.w_form}\n"
            f"Final confidence: {confidence:.2f}"
        )
        
        return Verdict(
            prediction=prediction,
            confidence=round(confidence, 2),
            reasoning=reasoning
        )
