#!/usr/bin/env python3
"""
Example script showing programmatic usage of the PLC Data Collector
"""

import time
import os
from datetime import datetime
from dotenv import load_dotenv

from plc_config import PLCConfig
from plc_connection import PLCManager
from database_manager import SupabaseManager


def example_basic_usage():
    """Basic example of setting up and using the data collector"""
    
    # Load environment variables
    load_dotenv()
    
    # Initialize components
    config_mgr = PLCConfig()
    plc_mgr = PLCManager()
    db_mgr = SupabaseManager()
    
    # Example 1: Create a new PLC configuration
    plc_config = {
        'controller_type': 'CompactLogix',
        'ip_address': '192.168.1.100',
        'slot': 0
    }
    config_mgr.create_plc_config('MyPLC', plc_config)
    
    # Example 2: Import tags from CSV
    config_mgr.import_tag_list('MyPLC', 'sample_tags.csv')
    
    # Example 3: Connect to PLC
    config = config_mgr.load_plc_config('MyPLC')
    if plc_mgr.add_plc('MyPLC', config):
        print("Connected to PLC successfully!")
    
    # Example 4: Read specific tags
    tags_to_read = ['Machine.Status', 'Machine.Speed', 'Machine.Temperature']
    values = plc_mgr.connections['MyPLC'].read_tags(tags_to_read)
    
    print("\nCurrent tag values:")
    for tag, value in values.items():
        print(f"  {tag}: {value}")
    
    # Example 5: Store data to Supabase
    data_packet = {
        'plc_name': 'MyPLC',
        'timestamp': datetime.now(),
        'data': values
    }
    
    if db_mgr.process_data_packet(data_packet):
        print("\nData stored successfully!")
    
    # Cleanup
    plc_mgr.remove_plc('MyPLC')


def example_continuous_collection():
    """Example of continuous data collection"""
    
    load_dotenv()
    
    # Initialize
    config_mgr = PLCConfig()
    plc_mgr = PLCManager()
    db_mgr = SupabaseManager()
    
    # Load existing configuration
    plc_name = 'MyPLC'
    config = config_mgr.load_plc_config(plc_name)
    tags_df = config_mgr.load_tag_list(plc_name)
    
    if not config or tags_df is None:
        print("Please set up PLC configuration first")
        return
    
    # Connect to PLC
    if not plc_mgr.add_plc(plc_name, config):
        print("Failed to connect to PLC")
        return
    
    # Start collection
    tag_names = tags_df['tag_name'].tolist()
    plc_mgr.start_collection(plc_name, tag_names, scan_rate=1.0)
    
    print("Collecting data... Press Ctrl+C to stop")
    
    try:
        while True:
            # Process collected data
            data_packets = plc_mgr.get_all_collected_data()
            
            for packet in data_packets:
                # Store in database
                db_mgr.process_data_packet(packet)
                
                # Print summary
                print(f"[{packet['timestamp'].strftime('%H:%M:%S')}] "
                      f"Collected {len(packet['data'])} tags from {packet['plc_name']}")
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping collection...")
        plc_mgr.stop_all_collections()
        plc_mgr.remove_plc(plc_name)


def example_read_specific_tags():
    """Example of reading specific tags on demand"""
    
    load_dotenv()
    
    config_mgr = PLCConfig()
    plc_mgr = PLCManager()
    
    # Connect to PLC
    plc_name = 'MyPLC'
    config = config_mgr.load_plc_config(plc_name)
    
    if not plc_mgr.add_plc(plc_name, config):
        print("Failed to connect to PLC")
        return
    
    plc_conn = plc_mgr.connections[plc_name]
    
    # Read individual tags
    print("\nReading individual tags:")
    print(f"Machine Status: {plc_conn.read_tag('Machine.Status')}")
    print(f"Machine Speed: {plc_conn.read_tag('Machine.Speed')}")
    
    # Read multiple tags at once (more efficient)
    print("\nReading multiple tags:")
    tags = ['Machine.Status', 'Machine.Speed', 'Machine.Temperature', 
            'Motor1.Current', 'Safety.EStop']
    values = plc_conn.read_tags(tags)
    
    for tag, value in values.items():
        print(f"  {tag}: {value}")
    
    # Cleanup
    plc_mgr.remove_plc(plc_name)


def example_query_database():
    """Example of querying stored data from Supabase"""
    
    load_dotenv()
    db_mgr = SupabaseManager()
    
    # Get latest real-time values for a PLC
    print("\n=== Latest Real-time Values ===")
    latest = db_mgr.get_latest_values('MyPLC')
    
    for tag, data in latest.items():
        print(f"{tag}:")
        print(f"  Value: {data['value']}")
        print(f"  Timestamp: {data['timestamp']}")
    
    # Query historical data
    print("\n=== Recent Historical Data ===")
    historical = db_mgr.get_historical_data(
        plc_name='MyPLC',
        tag_name='Machine.Speed',
        limit=10
    )
    
    for record in historical:
        timestamp = record['timestamp']
        value = record.get('tag_value', {}).get('value', 'N/A')
        print(f"{timestamp}: {value}")
    
    # Get statistics
    print("\n=== Database Statistics ===")
    stats = db_mgr.get_statistics()
    print(f"Historical records: {stats['historical_records']:,}")
    print(f"Real-time tags: {stats['realtime_tags']:,}")


def example_write_tag():
    """Example of writing a value to a PLC tag"""
    
    load_dotenv()
    
    config_mgr = PLCConfig()
    plc_mgr = PLCManager()
    
    # Connect to PLC
    plc_name = 'MyPLC'
    config = config_mgr.load_plc_config(plc_name)
    
    if not plc_mgr.add_plc(plc_name, config):
        print("Failed to connect to PLC")
        return
    
    plc_conn = plc_mgr.connections[plc_name]
    
    # Write a value (be careful with this in production!)
    tag_name = 'Test.WriteTag'
    new_value = 42
    
    if plc_conn.write_tag(tag_name, new_value):
        print(f"Successfully wrote {new_value} to {tag_name}")
        
        # Read back to verify
        read_value = plc_conn.read_tag(tag_name)
        print(f"Read back value: {read_value}")
    else:
        print(f"Failed to write to {tag_name}")
    
    # Cleanup
    plc_mgr.remove_plc(plc_name)


def example_multiple_plcs():
    """Example of managing multiple PLCs simultaneously"""
    
    load_dotenv()
    
    config_mgr = PLCConfig()
    plc_mgr = PLCManager()
    db_mgr = SupabaseManager()
    
    # Define multiple PLCs
    plcs = [
        {'name': 'Line1_PLC', 'ip': '192.168.1.100', 'type': 'CompactLogix'},
        {'name': 'Line2_PLC', 'ip': '192.168.1.101', 'type': 'CompactLogix'},
        {'name': 'Utility_PLC', 'ip': '192.168.1.102', 'type': 'MicroLogix1400'}
    ]
    
    # Configure and connect to all PLCs
    for plc in plcs:
        # Create configuration
        config_data = {
            'controller_type': plc['type'],
            'ip_address': plc['ip'],
            'slot': 0 if 'Logix' in plc['type'] else None
        }
        config_mgr.create_plc_config(plc['name'], config_data)
        
        # Import same tag list (or different ones)
        config_mgr.import_tag_list(plc['name'], 'sample_tags.csv')
        
        # Connect
        config = config_mgr.load_plc_config(plc['name'])
        if plc_mgr.add_plc(plc['name'], config):
            print(f"Connected to {plc['name']}")
            
            # Start collection
            tags_df = config_mgr.load_tag_list(plc['name'])
            tag_names = tags_df['tag_name'].tolist()
            plc_mgr.start_collection(plc['name'], tag_names, scan_rate=2.0)
    
    print("\nCollecting from multiple PLCs... Press Ctrl+C to stop")
    
    try:
        while True:
            # Process all collected data
            data_packets = plc_mgr.get_all_collected_data()
            
            if data_packets:
                # Batch process to database
                success = db_mgr.batch_process_data(data_packets)
                print(f"Processed {success}/{len(data_packets)} data packets")
                
                # Show status
                status = plc_mgr.get_status()
                for name, info in status.items():
                    status_str = "Connected" if info['connected'] else "Disconnected"
                    print(f"  {name}: {status_str}, Errors: {info['error_count']}")
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\nShutting down...")
        plc_mgr.stop_all_collections()
        for plc in plcs:
            plc_mgr.remove_plc(plc['name'])


if __name__ == '__main__':
    print("PLC Data Collector - Usage Examples")
    print("=" * 50)
    print("\nAvailable examples:")
    print("1. Basic usage")
    print("2. Continuous collection")
    print("3. Read specific tags")
    print("4. Query database")
    print("5. Write tag value")
    print("6. Multiple PLCs")
    
    choice = input("\nSelect example to run (1-6): ").strip()
    
    examples = {
        '1': example_basic_usage,
        '2': example_continuous_collection,
        '3': example_read_specific_tags,
        '4': example_query_database,
        '5': example_write_tag,
        '6': example_multiple_plcs
    }
    
    if choice in examples:
        print(f"\nRunning example {choice}...\n")
        examples[choice]()
    else:
        print("Invalid selection")
