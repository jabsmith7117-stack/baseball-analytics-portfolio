DROP TABLE IF EXISTS teams;
DROP TABLE IF EXISTS hitters;
DROP TABLE IF EXISTS hitter_season_stats;
DROP TABLE IF EXISTS hitter_platoon_splits;
DROP TABLE IF EXISTS hitter_pitch_type_splits;
DROP TABLE IF EXISTS hitter_zone_splits;
DROP TABLE IF EXISTS pitchers;
DROP TABLE IF EXISTS pitcher_season_stats;
DROP TABLE IF EXISTS pitcher_platoon_splits;
DROP TABLE IF EXISTS pitcher_pitch_type_splits;

CREATE TABLE teams (
    team_abbr TEXT PRIMARY KEY
);

CREATE TABLE hitters (
    batter_id INTEGER PRIMARY KEY,
    batter_name TEXT NOT NULL,
    team_abbr TEXT,
    bats TEXT,
    FOREIGN KEY (team_abbr) REFERENCES teams (team_abbr)
);

CREATE TABLE hitter_season_stats (
    batter_id INTEGER PRIMARY KEY,
    total_pa INTEGER,
    at_bats INTEGER,
    hits INTEGER,
    home_runs INTEGER,
    batting_avg REAL,
    on_base_pct REAL,
    slugging_pct REAL,
    ops REAL,
    iso REAL,
    babip REAL,
    woba REAL,
    xwoba REAL,
    xba REAL,
    xwobacon REAL,
    k_rate REAL,
    bb_rate REAL,
    chase_rate REAL,
    whiff_rate REAL,
    hard_hit_rate REAL,
    avg_exit_velo REAL,
    avg_bat_speed REAL,
    avg_swing_length REAL,
    barrel_rate REAL,
    sweet_spot_rate REAL,
    in_zone_contact_rate REAL,
    out_zone_contact_rate REAL,
    pulled_flyball_rate REAL,
    fly_ball_rate REAL,
    line_drive_rate REAL,
    ground_ball_rate REAL,
    FOREIGN KEY (batter_id) REFERENCES hitters (batter_id)
);

CREATE TABLE hitter_platoon_splits (
    batter_id INTEGER,
    vs_throws TEXT,
    performance_pa INTEGER,
    woba REAL,
    xwoba REAL,
    k_rate REAL,
    whiff_rate REAL,
    hard_hit_rate REAL,
    PRIMARY KEY (batter_id, vs_throws),
    FOREIGN KEY (batter_id) REFERENCES hitters (batter_id)
);

CREATE TABLE hitter_pitch_type_splits (
    batter_id INTEGER,
    pitch_type TEXT,
    performance_pa INTEGER,
    woba REAL,
    xwoba REAL,
    whiff_rate REAL,
    hard_hit_rate REAL,
    PRIMARY KEY (batter_id, pitch_type),
    FOREIGN KEY (batter_id) REFERENCES hitters (batter_id)
);

CREATE TABLE hitter_zone_splits (
    batter_id INTEGER,
    zone INTEGER,
    performance_pa INTEGER,
    woba REAL,
    hard_hit_rate REAL,
    PRIMARY KEY (batter_id, zone),
    FOREIGN KEY (batter_id) REFERENCES hitters (batter_id)
);

CREATE TABLE pitchers (
    pitcher_id INTEGER PRIMARY KEY,
    pitcher_name TEXT NOT NULL,
    team_abbr TEXT,
    throws TEXT,
    FOREIGN KEY (team_abbr) REFERENCES teams (team_abbr)
);

CREATE TABLE pitcher_season_stats (
    pitcher_id INTEGER PRIMARY KEY,
    total_pa INTEGER,
    hits_allowed INTEGER,
    home_runs_allowed INTEGER,
    avg_against REAL,
    obp_against REAL,
    slg_against REAL,
    ops_against REAL,
    woba_against REAL,
    xwoba_against REAL,
    xba_against REAL,
    xwobacon_against REAL,
    k_rate REAL,
    bb_rate REAL,
    csw_rate REAL,
    chase_rate_induced REAL,
    whiff_rate_induced REAL,
    hard_hit_rate_allowed REAL,
    avg_exit_velo_allowed REAL,
    FOREIGN KEY (pitcher_id) REFERENCES pitchers (pitcher_id)
);

CREATE TABLE pitcher_platoon_splits (
    pitcher_id INTEGER,
    vs_stand TEXT,
    performance_pa INTEGER,
    woba_against REAL,
    k_rate REAL,
    whiff_rate_induced REAL,
    hard_hit_rate_allowed REAL,
    PRIMARY KEY (pitcher_id, vs_stand),
    FOREIGN KEY (pitcher_id) REFERENCES pitchers (pitcher_id)
);

CREATE TABLE pitcher_pitch_type_splits (
    pitcher_id INTEGER,
    pitch_type TEXT,
    usage_rate REAL,
    avg_velocity REAL,
    avg_spin_rate REAL,
    performance_pa INTEGER,
    woba_against REAL,
    whiff_rate_induced REAL,
    PRIMARY KEY (pitcher_id, pitch_type),
    FOREIGN KEY (pitcher_id) REFERENCES pitchers (pitcher_id)
);