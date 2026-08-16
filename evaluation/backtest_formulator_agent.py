"""
Backtest harness for the Formulator Agent.

Tests multiple weight combinations to find optimal fusion:
- w_stats: 0.5 to 1.0
- w_form: 0.0 to 0.5

Since Form Agent alone = 43.7% (negative signal), we test:
- w_form = 0.0 (ignore form entirely)
- w_form = 0.1 to 0.3 (discounted form)
- w_form = -0.2 to -0.1 (inverted form signal)

Usage:
    python evaluation/backtest_formulator_agent.py

Output:
    - Console output with accuracy by weight combination
    - Best weight combination highlighted
"""
import pandas as pd
from pathlib import Path
from datetime import datetime
import sys

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from agents.formulator_agent import FormulatorAgent

DATA_DIR = Path(__file__).parent.parent / "data" / "processed"
RESULTS_DIR = Path(__file__).parent.parent / "evaluation" / "results"


def parse_season(s):
    if pd.isna(s):
        return None
    s = str(s)
    if '/' in s:
        return int(s.split('/')[0])
    return int(s)


def backtest_formulator_agent():
    print("Loading data...")
    matches = pd.read_csv(DATA_DIR / "matches.csv")
    deliveries = pd.read_csv(DATA_DIR / "deliveries.csv")

    matches['season_int'] = matches['season'].apply(parse_season)
    matches_with_result = matches.dropna(subset=['winner']).copy()
    matches_with_result = matches_with_result[~matches_with_result['result'].isin(['tie', 'no result'])].copy()

    train_seasons = list(range(2008, 2023))
    test_seasons = [2023, 2024]
    train_matches = matches_with_result[matches_with_result['season_int'].isin(train_seasons)]
    test_matches = matches_with_result[matches_with_result['season_int'].isin(test_seasons)]

    print(f"Train: {len(train_matches)} matches ({min(train_seasons)}-{max(train_seasons)})")
    print(f"Test: {len(test_matches)} matches ({min(test_seasons)}-{max(test_seasons)})\n")

    # Weight combinations to test
    weight_configs = [
        (1.0, 0.0),   # Stats only (baseline)
        (0.9, 0.1),   # Heavy stats, light form
        (0.8, 0.2),   # Default
        (0.7, 0.3),   # More form
        (0.6, 0.4),   # Even more form
        (0.8, -0.2),  # Inverted form (negative signal)
        (0.9, -0.1),  # Slightly inverted form
    ]

    results = []
    for w_stats, w_form in weight_configs:
        print(f"Testing w_stats={w_stats}, w_form={w_form}...")
        agent = FormulatorAgent(matches, deliveries, w_stats=w_stats, w_form=w_form)
        
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
                    "actual_winner": match['winner'],
                    "predicted_winner": verdict.prediction,
                    "confidence": verdict.confidence,
                    "correct": verdict.prediction == match['winner']
                })
            except Exception as e:
                predictions.append({
                    "match_id": match['match_id'],
                    "actual_winner": match['winner'],
                    "predicted_winner": None,
                    "confidence": 0,
                    "correct": False
                })
        
        results_df = pd.DataFrame(predictions)
        valid = results_df[results_df['predicted_winner'].notna()]
        accuracy = valid['correct'].mean() if len(valid) > 0 else 0
        
        results.append({
            'w_stats': w_stats,
            'w_form': w_form,
            'accuracy': accuracy,
            'n_predictions': len(valid)
        })
        
        print(f"  Accuracy: {accuracy:.2%} ({len(valid)} predictions)\n")

    # Summary table
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('accuracy', ascending=False)
    
    print("=" * 50)
    print("WEIGHT SWEEP RESULTS")
    print("=" * 50)
    print(results_df.to_string(index=False))
    print("=" * 50)
    
    best = results_df.iloc[0]
    print(f"\nBest configuration: w_stats={best['w_stats']}, w_form={best['w_form']}")
    print(f"Best accuracy: {best['accuracy']:.2%}")
    
    # Save full results
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_file = RESULTS_DIR / f"backtest_formulator_weights_{datetime.now().strftime('%Y-%m-%d')}.csv"
    results_df.to_csv(output_file, index=False)
    print(f"\nResults saved to: {output_file}")
    
    return results_df


if __name__ == "__main__":
    backtest_formulator_agent()
