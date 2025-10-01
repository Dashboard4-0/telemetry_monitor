"""
PLC Connection Manager
Handles communication with CompactLogix and MicroLogix PLCs using pycomm3
"""

import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pycomm3 import LogixDriver, SLCDriver
import threading
import queue


class PLCConnection:
    """Manages connection and data reading from a single PLC"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize PLC connection"""
        self.name = name
        self.config = config
        self.driver = None
        self.connected = False
        self.last_read_time = None
        self.error_count = 0
        self.max_retries = 3
        
    def connect(self) -> bool:
        """Establish connection to PLC"""
        try:
            driver_type = self.config.get('driver', 'LogixDriver')
            ip_address = self.config['ip_address']
            
            if driver_type == 'LogixDriver':
                # CompactLogix, ControlLogix, Micro800 series
                slot = self.config.get('slot', 0)
                self.driver = LogixDriver(ip_address, slot=slot)
            elif driver_type == 'SLCDriver':
                # MicroLogix series
                self.driver = SLCDriver(ip_address)
            else:
                raise ValueError(f"Unsupported driver type: {driver_type}")
            
            # Open connection
            self.driver.open()
            
            # Verify connection by getting controller info
            if hasattr(self.driver, 'get_plc_info'):
                info = self.driver.get_plc_info()
                if info:
                    print(f"✓ Connected to {self.name}")
                    print(f"  Controller: {info.get('product_name', 'Unknown')}")
                    print(f"  Revision: {info.get('revision', 'Unknown')}")
            else:
                print(f"✓ Connected to {self.name} at {ip_address}")
            
            self.connected = True
            self.error_count = 0
            return True
            
        except Exception as e:
            print(f"✗ Failed to connect to {self.name}: {e}")
            self.connected = False
            self.error_count += 1
            return False
    
    def disconnect(self):
        """Disconnect from PLC"""
        try:
            if self.driver:
                self.driver.close()
            self.connected = False
            print(f"Disconnected from {self.name}")
        except Exception as e:
            print(f"Error disconnecting from {self.name}: {e}")
    
    def read_tag(self, tag_name: str) -> Optional[Any]:
        """Read a single tag value"""
        if not self.connected:
            if not self.connect():
                return None
        
        try:
            result = self.driver.read(tag_name)
            if result:
                self.error_count = 0
                return result.value if hasattr(result, 'value') else result
            return None
            
        except Exception as e:
            print(f"Error reading tag {tag_name} from {self.name}: {e}")
            self.error_count += 1
            
            # Reconnect if too many errors
            if self.error_count >= self.max_retries:
                self.connected = False
                self.disconnect()
            
            return None
    
    def read_tags(self, tag_names: List[str]) -> Dict[str, Any]:
        """Read multiple tags at once"""
        if not self.connected:
            if not self.connect():
                return {}
        
        results = {}
        
        try:
            # Try batch read if supported
            if hasattr(self.driver, 'read') and isinstance(tag_names, list):
                # For LogixDriver, we can read multiple tags at once
                if isinstance(self.driver, LogixDriver):
                    read_results = self.driver.read(*tag_names)
                    
                    if isinstance(read_results, list):
                        for i, result in enumerate(read_results):
                            if result and i < len(tag_names):
                                value = result.value if hasattr(result, 'value') else None
                                results[tag_names[i]] = value
                    elif read_results:
                        # Single tag result
                        value = read_results.value if hasattr(read_results, 'value') else None
                        results[tag_names[0]] = value
                else:
                    # For SLCDriver, read tags one by one
                    for tag_name in tag_names:
                        value = self.read_tag(tag_name)
                        if value is not None:
                            results[tag_name] = value
            else:
                # Fallback to reading tags one by one
                for tag_name in tag_names:
                    value = self.read_tag(tag_name)
                    if value is not None:
                        results[tag_name] = value
            
            self.last_read_time = datetime.now()
            self.error_count = 0
            
        except Exception as e:
            print(f"Error reading tags from {self.name}: {e}")
            self.error_count += 1
            
            if self.error_count >= self.max_retries:
                self.connected = False
                self.disconnect()
        
        return results
    
    def write_tag(self, tag_name: str, value: Any) -> bool:
        """Write a value to a tag"""
        if not self.connected:
            if not self.connect():
                return False
        
        try:
            result = self.driver.write(tag_name, value)
            return result is not None
            
        except Exception as e:
            print(f"Error writing tag {tag_name} on {self.name}: {e}")
            return False
    
    def get_tag_list(self) -> Optional[List[Dict[str, Any]]]:
        """Get list of available tags from PLC (if supported)"""
        if not self.connected:
            if not self.connect():
                return None
        
        try:
            if isinstance(self.driver, LogixDriver):
                # Get tag list for Logix controllers
                tags = self.driver.get_tag_list()
                if tags:
                    return [
                        {
                            'name': tag.get('tag_name', ''),
                            'data_type': tag.get('data_type', ''),
                            'dim': tag.get('dim', 0)
                        }
                        for tag in tags
                    ]
            else:
                print(f"Tag list discovery not supported for {self.config.get('controller_type')}")
                return None
                
        except Exception as e:
            print(f"Error getting tag list from {self.name}: {e}")
            return None


class PLCManager:
    """Manages multiple PLC connections and data collection"""
    
    def __init__(self):
        """Initialize PLC manager"""
        self.connections: Dict[str, PLCConnection] = {}
        self.data_queue = queue.Queue()
        self.running = False
        self.collection_threads = {}
    
    def add_plc(self, name: str, config: Dict[str, Any]) -> bool:
        """Add a new PLC to manage"""
        try:
            if name in self.connections:
                print(f"PLC {name} already exists")
                return False
            
            plc = PLCConnection(name, config)
            if plc.connect():
                self.connections[name] = plc
                return True
            return False
            
        except Exception as e:
            print(f"Error adding PLC {name}: {e}")
            return False
    
    def remove_plc(self, name: str) -> bool:
        """Remove a PLC from management"""
        try:
            if name in self.connections:
                # Stop collection thread if running
                if name in self.collection_threads:
                    self.stop_collection(name)
                
                # Disconnect and remove
                self.connections[name].disconnect()
                del self.connections[name]
                print(f"Removed PLC {name}")
                return True
            return False
            
        except Exception as e:
            print(f"Error removing PLC {name}: {e}")
            return False
    
    def start_collection(self, name: str, tag_names: List[str], scan_rate: float = 1.0):
        """Start data collection for a PLC"""
        if name not in self.connections:
            print(f"PLC {name} not found")
            return
        
        if name in self.collection_threads and self.collection_threads[name].is_alive():
            print(f"Collection already running for {name}")
            return
        
        def collect_data():
            """Thread function for collecting data"""
            plc = self.connections[name]
            while self.running and name in self.connections:
                try:
                    # Read all tags
                    data = plc.read_tags(tag_names)
                    
                    if data:
                        # Add timestamp and PLC name
                        data_packet = {
                            'plc_name': name,
                            'timestamp': datetime.now(),
                            'data': data
                        }
                        self.data_queue.put(data_packet)
                    
                    # Wait for next scan
                    time.sleep(scan_rate)
                    
                except Exception as e:
                    print(f"Error in collection thread for {name}: {e}")
                    time.sleep(scan_rate)
        
        # Start collection thread
        self.running = True
        thread = threading.Thread(target=collect_data, daemon=True)
        thread.start()
        self.collection_threads[name] = thread
        print(f"Started data collection for {name} (scan rate: {scan_rate}s)")
    
    def stop_collection(self, name: str):
        """Stop data collection for a PLC"""
        if name in self.collection_threads:
            print(f"Stopping collection for {name}")
            # Thread will stop on next iteration when self.running is False
    
    def stop_all_collections(self):
        """Stop all data collection threads"""
        self.running = False
        time.sleep(1)  # Give threads time to stop
        self.collection_threads.clear()
        print("Stopped all data collections")
    
    def get_collected_data(self) -> Optional[Dict[str, Any]]:
        """Get next data packet from queue"""
        try:
            if not self.data_queue.empty():
                return self.data_queue.get_nowait()
            return None
        except queue.Empty:
            return None
    
    def get_all_collected_data(self) -> List[Dict[str, Any]]:
        """Get all available data packets from queue"""
        data_packets = []
        while not self.data_queue.empty():
            try:
                data_packets.append(self.data_queue.get_nowait())
            except queue.Empty:
                break
        return data_packets
    
    def test_connection(self, name: str) -> bool:
        """Test connection to a PLC"""
        if name in self.connections:
            plc = self.connections[name]
            if not plc.connected:
                return plc.connect()
            return True
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all PLCs"""
        status = {}
        for name, plc in self.connections.items():
            status[name] = {
                'connected': plc.connected,
                'last_read': plc.last_read_time.isoformat() if plc.last_read_time else None,
                'error_count': plc.error_count,
                'collecting': name in self.collection_threads and self.collection_threads[name].is_alive()
            }
        return status
