-- =====================================================
-- PLC Data Collector - Minimal Supabase Schema
-- =====================================================
-- Quick setup version with just the essential tables
-- Use this for a simple setup or if you prefer minimal configuration
-- =====================================================

-- Historical data table (stores all data points)
CREATE TABLE IF NOT EXISTS plc_data_historical (
    id BIGSERIAL PRIMARY KEY,
    plc_name TEXT NOT NULL,
    tag_name TEXT NOT NULL,
    tag_value JSONB,
    timestamp TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Real-time data table (stores latest values only)
CREATE TABLE IF NOT EXISTS plc_data_realtime (
    id TEXT PRIMARY KEY,
    plc_name TEXT NOT NULL,
    tag_name TEXT NOT NULL,
    tag_value JSONB,
    timestamp TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Essential indexes for performance
CREATE INDEX IF NOT EXISTS idx_historical_plc_tag_time 
    ON plc_data_historical(plc_name, tag_name, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_realtime_plc_tag 
    ON plc_data_realtime(plc_name, tag_name);

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'PLC Data Collector tables created successfully!';
    RAISE NOTICE 'You can now run the application with your Supabase credentials.';
END $$;
