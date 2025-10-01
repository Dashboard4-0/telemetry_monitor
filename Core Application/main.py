#!/usr/bin/env python3
"""
PLC Data Collector
Main application for collecting data from PLCs and storing in Supabase
"""

import os
import sys
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
from colorama import init, Fore, Style
from tabulate import tabulate
from dotenv import load_dotenv
import threading
import signal

from plc_config import PLCConfig
from plc_connection import PLCManager
from database_manager import SupabaseManager


# Initialize colorama for colored console output
init(autoreset=True)


class PLCDataCollector:
    """Main application class"""
    
    def __init__(self):
        """Initialize the application"""
        # Load environment variables
        load_dotenv()
        
        # Initialize components
        self.config_manager = PLCConfig()
        self.plc_manager = PLCManager()
        self.db_manager = None
        
        # Initialize Supabase if credentials are available
        self._init_database()
        
        # Data collection control
        self.collection_active = False
        self.collection_thread = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _init_database(self):
        """Initialize database connection"""
        try:
            self.db_manager = SupabaseManager()
            if self.db_manager.test_connection():
                print(f"{Fore.GREEN}✓ Database connected{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.YELLOW}⚠ Database not configured: {e}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}  Set SUPABASE_URL and SUPABASE_KEY in .env file{Style.RESET_ALL}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n{Fore.YELLOW}Shutting down...{Style.RESET_ALL}")
        self.stop_collection()
        sys.exit(0)
    
    def setup_plc(self):
        """Interactive PLC setup"""
        print(f"\n{Fore.CYAN}=== PLC Setup ==={Style.RESET_ALL}")
        
        # Get PLC name
        name = input("Enter PLC name: ").strip()
        if not name:
            print(f"{Fore.RED}✗ PLC name is required{Style.RESET_ALL}")
            return
        
        # Show supported controllers
        print(f"\n{Fore.CYAN}Supported Controller Types:{Style.RESET_ALL}")
        controllers = list(PLCConfig.SUPPORTED_CONTROLLERS.keys())
        for i, ctrl in enumerate(controllers, 1):
            desc = PLCConfig.SUPPORTED_CONTROLLERS[ctrl]['description']
            print(f"  {i}. {ctrl} - {desc}")
        
        # Get controller type
        try:
            choice = int(input("\nSelect controller type (number): "))
            if 1 <= choice <= len(controllers):
                controller_type = controllers[choice - 1]
            else:
                print(f"{Fore.RED}✗ Invalid selection{Style.RESET_ALL}")
                return
        except ValueError:
            print(f"{Fore.RED}✗ Invalid input{Style.RESET_ALL}")
            return
        
        # Get IP address
        ip_address = input("Enter PLC IP address: ").strip()
        if not ip_address:
            print(f"{Fore.RED}✗ IP address is required{Style.RESET_ALL}")
            return
        
        # Get subnet mask (optional)
        subnet = input("Enter subnet mask (optional, press Enter to skip): ").strip()
        
        # Get slot number for Logix controllers
        slot = None
        controller_info = PLCConfig.SUPPORTED_CONTROLLERS[controller_type]
        if controller_info['driver'] == 'LogixDriver':
            slot_input = input(f"Enter slot number (default: {controller_info['default_slot']}): ").strip()
            if slot_input:
                try:
                    slot = int(slot_input)
                except ValueError:
                    slot = controller_info['default_slot']
            else:
                slot = controller_info['default_slot']
        
        # Create configuration
        config_data = {
            'controller_type': controller_type,
            'ip_address': ip_address
        }
        
        if subnet:
            config_data['subnet'] = subnet
        if slot is not None:
            config_data['slot'] = slot
        
        # Save configuration
        if self.config_manager.create_plc_config(name, config_data):
            print(f"{Fore.GREEN}✓ PLC '{name}' configured successfully{Style.RESET_ALL}")
            
            # Ask to import tag list
            import_tags = input("\nDo you want to import a tag list CSV? (y/n): ").strip().lower()
            if import_tags == 'y':
                csv_file = input("Enter CSV file path: ").strip()
                if os.path.exists(csv_file):
                    self.config_manager.import_tag_list(name, csv_file)
                else:
                    print(f"{Fore.RED}✗ File not found{Style.RESET_ALL}")
            
            # Test connection
            test = input("\nTest connection now? (y/n): ").strip().lower()
            if test == 'y':
                self.test_plc_connection(name)
    
    def list_plcs(self):
        """List all configured PLCs"""
        configs = self.config_manager.list_plc_configs()
        
        if not configs:
            print(f"{Fore.YELLOW}No PLCs configured{Style.RESET_ALL}")
            return
        
        print(f"\n{Fore.CYAN}=== Configured PLCs ==={Style.RESET_ALL}")
        
        table_data = []
        for name in configs:
            summary = self.config_manager.get_config_summary(name)
            if summary:
                status = "Connected" if name in self.plc_manager.connections else "Not connected"
                tag_count = summary['tags']['count'] if summary['tags'] else 0
                
                table_data.append([
                    name,
                    summary['controller_type'],
                    summary['ip_address'],
                    status,
                    tag_count
                ])
        
        headers = ['Name', 'Type', 'IP Address', 'Status', 'Tags']
        print(tabulate(table_data, headers=headers, tablefmt='grid'))
    
    def test_plc_connection(self, name: str = None):
        """Test connection to a PLC"""
        if not name:
            configs = self.config_manager.list_plc_configs()
            if not configs:
                print(f"{Fore.YELLOW}No PLCs configured{Style.RESET_ALL}")
                return
            
            print("Available PLCs:")
            for i, plc_name in enumerate(configs, 1):
                print(f"  {i}. {plc_name}")
            
            try:
                choice = int(input("Select PLC to test (number): "))
                if 1 <= choice <= len(configs):
                    name = configs[choice - 1]
                else:
                    print(f"{Fore.RED}✗ Invalid selection{Style.RESET_ALL}")
                    return
            except ValueError:
                print(f"{Fore.RED}✗ Invalid input{Style.RESET_ALL}")
                return
        
        # Load configuration
        config = self.config_manager.load_plc_config(name)
        if not config:
            return
        
        print(f"\n{Fore.CYAN}Testing connection to {name}...{Style.RESET_ALL}")
        
        # Add or test PLC
        if name not in self.plc_manager.connections:
            if self.plc_manager.add_plc(name, config):
                print(f"{Fore.GREEN}✓ Connection successful{Style.RESET_ALL}")
                
                # Try to read a tag if available
                tags_df = self.config_manager.load_tag_list(name)
                if tags_df is not None and len(tags_df) > 0:
                    test_tag = tags_df.iloc[0]['tag_name']
                    print(f"Testing tag read: {test_tag}")
                    value = self.plc_manager.connections[name].read_tag(test_tag)
                    if value is not None:
                        print(f"{Fore.GREEN}✓ Tag value: {value}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}✗ Connection failed{Style.RESET_ALL}")
        else:
            if self.plc_manager.test_connection(name):
                print(f"{Fore.GREEN}✓ Connection active{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}✗ Connection failed{Style.RESET_ALL}")
    
    def import_tags(self):
        """Import tag list for a PLC"""
        configs = self.config_manager.list_plc_configs()
        if not configs:
            print(f"{Fore.YELLOW}No PLCs configured{Style.RESET_ALL}")
            return
        
        print("Available PLCs:")
        for i, plc_name in enumerate(configs, 1):
            print(f"  {i}. {plc_name}")
        
        try:
            choice = int(input("Select PLC (number): "))
            if 1 <= choice <= len(configs):
                name = configs[choice - 1]
            else:
                print(f"{Fore.RED}✗ Invalid selection{Style.RESET_ALL}")
                return
        except ValueError:
            print(f"{Fore.RED}✗ Invalid input{Style.RESET_ALL}")
            return
        
        csv_file = input("Enter CSV file path: ").strip()
        if os.path.exists(csv_file):
            self.config_manager.import_tag_list(name, csv_file)
        else:
            print(f"{Fore.RED}✗ File not found{Style.RESET_ALL}")
    
    def start_collection(self):
        """Start data collection for all configured PLCs"""
        if self.collection_active:
            print(f"{Fore.YELLOW}Collection already running{Style.RESET_ALL}")
            return
        
        if not self.db_manager:
            print(f"{Fore.RED}✗ Database not configured{Style.RESET_ALL}")
            print("Please set SUPABASE_URL and SUPABASE_KEY in .env file")
            return
        
        configs = self.config_manager.list_plc_configs()
        if not configs:
            print(f"{Fore.YELLOW}No PLCs configured{Style.RESET_ALL}")
            return
        
        print(f"\n{Fore.CYAN}Starting data collection...{Style.RESET_ALL}")
        
        # Connect to all PLCs and start collection
        for name in configs:
            config = self.config_manager.load_plc_config(name)
            if not config:
                continue
            
            # Load tag list
            tags_df = self.config_manager.load_tag_list(name)
            if tags_df is None or len(tags_df) == 0:
                print(f"{Fore.YELLOW}⚠ No tags configured for {name}{Style.RESET_ALL}")
                continue
            
            # Add PLC if not already connected
            if name not in self.plc_manager.connections:
                if not self.plc_manager.add_plc(name, config):
                    print(f"{Fore.RED}✗ Failed to connect to {name}{Style.RESET_ALL}")
                    continue
            
            # Start collection
            tag_names = tags_df['tag_name'].tolist()
            scan_rate = tags_df['scan_rate'].iloc[0] if 'scan_rate' in tags_df.columns else 1.0
            self.plc_manager.start_collection(name, tag_names, scan_rate)
        
        # Start data processing thread
        self.collection_active = True
        self.collection_thread = threading.Thread(target=self._process_data_loop, daemon=True)
        self.collection_thread.start()
        
        print(f"{Fore.GREEN}✓ Data collection started{Style.RESET_ALL}")
        print(f"Press Ctrl+C to stop...")
    
    def _process_data_loop(self):
        """Background thread to process collected data"""
        while self.collection_active:
            try:
                # Get all available data
                data_packets = self.plc_manager.get_all_collected_data()
                
                if data_packets:
                    # Process data to database
                    success = self.db_manager.batch_process_data(data_packets)
                    if success > 0:
                        print(f"{Fore.GREEN}✓ Processed {success} data packets{Style.RESET_ALL}")
                
                # Short sleep to prevent CPU spinning
                time.sleep(0.1)
                
            except Exception as e:
                print(f"{Fore.RED}Error processing data: {e}{Style.RESET_ALL}")
                time.sleep(1)
    
    def stop_collection(self):
        """Stop all data collection"""
        if not self.collection_active:
            return
        
        print(f"\n{Fore.YELLOW}Stopping data collection...{Style.RESET_ALL}")
        
        # Stop collection flag
        self.collection_active = False
        
        # Stop all PLC collections
        self.plc_manager.stop_all_collections()
        
        # Wait for processing thread to finish
        if self.collection_thread:
            self.collection_thread.join(timeout=2)
        
        print(f"{Fore.GREEN}✓ Data collection stopped{Style.RESET_ALL}")
    
    def view_data(self):
        """View collected data"""
        if not self.db_manager:
            print(f"{Fore.RED}✗ Database not configured{Style.RESET_ALL}")
            return
        
        print(f"\n{Fore.CYAN}=== View Data ==={Style.RESET_ALL}")
        print("1. View real-time values")
        print("2. View historical data")
        print("3. Database statistics")
        
        try:
            choice = int(input("Select option: "))
            
            if choice == 1:
                self._view_realtime_data()
            elif choice == 2:
                self._view_historical_data()
            elif choice == 3:
                self._view_statistics()
            else:
                print(f"{Fore.RED}✗ Invalid selection{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}✗ Invalid input{Style.RESET_ALL}")
    
    def _view_realtime_data(self):
        """View current real-time values"""
        plc_name = input("Enter PLC name (or press Enter for all): ").strip()
        
        data = self.db_manager.get_realtime_data(plc_name=plc_name if plc_name else None)
        
        if not data:
            print(f"{Fore.YELLOW}No data found{Style.RESET_ALL}")
            return
        
        table_data = []
        for record in data[:20]:  # Limit display
            table_data.append([
                record['plc_name'],
                record['tag_name'],
                record.get('tag_value', {}).get('value', 'N/A'),
                record['timestamp'][:19],
                record['updated_at'][:19]
            ])
        
        headers = ['PLC', 'Tag', 'Value', 'Timestamp', 'Updated']
        print(tabulate(table_data, headers=headers, tablefmt='grid'))
        
        if len(data) > 20:
            print(f"\n{Fore.YELLOW}Showing first 20 of {len(data)} records{Style.RESET_ALL}")
    
    def _view_historical_data(self):
        """View historical data"""
        plc_name = input("Enter PLC name (or press Enter for all): ").strip()
        tag_name = input("Enter tag name (or press Enter for all): ").strip()
        
        data = self.db_manager.get_historical_data(
            plc_name=plc_name if plc_name else None,
            tag_name=tag_name if tag_name else None,
            limit=20
        )
        
        if not data:
            print(f"{Fore.YELLOW}No data found{Style.RESET_ALL}")
            return
        
        table_data = []
        for record in data:
            table_data.append([
                record['plc_name'],
                record['tag_name'],
                record.get('tag_value', {}).get('value', 'N/A'),
                record['timestamp'][:19]
            ])
        
        headers = ['PLC', 'Tag', 'Value', 'Timestamp']
        print(tabulate(table_data, headers=headers, tablefmt='grid'))
    
    def _view_statistics(self):
        """View database statistics"""
        stats = self.db_manager.get_statistics()
        plc_status = self.plc_manager.get_status()
        
        print(f"\n{Fore.CYAN}=== Database Statistics ==={Style.RESET_ALL}")
        print(f"Historical records: {stats['historical_records']:,}")
        print(f"Real-time tags: {stats['realtime_tags']:,}")
        
        if plc_status:
            print(f"\n{Fore.CYAN}=== PLC Status ==={Style.RESET_ALL}")
            for name, status in plc_status.items():
                connected = f"{Fore.GREEN}Connected{Style.RESET_ALL}" if status['connected'] else f"{Fore.RED}Disconnected{Style.RESET_ALL}"
                collecting = f"{Fore.GREEN}Active{Style.RESET_ALL}" if status['collecting'] else f"{Fore.YELLOW}Idle{Style.RESET_ALL}"
                print(f"{name}: {connected}, Collection: {collecting}, Errors: {status['error_count']}")
    
    def run_interactive(self):
        """Run interactive CLI menu"""
        print(f"\n{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}    PLC Data Collector for Supabase    {Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
        
        while True:
            print(f"\n{Fore.CYAN}=== Main Menu ==={Style.RESET_ALL}")
            print("1. Setup new PLC")
            print("2. List configured PLCs")
            print("3. Test PLC connection")
            print("4. Import tag list (CSV)")
            print("5. Start data collection")
            print("6. Stop data collection")
            print("7. View collected data")
            print("8. Exit")
            
            try:
                choice = input("\nSelect option: ").strip()
                
                if choice == '1':
                    self.setup_plc()
                elif choice == '2':
                    self.list_plcs()
                elif choice == '3':
                    self.test_plc_connection()
                elif choice == '4':
                    self.import_tags()
                elif choice == '5':
                    self.start_collection()
                    # Keep running until stopped
                    try:
                        while self.collection_active:
                            time.sleep(1)
                    except KeyboardInterrupt:
                        self.stop_collection()
                elif choice == '6':
                    self.stop_collection()
                elif choice == '7':
                    self.view_data()
                elif choice == '8':
                    self.stop_collection()
                    print(f"\n{Fore.CYAN}Goodbye!{Style.RESET_ALL}")
                    break
                else:
                    print(f"{Fore.RED}✗ Invalid option{Style.RESET_ALL}")
                    
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Use option 8 to exit{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='PLC Data Collector for Supabase')
    parser.add_argument('--setup', action='store_true', help='Setup a new PLC')
    parser.add_argument('--list', action='store_true', help='List configured PLCs')
    parser.add_argument('--test', metavar='NAME', help='Test PLC connection')
    parser.add_argument('--collect', action='store_true', help='Start data collection')
    parser.add_argument('--import-tags', nargs=2, metavar=('PLC_NAME', 'CSV_FILE'), 
                       help='Import tag list from CSV')
    
    args = parser.parse_args()
    
    # Create application instance
    app = PLCDataCollector()
    
    # Handle command line arguments
    if args.setup:
        app.setup_plc()
    elif args.list:
        app.list_plcs()
    elif args.test:
        app.test_plc_connection(args.test)
    elif args.import_tags:
        plc_name, csv_file = args.import_tags
        if os.path.exists(csv_file):
            app.config_manager.import_tag_list(plc_name, csv_file)
        else:
            print(f"{Fore.RED}✗ File not found: {csv_file}{Style.RESET_ALL}")
    elif args.collect:
        app.start_collection()
        try:
            while app.collection_active:
                time.sleep(1)
        except KeyboardInterrupt:
            app.stop_collection()
    else:
        # Run interactive mode
        app.run_interactive()


if __name__ == '__main__':
    main()
