CREATE TABLE IF NOT EXISTS ping_table (
    id BIGSERIAL PRIMARY KEY,
    pinged_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    caller VARCHAR(64) NOT NULL DEFAULT 'github-actions-keepalive'
);

CREATE TABLE IF NOT EXISTS sackmann_match_records (
    match_id VARCHAR(64) PRIMARY KEY,
    tourney_id VARCHAR(32) NOT NULL,
    tourney_name VARCHAR(128) NOT NULL,
    surface VARCHAR(16) NOT NULL,
    draw_size SMALLINT,
    tourney_level VARCHAR(8),
    tourney_date DATE NOT NULL,
    match_num INTEGER NOT NULL,
    winner_id INTEGER NOT NULL,
    winner_seed VARCHAR(8),
    winner_entry VARCHAR(8),
    winner_name VARCHAR(128) NOT NULL,
    winner_hand VARCHAR(4),
    winner_ht SMALLINT,
    winner_ioc VARCHAR(8),
    winner_age NUMERIC(5, 2),
    loser_id INTEGER NOT NULL,
    loser_seed VARCHAR(8),
    loser_entry VARCHAR(8),
    loser_name VARCHAR(128) NOT NULL,
    loser_hand VARCHAR(4),
    loser_ht SMALLINT,
    loser_ioc VARCHAR(8),
    loser_age NUMERIC(5, 2),
    score VARCHAR(64) NOT NULL,
    best_of SMALLINT NOT NULL DEFAULT 3,
    round VARCHAR(16) NOT NULL,
    minutes INTEGER,
    w_ace INTEGER,
    w_df INTEGER,
    w_svpt INTEGER,
    w_1st_in INTEGER,
    w_1st_won INTEGER,
    w_2nd_won INTEGER,
    w_sv_gms INTEGER,
    w_bp_saved INTEGER,
    w_bp_faced INTEGER,
    l_ace INTEGER,
    l_df INTEGER,
    l_svpt INTEGER,
    l_1st_in INTEGER,
    l_1st_won INTEGER,
    l_2nd_won INTEGER,
    l_sv_gms INTEGER,
    l_bp_saved INTEGER,
    l_bp_faced INTEGER,
    winner_rank INTEGER,
    winner_rank_points INTEGER,
    loser_rank INTEGER,
    loser_rank_points INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS weather_telemetry (
    telemetry_id BIGSERIAL PRIMARY KEY,
    match_id VARCHAR(64) REFERENCES sackmann_match_records(match_id) ON DELETE CASCADE,
    tourney_id VARCHAR(32) NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL,
    latitude NUMERIC(8, 4) NOT NULL,
    longitude NUMERIC(8, 4) NOT NULL,
    temperature_c NUMERIC(5, 2) NOT NULL,
    relative_humidity_pct NUMERIC(5, 2) NOT NULL,
    surface_pressure_hpa NUMERIC(6, 2) NOT NULL,
    air_density_kg_m3 NUMERIC(6, 4) NOT NULL,
    vapor_pressure_deficit_kpa NUMERIC(6, 3) NOT NULL,
    aerodynamic_drag_fd NUMERIC(7, 3),
    court_pace_index NUMERIC(5, 2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS market_odds_clv (
    odds_id BIGSERIAL PRIMARY KEY,
    match_id VARCHAR(64) REFERENCES sackmann_match_records(match_id) ON DELETE CASCADE,
    bookmaker VARCHAR(64) NOT NULL,
    timestamp_captured TIMESTAMPTZ NOT NULL,
    is_closing_line BOOLEAN NOT NULL DEFAULT FALSE,
    winner_decimal_odds NUMERIC(8, 3) NOT NULL,
    loser_decimal_odds NUMERIC(8, 3) NOT NULL,
    winner_implied_prob_raw NUMERIC(6, 5) NOT NULL,
    loser_implied_prob_raw NUMERIC(6, 5) NOT NULL,
    winner_implied_prob_novig NUMERIC(6, 5) NOT NULL,
    loser_implied_prob_novig NUMERIC(6, 5) NOT NULL,
    model_utility_f NUMERIC(6, 5) NOT NULL,
    qdt_attraction_q NUMERIC(6, 5) NOT NULL,
    clv_edge_pct NUMERIC(6, 3),
    quarter_law_flag BOOLEAN NOT NULL DEFAULT FALSE,
    geter_anomaly_flag BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sackmann_tourney_date ON sackmann_match_records (tourney_date DESC);
CREATE INDEX IF NOT EXISTS idx_sackmann_players ON sackmann_match_records (winner_id, loser_id);
CREATE INDEX IF NOT EXISTS idx_weather_match_id ON weather_telemetry (match_id);
CREATE INDEX IF NOT EXISTS idx_market_match_id ON market_odds_clv (match_id);
