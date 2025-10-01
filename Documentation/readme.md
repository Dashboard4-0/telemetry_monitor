# PLC Data Collector

A robust Python tool for collecting data from Allen-Bradley CompactLogix and MicroLogix PLCs using pycomm3, with flexible database storage options supporting both cloud (Supabase) and local (SQLite) databases.

## Features

- ✅ Support for multiple PLC types (CompactLogix, ControlLogix, MicroLogix 1100/1400, Micro850/870)
- ✅ **Dual Database Support**: Choose between Supabase (cloud) or SQLite (local) storage
- ✅ **Interactive Setup Wizard**: Easy first-time configuration with guided database selection
- ✅ CSV-based tag list import for easy configuration
- ✅ Concurrent data collection from multiple PLCs
- ✅ Dual storage modes: Historical (append) and Real-time (upsert)
- ✅ Interactive CLI interface with colored output
- ✅ Connection testing and status monitoring
- ✅ Configurable scan rates per tag
- ✅ Automatic reconnection on connection loss
- ✅ Thread-safe data collection
- ✅ **Database Migration Tools**: Migrate data between Supabase and SQLite

## Prerequisites

- Python 3.8 or higher
- Network access to your PLCs
- **For Supabase**: Supabase account with a project created
- **For SQLite**: No additional requirements (uses local file storage)

## Quick Start

### 1. Installation

```bash
# Clone or download this repository
cd plc_data_collector

# Install required packages
pip install -r deployment/requirements.txt
```

### 2. First-Time Setup

Run the application for the first time to launch the interactive database setup wizard:

```bash
python Core\ Application/main.py
```

The wizard will guide you through:
- **Database Selection**: Choose between Supabase (cloud) or SQLite (local)
- **Configuration**: Enter connection details for your chosen database
- **Testing**: Verify your database connection

### 3. Database Options

#### Option A: SQLite (Recommended for beginners)
- **Pros**: Simple setup, no internet required, free, fast local access
- **Cons**: Single file, limited concurrent access, no cloud backup
- **Best for**: Local development, testing, small deployments

#### Option B: Supabase (Recommended for production)
- **Pros**: Scalable, cloud backup, real-time features, web dashboard
- **Cons**: Requires internet, setup complexity, monthly cost
- **Best for**: Production deployments, team collaboration, large datasets

### 4. Manual Database Setup (Optional)

If you prefer to configure manually, create a `.env` file:

```env
# For Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here

# For SQLite (optional)
SQLITE_DB_PATH=./data/plc_data.db
```

## Database Management

### Changing Database Type

To switch between database types:

1. **Reset Configuration**: Use the Database Management menu (option 8) in the main application
2. **Reconfigure**: Restart the application to run the setup wizard again
3. **Migrate Data**: Use the migration tools to transfer existing data

### Migration Tools

The system includes tools for migrating data between databases:

```bash
# Migrate from Supabase to SQLite
python Core\ Application/migration_tools.py --migrate-to-sqlite

# Migrate from SQLite to Supabase  
python Core\ Application/migration_tools.py --migrate-to-supabase
```

### Database Management Menu

The main application includes a Database Management menu (option 8) with options to:
- View current database configuration
- Test database connection
- View database statistics
- Reset configuration for re-setup

## Configuration

### Environment Variables

Create a `.env` file with your Supabase credentials:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
```

### Tag List CSV Format

Create CSV files with your PLC tags in the following format:

```csv
tag_name,description,data_type,scan_rate
Machine.Status,Machine running status,DINT,1.0
Machine.Speed,Current speed,REAL,0.5
Machine.Temperature,Operating temp,REAL,2.0
```

Required columns:
- `tag_name`: The exact tag name in the PLC

Optional columns:
- `description`: Tag description (default: empty)
- `data_type`: Tag data type (default: AUTO)
- `scan_rate`: Scan rate in seconds (default: 1.0)

## Usage

### Interactive Mode

Run the tool in interactive mode for easy setup and management:

```bash
python main.py
```

This will present a menu with options to:
1. Setup new PLC
2. List configured PLCs
3. Test PLC connections
4. Import tag lists
5. Start/stop data collection
6. View collected data

### Command Line Mode

Use command line arguments for automation:

```bash
# Setup a new PLC
python main.py --setup

# List all configured PLCs
python main.py --list

# Test connection to a specific PLC
python main.py --test PLC_NAME

# Import tag list for a PLC
python main.py --import-tags PLC_NAME tags.csv

# Start data collection (runs continuously)
python main.py --collect
```

## PLC Setup Process

1. **Configure PLC**: Use the interactive setup or edit configuration files directly
2. **Import Tags**: Import your tag list from a CSV file
3. **Test Connection**: Verify the PLC is accessible
4. **Start Collection**: Begin collecting data to Supabase

### Example Setup Session

```bash
$ python main.py

=== Main Menu ===
1. Setup new PLC
...

Select option: 1

=== PLC Setup ===
Enter PLC name: Line1_Controller
Select controller type: CompactLogix
Enter PLC IP address: 192.168.1.100
Enter slot number (default: 0): 0
✓ PLC 'Line1_Controller' configured successfully

Do you want to import a tag list CSV? (y/n): y
Enter CSV file path: sample_tags.csv
✓ Imported 20 tags for PLC 'Line1_Controller'

Test connection now? (y/n): y
✓ Connected to Line1_Controller
  Controller: CompactLogix 5380
  Revision: 32.011
```

## Data Storage

### Historical Table
- Stores every data point with timestamp
- Used for trending, reporting, and analysis
- Data is never overwritten
- Configurable retention period

### Real-time Table
- Stores only the latest value for each tag
- Used for dashboards and current status displays
- Values are updated (upserted) on each scan
- Composite key: `plc_name + tag_name`

## Supported PLC Types

| Controller Type | Description | Driver | Default Slot |
|----------------|-------------|---------|--------------|
| CompactLogix | Allen-Bradley CompactLogix | LogixDriver | 0 |
| ControlLogix | Allen-Bradley ControlLogix | LogixDriver | 0 |
| MicroLogix1100 | Allen-Bradley MicroLogix 1100 | SLCDriver | N/A |
| MicroLogix1400 | Allen-Bradley MicroLogix 1400 | SLCDriver | N/A |
| Micro850 | Allen-Bradley Micro850 | LogixDriver | 0 |
| Micro870 | Allen-Bradley Micro870 | LogixDriver | 0 |

## Project Structure

```
plc_data_collector/
├── main.py              # Main application with CLI
├── plc_config.py        # PLC configuration management
├── plc_connection.py    # PLC communication using pycomm3
├── database_manager.py  # Supabase database operations
├── requirements.txt     # Python dependencies
├── .env.sample         # Sample environment configuration
├── sample_tags.csv     # Sample tag list CSV
├── README.md           # This file
└── configs/            # Configuration storage (created automatically)
    ├── plc_configs/    # PLC configuration files
    └── tag_lists/      # Tag list CSV files
```

## Troubleshooting

### Connection Issues

1. **Verify network connectivity**: Can you ping the PLC?
   ```bash
   ping 16.191.1.131
   ```

2. **Check IP configuration**: Ensure PLC IP and your computer are on same network

3. **Firewall settings**: Port 44818 (EtherNet/IP) must be open

4. **Slot number**: CompactLogix typically use slot 0, ControlLogix may vary

### Supabase Issues

1. **Authentication**: Verify your SUPABASE_URL and SUPABASE_KEY are correct

2. **Table creation**: Ensure tables were created with correct schema

3. **Permissions**: Check that your API key has INSERT/UPDATE permissions

### Tag Reading Issues

1. **Tag names**: Must match exactly (case-sensitive)

2. **Array tags**: Use format like `ArrayTag[0]` for array elements

3. **UDT members**: Use dot notation like `UDT_Tag.Member`

## Performance Considerations

- **Scan rates**: Set appropriate scan rates to avoid overloading PLCs
- **Tag grouping**: Reading multiple tags at once is more efficient
- **Database batching**: Data is batched before sending to Supabase
- **Connection pooling**: Each PLC maintains a persistent connection

## Security Notes

- Store Supabase credentials securely (use .env file)
- Consider using read-only access where possible
- Implement network segmentation for PLC networks
- Use VPN for remote access to PLCs

## Advanced Features

### Custom Scan Rates

Different tags can have different scan rates. In your CSV:
```csv
tag_name,scan_rate
Critical.Safety,0.1
Normal.Status,1.0
Slow.Counter,5.0
```

### Data Processing

The tool stores raw values in JSONB format, preserving data types:
```json
{
  "value": 123.45,
  "type": "float"
}
```

### Automatic Reconnection

If a PLC connection is lost, the tool will automatically attempt to reconnect with exponential backoff.

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

This project is provided as-is for educational and commercial use.

## Support

For issues specific to:
- **pycomm3**: Check the [pycomm3 documentation](https://github.com/ottowayi/pycomm3)
- **Supabase**: Refer to [Supabase documentation](https://supabase.io/docs)
- **This tool**: Open an issue in the repository

## Example Use Cases

1. **Production Monitoring**: Track production counts, speeds, and quality metrics
2. **Energy Management**: Monitor power consumption and efficiency
3. **Predictive Maintenance**: Collect vibration, temperature, and runtime data
4. **Quality Control**: Log inspection results and process parameters
5. **OEE Calculation**: Gather availability, performance, and quality data

## Future Enhancements

Planned features for future versions:
- [ ] Web dashboard for configuration and monitoring
- [ ] Data export to CSV/Excel
- [ ] Alert and notification system
- [ ] OPC UA support
- [ ] Modbus TCP support
- [x] Docker containerization
- [ ] Grafana integration
- [ ] Data transformation and calculations

---

**Note**: This tool is not affiliated with Rockwell Automation or Allen-Bradley. CompactLogix, ControlLogix, and MicroLogix are trademarks of Rockwell Automation, Inc.
