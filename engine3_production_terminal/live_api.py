import os
import asyncio
import httpx
import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI(title="Engine 3: Multi-Day Quantum Probability Radar")

# Global cache for the 7-day forward window
multi_day_cache = []

async def fetch_multi_day_schedule():
    """
    Background worker that continuously fetches today's live matches PLUS 
    the scheduled ATP/WTA slate for the next 7 days, processing all through the QDT Engine.
    """
    global multi_day_cache
    while True:
        try:
            now = datetime.datetime.now()
            today_str = now.strftime("%Y-%m-%d")
            tomorrow_str = (now + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            future_str = (now + datetime.timedelta(days=3)).strftime("%Y-%m-%d")
            
            # Simulated multi-day schedule ingestion
            simulated_multi_day_feed = [
                {"date": today_str, "status": "LIVE", "player_1": "Carlos Alcaraz", "player_2": "Jannik Sinner", "surface": "Hard", "p1_rank": 2, "p2_rank": 1, "market_odds_p1": 1.95, "market_odds_p2": 1.85},
                {"date": today_str, "status": "SCHEDULED", "player_1": "Ben Shelton", "player_2": "Frances Tiafoe", "surface": "Hard", "p1_rank": 13, "p2_rank": 16, "market_odds_p1": 1.70, "market_odds_p2": 2.15},
                {"date": tomorrow_str, "status": "UPCOMING", "player_1": "Aryna Sabalenka", "player_2": "Coco Gauff", "surface": "Hard", "p1_rank": 2, "p2_rank": 3, "market_odds_p1": 1.55, "market_odds_p2": 2.45},
                {"date": tomorrow_str, "status": "UPCOMING", "player_1": "Arthur Fils", "player_2": "Ugo Humbert", "surface": "Hard", "p1_rank": 24, "p2_rank": 15, "market_odds_p1": 2.10, "market_odds_p2": 1.75},
                {"date": future_str, "status": "UPCOMING", "player_1": "Novak Djokovic", "player_2": "Daniil Medvedev", "surface": "Hard", "p1_rank": 4, "p2_rank": 5, "market_odds_p1": 1.65, "market_odds_p2": 2.25},
            ]
            
            processed_matches = []
            for match in simulated_multi_day_feed:
                # 1. Classical Utility (f_model)
                rank_diff = float(match["p2_rank"]) - float(match["p1_rank"])
                f_model = max(0.15, min(0.85, 0.50 + (rank_diff * 0.003)))
                
                # 2. Market Implied Probability
                raw_p1 = 1.0 / match["market_odds_p1"]
                raw_p2 = 1.0 / match["market_odds_p2"]
                vig = raw_p1 + raw_p2
                p_market = raw_p1 / vig
                
                # 3. QDT Attraction Factor
                q_factor = p_market - f_model
                
                # 4. Fractional Kelly Execution
                edge = abs(q_factor)
                if edge >= 0.08:
                    signal = "EXECUTE (FADE PUBLIC)"
                    color = "#00ff00"
                    kelly = round(edge * 0.35 * 100, 2)
                    pick = match["player_1"] if q_factor < 0 else match["player_2"]
                else:
                    signal = "PASS (EFFICIENT)"
                    color = "#555555"
                    kelly = 0.0
                    pick = "NO PLAY"
                
                processed_matches.append({
                    "date": match["date"],
                    "status": match["status"],
                    "matchup": f"{match['player_1']} vs {match['player_2']}",
                    "f_model": f"{round(f_model * 100, 1)}%",
                    "p_market": f"{round(p_market * 100, 1)}%",
                    "q_factor": round(q_factor, 3),
                    "signal": signal,
                    "color": color,
                    "kelly": f"{kelly}%",
                    "pick": pick
                })
            
            multi_day_cache = processed_matches
            await asyncio.sleep(60) 
        except Exception as e:
            print(f"Ingestion Error: {e}")
            await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(fetch_multi_day_schedule())

@app.get("/api/radar")
async def get_radar_data():
    return {"status": "online", "matches": multi_day_cache}

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Engine 3: Multi-Day Production Terminal</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { background-color: #0a0a0a; color: #00ffff; font-family: 'Courier New', monospace; margin: 0; padding: 15px; }
            h2 { border-bottom: 1px solid #00ffff; padding-bottom: 5px; font-size: 1.2rem; display: flex; justify-content: space-between; align-items: center; }
            .controls { display: flex; gap: 10px; margin-bottom: 20px; }
            input[type="text"], select { flex: 1; padding: 12px; background: #1a1a1a; border: 1px solid #00ffff; color: #fff; font-size: 1rem; box-sizing: border-box; }
            .match-card { background: #111; border: 1px solid #333; padding: 15px; margin-bottom: 15px; border-radius: 4px; position: relative; }
            .match-date { position: absolute; top: 15px; right: 15px; font-size: 0.8rem; color: #ff00ff; border: 1px solid #ff00ff; padding: 2px 6px; border-radius: 3px; }
            .match-title { font-weight: bold; font-size: 1.1rem; color: #fff; margin-bottom: 15px; padding-right: 80px; }
            .stat-row { display: flex; justify-content: space-between; margin-bottom: 5px; font-size: 0.9rem; }
            .pick-box { margin-top: 10px; padding: 10px; text-align: center; font-weight: bold; font-size: 1.1rem; border-radius: 3px; }
        </style>
    </head>
    <body>
        <h2>QUANTUM PROBABILITY RADAR <span style="font-size: 0.8rem; color: #555;">v2.1</span></h2>
        <div class="controls">
            <input type="text" id="searchInput" placeholder="Search player..." onkeyup="filterMatches()">
            <select id="dateFilter" onchange="filterMatches()">
                <option value="ALL">All Days</option>
                <option value="LIVE">Live Now</option>
                <option value="TODAY">Today Only</option>
                <option value="TOMORROW">Tomorrow</option>
                <option value="FUTURE">Future 7-Day</option>
            </select>
        </div>
        <div id="radar-feed">Loading multi-day telemetry...</div>
        
        <script>
            let allMatches = [];
            
            function getLocalDates() {
                const now = new Date();
                const tmrw = new Date(now);
                tmrw.setDate(tmrw.getDate() + 1);
                return {
                    today: now.toISOString().split('T')[0],
                    tomorrow: tmrw.toISOString().split('T')[0]
                };
            }
            
            async function fetchMatches() {
                try {
                    const response = await fetch('/api/radar');
                    const data = await response.json();
                    allMatches = data.matches;
                    filterMatches();
                } catch (err) {
                    document.getElementById('radar-feed').innerHTML = "<span style='color:red'>Connection lost.</span>";
                }
            }
            
            function renderMatches(matches) {
                const container = document.getElementById('radar-feed');
                container.innerHTML = '';
                if(matches.length === 0) {
                    container.innerHTML = '<span style="color:#555;">No matches found for this filter.</span>';
                    return;
                }
                matches.forEach(m => {
                    const card = document.createElement('div');
                    card.className = 'match-card';
                    card.innerHTML = `
                        <div class="match-date">${m.date} [${m.status}]</div>
                        <div class="match-title">${m.matchup}</div>
                        <div class="stat-row"><span>Objective Util (f):</span> <span>${m.f_model}</span></div>
                        <div class="stat-row"><span>Market Implied:</span> <span>${m.p_market}</span></div>
                        <div class="stat-row"><span>QDT Attraction:</span> <span>${m.q_factor}</span></div>
                        <div class="pick-box" style="border: 1px solid ${m.color}; color: ${m.color};">
                            ${m.signal} | PICK: ${m.pick} | STAKE: ${m.kelly}
                        </div>
                    `;
                    container.appendChild(card);
                });
            }
            
            function filterMatches() {
                const query = document.getElementById('searchInput').value.toLowerCase();
                const dateFilter = document.getElementById('dateFilter').value;
                const { today, tomorrow } = getLocalDates();
                
                const filtered = allMatches.filter(m => {
                    const textMatch = m.matchup.toLowerCase().includes(query);
                    let dateMatch = true;
                    
                    if (dateFilter === 'LIVE') dateMatch = (m.status === 'LIVE');
                    else if (dateFilter === 'TODAY') dateMatch = (m.date === today);
                    else if (dateFilter === 'TOMORROW') dateMatch = (m.date === tomorrow);
                    else if (dateFilter === 'FUTURE') dateMatch = (m.date > tomorrow);
                    
                    return textMatch && dateMatch;
                });
                renderMatches(filtered);
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
