# Quick Start Guide - Dual Database Support

## Overview

The PLC Data Collector now supports both **Supabase** (cloud) and **SQLite** (local) databases. This guide helps you choose the right option and get started quickly.

## Database Comparison

| Feature | SQLite | Supabase |
|---------|--------|----------|
| **Setup Complexity** | ⭐ Simple | ⭐⭐⭐ Complex |
| **Internet Required** | ❌ No | ✅ Yes |
| **Cost** | 💚 Free | 💰 Paid (after free tier) |
| **Scalability** | ⭐ Limited | ⭐⭐⭐⭐⭐ High |
| **Concurrent Users** | ⭐ Single user | ⭐⭐⭐⭐⭐ Multiple users |
| **Backup** | ⭐ Manual | ⭐⭐⭐⭐⭐ Automatic |
| **Real-time Features** | ❌ No | ✅ Yes |
| **Web Dashboard** | ❌ No | ✅ Yes |

## Quick Start Options

### Option 1: SQLite (Recommended for Beginners)

**Best for**: Local development, testing, single-user deployments

1. **Install and Run**:
   ```bash
   pip install -r deployment/requirements.txt
   python Core\ Application/main.py
   ```

2. **Choose SQLite** in the setup wizard
3. **Accept default path** or specify custom location
4. **Start collecting data** immediately!

**Pros**: No internet needed, simple setup, free
**Cons**: Single file, limited scalability

### Option 2: Supabase (Recommended for Production)

**Best for**: Production deployments, team collaboration, large datasets

1. **Create Supabase Project**:
   - Go to [supabase.com](https://supabase.com)
   - Create new project
   - Get URL and API key from Settings → API

2. **Set up Database Schema**:
   - Copy contents of `deployment/supabase_schema.sql`
   - Run in Supabase SQL Editor

3. **Install and Run**:
   ```bash
   pip install -r deployment/requirements.txt
   python Core\ Application/main.py
   ```

4. **Choose Supabase** in the setup wizard
5. **Enter your credentials** when prompted

**Pros**: Scalable, cloud backup, real-time features
**Cons**: Requires internet, setup complexity

## First-Time Setup Wizard

When you run the application for the first time, you'll see:

```
============================================================
    PLC Data Collector - Database Setup Wizard    
============================================================

Welcome! Let's configure your database for storing PLC data.
You can change this configuration later by deleting the database_config.json file.

Available Database Options:

1. Supabase
   Cloud-hosted PostgreSQL database
   Pros: Scalable, Cloud backup, Real-time features, Web dashboard
   Cons: Requires internet, Setup complexity, Monthly cost

2. SQLite
   Local file-based database
   Pros: Simple setup, No internet required, Free, Fast local access
   Cons: Single file, Limited concurrent access, No cloud backup

Select database type (1-2): 
```

## Manual Configuration (Advanced)

If you prefer to configure manually, create a `.env` file:

### For SQLite:
```env
SQLITE_DB_PATH=./data/plc_data.db
```

### For Supabase:
```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-key-here
```

## Switching Database Types

### Method 1: Reset and Reconfigure
1. Use Database Management menu (option 8) in main application
2. Choose "Reconfigure database"
3. Restart application to run setup wizard again

### Method 2: Manual Reset
1. Delete `database_config.json` file
2. Restart application to run setup wizard

### Method 3: Migrate Existing Data
Use the migration tools to transfer data between databases:

```bash
# Migrate from Supabase to SQLite
python Core\ Application/migration_tools.py --migrate-to-sqlite

# Migrate from SQLite to Supabase
python Core\ Application/migration_tools.py --migrate-to-supabase
```

## Docker Deployment

The Docker configuration supports both database types:

```bash
# Build and run with SQLite
docker-compose up -d

# Or configure Supabase in .env file first
echo "SUPABASE_URL=https://your-project.supabase.co" >> .env
echo "SUPABASE_KEY=your-key" >> .env
docker-compose up -d
```

## Troubleshooting

### SQLite Issues
- **Permission errors**: Ensure write access to database directory
- **File locked**: Close other applications using the database file
- **Path issues**: Use absolute paths for database location

### Supabase Issues
- **Connection failed**: Check URL and API key format
- **Schema missing**: Run `deployment/supabase_schema.sql` in Supabase SQL Editor
- **Rate limits**: Check Supabase usage limits

### General Issues
- **First run**: Delete `database_config.json` to restart setup wizard
- **Environment variables**: Check `.env` file format and values
- **Network issues**: Ensure PLC network connectivity

## Next Steps

1. **Configure PLCs**: Use the main menu to add your PLCs
2. **Import Tags**: Upload CSV files with your tag lists
3. **Start Collection**: Begin data collection
4. **Monitor Data**: Use the view data options to check collected information

## Support

- **Documentation**: See `Documentation/readme.md` for full documentation
- **Examples**: Check `Documentation/examples.py` for code examples
- **Docker**: See `deployment/DOCKER_README.md` for Docker setup
