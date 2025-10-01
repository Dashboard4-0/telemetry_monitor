-- =====================================================
-- PLC Data Collector - Supabase Database Schema
-- =====================================================
-- This SQL script creates the complete database schema
-- for the PLC Data Collector application.
--
-- Run this script in your Supabase SQL Editor to set up
-- the required tables, indexes, and functions.
-- =====================================================

-- =====================================================
-- 1. HISTORICAL DATA TABLE
-- =====================================================
-- Stores every data point with timestamp for trending,
-- reporting, and analysis. Data is never overwritten.

CREATE TABLE IF NOT EXISTS plc_data_historical (
    id BIGSERIAL PRIMARY KEY,
    plc_name TEXT NOT NULL,
    tag_name TEXT NOT NULL,
    tag_value JSONB,
    timestamp TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- 2. REAL-TIME DATA TABLE
-- =====================================================
-- Stores only the latest value for each tag.
-- Used for dashboards and current status displays.
-- Values are updated (upserted) on each scan.

CREATE TABLE IF NOT EXISTS plc_data_realtime (
    id TEXT PRIMARY KEY,  -- Composite key: plc_name + "_" + tag_name
    plc_name TEXT NOT NULL,
    tag_name TEXT NOT NULL,
    tag_value JSONB,
    timestamp TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- 3. INDEXES FOR PERFORMANCE
-- =====================================================

-- Historical table indexes
CREATE INDEX IF NOT EXISTS idx_historical_plc_tag_time 
    ON plc_data_historical(plc_name, tag_name, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_historical_timestamp 
    ON plc_data_historical(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_historical_plc_name 
    ON plc_data_historical(plc_name);

CREATE INDEX IF NOT EXISTS idx_historical_tag_name 
    ON plc_data_historical(tag_name);

-- Real-time table indexes
CREATE INDEX IF NOT EXISTS idx_realtime_plc_tag 
    ON plc_data_realtime(plc_name, tag_name);

CREATE INDEX IF NOT EXISTS idx_realtime_plc_name 
    ON plc_data_realtime(plc_name);

CREATE INDEX IF NOT EXISTS idx_realtime_updated_at 
    ON plc_data_realtime(updated_at DESC);

-- =====================================================
-- 4. ROW LEVEL SECURITY (RLS) POLICIES
-- =====================================================
-- Enable RLS for security (optional but recommended)

-- Enable RLS on both tables
ALTER TABLE plc_data_historical ENABLE ROW LEVEL SECURITY;
ALTER TABLE plc_data_realtime ENABLE ROW LEVEL SECURITY;

-- Allow authenticated users to read all data
CREATE POLICY "Allow authenticated read access" ON plc_data_historical
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Allow authenticated read access" ON plc_data_realtime
    FOR SELECT USING (auth.role() = 'authenticated');

-- Allow service role to insert/update data (for the application)
CREATE POLICY "Allow service role full access" ON plc_data_historical
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Allow service role full access" ON plc_data_realtime
    FOR ALL USING (auth.role() = 'service_role');

-- =====================================================
-- 5. HELPFUL FUNCTIONS
-- =====================================================

-- Function to get latest values for a specific PLC
CREATE OR REPLACE FUNCTION get_latest_plc_values(plc_name_param TEXT)
RETURNS TABLE (
    tag_name TEXT,
    tag_value JSONB,
    data_timestamp TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        rt.tag_name,
        rt.tag_value,
        rt.timestamp,
        rt.updated_at
    FROM plc_data_realtime rt
    WHERE rt.plc_name = plc_name_param
    ORDER BY rt.tag_name;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get historical data for a specific PLC and tag
CREATE OR REPLACE FUNCTION get_historical_data(
    plc_name_param TEXT,
    tag_name_param TEXT,
    hours_back INTEGER DEFAULT 24,
    limit_records INTEGER DEFAULT 1000
)
RETURNS TABLE (
    id BIGINT,
    tag_value JSONB,
    data_timestamp TIMESTAMPTZ,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        h.id,
        h.tag_value,
        h.timestamp,
        h.created_at
    FROM plc_data_historical h
    WHERE h.plc_name = plc_name_param
      AND h.tag_name = tag_name_param
      AND h.timestamp >= NOW() - INTERVAL '1 hour' * hours_back
    ORDER BY h.timestamp DESC
    LIMIT limit_records;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to clean up old historical data
CREATE OR REPLACE FUNCTION cleanup_old_historical_data(days_to_keep INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM plc_data_historical
    WHERE timestamp < NOW() - INTERVAL '1 day' * days_to_keep;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- 6. AUTOMATED CLEANUP TRIGGER
-- =====================================================
-- Optional: Automatically clean up old historical data
-- Uncomment the following if you want automatic cleanup

-- CREATE OR REPLACE FUNCTION trigger_cleanup_old_data()
-- RETURNS TRIGGER AS $$
-- BEGIN
--     -- Only run cleanup once per day to avoid performance issues
--     IF NOT EXISTS (
--         SELECT 1 FROM pg_stat_user_tables 
--         WHERE schemaname = 'public' 
--           AND relname = 'cleanup_log'
--     ) THEN
--         CREATE TABLE IF NOT EXISTS cleanup_log (
--             id SERIAL PRIMARY KEY,
--             last_cleanup TIMESTAMPTZ DEFAULT NOW(),
--             deleted_records INTEGER DEFAULT 0
--         );
--     END IF;
--     
--     -- Only cleanup if last cleanup was more than 24 hours ago
--     IF NOT EXISTS (
--         SELECT 1 FROM cleanup_log 
--         WHERE last_cleanup > NOW() - INTERVAL '24 hours'
--     ) THEN
--         INSERT INTO cleanup_log (deleted_records)
--         VALUES (cleanup_old_historical_data(30));
--     END IF;
--     
--     RETURN NULL;
-- END;
-- $$ LANGUAGE plpgsql;

-- CREATE TRIGGER cleanup_trigger
--     AFTER INSERT ON plc_data_historical
--     FOR EACH STATEMENT
--     EXECUTE FUNCTION trigger_cleanup_old_data();

-- =====================================================
-- 7. USEFUL VIEWS
-- =====================================================

-- View for PLC status summary
CREATE OR REPLACE VIEW plc_status_summary AS
SELECT 
    plc_name,
    COUNT(DISTINCT tag_name) as active_tags,
    MAX(updated_at) as last_update,
    MIN(updated_at) as first_update,
    NOW() - MAX(updated_at) as time_since_last_update
FROM plc_data_realtime
GROUP BY plc_name
ORDER BY plc_name;

-- View for tag statistics
CREATE OR REPLACE VIEW tag_statistics AS
SELECT 
    plc_name,
    tag_name,
    tag_value,
    timestamp as data_timestamp,
    updated_at,
    NOW() - updated_at as age
FROM plc_data_realtime
ORDER BY plc_name, tag_name;

-- View for recent data activity
CREATE OR REPLACE VIEW recent_activity AS
SELECT 
    'Historical' as data_type,
    plc_name,
    COUNT(*) as record_count,
    MAX(timestamp) as latest_timestamp,
    MIN(timestamp) as earliest_timestamp
FROM plc_data_historical
WHERE timestamp >= NOW() - INTERVAL '1 hour'
GROUP BY plc_name

UNION ALL

SELECT 
    'Real-time' as data_type,
    plc_name,
    COUNT(*) as record_count,
    MAX(updated_at) as latest_timestamp,
    MIN(updated_at) as earliest_timestamp
FROM plc_data_realtime
WHERE updated_at >= NOW() - INTERVAL '1 hour'
GROUP BY plc_name

ORDER BY plc_name, data_type;

-- =====================================================
-- 8. SAMPLE QUERIES
-- =====================================================

-- Example queries you can run after setting up the schema:

-- Get all latest values for a PLC:
-- SELECT * FROM get_latest_plc_values('MyPLC');

-- Get historical data for a specific tag:
-- SELECT * FROM get_historical_data('MyPLC', 'Machine.Speed', 24, 100);

-- Get PLC status summary:
-- SELECT * FROM plc_status_summary;

-- Get tag statistics:
-- SELECT * FROM tag_statistics WHERE plc_name = 'MyPLC';

-- Get recent activity:
-- SELECT * FROM recent_activity;

-- Clean up old data (manual):
-- SELECT cleanup_old_historical_data(30);

-- =====================================================
-- 9. COMPLETION MESSAGE
-- =====================================================

-- This will show a message when the script completes
DO $$
BEGIN
    RAISE NOTICE '=====================================================';
    RAISE NOTICE 'PLC Data Collector Database Schema Created Successfully!';
    RAISE NOTICE '=====================================================';
    RAISE NOTICE 'Tables created:';
    RAISE NOTICE '- plc_data_historical (for storing all data points)';
    RAISE NOTICE '- plc_data_realtime (for storing latest values)';
    RAISE NOTICE '';
    RAISE NOTICE 'Functions created:';
    RAISE NOTICE '- get_latest_plc_values(plc_name)';
    RAISE NOTICE '- get_historical_data(plc_name, tag_name, hours_back, limit)';
    RAISE NOTICE '- cleanup_old_historical_data(days_to_keep)';
    RAISE NOTICE '';
    RAISE NOTICE 'Views created:';
    RAISE NOTICE '- plc_status_summary';
    RAISE NOTICE '- tag_statistics';
    RAISE NOTICE '- recent_activity';
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '1. Configure your .env file with SUPABASE_URL and SUPABASE_KEY';
    RAISE NOTICE '2. Run the PLC Data Collector application';
    RAISE NOTICE '3. Use the sample queries above to explore your data';
    RAISE NOTICE '=====================================================';
END $$;
