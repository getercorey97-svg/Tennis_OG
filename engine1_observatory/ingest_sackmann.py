import io
import math
import requests
import pandas as pd
from typing import List, Dict, Any
from db_client import batch_upsert

BASE_URL = "https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/atp_matches_{year}.csv"
YEARS = [2021, 2022, 2023, 2024, 2025, 2026]

def clean_val(val, target_type):
    if pd.isna(val) or val is None or val == "":
        return None
    try:
        if target_type == "int":
            return int(float(val))
        elif target_type == "float":
            return round(float(val), 2)
        elif target_type == "str":
            return str(val).strip()
    except (ValueError, TypeError):
        return None
    return val

def format_date(raw_date):
    if pd.isna(raw_date):
        return "1970-01-01"
    s = str(int(raw_date)) if isinstance(raw_date, (int, float)) else str(raw_date).strip()
    if len(s) == 8:
        return f"{s[0:4]}-{s[4:6]}-{s[6:8]}"
    return "1970-01-01"

def fetch_and_parse_year(year: int) -> List[Dict[str, Any]]:
    url = BASE_URL.format(year=year)
    print(f"Fetching ATP historical records for {year}: {url}")
    res = requests.get(url, timeout=30)
    if res.status_code != 200:
        print(f"Skipping {year}: status code {res.status_code}")
        return []

    df = pd.read_csv(io.StringIO(res.text))
    records = []

    for _, row in df.iterrows():
        tourney_id = clean_val(row.get("tourney_id"), "str")
        match_num = clean_val(row.get("match_num"), "int")
        if not tourney_id or match_num is None:
            continue

        match_id = f"{tourney_id}_{match_num}"
        record = {
            "match_id": match_id,
            "tourney_id": tourney_id,
            "tourney_name": clean_val(row.get("tourney_name"), "str") or "Unknown",
            "surface": clean_val(row.get("surface"), "str") or "Hard",
            "draw_size": clean_val(row.get("draw_size"), "int"),
            "tourney_level": clean_val(row.get("tourney_level"), "str"),
            "tourney_date": format_date(row.get("tourney_date")),
            "match_num": match_num,
            "winner_id": clean_val(row.get("winner_id"), "int") or 0,
            "winner_seed": clean_val(row.get("winner_seed"), "str"),
            "winner_entry": clean_val(row.get("winner_entry"), "str"),
            "winner_name": clean_val(row.get("winner_name"), "str") or "Unknown",
            "winner_hand": clean_val(row.get("winner_hand"), "str"),
            "winner_ht": clean_val(row.get("winner_ht"), "int"),
            "winner_ioc": clean_val(row.get("winner_ioc"), "str"),
            "winner_age": clean_val(row.get("winner_age"), "float"),
            "loser_id": clean_val(row.get("loser_id"), "int") or 0,
            "loser_seed": clean_val(row.get("loser_seed"), "str"),
            "loser_entry": clean_val(row.get("loser_entry"), "str"),
            "loser_name": clean_val(row.get("loser_name"), "str") or "Unknown",
            "loser_hand": clean_val(row.get("loser_hand"), "str"),
            "loser_ht": clean_val(row.get("loser_ht"), "int"),
            "loser_ioc": clean_val(row.get("loser_ioc"), "str"),
            "loser_age": clean_val(row.get("loser_age"), "float"),
            "score": clean_val(row.get("score"), "str") or "0-0",
            "best_of": clean_val(row.get("best_of"), "int") or 3,
            "round": clean_val(row.get("round"), "str") or "R32",
            "minutes": clean_val(row.get("minutes"), "int"),
            "w_ace": clean_val(row.get("w_ace"), "int"),
            "w_df": clean_val(row.get("w_df"), "int"),
            "w_svpt": clean_val(row.get("w_svpt"), "int"),
            "w_1st_in": clean_val(row.get("w_1stIn"), "int"),
            "w_1st_won": clean_val(row.get("w_1stWon"), "int"),
            "w_2nd_won": clean_val(row.get("w_2ndWon"), "int"),
            "w_sv_gms": clean_val(row.get("w_SvGms"), "int"),
            "w_bp_saved": clean_val(row.get("w_bpSaved"), "int"),
            "w_bp_faced": clean_val(row.get("w_bpFaced"), "int"),
            "l_ace": clean_val(row.get("l_ace"), "int"),
            "l_df": clean_val(row.get("l_df"), "int"),
            "l_svpt": clean_val(row.get("l_svpt"), "int"),
            "l_1st_in": clean_val(row.get("l_1stIn"), "int"),
            "l_1st_won": clean_val(row.get("l_1stWon"), "int"),
            "l_2nd_won": clean_val(row.get("l_2ndWon"), "int"),
            "l_sv_gms": clean_val(row.get("l_SvGms"), "int"),
            "l_bp_saved": clean_val(row.get("l_bpSaved"), "int"),
            "l_bp_faced": clean_val(row.get("l_bpFaced"), "int"),
            "winner_rank": clean_val(row.get("winner_rank"), "int"),
            "winner_rank_points": clean_val(row.get("winner_rank_points"), "int"),
            "loser_rank": clean_val(row.get("loser_rank"), "int"),
            "loser_rank_points": clean_val(row.get("loser_rank_points"), "int")
        }
        records.append(record)

    return records

def run_historical_seeding():
    total_seeded = 0
    for year in YEARS:
        records = fetch_and_parse_year(year)
        if records:
            print(f"Upserting {len(records)} records for year {year} into Supabase...")
            committed = batch_upsert("sackmann_match_records", records, chunk_size=500)
            total_seeded += committed
            print(f"Completed {year}: {committed} matches committed.")
    print(f"5-Year Historical Seeding Complete. Total matches in database: {total_seeded}")

if __name__ == "__main__":
    run_historical_seeding()
