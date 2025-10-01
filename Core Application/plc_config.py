"""
PLC Configuration Manager
Handles PLC setup, configuration storage, and tag list management
"""

import os
import yaml
import pandas as pd
from typing import Dict, List, Optional, Any
from pathlib import Path


class PLCConfig:
    """Manages PLC configurations and tag lists"""
    
    SUPPORTED_CONTROLLERS = {
        'CompactLogix': {
            'description': 'Allen-Bradley CompactLogix',
            'driver': 'LogixDriver',
            'default_slot': 0
        },
        'ControlLogix': {
            'description': 'Allen-Bradley ControlLogix',
            'driver': 'LogixDriver',
            'default_slot': 0
        },
        'MicroLogix1100': {
            'description': 'Allen-Bradley MicroLogix 1100',
            'driver': 'SLCDriver',
            'default_slot': None
        },
        'MicroLogix1400': {
            'description': 'Allen-Bradley MicroLogix 1400',
            'driver': 'SLCDriver',
            'default_slot': None
        },
        'Micro850': {
            'description': 'Allen-Bradley Micro850',
            'driver': 'LogixDriver',
            'default_slot': 0
        },
        'Micro870': {
            'description': 'Allen-Bradley Micro870',
            'driver': 'LogixDriver',
            'default_slot': 0
        }
    }
    
    def __init__(self, config_dir: str = './configs'):
        """Initialize configuration manager"""
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.plc_configs_dir = self.config_dir / 'plc_configs'
        self.plc_configs_dir.mkdir(exist_ok=True)
        self.tag_lists_dir = self.config_dir / 'tag_lists'
        self.tag_lists_dir.mkdir(exist_ok=True)
    
    def create_plc_config(self, name: str, config_data: Dict[str, Any]) -> bool:
        """Create a new PLC configuration"""
        try:
            # Validate controller type
            if config_data['controller_type'] not in self.SUPPORTED_CONTROLLERS:
                raise ValueError(f"Unsupported controller type: {config_data['controller_type']}")
            
            # Add driver information based on controller type
            controller_info = self.SUPPORTED_CONTROLLERS[config_data['controller_type']]
            config_data['driver'] = controller_info['driver']
            if controller_info['default_slot'] is not None and 'slot' not in config_data:
                config_data['slot'] = controller_info['default_slot']
            
            # Save configuration
            config_file = self.plc_configs_dir / f"{name}.yaml"
            with open(config_file, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False)
            
            print(f"✓ PLC configuration '{name}' created successfully")
            return True
            
        except Exception as e:
            print(f"✗ Error creating PLC configuration: {e}")
            return False
    
    def load_plc_config(self, name: str) -> Optional[Dict[str, Any]]:
        """Load a PLC configuration by name"""
        try:
            config_file = self.plc_configs_dir / f"{name}.yaml"
            if not config_file.exists():
                print(f"✗ Configuration '{name}' not found")
                return None
            
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            return config
            
        except Exception as e:
            print(f"✗ Error loading configuration: {e}")
            return None
    
    def list_plc_configs(self) -> List[str]:
        """List all available PLC configurations"""
        configs = []
        for config_file in self.plc_configs_dir.glob("*.yaml"):
            configs.append(config_file.stem)
        return configs
    
    def import_tag_list(self, plc_name: str, csv_file: str) -> bool:
        """Import tag list from CSV file
        
        Supports multiple CSV formats:
        1. Standard format: tag_name, description, data_type, scan_rate
        2. Alternative format: NAME, DESCRIPTION, DATATYPE (tab-separated)
        """
        try:
            # Try to detect CSV format and read accordingly
            df = self._read_csv_with_format_detection(csv_file)
            
            if df is None or df.empty:
                raise ValueError("CSV file is empty or could not be read")
            
            # Normalize column names to standard format
            df = self._normalize_csv_columns(df)
            
            # Validate that we have the required tag_name column
            if 'tag_name' not in df.columns:
                raise ValueError("CSV must contain a column for tag names (tag_name or NAME)")
            
            # Add default values for missing columns
            if 'description' not in df.columns:
                df['description'] = ''
            if 'data_type' not in df.columns:
                df['data_type'] = 'AUTO'
            if 'scan_rate' not in df.columns:
                df['scan_rate'] = 1.0  # Default 1 second scan rate
            
            # Clean up data - remove empty rows and handle missing values
            df = df.dropna(subset=['tag_name'])  # Remove rows with empty tag names
            df = df[df['tag_name'].str.strip() != '']  # Remove rows with whitespace-only tag names
            
            if df.empty:
                raise ValueError("No valid tags found in CSV file")
            
            # Save processed tag list
            tag_file = self.tag_lists_dir / f"{plc_name}_tags.csv"
            df.to_csv(tag_file, index=False)
            
            print(f"✓ Imported {len(df)} tags for PLC '{plc_name}'")
            return True
            
        except Exception as e:
            print(f"✗ Error importing tag list: {e}")
            return False
    
    def _read_csv_with_format_detection(self, csv_file: str) -> Optional[pd.DataFrame]:
        """Read CSV file with automatic format detection"""
        df = None
        
        # Try comma-separated first (standard format)
        try:
            df = pd.read_csv(csv_file)
            
            # Check if this looks like the standard format
            if 'tag_name' in df.columns or 'NAME' in df.columns:
                return df
        except Exception as e:
            # Comma-separated failed, will try tab-separated below
            pass
        
        # Try tab-separated (alternative format common in PLC exports)
        try:
            df_tab = pd.read_csv(csv_file, sep='\t')
            if 'NAME' in df_tab.columns or 'tag_name' in df_tab.columns:
                return df_tab
            # If tab-separated works but doesn't have expected columns, still use it
            if not df_tab.empty:
                return df_tab
        except Exception as e:
            pass
        
        # If both fail, try to return whichever one we got (even if incomplete)
        if df is not None:
            return df
        
        print(f"Error reading CSV file: Unable to parse as comma or tab-separated")
        return None
    
    def _normalize_csv_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names to standard format"""
        # Create a copy to avoid modifying the original
        df_normalized = df.copy()
        
        # Column mapping from alternative formats to standard format
        column_mapping = {
            'NAME': 'tag_name',
            'TAG_NAME': 'tag_name',
            'Tag_Name': 'tag_name',
            'tag': 'tag_name',
            'DESCRIPTION': 'description',
            'DESC': 'description',
            'DATATYPE': 'data_type',
            'DATA_TYPE': 'data_type',
            'DataType': 'data_type',
            'TYPE': 'data_type',
            'SCAN_RATE': 'scan_rate',
            'SCANRATE': 'scan_rate',
            'RATE': 'scan_rate',
            'INTERVAL': 'scan_rate'
        }
        
        # Rename columns based on mapping
        df_normalized = df_normalized.rename(columns=column_mapping)
        
        return df_normalized
    
    def load_tag_list(self, plc_name: str) -> Optional[pd.DataFrame]:
        """Load tag list for a PLC"""
        try:
            tag_file = self.tag_lists_dir / f"{plc_name}_tags.csv"
            if not tag_file.exists():
                print(f"✗ Tag list for '{plc_name}' not found")
                return None
            
            df = pd.read_csv(tag_file)
            return df
            
        except Exception as e:
            print(f"✗ Error loading tag list: {e}")
            return None
    
    def update_plc_config(self, name: str, updates: Dict[str, Any]) -> bool:
        """Update an existing PLC configuration"""
        try:
            config = self.load_plc_config(name)
            if not config:
                return False
            
            # Update configuration
            config.update(updates)
            
            # Save updated configuration
            config_file = self.plc_configs_dir / f"{name}.yaml"
            with open(config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            print(f"✓ Configuration '{name}' updated successfully")
            return True
            
        except Exception as e:
            print(f"✗ Error updating configuration: {e}")
            return False
    
    def delete_plc_config(self, name: str) -> bool:
        """Delete a PLC configuration and its tag list"""
        try:
            # Delete configuration file
            config_file = self.plc_configs_dir / f"{name}.yaml"
            if config_file.exists():
                config_file.unlink()
            
            # Delete tag list if exists
            tag_file = self.tag_lists_dir / f"{name}_tags.csv"
            if tag_file.exists():
                tag_file.unlink()
            
            print(f"✓ Configuration '{name}' deleted successfully")
            return True
            
        except Exception as e:
            print(f"✗ Error deleting configuration: {e}")
            return False
    
    def get_config_summary(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a summary of PLC configuration and tag list"""
        config = self.load_plc_config(name)
        if not config:
            return None
        
        summary = {
            'name': name,
            'controller_type': config.get('controller_type'),
            'ip_address': config.get('ip_address'),
            'driver': config.get('driver'),
            'tags': None
        }
        
        # Add tag list info if available
        tags_df = self.load_tag_list(name)
        if tags_df is not None:
            summary['tags'] = {
                'count': len(tags_df),
                'tag_names': tags_df['tag_name'].tolist()[:10],  # First 10 tags as preview
                'has_more': len(tags_df) > 10
            }
        
        return summary
