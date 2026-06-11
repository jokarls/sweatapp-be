-- Migration: Add apparent temperature and weather code columns
ALTER TABLE "activity" 
ADD COLUMN IF NOT EXISTS apparent_temp_celsius_api FLOAT,
ADD COLUMN IF NOT EXISTS weather_code_api INTEGER;
