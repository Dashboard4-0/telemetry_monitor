"""
SQLite Database Manager
Handles data storage to SQLite with both historical and real-time tables
"""

import os
import sqlite3
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from database_interface import DatabaseManager


class SQLiteManager(DatabaseManager):
    """Manages SQLite database operations for PLC data"""
    
    def __init__(self, db_path: str = None):
        """Initialize SQLite connection"""
        if db_path is None:
            # Default to local database file
            db_path = os.path.join(os.getcwd(), 'plc_data.db')
        
        self.db_path = db_path
        self.historical_table = 'plc_data_historical'
        self.realtime_table = 'plc_data_realtime'
        
        # Ensure database directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database and tables
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database and create tables if they don't exist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create historical table
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS {self.historical_table} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        plc_name TEXT NOT NULL,
                        tag_name TEXT NOT NULL,
                        tag_value TEXT,
                        timestamp TEXT NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create real-time table
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS {self.realtime_table} (
                        id TEXT PRIMARY KEY,
                        plc_name TEXT NOT NULL,
                        tag_name TEXT NOT NULL,
                        tag_value TEXT,
                        timestamp TEXT NOT NULL,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create indexes for performance
                cursor.execute(f'''
                    CREATE INDEX IF NOT EXISTS idx_historical_plc_tag_time 
                    ON {self.historical_table}(plc_name, tag_name, timestamp DESC)
                ''')
                
                cursor.execute(f'''
                    CREATE INDEX IF NOT EXISTS idx_historical_timestamp 
                    ON {self.historical_table}(timestamp DESC)
                ''')
                
                cursor.execute(f'''
                    CREATE INDEX IF NOT EXISTS idx_historical_plc_name 
                    ON {self.historical_table}(plc_name)
                ''')
                
                cursor.execute(f'''
                    CREATE INDEX IF NOT EXISTS idx_realtime_plc_name 
                    ON {self.realtime_table}(plc_name)
                ''')
                
                conn.commit()
                
        except Exception as e:
            raise ValueError(f"Failed to initialize SQLite database: {e}")
    
    def test_connection(self) -> bool:
        """Test SQLite connection"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                if result:
                    print("✓ SQLite connection successful")
                    return True
        except Exception as e:
            print(f"✗ SQLite connection failed: {e}")
            return False
    
    def insert_historical_data(self, plc_name: str, tag_data: Dict[str, Any], 
                             timestamp: datetime = None) -> bool:
        """Insert data into historical table"""
        try:
            if timestamp is None:
                timestamp = datetime.now()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Prepare batch insert data
                records = []
                for tag_name, tag_value in tag_data.items():
                    record = (
                        plc_name,
                        tag_name,
                        json.dumps(self._serialize_value(tag_value)),
                        timestamp.isoformat()
                    )
                    records.append(record)
                
                # Batch insert
                if records:
                    cursor.executemany(f'''
                        INSERT INTO {self.historical_table} 
                        (plc_name, tag_name, tag_value, timestamp) 
                        VALUES (?, ?, ?, ?)
                    ''', records)
                    conn.commit()
                    return True
                
                return False
                
        except Exception as e:
            print(f"Error inserting historical data: {e}")
            return False
    
    def upsert_realtime_data(self, plc_name: str, tag_data: Dict[str, Any], 
                           timestamp: datetime = None) -> bool:
        """Upsert data into real-time table"""
        try:
            if timestamp is None:
                timestamp = datetime.now()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Prepare upsert data
                records = []
                for tag_name, tag_value in tag_data.items():
                    # Create composite key
                    composite_id = f"{plc_name}_{tag_name}"
                    
                    record = (
                        composite_id,
                        plc_name,
                        tag_name,
                        json.dumps(self._serialize_value(tag_value)),
                        timestamp.isoformat(),
                        datetime.now().isoformat()
                    )
                    records.append(record)
                
                # Batch upsert using INSERT OR REPLACE
                if records:
                    cursor.executemany(f'''
                        INSERT OR REPLACE INTO {self.realtime_table} 
                        (id, plc_name, tag_name, tag_value, timestamp, updated_at) 
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', records)
                    conn.commit()
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
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Build query
                query = f"SELECT * FROM {self.historical_table}"
                conditions = []
                params = []
                
                if plc_name:
                    conditions.append("plc_name = ?")
                    params.append(plc_name)
                
                if tag_name:
                    conditions.append("tag_name = ?")
                    params.append(tag_name)
                
                if start_time:
                    conditions.append("timestamp >= ?")
                    params.append(start_time.isoformat())
                
                if end_time:
                    conditions.append("timestamp <= ?")
                    params.append(end_time.isoformat())
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                query += f" ORDER BY timestamp DESC LIMIT {limit}"
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                # Convert to list of dictionaries
                columns = [description[0] for description in cursor.description]
                result = []
                for row in rows:
                    record = dict(zip(columns, row))
                    # Deserialize tag_value
                    if record['tag_value']:
                        record['tag_value'] = json.loads(record['tag_value'])
                    result.append(record)
                
                return result
                
        except Exception as e:
            print(f"Error querying historical data: {e}")
            return []
    
    def get_realtime_data(self, plc_name: str = None, tag_name: str = None) -> List[Dict[str, Any]]:
        """Get current real-time values"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Build query
                query = f"SELECT * FROM {self.realtime_table}"
                conditions = []
                params = []
                
                if plc_name:
                    conditions.append("plc_name = ?")
                    params.append(plc_name)
                
                if tag_name:
                    conditions.append("tag_name = ?")
                    params.append(tag_name)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                query += " ORDER BY updated_at DESC"
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                # Convert to list of dictionaries
                columns = [description[0] for description in cursor.description]
                result = []
                for row in rows:
                    record = dict(zip(columns, row))
                    # Deserialize tag_value
                    if record['tag_value']:
                        record['tag_value'] = json.loads(record['tag_value'])
                    result.append(record)
                
                return result
                
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
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get historical count
                cursor.execute(f"SELECT COUNT(*) FROM {self.historical_table}")
                historical_count = cursor.fetchone()[0]
                
                # Get real-time count
                cursor.execute(f"SELECT COUNT(*) FROM {self.realtime_table}")
                realtime_count = cursor.fetchone()[0]
                
                stats = {
                    'historical_records': historical_count,
                    'realtime_tags': realtime_count
                }
                
                return stats
                
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {'historical_records': 0, 'realtime_tags': 0}
    
    def delete_old_historical_data(self, days_to_keep: int = 30) -> int:
        """Delete historical data older than specified days"""
        try:
            cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days_to_keep)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute(f'''
                    DELETE FROM {self.historical_table} 
                    WHERE timestamp < ?
                ''', (cutoff_date.isoformat(),))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                print(f"Deleted {deleted_count} old historical records")
                return deleted_count
                
        except Exception as e:
            print(f"Error deleting old data: {e}")
            return 0
