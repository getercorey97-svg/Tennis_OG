import io
import requests
import pandas as pd
from db_client import get_supabase_client, batch_upsert

def fetch_and_parse_market_odds():
    client = get_supabase_client()
    print("Fetching recent matches to bind historical closing lines...")
    
    # Retrieve match IDs and player names to map the odds
    res = client.table("sackmann_match_records").select("match_id, tourney_date, winner_name, loser_name").order("tourney_date", desc=True).limit(200).execute()
    matches = res.data
    if not matches:
        print("No matches in DB to bind odds. Run ingest_sackmann.py first.")
        return

    # Fetch factual historical closing lines
    url = "http://www.tennis-data.co.uk/2024/2024.csv"
    try:
        req = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        df_odds = pd.read_csv(io.StringIO(req.text))
    except Exception as e:
        print(f"Failed to fetch historical odds: {e}")
        return

    odds_records = []
    for match in matches:
        # Fuzzy match utilizing player last names
        w_last = str(match['winner_name']).split()[-1]
        l_last = str(match['loser_name']).split()[-1]
        
        match_row = df_odds[(df_odds['Winner'].str.contains(w_last, na=False, case=False)) & 
                            (df_odds['Loser'].str.contains(l_last, na=False, case=False))]
        
        if not match_row.empty:
            row = match_row.iloc[0]
            b365_w = float(row.get('B365W', 0))
            b365_l = float(row.get('B365L', 0))
            
            if b365_w <= 0 or b365_l <= 0: 
                continue

            # Vig Extraction
            raw_w = 1.0 / b365_w
            raw_l = 1.0 / b365_l
            vig = raw_w + raw_l
            novig_w = raw_w / vig
            novig_l = raw_l / vig
            
            # Classical Utility Baseline Estimate (f_model)
            rank_w = float(row.get('WRank', 100)) if pd.notna(row.get('WRank')) else 100.0
            rank_l = float(row.get('LRank', 100)) if pd.notna(row.get('LRank')) else 100.0
            
            f_model = 0.5 + ((rank_l - rank_w) * 0.001)
            f_model = max(0.05, min(0.95, f_model)) # Bounding
            
            # QDT Attraction Factor (q_market = p_market - f_model)
            q_market = novig_w - f_model
            
            # Mathematical Flags
            q_flag = True if 0.20 <= abs(q_market) <= 0.28 else False
            anomaly_flag = True if abs(q_market) >= 0.30 else False

            rec = {
                "match_id": match['match_id'],
                "bookmaker": "Bet365_Closing",
                "timestamp_captured": f"{match['tourney_date']}T00:00:00Z",
                "is_closing_line": True,
                "winner_decimal_odds": b365_w,
                "loser_decimal_odds": b365_l,
                "winner_implied_prob_raw": round(raw_w, 5),
                "loser_implied_prob_raw": round(raw_l, 5),
                "winner_implied_prob_novig": round(novig_w, 5),
                "loser_implied_prob_novig": round(novig_l, 5),
                "model_utility_f": round(f_model, 5),
                "qdt_attraction_q": round(q_market, 5),
                "clv_edge_pct": round(abs(q_market) * 100, 2),
                "quarter_law_flag": q_flag,
                "geter_anomaly_flag": anomaly_flag
            }
            odds_records.append(rec)
            print(f"Mapped Odds for {match['match_id']} | Q-Factor: {round(q_market, 3)} | Quarter Law: {q_flag}")
            
    if odds_records:
        print(f"Upserting {len(odds_records)} QDT odds records...")
        batch_upsert("market_odds_clv", odds_records, chunk_size=100)
        print("Batch 4 Complete: Market Odds & QDT Engine Seeded.")

if __name__ == "__main__":
    fetch_and_parse_market_odds()
