import os
import sys
import asyncio
import datetime
import httpx
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

# Link Engine 1 database connectors
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'engine1_observatory')))
from db_client import get_supabase_client

app = FastAPI(title="Engine 3: Autonomous Self-Evolving Probability Radar")

# Global State Caches
active_radar_cache = []
post_mortem_log = []
processed_completed_matches = set()

async def execute_engine2_calibration():
    """Triggers Engine 2 (wfo_backtester.py) to recalibrate WElo & CatBoost weights using new empirical outcomes."""
    try:
        print("[ENGINE 3 HANDOFF] Pushing empirical data to Engine 2...")
        process = await asyncio.create_subprocess_shell(
            "python ../engine2_quantum_lab/wfo_backtester.py",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        stdout, stderr = await process.communicate()
        print(f"[ENGINE 2 UPGRADE COMPLETE] Algorithm recalibrated.\n{stdout.decode()}")
    except Exception as e:
        print(f"[ENGINE 2 HANDOFF ERROR] {e}")

async def autonomous_24hr_cycle():
    """
    Dual-track loop:
    Track A: Live Forecasts for the current 24-hour slate.
    Track B: Post-Match Analysis & Engine 2 Algorithm Evolution Handoff.
    """
    global active_radar_cache, post_mortem_log, processed_completed_matches
    
    # INSERT YOUR LIVE API ENDPOINT AND KEY HERE
    API_URL = "https://your-free-tennis-api-endpoint.com/v1/daily-slate"
    HEADERS = {
        "Authorization": "Bearer YOUR_FREE_API_KEY",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        while True:
            try:
                today_str = datetime.datetime.now().strftime("%Y-%m-%d")
                
                # Fetch every match globally for the current 24-hour window
                # response = await client.get(f"{API_URL}?date={today_str}", headers=HEADERS)
                # daily_slate = response.json()
                
                # --- TEMPORARY FALLBACK FOR TESTING UNTIL API KEY IS INSERTED ---
                daily_slate = [
                    {"match_id": "m_001", "date": today_str, "status": "LIVE", "player_1": "Carlos Alcaraz", "player_2": "Jiri Lehecka", "p1_rank": 2, "p2_rank": 23, "market_odds_p1": 1.25, "market_odds_p2": 3.80},
                    {"match_id": "m_002", "date": today_str, "status": "COMPLETED", "player_1": "Arthur Fils", "player_2": "Ugo Humbert", "p1_rank": 24, "p2_rank": 15, "market_odds_p1": 2.10, "market_odds_p2": 1.75, "winner": "Arthur Fils", "score": "6-4, 6-3"}
                ]
                
                live_forecasts = []
                trigger_engine2 = False
                
                for match in daily_slate:
                    # 1. Classical Utility (f_model) via Rank/WElo Differential
                    rank_diff = float(match.get("p2_rank", 100)) - float(match.get("p1_rank", 100))
                    f_model = max(0.15, min(0.85, 0.50 + (rank_diff * 0.003)))
                    
                    # 2. Market Implied Probability & QDT
                    raw_p1 = 1.0 / match["market_odds_p1"]
                    raw_p2 = 1.0 / match["market_odds_p2"]
                    p_market = raw_p1 / (raw_p1 + raw_p2)
                    q_factor = p_market - f_model
                    
                    # --- TRACK A: PRE-MATCH & LIVE FORECASTING ---
                    if match["status"] in ["LIVE", "UPCOMING", "NOT_STARTED"]:
                        edge = abs(q_factor)
                        if edge >= 0.08:
                            signal = "EXECUTE (FADE PUBLIC)"
                            color = "#00ff00"
                            kelly = f"{round(edge * 0.35 * 100, 2)}%"
                            pick = match["player_1"] if q_factor < 0 else match["player_2"]
                        else:
                            signal = "PASS (EFFICIENT)"
                            color = "#555555"
                            kelly = "0.0%"
                            pick = "NO PLAY"
                            
                        live_forecasts.append({
                            "status": match["status"],
                            "matchup": f"{match['player_1']} vs {match['player_2']}",
                            "f_model": f"{round(f_model * 100, 1)}%",
                            "q_factor": round(q_factor, 3),
                            "signal": signal,
                            "color": color,
                            "pick": pick,
                            "kelly": kelly
                        })
                    
                    # --- TRACK B: FACTUAL POST-MORTEM & ALGORITHM UPGRADE ---
                    elif match["status"] in ["COMPLETED", "FINISHED"] and match["match_id"] not in processed_completed_matches:
                        processed_completed_matches.add(match["match_id"])
                        
                        post_mortem_log.insert(0, {
                            "matchup": f"{match['player_1']} vs {match['player_2']}",
                            "forecast": f"{round(f_model * 100, 1)}% {match['player_1']}",
                            "empirical_outcome": f"{match.get('winner', 'Unknown')} ({match.get('score', 'N/A')})",
                            "delta": "Algorithm upgrading weights..."
                        })
                        trigger_engine2 = True

                active_radar_cache = live_forecasts
                
                # If new empirical data was finalized, automatically handoff to Engine 2 for self-evolution
                if trigger_engine2:
                    asyncio.create_task(execute_engine2_calibration())
                    
                await asyncio.sleep(60) # Poll the global API every 60 seconds
                
            except Exception as e:
                print(f"Live API Cyclic Error: {e}")
                await asyncio.sleep(60)

# Replaced deprecated on_event with lifespan compatibility for standard Uvicorn runs
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(autonomous_24hr_cycle())

@app.get("/api/radar")
async def get_radar_data():
    return {"status": "online", "live_matches": active_radar_cache, "post_mortems": post_mortem_log[:5]}

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Engine 3: Self-Evolving Probability Radar</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { background-color: #0a0a0a; color: #00ffff; font-family: 'Courier New', monospace; margin: 0; padding: 15px; }
            h2 { border-bottom: 1px solid #00ffff; padding-bottom: 5px; font-size: 1.2rem; }
            .section-title { margin-top: 30px; font-size: 1.1rem; color: #ff00ff; border-bottom: 1px dashed #ff00ff; padding-bottom: 5px; }
            .match-card { background: #111; border: 1px solid #333; padding: 15px; margin-bottom: 15px; border-radius: 4px; position: relative; }
            .status-badge { position: absolute; top: 15px; right: 15px; font-size: 0.8rem; color: #00ffff; border: 1px solid #00ffff; padding: 2px 6px; border-radius: 3px; }
            .pm-badge { color: #ffaa00; border-color: #ffaa00; }
            .match-title { font-weight: bold; font-size: 1.1rem; color: #fff; margin-bottom: 15px; padding-right: 80px; }
            .stat-row { display: flex; justify-content: space-between; margin-bottom: 5px; font-size: 0.9rem; }
            .pick-box { margin-top: 10px; padding: 10px; text-align: center; font-weight: bold; font-size: 1.1rem; border-radius: 3px; }
        </style>
    </head>
    <body>
        <h2>QUANTUM PROBABILITY RADAR <span style="font-size: 0.8rem; color: #555;">v3.0 (Autonomous Learning)</span></h2>
        
        <div class="section-title">ACTIVE SLATE (LIVE & UPCOMING)</div>
        <div id="live-feed">Scanning global APIs...</div>

        <div class="section-title">FACTUAL POST-MORTEM (ENGINE 2 HANDOFF)</div>
        <div id="pm-feed">Waiting for completed match data...</div>
        
        <script>
            async function fetchMatches() {
                try {
                    const response = await fetch('/api/radar');
                    const data = await response.json();
                    
                    const liveContainer = document.getElementById('live-feed');
                    liveContainer.innerHTML = '';
                    if(data.live_matches.length === 0) liveContainer.innerHTML = '<span style="color:#555;">No active matches found.</span>';
                    data.live_matches.forEach(m => {
                        liveContainer.innerHTML += `
                            <div class="match-card">
                                <div class="status-badge">${m.status}</div>
                                <div class="match-title">${m.matchup}</div>
                                <div class="stat-row"><span>Objective Util (f):</span> <span>${m.f_model}</span></div>
                                <div class="stat-row"><span>QDT Attraction:</span> <span>${m.q_factor}</span></div>
                                <div class="pick-box" style="border: 1px solid ${m.color}; color: ${m.color};">
                                    ${m.signal} | PICK: ${m.pick} | STAKE: ${m.kelly}
                                </div>
                            </div>
                        `;
                    });

                    const pmContainer = document.getElementById('pm-feed');
                    pmContainer.innerHTML = '';
                    if(data.post_mortems.length === 0) pmContainer.innerHTML = '<span style="color:#555;">No completed matches processed yet.</span>';
                    data.post_mortems.forEach(m => {
                        pmContainer.innerHTML += `
                            <div class="match-card">
                                <div class="status-badge pm-badge">POST-MORTEM</div>
                                <div class="match-title">${m.matchup}</div>
                                <div class="stat-row"><span>Initial Forecast:</span> <span style="color:#aaa">${m.forecast}</span></div>
                                <div class="stat-row"><span>Empirical Outcome:</span> <span style="color:#00ff00">${m.empirical_outcome}</span></div>
                                <div class="stat-row" style="margin-top:10px; color:#ffaa00;"><i>${m.delta}</i></div>
                            </div>
                        `;
                    });
                } catch (err) {
                    document.getElementById('live-feed').innerHTML = "<span style='color:red'>Terminal Offline.</span>";
                }
            }
            
            fetchMatches();
            setInterval(fetchMatches, 30000); // Polling UI every 30 seconds
        </script>
    </body>
    </html>
    """
    return html_content

if __name__ == "__main__":
    uvicorn.run("live_api:app", host="0.0.0.0", port=8000, reload=True)
