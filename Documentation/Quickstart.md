# Quick Start Guide

## 🚀 Get Running in 5 Minutes

### Prerequisites
- Python 3.8+ installed
- Access to your PLCs on the network
- Supabase account (free tier works)

### Step 1: Installation
```bash
# Run the setup script
chmod +x setup.sh
./setup.sh

# Or manually:
pip install -r requirements.txt
cp .env.sample .env
```

### Step 2: Configure Supabase

1. Go to your [Supabase Dashboard](https://app.supabase.com)
2. Create a new project or use existing
3. Go to SQL Editor and run:

**Quick Setup**: Copy and run `deployment/supabase_schema_minimal.sql`

**Complete Setup**: Copy and run `deployment/supabase_schema.sql`

See `deployment/SUPABASE_SETUP.md` for detailed instructions.

4. Get your credentials from Settings > API:
   - Copy the URL and anon key to `.env`:
```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6Ikp.....
```

### Step 3: Configure Your First PLC

```bash
# Run the tool
python main.py

# Select option 1: Setup new PLC
# Follow the prompts:
#   - Name: MyPLC
#   - Type: CompactLogix (or your PLC type)
#   - IP: 192.168.1.100 (your PLC's IP)
#   - Slot: 0 (usually 0 for CompactLogix)
```

### Step 4: Import Tags

Option A: Use the sample tags:
```bash
# In the menu, select option 4: Import tag list
# Use: sample_tags.csv
```

Option B: Create your own CSV:
```csv
tag_name,description,data_type,scan_rate
YourTag.Name,Description,DINT,1.0
Another.Tag,Description,REAL,0.5
```

### Step 5: Test & Collect

```bash
# Test connection (option 3)
# If successful, start collection (option 5)
```

## 🎯 Common PLC Configurations

### CompactLogix L3x
```yaml
controller_type: CompactLogix
ip_address: 192.168.1.100
slot: 0
```

### MicroLogix 1400
```yaml
controller_type: MicroLogix1400
ip_address: 192.168.1.101
# No slot needed
```

### ControlLogix
```yaml
controller_type: ControlLogix
ip_address: 192.168.1.102
slot: 2  # Check your rack configuration
```

## 📊 Viewing Your Data

### In Supabase
1. Go to Table Editor in Supabase
2. View `plc_data_realtime` for current values
3. View `plc_data_historical` for trends

### In the Tool
```bash
# Select option 7: View collected data
# Choose real-time or historical view
```

### Via SQL (in Supabase)
```sql
-- Latest values
SELECT * FROM plc_data_realtime 
WHERE plc_name = 'MyPLC'
ORDER BY updated_at DESC;

-- Historical trend
SELECT * FROM plc_data_historical 
WHERE plc_name = 'MyPLC' 
  AND tag_name = 'Machine.Speed'
  AND timestamp > NOW() - INTERVAL '1 hour'
ORDER BY timestamp DESC;
```

## 🐳 Docker Deployment

### Quick Start

```bash
# From the project root directory
cd deployment
./build.sh

# Or manually with Docker Compose
docker-compose -f deployment/docker-compose.yml up -d

# Access the container interactively
docker-compose -f deployment/docker-compose.yml run --rm plc-collector
```

### Docker Configuration

The Docker setup includes:
- Multi-stage build for optimized image size
- Proper file copying from correct source directories
- Environment variable configuration
- Volume mounts for persistent configuration
- Host network mode for PLC access

See `deployment/DOCKER_README.md` for detailed Docker deployment instructions.

## 🔧 Troubleshooting Quick Fixes

### Can't Connect to PLC?
```bash
# Test network connectivity
ping 192.168.1.100  # Your PLC IP

# Check Windows Firewall (if on Windows)
# Port 44818 must be open for EtherNet/IP
```

### Wrong Slot Number?
- CompactLogix: Usually slot 0
- ControlLogix: Check your rack, often 0-3
- MicroLogix: No slot needed

### Tag Read Errors?
- Check exact tag name spelling (case-sensitive!)
- For arrays: use `TagName[0]` format
- For UDTs: use `UDT.Member` format

### Database Errors?
```bash
# Verify credentials in .env
# Test connection:
python -c "from database_manager import SupabaseManager; SupabaseManager().test_connection()"
```

## 📝 Example Tag Names

### Common CompactLogix Tags
```
Local:1:I.Data[0]     # Input module
Local:2:O.Data[0]     # Output module
Program:MainProgram.Tag
Controller.Tag
```

### Common MicroLogix Tags
```
N7:0                  # Integer file
F8:0                  # Float file
B3:0/0                # Binary bit
T4:0.ACC              # Timer accumulator
C5:0.ACC              # Counter accumulator
```

## 🎓 Next Steps

1. **Set up multiple PLCs**: Configure all your controllers
2. **Create dashboards**: Use Grafana or Supbase's built-in dashboards
3. **Set up alerts**: Use Supabase functions for notifications
4. **Optimize scan rates**: Adjust per tag based on your needs
5. **Implement data retention**: Clean up old historical data

## 💡 Pro Tips

- Start with slow scan rates (5-10 seconds) and optimize later
- Group similar tags by scan rate for efficiency
- Use the examples.py file to build custom scripts
- Monitor the error_count in PLC status
- Set up a cron job or Windows Task for automatic startup

## 📞 Getting Help

1. Check the full README.md for detailed documentation
2. Review examples.py for code samples
3. Check pycomm3 documentation for PLC-specific issues
4. Consult Supabase docs for database questions

---

**Ready to collect data!** 🎉
