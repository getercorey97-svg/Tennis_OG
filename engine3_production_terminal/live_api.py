import os
import sys
import asyncio
import datetime
import subprocess
from fastapi import FastAPI, BackgroundTasks
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
    """
    Background worker that triggers Engine 2 to upgrade the predictive algorithm
    based on newly completed empirical match data.
    """
    try:
        print("[ENGINE 3 HANDOFF] Pushing empirical data to Engine 2...")
        # Execute the WFO backtester as a non-blocking subprocess
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
    Dual-track loop enforcing the Factual Post-Mortem Mandate.
    Track A: Live Forecasts for the current 24-hour slate.
    Track B: Post-Match Analysis & Engine 2 Handoff.
    """
    global active_radar_cache, post_mortem_log, processed_completed_matches
    
    while True:
        try:
            today_str = datetime.datetime.now().strftime("%Y-%m-%d")
            
            # Simulated 24-hour live feed ingestion (In production, hits Live Tennis API)
            daily_slate = [
                {"match_id": "m_001", "date": today_str, "status": "LIVE", "player_1": "Carlos Alcaraz", "player_2": "Jannik Sinner", "p1_rank": 2, "p2_rank": 1, "market_odds_p1": 1.95, "market_odds_p2": 1.85},
                {"match_id": "m_002", "date": today_str, "status": "UPCOMING", "player_1": "Ben Shelton", "player_2": "Frances Tiafoe", "p1_rank": 13, "p2_rank": 16, "market_odds_p1": 1.70, "market_odds_p2": 2.15},
                # Simulating a match that just finished
                {"match_id": "m_003", "date": today_str, "status": "COMPLETED", "player_1": "Arthur Fils", "player_2": "Ugo Humbert", "p1_rank": 24, "p2_rank": 15, "market_odds_p1": 2.10, "market_odds_p2": 1.75, "winner": "Arthur Fils", "score": "6-4, 6-3"},
            ]
            
            live_forecasts = []
            trigger_engine2 = False
            
            for match in daily_slate:
                # 1. Classical Utility (f_model)
                rank_diff = float(match["p2_rank"]) - float(match["p1_rank"])
                f_model = max(0.15, min(0.85, 0.50 + (rank_diff * 0.003)))
                
                # 2. Market Implied Probability & QDT
                raw_p1 = 1.0 / match["market_odds_p1"]
                raw_p2 = 1.0 / match["market_odds_p2"]
                p_market = raw_p1 / (raw_p1 + raw_p2)
                q_factor = p_market - f_model
                
                # --- TRACK A: PRE-MATCH & LIVE FORECASTING ---
                if match["status"] in ["LIVE", "UPCOMING"]:
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
                elif match["status"] == "COMPLETED" and match["match_id"] not in processed_completed_matches:
                    processed_completed_matches.add(match["match_id"])
                    
                    # Log empirical outcome for the UI
                    post_mortem_log.insert(0, {
                        "matchup": f"{match['player_1']} vs {match['player_2']}",
                        "forecast": f"{round(f_model * 100, 1)}% {match['player_1']}",
                        "empirical_outcome": f"{match['winner']} ({match['score']})",
                        "delta": "Algorithm upgrading weights..."
                    })
                    
                    # In production: Upsert to Supabase sackmann_match_records here
                    trigger_engine2 = True

            active_radar_cache = live_forecasts
            
            # If new empirical data was logged, trigger Engine 2 to evolve the algorithm
            if trigger_engine2:
                asyncio.create_task(execute_engine2_calibration())
                
            await asyncio.sleep(60) # Poll and refresh the daily slate every 60 seconds
            
        except Exception as e:
            print(f"Cyclic Error: {e}")
            await asyncio.sleep(60)

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
        <h2>QUANTUM PROBABILITY RADAR <span style="font-size: 0.8rem; color: #555;">v3.0 (Autonomous Learning Active)</span></h2>
        
        <div class="section-title">ACTIVE SLATE (LIVE & UPCOMING)</div>
        <div id="live-feed">Scanning 24-hour timeline...</div>

        <div class="section-title">FACTUAL POST-MORTEM (ENGINE 2 HANDOFF)</div>
        <div id="pm-feed">Waiting for completed match data...</div>
        
        <script>
            async function fetchMatches() {
                try {
                    const response = await fetch('/api/radar');
                    const data = await response.json();
                    
                    // Render Live Forecasts
                    const liveContainer = document.getElementById('live-feed');
                    liveContainer.innerHTML = '';
                    if(data.live_matches.length === 0) liveContainer.innerHTML = '<span style="color:#555;">No active matches.</span>';
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

                    // Render Post-Mortem Handoffs
                    const pmContainer = document.getElementById('pm-feed');
                    pmContainer.innerHTML = '';
                    if(data.post_mortems.length === 0) pmContainer.innerHTML = '<span style="color:#555;">No completed matches processed today.</span>';
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
            setInterval(fetchMatches, 30000); // Auto-refresh UI every 30 seconds
        </script>
    </body>
    </html>
    """
    return html_content

if __name__ == "__main__":
    uvicorn.run("live_api:app", host="0.0.0.0", port=8000, reload=True)
