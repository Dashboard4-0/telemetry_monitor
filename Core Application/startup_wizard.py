"""
Startup Wizard
Interactive database configuration wizard for first-time setup
"""

import os
import json
from typing import Dict, Any, Optional
from colorama import Fore, Style

from database_factory import DatabaseFactory


class StartupWizard:
    """Interactive wizard for database configuration"""
    
    def __init__(self):
        """Initialize startup wizard"""
        self.factory = DatabaseFactory()
        self.config_file = os.path.join(os.getcwd(), 'database_config.json')
    
    def is_first_run(self) -> bool:
        """Check if this is the first run (no database config exists)"""
        return not os.path.exists(self.config_file)
    
    def run_wizard(self) -> Optional[Dict[str, Any]]:
        """Run the interactive database configuration wizard"""
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}    PLC Data Collector - Database Setup Wizard    {Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        
        print(f"\n{Fore.YELLOW}Welcome! Let's configure your database for storing PLC data.{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}You can change this configuration later by deleting the database_config.json file.{Style.RESET_ALL}")
        
        # Show available database options
        databases = self.factory.get_available_databases()
        
        print(f"\n{Fore.CYAN}Available Database Options:{Style.RESET_ALL}")
        print()
        
        for i, (db_type, info) in enumerate(databases.items(), 1):
            print(f"{Fore.GREEN}{i}. {info['name']}{Style.RESET_ALL}")
            print(f"   {info['description']}")
            print(f"   {Fore.GREEN}Pros:{Style.RESET_ALL} {', '.join(info['pros'])}")
            print(f"   {Fore.RED}Cons:{Style.RESET_ALL} {', '.join(info['cons'])}")
            print()
        
        # Get user selection
        while True:
            try:
                choice = input(f"Select database type (1-{len(databases)}): ").strip()
                choice_num = int(choice)
                
                if 1 <= choice_num <= len(databases):
                    selected_type = list(databases.keys())[choice_num - 1]
                    break
                else:
                    print(f"{Fore.RED}✗ Invalid selection. Please choose 1-{len(databases)}{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED}✗ Invalid input. Please enter a number{Style.RESET_ALL}")
        
        # Configure selected database
        config = self._configure_database(selected_type)
        if config is None:
            return None
        
        # Save configuration
        self.factory.save_database_config(selected_type, config)
        
        # Test connection
        print(f"\n{Fore.CYAN}Testing database connection...{Style.RESET_ALL}")
        manager = self.factory.create_database_manager(selected_type, **config)
        
        if manager:
            print(f"{Fore.GREEN}✓ Database configuration successful!{Style.RESET_ALL}")
            return {'type': selected_type, 'config': config}
        else:
            print(f"{Fore.RED}✗ Database configuration failed{Style.RESET_ALL}")
            return None
    
    def _configure_database(self, database_type: str) -> Optional[Dict[str, Any]]:
        """Configure specific database type"""
        if database_type == 'supabase':
            return self._configure_supabase()
        elif database_type == 'sqlite':
            return self._configure_sqlite()
        else:
            print(f"{Fore.RED}Unsupported database type: {database_type}{Style.RESET_ALL}")
            return None
    
    def _configure_supabase(self) -> Optional[Dict[str, Any]]:
        """Configure Supabase database"""
        print(f"\n{Fore.CYAN}=== Supabase Configuration ==={Style.RESET_ALL}")
        print(f"{Fore.YELLOW}You'll need your Supabase project URL and API key.{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Get these from: https://app.supabase.com → Your Project → Settings → API{Style.RESET_ALL}")
        print()
        
        # Get Supabase URL
        while True:
            url = input("Enter Supabase URL (e.g., https://abc123.supabase.co): ").strip()
            if url and url.startswith('https://') and 'supabase.co' in url:
                break
            elif url:
                print(f"{Fore.RED}✗ Invalid URL format. Should be https://abc123.supabase.co{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}✗ URL is required{Style.RESET_ALL}")
        
        # Get Supabase Key
        while True:
            key = input("Enter Supabase API Key (anon public key): ").strip()
            if key and key.startswith('eyJ'):
                break
            elif key:
                print(f"{Fore.RED}✗ Invalid key format. Should start with 'eyJ'{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}✗ API key is required{Style.RESET_ALL}")
        
        return {'url': url, 'key': key}
    
    def _configure_sqlite(self) -> Optional[Dict[str, Any]]:
        """Configure SQLite database"""
        print(f"\n{Fore.CYAN}=== SQLite Configuration ==={Style.RESET_ALL}")
        print(f"{Fore.YELLOW}SQLite stores data in a local file. No additional setup required!{Style.RESET_ALL}")
        print()
        
        # Get database file path
        default_path = os.path.join(os.getcwd(), 'plc_data.db')
        path_input = input(f"Enter database file path (default: {default_path}): ").strip()
        
        if not path_input:
            db_path = default_path
        else:
            db_path = path_input
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        
        print(f"{Fore.GREEN}✓ SQLite database will be created at: {db_path}{Style.RESET_ALL}")
        
        return {'db_path': db_path}
    
    def show_database_info(self):
        """Show current database configuration"""
        if not os.path.exists(self.config_file):
            print(f"{Fore.YELLOW}No database configuration found{Style.RESET_ALL}")
            return
        
        try:
            with open(self.config_file, 'r') as f:
                config_data = json.load(f)
            
            db_type = config_data.get('database_type')
            config = config_data.get('config', {})
            
            db_info = self.factory.get_database_info(db_type)
            if db_info:
                print(f"\n{Fore.CYAN}Current Database Configuration:{Style.RESET_ALL}")
                print(f"Type: {db_info['name']}")
                print(f"Description: {db_info['description']}")
                
                if db_type == 'supabase':
                    url = config.get('url', 'Not configured')
                    print(f"URL: {url}")
                elif db_type == 'sqlite':
                    db_path = config.get('db_path', 'Not configured')
                    print(f"Database file: {db_path}")
                
        except Exception as e:
            print(f"{Fore.RED}Error reading database configuration: {e}{Style.RESET_ALL}")
    
    def reset_configuration(self):
        """Reset database configuration"""
        if os.path.exists(self.config_file):
            try:
                os.remove(self.config_file)
                print(f"{Fore.GREEN}✓ Database configuration reset{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Run the application again to reconfigure your database{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}Error resetting configuration: {e}{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}No configuration to reset{Style.RESET_ALL}")
