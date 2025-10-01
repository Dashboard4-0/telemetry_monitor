# Supabase Database Setup Guide

## Overview

This guide explains how to set up your Supabase database for the PLC Data Collector application.

## Prerequisites

- Supabase account (free tier available)
- Supabase project created
- Access to Supabase SQL Editor

## Quick Setup (5 minutes)

### Step 1: Create Supabase Project

1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Click "New Project"
3. Choose organization and enter project details
4. Wait for project creation (2-3 minutes)

### Step 2: Get Your Credentials

1. Go to Settings → API
2. Copy the following:
   - **Project URL** (looks like: `https://abcdefghijklmnop.supabase.co`)
   - **anon public key** (starts with `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`)

### Step 3: Configure Environment

Add these to your `.env` file:

```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-key-here
```

### Step 4: Create Database Schema

Choose one of these options:

#### Option A: Minimal Setup (Recommended for beginners)

1. Go to Supabase → SQL Editor
2. Copy the contents of `deployment/supabase_schema_minimal.sql`
3. Paste into SQL Editor
4. Click "Run"

#### Option B: Complete Setup (Recommended for production)

1. Go to Supabase → SQL Editor
2. Copy the contents of `deployment/supabase_schema.sql` (FIXED VERSION)
3. Paste into SQL Editor
4. Click "Run"

**Note**: The complete schema has been fixed to resolve PostgreSQL reserved keyword conflicts.

### Step 5: Test Connection

Run the PLC Data Collector application - it will automatically test the connection.

## Schema Details

### Tables Created

#### 1. `plc_data_historical`
- **Purpose**: Stores every data point for trending and analysis
- **Key Features**: 
  - Never overwrites data
  - Optimized for time-series queries
  - Includes indexes for fast retrieval

#### 2. `plc_data_realtime`
- **Purpose**: Stores only the latest value for each tag
- **Key Features**:
  - Updates existing records (upsert)
  - Fast access for dashboards
  - Composite primary key: `plc_name + "_" + tag_name`

### Data Structure

Both tables store tag values in JSONB format:

```json
{
  "value": 123.45,
  "type": "float"
}
```

This preserves:
- Original data types (int, float, bool, string)
- Complex data structures (arrays, objects)
- Metadata about the data type

## Complete Setup Features

The complete schema includes:

### 🔐 Security
- Row Level Security (RLS) policies
- Separate access for authenticated users and service role

### 📊 Helper Functions
- `get_latest_plc_values(plc_name)` - Get all current values for a PLC
- `get_historical_data(plc_name, tag_name, hours_back, limit)` - Get historical data
- `cleanup_old_historical_data(days_to_keep)` - Clean up old data

### 📈 Monitoring Views
- `plc_status_summary` - Overview of all PLCs
- `tag_statistics` - Current tag values with metadata
- `recent_activity` - Recent data collection activity

### 🧹 Automated Cleanup
- Optional trigger for automatic old data cleanup
- Configurable retention periods

## Sample Queries

After setup, you can use these queries in Supabase:

```sql
-- Get all current values for a PLC
SELECT * FROM get_latest_plc_values('MyPLC');

-- Get historical data for a specific tag
SELECT * FROM get_historical_data('MyPLC', 'Machine.Speed', 24, 100);

-- Get PLC status summary
SELECT * FROM plc_status_summary;

-- Get recent activity
SELECT * FROM recent_activity;

-- Manual cleanup of old data
SELECT cleanup_old_historical_data(30);
```

## Troubleshooting

### Connection Issues

1. **"Invalid API key"**
   - Verify your SUPABASE_KEY is correct
   - Make sure you're using the `anon` key, not the `service_role` key

2. **"Project not found"**
   - Check your SUPABASE_URL is correct
   - Ensure the project is active in Supabase dashboard

3. **"Table doesn't exist"**
   - Run the schema creation SQL in Supabase SQL Editor
   - Check for any errors in the SQL execution

4. **SQL syntax errors (timestamp conflicts)**
   - Use the fixed version: `deployment/supabase_schema.sql`
   - The minimal version (`supabase_schema_minimal.sql`) should always work
   - If you still get errors, try running the SQL in smaller chunks

### Data Issues

1. **No data appearing**
   - Check PLC connection status in the application
   - Verify tag names match exactly (case-sensitive)
   - Check Supabase logs for errors

2. **Performance issues**
   - Ensure indexes were created properly
   - Consider data retention policies for large datasets

## Security Best Practices

### For Development
- Use the `anon` key in your `.env` file
- Enable RLS policies (included in complete setup)

### For Production
- Consider using service role key for the application
- Implement custom RLS policies for your use case
- Use environment variables for credentials
- Enable Supabase's built-in security features

## Data Retention

### Default Settings
- Historical data: Keep forever (no automatic cleanup)
- Real-time data: Keep all records (updates existing)

### Custom Retention
```sql
-- Clean up historical data older than 90 days
SELECT cleanup_old_historical_data(90);

-- Check how much data you have
SELECT 
    plc_name,
    COUNT(*) as records,
    MIN(timestamp) as oldest,
    MAX(timestamp) as newest
FROM plc_data_historical
GROUP BY plc_name;
```

## Monitoring and Maintenance

### Check Data Collection Status
```sql
SELECT * FROM plc_status_summary;
```

### Monitor Storage Usage
```sql
-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public' 
  AND tablename LIKE 'plc_data%';
```

### Performance Monitoring
```sql
-- Check index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;
```

## Support

For issues with Supabase setup:
1. Check the Supabase documentation
2. Verify your credentials and project status
3. Review the SQL execution logs in Supabase
4. Test with the minimal schema first

---

**Next Steps**: After setting up Supabase, configure your PLC connections and start collecting data!
