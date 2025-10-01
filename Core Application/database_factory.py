"""
Database Factory
Handles database type selection and initialization
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path

from database_interface import DatabaseManager
from database_manager import SupabaseManager
from sqlite_manager import SQLiteManager


class DatabaseFactory:
    """Factory class for creating database managers"""
    
    SUPPORTED_DATABASES = {
        'supabase': {
            'name': 'Supabase',
            'description': 'Cloud-hosted PostgreSQL database',
            'pros': ['Scalable', 'Cloud backup', 'Real-time features', 'Web dashboard'],
            'cons': ['Requires internet', 'Setup complexity', 'Monthly cost'],
            'class': SupabaseManager
        },
        'sqlite': {
            'name': 'SQLite',
            'description': 'Local file-based database',
            'pros': ['Simple setup', 'No internet required', 'Free', 'Fast local access'],
            'cons': ['Single file', 'Limited concurrent access', 'No cloud backup'],
            'class': SQLiteManager
        }
    }
    
    def __init__(self):
        """Initialize database factory"""
        self.config_file = os.path.join(os.getcwd(), 'database_config.json')
    
    def get_database_type(self) -> Optional[str]:
        """Get configured database type"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    return config.get('database_type')
        except Exception as e:
            print(f"Error reading database config: {e}")
        return None
    
    def save_database_config(self, database_type: str, config: Dict[str, Any]):
        """Save database configuration"""
        try:
            config_data = {
                'database_type': database_type,
                'config': config
            }
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            print(f"✓ Database configuration saved")
        except Exception as e:
            print(f"Error saving database config: {e}")
    
    def create_database_manager(self, database_type: str = None, **kwargs) -> Optional[DatabaseManager]:
        """Create and initialize database manager"""
        try:
            # Use provided type or get from config
            if database_type is None:
                database_type = self.get_database_type()
            
            if database_type is None:
                print("No database type configured")
                return None
            
            if database_type not in self.SUPPORTED_DATABASES:
                print(f"Unsupported database type: {database_type}")
                return None
            
            db_info = self.SUPPORTED_DATABASES[database_type]
            db_class = db_info['class']
            
            # Create database manager instance
            if database_type == 'supabase':
                manager = db_class(
                    url=kwargs.get('url') or os.getenv('SUPABASE_URL'),
                    key=kwargs.get('key') or os.getenv('SUPABASE_KEY')
                )
            elif database_type == 'sqlite':
                manager = db_class(
                    db_path=kwargs.get('db_path') or os.getenv('SQLITE_DB_PATH')
                )
            else:
                manager = db_class(**kwargs)
            
            # Test connection
            if manager.test_connection():
                print(f"✓ {db_info['name']} database connected")
                return manager
            else:
                print(f"✗ Failed to connect to {db_info['name']} database")
                return None
                
        except Exception as e:
            print(f"Error creating database manager: {e}")
            return None
    
    def get_available_databases(self) -> Dict[str, Dict[str, Any]]:
        """Get list of available database types"""
        return self.SUPPORTED_DATABASES.copy()
    
    def validate_database_config(self, database_type: str, config: Dict[str, Any]) -> bool:
        """Validate database configuration"""
        if database_type not in self.SUPPORTED_DATABASES:
            return False
        
        if database_type == 'supabase':
            return bool(config.get('url') and config.get('key'))
        elif database_type == 'sqlite':
            # SQLite doesn't require special config, just path
            return True
        
        return False
    
    def get_database_info(self, database_type: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific database type"""
        return self.SUPPORTED_DATABASES.get(database_type)
