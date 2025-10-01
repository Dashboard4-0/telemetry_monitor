"""
Database Migration Tools
Tools for migrating data between Supabase and SQLite databases
"""

import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from colorama import Fore, Style

from database_factory import DatabaseFactory
from database_manager import SupabaseManager
from sqlite_manager import SQLiteManager


class DatabaseMigrator:
    """Handles migration between different database types"""
    
    def __init__(self):
        """Initialize migrator"""
        self.factory = DatabaseFactory()
    
    def migrate_supabase_to_sqlite(self, supabase_config: Dict[str, Any], 
                                 sqlite_config: Dict[str, Any]) -> bool:
        """Migrate data from Supabase to SQLite"""
        try:
            print(f"{Fore.CYAN}Starting migration from Supabase to SQLite...{Style.RESET_ALL}")
            
            # Initialize source and destination databases
            source_db = SupabaseManager(**supabase_config)
            dest_db = SQLiteManager(**sqlite_config)
            
            if not source_db.test_connection():
                print(f"{Fore.RED}✗ Failed to connect to Supabase{Style.RESET_ALL}")
                return False
            
            if not dest_db.test_connection():
                print(f"{Fore.RED}✗ Failed to connect to SQLite{Style.RESET_ALL}")
                return False
            
            # Migrate historical data
            print(f"{Fore.YELLOW}Migrating historical data...{Style.RESET_ALL}")
            historical_count = self._migrate_historical_data(source_db, dest_db)
            
            # Migrate real-time data
            print(f"{Fore.YELLOW}Migrating real-time data...{Style.RESET_ALL}")
            realtime_count = self._migrate_realtime_data(source_db, dest_db)
            
            print(f"{Fore.GREEN}✓ Migration completed successfully!{Style.RESET_ALL}")
            print(f"  Historical records: {historical_count}")
            print(f"  Real-time records: {realtime_count}")
            
            return True
            
        except Exception as e:
            print(f"{Fore.RED}✗ Migration failed: {e}{Style.RESET_ALL}")
            return False
    
    def migrate_sqlite_to_supabase(self, sqlite_config: Dict[str, Any], 
                                 supabase_config: Dict[str, Any]) -> bool:
        """Migrate data from SQLite to Supabase"""
        try:
            print(f"{Fore.CYAN}Starting migration from SQLite to Supabase...{Style.RESET_ALL}")
            
            # Initialize source and destination databases
            source_db = SQLiteManager(**sqlite_config)
            dest_db = SupabaseManager(**supabase_config)
            
            if not source_db.test_connection():
                print(f"{Fore.RED}✗ Failed to connect to SQLite{Style.RESET_ALL}")
                return False
            
            if not dest_db.test_connection():
                print(f"{Fore.RED}✗ Failed to connect to Supabase{Style.RESET_ALL}")
                return False
            
            # Migrate historical data
            print(f"{Fore.YELLOW}Migrating historical data...{Style.RESET_ALL}")
            historical_count = self._migrate_historical_data(source_db, dest_db)
            
            # Migrate real-time data
            print(f"{Fore.YELLOW}Migrating real-time data...{Style.RESET_ALL}")
            realtime_count = self._migrate_realtime_data(source_db, dest_db)
            
            print(f"{Fore.GREEN}✓ Migration completed successfully!{Style.RESET_ALL}")
            print(f"  Historical records: {historical_count}")
            print(f"  Real-time records: {realtime_count}")
            
            return True
            
        except Exception as e:
            print(f"{Fore.RED}✗ Migration failed: {e}{Style.RESET_ALL}")
            return False
    
    def _migrate_historical_data(self, source_db, dest_db) -> int:
        """Migrate historical data between databases"""
        migrated_count = 0
        batch_size = 1000
        offset = 0
        
        while True:
            # Get batch of historical data
            data = source_db.get_historical_data(limit=batch_size)
            if not data:
                break
            
            # Process batch
            for record in data:
                try:
                    # Convert record to data packet format
                    data_packet = {
                        'plc_name': record['plc_name'],
                        'timestamp': datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00')),
                        'data': {record['tag_name']: record['tag_value']}
                    }
                    
                    if dest_db.process_data_packet(data_packet):
                        migrated_count += 1
                    
                except Exception as e:
                    print(f"{Fore.YELLOW}Warning: Failed to migrate record: {e}{Style.RESET_ALL}")
            
            # Check if we got fewer records than batch size (end of data)
            if len(data) < batch_size:
                break
            
            offset += batch_size
            print(f"  Migrated {migrated_count} historical records...")
        
        return migrated_count
    
    def _migrate_realtime_data(self, source_db, dest_db) -> int:
        """Migrate real-time data between databases"""
        migrated_count = 0
        
        # Get all real-time data
        data = source_db.get_realtime_data()
        
        for record in data:
            try:
                # Convert record to data packet format
                data_packet = {
                    'plc_name': record['plc_name'],
                    'timestamp': datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00')),
                    'data': {record['tag_name']: record['tag_value']}
                }
                
                if dest_db.process_data_packet(data_packet):
                    migrated_count += 1
                
            except Exception as e:
                print(f"{Fore.YELLOW}Warning: Failed to migrate record: {e}{Style.RESET_ALL}")
        
        return migrated_count
    
    def compare_databases(self, db1_config: Dict[str, Any], db1_type: str,
                         db2_config: Dict[str, Any], db2_type: str) -> bool:
        """Compare data between two databases"""
        try:
            print(f"{Fore.CYAN}Comparing databases...{Style.RESET_ALL}")
            
            # Initialize databases
            if db1_type == 'supabase':
                db1 = SupabaseManager(**db1_config)
            else:
                db1 = SQLiteManager(**db1_config)
            
            if db2_type == 'supabase':
                db2 = SupabaseManager(**db2_config)
            else:
                db2 = SQLiteManager(**db2_config)
            
            if not db1.test_connection() or not db2.test_connection():
                print(f"{Fore.RED}✗ Failed to connect to one or both databases{Style.RESET_ALL}")
                return False
            
            # Compare statistics
            stats1 = db1.get_statistics()
            stats2 = db2.get_statistics()
            
            print(f"\n{Fore.CYAN}Database Comparison:{Style.RESET_ALL}")
            print(f"Database 1 ({db1_type}):")
            print(f"  Historical records: {stats1['historical_records']:,}")
            print(f"  Real-time records: {stats1['realtime_tags']:,}")
            
            print(f"Database 2 ({db2_type}):")
            print(f"  Historical records: {stats2['historical_records']:,}")
            print(f"  Real-time records: {stats2['realtime_tags']:,}")
            
            # Check if counts match
            historical_match = stats1['historical_records'] == stats2['historical_records']
            realtime_match = stats1['realtime_tags'] == stats2['realtime_tags']
            
            if historical_match and realtime_match:
                print(f"{Fore.GREEN}✓ Databases have matching record counts{Style.RESET_ALL}")
                return True
            else:
                print(f"{Fore.YELLOW}⚠ Databases have different record counts{Style.RESET_ALL}")
                return False
                
        except Exception as e:
            print(f"{Fore.RED}✗ Comparison failed: {e}{Style.RESET_ALL}")
            return False


def main():
    """Command-line interface for migration tools"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Database Migration Tools')
    parser.add_argument('--migrate-to-sqlite', action='store_true', 
                       help='Migrate from Supabase to SQLite')
    parser.add_argument('--migrate-to-supabase', action='store_true', 
                       help='Migrate from SQLite to Supabase')
    parser.add_argument('--compare', action='store_true', 
                       help='Compare two databases')
    
    args = parser.parse_args()
    
    migrator = DatabaseMigrator()
    
    if args.migrate_to_sqlite:
        print(f"{Fore.CYAN}Supabase to SQLite Migration{Style.RESET_ALL}")
        print("Enter Supabase credentials:")
        url = input("Supabase URL: ").strip()
        key = input("Supabase Key: ").strip()
        
        print("Enter SQLite configuration:")
        db_path = input("SQLite DB Path (default: ./plc_data.db): ").strip()
        if not db_path:
            db_path = "./plc_data.db"
        
        supabase_config = {'url': url, 'key': key}
        sqlite_config = {'db_path': db_path}
        
        migrator.migrate_supabase_to_sqlite(supabase_config, sqlite_config)
    
    elif args.migrate_to_supabase:
        print(f"{Fore.CYAN}SQLite to Supabase Migration{Style.RESET_ALL}")
        print("Enter SQLite configuration:")
        db_path = input("SQLite DB Path: ").strip()
        
        print("Enter Supabase credentials:")
        url = input("Supabase URL: ").strip()
        key = input("Supabase Key: ").strip()
        
        sqlite_config = {'db_path': db_path}
        supabase_config = {'url': url, 'key': key}
        
        migrator.migrate_sqlite_to_supabase(sqlite_config, supabase_config)
    
    elif args.compare:
        print(f"{Fore.CYAN}Database Comparison{Style.RESET_ALL}")
        print("This feature requires manual configuration in the code.")
        print("Use the migrator.compare_databases() method directly.")
    
    else:
        print(f"{Fore.YELLOW}No migration operation specified{Style.RESET_ALL}")
        print("Use --help for available options")


if __name__ == '__main__':
    main()
