import requests
import math
import datetime
from db_client import get_supabase_client, batch_upsert

# Major tournament coordinate mapping (Latitude, Longitude)
TOURNEY_COORDS = {
    "Australian Open": (-37.82, 144.98),
    "Roland Garros": (48.84, 2.25),
    "Wimbledon": (51.43, -0.21),
    "US Open": (40.75, -73.84),
    "Indian Wells": (33.72, -116.30),
    "Miami": (25.96, -80.24),
    "Monte Carlo": (43.75, 7.43),
    "Madrid": (40.37, -3.64),
    "Rome": (41.93, 12.45),
    "Shanghai Masters": (31.23, 121.47),
    "Paris Masters": (48.84, 2.38),
    "Cincinnati": (39.34, -84.27),
    "Canada": (45.53, -73.62) # Montreal baseline
}

# Standard Tennis Ball Constants for Drag Calculation
BALL_MASS_KG = 0.0577
BALL_AREA_M2 = 0.0033
DRAG_COEFF_CD = 0.55
STANDARD_VELOCITY_MS = 30.0 # ~67 mph average groundstroke

def calculate_thermodynamics(temp_c, rh_pct, pressure_hpa):
    """Calculates Air Density (rho) and Vapor Pressure Deficit (VPD)."""
    # 1. Air Density (Ideal Gas Law with humidity approximation)
    temp_k = temp_c + 273.15
    pressure_pa = pressure_hpa * 100
    r_specific = 287.058 # Specific gas constant for dry air
    air_density = pressure_pa / (r_specific * temp_k)
    
    # 2. Vapor Pressure Deficit (VPD)
    svp = 0.61078 * math.exp((17.27 * temp_c) / (temp_c + 237.3))
    avp = svp * (rh_pct / 100.0)
    vpd = svp - avp
    
    return round(air_density, 4), round(vpd, 3)

def calculate_aerodynamic_drag(air_density):
    """Calculates F_D = 0.5 * C_D * rho * A * v^2"""
    drag = 0.5 * DRAG_COEFF_CD * air_density * BALL_AREA_M2 * (STANDARD_VELOCITY_MS ** 2)
    return round(drag, 3)

def fetch_weather_for_matches():
    client = get_supabase_client()
    
    # Fetch 50 recent matches to seed weather data
    print("Fetching matches from database...")
    response = client.table("sackmann_match_records").select("match_id, tourney_name, tourney_id, tourney_date").order("tourney_date", desc=True).limit(50).execute()
    matches = response.data
    
    if not matches:
        print("No matches found. Run ingest_sackmann.py first.")
        return

    telemetry_records = []
    
    for match in matches:
        tourney_name = match.get("tourney_name", "")
        match_date = match.get("tourney_date")
        
        # Default to Shanghai if tournament not in strict mapping for testing
        coords = TOURNEY_COORDS.get(tourney_name, TOURNEY_COORDS["Shanghai Masters"])
        lat, lon = coords[0], coords[1]
        
        # Open-Meteo Historical API (No API Key required)
        url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={match_date}&end_date={match_date}&hourly=temperature_2m,relative_humidity_2m,surface_pressure"
        
        try:
            res = requests.get(url, timeout=15)
            if res.status_code == 200:
                data = res.json()
                hourly = data.get("hourly", {})
                
                # Sample the 14:00 (2:00 PM) timeslot for afternoon match approximation
                if hourly and "temperature_2m" in hourly and len(hourly["temperature_2m"]) > 14:
                    temp_c = hourly["temperature_2m"][14]
                    rh_pct = hourly["relative_humidity_2m"][14]
                    pressure_hpa = hourly["surface_pressure"][14]
                    
                    if temp_c is None or rh_pct is None or pressure_hpa is None:
                        continue
                        
                    rho, vpd = calculate_thermodynamics(temp_c, rh_pct, pressure_hpa)
                    f_d = calculate_aerodynamic_drag(rho)
                    
                    record = {
                        "match_id": match["match_id"],
                        "tourney_id": match["tourney_id"],
                        "recorded_at": f"{match_date}T14:00:00Z",
                        "latitude": lat,
                        "longitude": lon,
                        "temperature_c": temp_c,
                        "relative_humidity_pct": rh_pct,
                        "surface_pressure_hpa": pressure_hpa,
                        "air_density_kg_m3": rho,
                        "vapor_pressure_deficit_kpa": vpd,
                        "aerodynamic_drag_fd": f_d,
                        "court_pace_index": 35.0 # Baseline hardcourt CPI for V1
                    }
                    telemetry_records.append(record)
                    print(f"Calculated aerodynamics for {match['match_id']}: Rho={rho}, F_D={f_d}")
        except Exception as e:
            print(f"Failed to fetch weather for {match['match_id']}: {e}")

    if telemetry_records:
        print(f"Upserting {len(telemetry_records)} atmospheric records to Supabase...")
        batch_upsert("weather_telemetry", telemetry_records, chunk_size=100)
        print("Batch 3 Complete: Atmospheric Engine Seeded.")

if __name__ == "__main__":
    fetch_weather_for_matches()
