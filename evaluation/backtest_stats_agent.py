"""
Backtest harness for the Stats Agent.

Evaluates prediction accuracy on historical IPL matches by:
1. Splitting data into train (2008-2022) and test (2023-2024) seasons
2. For each test match, asking the Stats Agent to predict the winner
3. Comparing predictions against actual results
4. Reporting overall accuracy and per-team breakdowns

Usage:
    python evaluation/backtest_stats_agent.py

Output:
    - evaluation/results/backtest_stats_agent_YYYY-MM-DD.csv (per-match predictions)
    - Console output with overall accuracy and key metrics
"""
import pandas as pd
from pathlib import Path
from datetime import datetime
from agents.stats_agent import StatsAgent

DATA_DIR = Path(__file__).parent.parent / "data" / "processed"
RESULTS_DIR = Path(__file__).parent.parent / "evaluation" / "results"


def backtest_stats_agent():
    print("Loading data...")
    matches = pd.read_csv(DATA_DIR / "matches.csv")
    deliveries = pd.read_csv(DATA_DIR / "deliveries.csv")

    # Filter to matches with a clear winner (exclude ties/no-results)
    matches_with_result = matches.dropna(subset=['winner']).copy()
    matches_with_result = matches_with_result[~matches_with_result['result'].isin(['tie', 'no result'])].copy()

    # Train/test split by season
    train_seasons = list(range(2008, 2023))  # 2008-2022
    test_seasons = [2023, 2024]  # 2023-2024
    train_matches = matches_with_result[matches_with_result['season'].isin(train_seasons)]
    test_matches = matches_with_result[matches_with_result['season'].isin(test_seasons)]

    print(f"Train: {len(train_matches)} matches ({min(train_seasons)}-{max(train_seasons)})")
    print(f"Test: {len(test_matches)} matches ({min(test_seasons)}-{max(test_seasons)})")

    # Train the agent on full historical data (Stats Agent uses all data for aggregates)
    agent = StatsAgent(matches, deliveries)

    # Generate predictions for each test match
    predictions = []
    for idx, match in test_matches.iterrows():
        q = {
            "type": "toss_bat_gamble",
            "teams": [match['team1'], match['team2']],
            "venue": match['venue'] if isinstance(match['venue'], str) else None
        }
        try:
            verdict = agent.analyze(q)
            predictions.append({
                "match_id": match['match_id'],
                "season": match['season'],
                "team1": match['team1'],
                "team2": match['team2'],
                "venue": match['venue'],
                "actual_winner": match['winner'],
                "predicted_winner": verdict.prediction,
                "confidence": verdict.confidence,
                "reasoning": verdict.reasoning,
                "correct": verdict.prediction == match['winner']
            })
        except Exception as e:
            predictions.append({
                "match_id": match['match_id'],
                "season": match['season'],
                "team1": match['team1'],
                "team2": match['team2'],
                "venue": match['venue'],
                "actual_winner": match['winner'],
                "predicted_winner": None,
                "confidence": 0,
                "reasoning": str(e),
                "correct": False
            })

    results_df = pd.DataFrame(predictions)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_file = RESULTS_DIR / f"backtest_stats_agent_{datetime.now().strftime('%Y-%m-%d')}.csv"
    results_df.to_csv(output_file, index=False)

    # Compute metrics
    valid_predictions = results_df[results_df['predicted_winner'].notna()]
    accuracy = valid_predictions['correct'].mean()
    avg_confidence = valid_predictions['confidence'].mean()

    print(f"\n=== Backtest Results ===")
    print(f"Total test matches: {len(test_matches)}")
    print(f"Valid predictions: {len(valid_predictions)}")
    print(f"Accuracy: {accuracy:.2%}")
    print(f"Average confidence: {avg_confidence:.2f}")

    # Per-team breakdown
    team_accuracy = []
    for team in valid_predictions['actual_winner'].unique():
        team_matches = valid_predictions[valid_predictions['actual_winner'] == team]
        team_acc = team_matches['correct'].mean()
        team_accuracy.append((team, len(team_matches), team_acc))
    team_accuracy.sort(key=lambda x: -x[2])

    print(f"\n=== Per-team accuracy (top 5) ===")
    for team, n, acc in team_accuracy[:5]:
        print(f"{team}: {acc:.2%} ({n} matches)")

    print(f"\nResults saved to: {output_file}")
    return results_df


if __name__ == "__main__":
    backtest_stats_agent()
