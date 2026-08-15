"""
Cricsheet JSON data loader for cricket-ai-council.

Schema verified against real IPL match files (Cricsheet data_version 1.2.0).
Known quirks handled:
  - `event` field shape varies across matches ({name, stage} vs {matchnumber, name})
  - Wides/no-balls/byes can appear as their own delivery entry sharing the same
    `actual_delivery` label as the next legal ball (e.g. two "1.5" entries) --
    we use `actual_delivery` itself as the identifier, not a manual ball counter,
    and flag `is_legal_delivery` separately for over-completion logic.
  - `extras` breakdown (wides/noballs/legbyes/byes) captured per delivery.
  - `registry.people` name->id map captured to disambiguate players across seasons.
  - `fielders` entries may carry `substitute: true`.

Usage:
    1. Download IPL (or other) match data from https://cricsheet.org/downloads/
    2. Unzip into data/raw/ (each match becomes one <id>.json file)
    3. Run: python data/load_cricsheet.py

Produces in data/processed/:
    - matches.csv      one row per match
    - deliveries.csv   one row per delivery (legal + extras)
    - players_registry.csv   name -> cricsheet person id, per match
"""
import json
from pathlib import Path
import pandas as pd

RAW_DIR = Path(__file__).parent / "raw"
PROCESSED_DIR = Path(__file__).parent / "processed"


def parse_match_info(match_json: dict, match_id: str) -> dict:
    info = match_json["info"]
    outcome = info.get("outcome", {})
    toss = info.get("toss", {})
    event = info.get("event", {})
    return {
        "match_id": match_id,
        "season": info.get("season"),
        "event_name": event.get("name"),
        "event_stage": event.get("stage"),
        "match_number": event.get("match_number"),
        "team1": info.get("teams", [None, None])[0],
        "team2": info.get("teams", [None, None])[1] if len(info.get("teams", [])) > 1 else None,
        "venue": info.get("venue"),
        "city": info.get("city"),
        "dates": ",".join(info.get("dates", [])),
        "match_type": info.get("match_type"),
        "gender": info.get("gender"),
        "toss_winner": toss.get("winner"),
        "toss_decision": toss.get("decision"),
        "toss_uncontested": toss.get("uncontested"),
        "winner": outcome.get("winner"),
        "win_by_runs": outcome.get("by", {}).get("runs"),
        "win_by_wickets": outcome.get("by", {}).get("wickets"),
        "result": outcome.get("result"),
        "player_of_match": ",".join(info.get("player_of_match", [])) if info.get("player_of_match") else None,
    }


def parse_deliveries(match_json: dict, match_id: str) -> list[dict]:
    rows = []
    for inn_idx, innings in enumerate(match_json.get("innings", [])):
        team = innings.get("team")
        legal_ball_counter = 0
        current_over = None
        for over in innings.get("overs", []):
            over_num = over.get("over")
            if over_num != current_over:
                legal_ball_counter = 0
                current_over = over_num
            for delivery in over.get("deliveries", []):
                extras = delivery.get("extras", {})
                runs = delivery.get("runs", {})
                wickets = delivery.get("wickets", [])
                is_legal = not extras.get("wides") and not extras.get("noballs")
                if is_legal:
                    legal_ball_counter += 1
                rows.append({
                    "match_id": match_id,
                    "innings": inn_idx + 1,
                    "batting_team": team,
                    "over": over_num,
                    "actual_delivery": delivery.get("actual_delivery"),
                    "legal_ball_in_over": legal_ball_counter if is_legal else None,
                    "is_legal_delivery": is_legal,
                    "batter": delivery.get("batter"),
                    "bowler": delivery.get("bowler"),
                    "non_striker": delivery.get("non_striker"),
                    "runs_batter": runs.get("batter", 0),
                    "runs_extras": runs.get("extras", 0),
                    "runs_total": runs.get("total", 0),
                    "extra_wides": extras.get("wides"),
                    "extra_noballs": extras.get("noballs"),
                    "extra_byes": extras.get("byes"),
                    "extra_legbyes": extras.get("legbyes"),
                    "is_wicket": len(wickets) > 0,
                    "player_out": wickets[0]["player_out"] if wickets else None,
                    "dismissal_kind": wickets[0]["kind"] if wickets else None,
                    "fielder": (
                        wickets[0]["fielders"][0]["name"]
                        if wickets and wickets[0].get("fielders") else None
                    ),
                    "fielder_is_substitute": (
                        wickets[0]["fielders"][0].get("substitute", False)
                        if wickets and wickets[0].get("fielders") else None
                    ),
                })
    return rows


def parse_registry(match_json: dict, match_id: str) -> list[dict]:
    people = match_json.get("info", {}).get("registry", {}).get("people", {})
    return [{"match_id": match_id, "player_name": name, "person_id": pid} for name, pid in people.items()]


def load_all_matches(raw_dir: Path = RAW_DIR):
    match_rows, delivery_rows, registry_rows = [], [], []
    json_files = list(raw_dir.glob("*.json"))
    if not json_files:
        raise FileNotFoundError(
            f"No .json files found in {raw_dir}. Download and unzip Cricsheet data there first."
        )
    for path in json_files:
        match_id = path.stem
        try:
            with open(path, encoding="utf-8") as f:
                match_json = json.load(f)
            match_rows.append(parse_match_info(match_json, match_id))
            delivery_rows.extend(parse_deliveries(match_json, match_id))
            registry_rows.extend(parse_registry(match_json, match_id))
        except (KeyError, json.JSONDecodeError) as e:
            print(f"Skipping {path.name}: {e}")
    return pd.DataFrame(match_rows), pd.DataFrame(delivery_rows), pd.DataFrame(registry_rows)


if __name__ == "__main__":
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    matches_df, deliveries_df, registry_df = load_all_matches()
    matches_df.to_csv(PROCESSED_DIR / "matches.csv", index=False)
    deliveries_df.to_csv(PROCESSED_DIR / "deliveries.csv", index=False)
    registry_df.drop_duplicates(subset=["player_name", "person_id"]).to_csv(
        PROCESSED_DIR / "players_registry.csv", index=False
    )
    print(f"Parsed {len(matches_df)} matches, {len(deliveries_df)} deliveries.")
    print(f"Saved to {PROCESSED_DIR}/")
