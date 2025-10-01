"""
Supabase Database Manager
Handles data storage to Supabase with both historical and real-time tables
"""

import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import ssl
import httpx

# Disable SSL verification for Docker environments
if os.getenv('DOCKER_ENV', 'false').lower() == 'true':
    # Monkey-patch httpx to disable SSL verification globally
    import warnings
    warnings.filterwarnings('ignore')
    
    _original_init = httpx.Client.__init__
    def _patched_init(self, *args, **kwargs):
        kwargs['verify'] = False
        _original_init(self, *args, **kwargs)
    httpx.Client.__init__ = _patched_init

from supabase import create_client, Client


class SupabaseManager:
    """Manages Supabase database operations for PLC data"""
    
    def __init__(self, url: str = None, key: str = None):
        """Initialize Supabase connection"""
        self.url = url or os.getenv('SUPABASE_URL')
        self.key = key or os.getenv('SUPABASE_KEY')
        
        if not self.url or not self.key:
            raise ValueError("Supabase URL and Key are required. Set SUPABASE_URL and SUPABASE_KEY environment variables.")
        
        self.client: Client = create_client(self.url, self.key)
        self.historical_table = 'plc_data_historical'
        self.realtime_table = 'plc_data_realtime'
        
        # Initialize tables if they don't exist
        self._ensure_tables_exist()
    
    def _ensure_tables_exist(self):
        """Ensure required tables exist in Supabase"""
        print("""
        ⚠️  Supabase tables need to be created before using the application.
        
        📋 Required Tables:
        
        1. plc_data_historical (stores all data points):
           - id (bigint, primary key, auto-increment)
           - plc_name (text)
           - tag_name (text)
           - tag_value (jsonb)
           - timestamp (timestamptz)
           - created_at (timestamptz, default: now())
           
        2. plc_data_realtime (stores latest values only):
           - id (text, primary key) - Composite key: plc_name + "_" + tag_name
           - plc_name (text)
           - tag_name (text)
           - tag_value (jsonb)
           - timestamp (timestamptz)
           - updated_at (timestamptz, default: now())
        
        🚀 Quick Setup Options:
        
        Option 1 - Minimal Setup:
        Copy and run: deployment/supabase_schema_minimal.sql in Supabase SQL Editor
        
        Option 2 - Complete Setup (Recommended):
        Copy and run: deployment/supabase_schema.sql in Supabase SQL Editor
        
        📖 The complete setup includes:
        - Tables with proper indexes
        - Row Level Security (RLS) policies
        - Helper functions for data queries
        - Useful views for monitoring
        - Automated cleanup functions
        
        💡 After creating tables, restart the application to begin data collection.
        """)
    
    def insert_historical_data(self, plc_name: str, tag_data: Dict[str, Any], timestamp: datetime = None) -> bool:
        """Insert data into historical table"""
        try:
            if timestamp is None:
                timestamp = datetime.now()
            
            # Prepare batch insert data
            records = []
            for tag_name, tag_value in tag_data.items():
                record = {
                    'plc_name': plc_name,
                    'tag_name': tag_name,
                    'tag_value': self._serialize_value(tag_value),
                    'timestamp': timestamp.isoformat()
                }
                records.append(record)
            
            # Batch insert
            if records:
                response = self.client.table(self.historical_table).insert(records).execute()
                return True
            
            return False
            
        except Exception as e:
            print(f"Error inserting historical data: {e}")
            return False
    
    def upsert_realtime_data(self, plc_name: str, tag_data: Dict[str, Any], timestamp: datetime = None) -> bool:
        """Upsert data into real-time table (update if exists, insert if not)"""
        try:
            if timestamp is None:
                timestamp = datetime.now()
            
            # Prepare upsert data
            records = []
            for tag_name, tag_value in tag_data.items():
                # Create composite key
                composite_id = f"{plc_name}_{tag_name}"
                
                record = {
                    'id': composite_id,
                    'plc_name': plc_name,
                    'tag_name': tag_name,
                    'tag_value': self._serialize_value(tag_value),
                    'timestamp': timestamp.isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                records.append(record)
            
            # Batch upsert
            if records:
                response = self.client.table(self.realtime_table).upsert(records).execute()
                return True
            
            return False
            
        except Exception as e:
            print(f"Error upserting real-time data: {e}")
            return False
    
    def process_data_packet(self, data_packet: Dict[str, Any]) -> bool:
        """Process a data packet and store in both tables"""
        try:
            plc_name = data_packet['plc_name']
            timestamp = data_packet['timestamp']
            tag_data = data_packet['data']
            
            # Insert into historical table
            historical_success = self.insert_historical_data(plc_name, tag_data, timestamp)
            
            # Upsert into real-time table
            realtime_success = self.upsert_realtime_data(plc_name, tag_data, timestamp)
            
            return historical_success and realtime_success
            
        except Exception as e:
            print(f"Error processing data packet: {e}")
            return False
    
    def batch_process_data(self, data_packets: List[Dict[str, Any]]) -> int:
        """Process multiple data packets"""
        success_count = 0
        for packet in data_packets:
            if self.process_data_packet(packet):
                success_count += 1
        
        return success_count
    
    def get_historical_data(self, plc_name: str = None, tag_name: str = None, 
                           start_time: datetime = None, end_time: datetime = None, 
                           limit: int = 100) -> List[Dict[str, Any]]:
        """Query historical data with filters"""
        try:
            query = self.client.table(self.historical_table).select('*')
            
            if plc_name:
                query = query.eq('plc_name', plc_name)
            if tag_name:
                query = query.eq('tag_name', tag_name)
            if start_time:
                query = query.gte('timestamp', start_time.isoformat())
            if end_time:
                query = query.lte('timestamp', end_time.isoformat())
            
            query = query.order('timestamp', desc=True).limit(limit)
            
            response = query.execute()
            return response.data if response.data else []
            
        except Exception as e:
            print(f"Error querying historical data: {e}")
            return []
    
    def get_realtime_data(self, plc_name: str = None, tag_name: str = None) -> List[Dict[str, Any]]:
        """Get current real-time values"""
        try:
            query = self.client.table(self.realtime_table).select('*')
            
            if plc_name:
                query = query.eq('plc_name', plc_name)
            if tag_name:
                query = query.eq('tag_name', tag_name)
            
            query = query.order('updated_at', desc=True)
            
            response = query.execute()
            return response.data if response.data else []
            
        except Exception as e:
            print(f"Error querying real-time data: {e}")
            return []
    
    def get_latest_values(self, plc_name: str) -> Dict[str, Any]:
        """Get all latest tag values for a PLC"""
        try:
            data = self.get_realtime_data(plc_name=plc_name)
            
            result = {}
            for record in data:
                tag_name = record['tag_name']
                tag_value = self._deserialize_value(record['tag_value'])
                result[tag_name] = {
                    'value': tag_value,
                    'timestamp': record['timestamp'],
                    'updated_at': record['updated_at']
                }
            
            return result
            
        except Exception as e:
            print(f"Error getting latest values: {e}")
            return {}
    
    def delete_old_historical_data(self, days_to_keep: int = 30) -> int:
        """Delete historical data older than specified days"""
        try:
            cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days_to_keep)
            
            response = self.client.table(self.historical_table)\
                .delete()\
                .lt('timestamp', cutoff_date.isoformat())\
                .execute()
            
            deleted_count = len(response.data) if response.data else 0
            print(f"Deleted {deleted_count} old historical records")
            return deleted_count
            
        except Exception as e:
            print(f"Error deleting old data: {e}")
            return 0
    
    def _serialize_value(self, value: Any) -> Any:
        """Serialize value for JSON storage"""
        if isinstance(value, (dict, list)):
            return value
        elif isinstance(value, (int, float, str, bool, type(None))):
            return {'value': value, 'type': type(value).__name__}
        else:
            # Convert complex types to string
            return {'value': str(value), 'type': type(value).__name__}
    
    def _deserialize_value(self, value: Any) -> Any:
        """Deserialize value from JSON storage"""
        if isinstance(value, dict) and 'value' in value and 'type' in value:
            val = value['value']
            val_type = value['type']
            
            # Try to restore original type
            if val_type == 'int':
                return int(val)
            elif val_type == 'float':
                return float(val)
            elif val_type == 'bool':
                return bool(val)
            else:
                return val
        
        return value
    
    def test_connection(self) -> bool:
        """Test Supabase connection"""
        try:
            # Try to query a small amount of data
            response = self.client.table(self.historical_table).select('*').limit(1).execute()
            print("✓ Supabase connection successful")
            return True
        except Exception as e:
            print(f"✗ Supabase connection failed: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            # Get counts from both tables
            historical_count = self.client.table(self.historical_table)\
                .select('*', count='exact').execute()
            realtime_count = self.client.table(self.realtime_table)\
                .select('*', count='exact').execute()
            
            stats = {
                'historical_records': historical_count.count if historical_count else 0,
                'realtime_tags': realtime_count.count if realtime_count else 0
            }
            
            return stats
            
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {'historical_records': 0, 'realtime_tags': 0}
