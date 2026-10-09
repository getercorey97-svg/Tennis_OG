import io, requests, pandas as pd
from db_client import batch_upsert
URLS = [
    "https://raw.githubusercontent.com/farhadGithub/tennis-atp-data/main/data/raw/atp_matches_{year}.csv",
    "https://raw.githubusercontent.com/Kadantte/tennis_atp/master/atp_matches_{year}.csv"
]
def clean_val(v, t):
    if pd.isna(v) or v is None or v == "": return None
    try: return int(float(v)) if t == "int" else round(float(v), 2) if t == "float" else str(v).strip()
    except: return None
def fetch_year(y):
    for base in URLS:
        res = requests.get(base.format(year=y), headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        if res.status_code == 200:
            df = pd.read_csv(io.StringIO(res.text))
            return [{"match_id": f"{clean_val(r.get('tourney_id'), 'str')}_{clean_val(r.get('match_num'), 'int')}", "tourney_id": clean_val(r.get('tourney_id'), 'str'), "tourney_name": clean_val(r.get('tourney_name'), 'str') or "Unknown", "surface": clean_val(r.get('surface'), 'str') or "Hard", "tourney_date": str(int(r.get('tourney_date')))[:4]+"-"+str(int(r.get('tourney_date')))[4:6]+"-"+str(int(r.get('tourney_date')))[6:8] if not pd.isna(r.get('tourney_date')) else "1970-01-01", "match_num": clean_val(r.get('match_num'), 'int'), "winner_id": clean_val(r.get('winner_id'), 'int') or 0, "winner_name": clean_val(r.get('winner_name'), 'str') or "Unknown", "loser_id": clean_val(r.get('loser_id'), 'int') or 0, "loser_name": clean_val(r.get('loser_name'), 'str') or "Unknown", "score": clean_val(r.get('score'), 'str') or "0-0", "round": clean_val(r.get('round'), 'str') or "R32", "winner_rank": clean_val(r.get('winner_rank'), 'int'), "loser_rank": clean_val(r.get('loser_rank'), 'int')} for _, r in df.iterrows() if clean_val(r.get('tourney_id'), 'str') and clean_val(r.get('match_num'), 'int') is not None]
    return []
if __name__ == "__main__":
    t = 0
    for y in [2021, 2022, 2023, 2024, 2025, 2026]:
        recs = fetch_year(y)
        if recs: t += batch_upsert("sackmann_match_records", recs, chunk_size=500)
    print(f"Seeding Complete. Total matches: {t}")
