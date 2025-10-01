"""
Abstract Database Interface
Defines the common interface for all database implementations
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime


class DatabaseManager(ABC):
    """Abstract base class for database managers"""
    
    @abstractmethod
    def __init__(self, **kwargs):
        """Initialize database connection"""
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test database connection"""
        pass
    
    @abstractmethod
    def insert_historical_data(self, plc_name: str, tag_data: Dict[str, Any], 
                             timestamp: datetime = None) -> bool:
        """Insert data into historical table"""
        pass
    
    @abstractmethod
    def upsert_realtime_data(self, plc_name: str, tag_data: Dict[str, Any], 
                           timestamp: datetime = None) -> bool:
        """Upsert data into real-time table"""
        pass
    
    @abstractmethod
    def process_data_packet(self, data_packet: Dict[str, Any]) -> bool:
        """Process a data packet and store in both tables"""
        pass
    
    @abstractmethod
    def batch_process_data(self, data_packets: List[Dict[str, Any]]) -> int:
        """Process multiple data packets"""
        pass
    
    @abstractmethod
    def get_historical_data(self, plc_name: str = None, tag_name: str = None, 
                          start_time: datetime = None, end_time: datetime = None, 
                          limit: int = 100) -> List[Dict[str, Any]]:
        """Query historical data with filters"""
        pass
    
    @abstractmethod
    def get_realtime_data(self, plc_name: str = None, tag_name: str = None) -> List[Dict[str, Any]]:
        """Get current real-time values"""
        pass
    
    @abstractmethod
    def get_latest_values(self, plc_name: str) -> Dict[str, Any]:
        """Get all latest tag values for a PLC"""
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        pass
    
    @abstractmethod
    def delete_old_historical_data(self, days_to_keep: int = 30) -> int:
        """Delete historical data older than specified days"""
        pass
    
    def _serialize_value(self, value: Any) -> Any:
        """Serialize value for storage (common implementation)"""
        if isinstance(value, (dict, list)):
            return value
        elif isinstance(value, (int, float, str, bool, type(None))):
            return {'value': value, 'type': type(value).__name__}
        else:
            # Convert complex types to string
            return {'value': str(value), 'type': type(value).__name__}
    
    def _deserialize_value(self, value: Any) -> Any:
        """Deserialize value from storage (common implementation)"""
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
