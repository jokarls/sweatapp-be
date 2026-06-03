-- SweatCheck Schema (Raw SQL)

-- Enum types for status
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'activity_status') THEN
        CREATE TYPE activity_status AS ENUM ('PENDING', 'COMPLETED');
    END IF;
END $$;

-- Table: user
CREATE TABLE IF NOT EXISTS "user" (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strava_athlete_id BIGINT UNIQUE NOT NULL,
    last_known_weight FLOAT,
    weight_unit VARCHAR(10) DEFAULT 'kg',
    fluid_unit VARCHAR(10) DEFAULT 'ml',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table: strava_token
CREATE TABLE IF NOT EXISTS "strava_token" (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- Table: activity
CREATE TABLE IF NOT EXISTS "activity" (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    strava_id BIGINT UNIQUE NOT NULL,
    
    -- Status and Flags
    status activity_status DEFAULT 'PENDING',
    is_indoor BOOLEAN DEFAULT FALSE,
    ignore_for_profile BOOLEAN DEFAULT FALSE,
    
    -- System/Strava/API Data
    activity_type VARCHAR(50),
    start_date TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    avg_heartrate FLOAT,
    relative_effort INTEGER,
    
    -- Weather (API)
    temp_celsius_api FLOAT,
    humidity_api INTEGER,
    
    -- User Input (Manual)
    weight_before_user FLOAT,
    weight_after_user FLOAT,
    fluid_intake_ml_user INTEGER,
    bathroom_visits_user INTEGER DEFAULT 0,
    clothing_index_user INTEGER, -- 1-3
    
    -- Weather (User Override)
    temp_celsius_user FLOAT,
    humidity_user INTEGER,
    
    -- Calculated Fields (The outcome)
    total_sweat_loss_ml INTEGER,
    sweat_rate_ml_per_hour FLOAT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indices for performance
CREATE INDEX IF NOT EXISTS idx_activity_user_id ON "activity"(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_strava_id ON "activity"(strava_id);
CREATE INDEX IF NOT EXISTS idx_strava_token_user_id ON "strava_token"(user_id);
