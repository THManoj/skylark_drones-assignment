import pandas as pd
from datetime import datetime
import os
import json

class CloudDataLoader:
    """
    Smart data loader that works with:
    - CSV files (local development)
    - Google Sheets (deployed/production)
    
    Automatically detects which backend to use based on environment.
    """
    
    def __init__(self, data_dir=".", use_sheets=False, sheets_sync=None):
        self.data_dir = data_dir
        self.use_sheets = use_sheets
        self.sheets_sync = sheets_sync
        
        self.pilots_df = None
        self.drones_df = None
        self.missions_df = None
        
        self.load_all_data()
    
    def load_all_data(self):
        """Load all data from appropriate source"""
        if self.use_sheets and self.sheets_sync:
            self._load_from_sheets()
        else:
            self._load_from_csv()
    
    def _load_from_csv(self):
        """Load data from CSV files"""
        try:
            self.pilots_df = pd.read_csv(os.path.join(self.data_dir, "pilot_roster.csv"))
            self.drones_df = pd.read_csv(os.path.join(self.data_dir, "drone_fleet.csv"))
            self.missions_df = pd.read_csv(os.path.join(self.data_dir, "missions.csv"))
            
            self._parse_dates()
            
        except FileNotFoundError as e:
            raise Exception(f"Data file not found: {e}")
        except Exception as e:
            raise Exception(f"Error loading data: {e}")
    
    def _load_from_sheets(self):
        """Load data from Google Sheets"""
        try:
            # Load pilots from sheet
            pilots_data = self.sheets_sync.read_pilots_from_sheet()
            if pilots_data is not None and not pilots_data.empty:
                self.pilots_df = pilots_data
            else:
                # Fallback to CSV if sheet is empty
                self.pilots_df = pd.read_csv(os.path.join(self.data_dir, "pilot_roster.csv"))
            
            # Load drones from sheet
            drones_data = self.sheets_sync.read_drones_from_sheet()
            if drones_data is not None and not drones_data.empty:
                self.drones_df = drones_data
            else:
                self.drones_df = pd.read_csv(os.path.join(self.data_dir, "drone_fleet.csv"))
            
            # Load missions from sheet
            missions_data = self.sheets_sync.read_missions_from_sheet()
            if missions_data is not None and not missions_data.empty:
                self.missions_df = missions_data
            else:
                self.missions_df = pd.read_csv(os.path.join(self.data_dir, "missions.csv"))
            
            self._parse_dates()
            
        except Exception as e:
            print(f"Error loading from sheets, falling back to CSV: {e}")
            self._load_from_csv()
    
    def _parse_dates(self):
        """Parse date columns"""
        try:
            self.pilots_df['available_from'] = pd.to_datetime(self.pilots_df['available_from'])
            self.drones_df['maintenance_due'] = pd.to_datetime(self.drones_df['maintenance_due'])
            self.missions_df['start_date'] = pd.to_datetime(self.missions_df['start_date'])
            self.missions_df['end_date'] = pd.to_datetime(self.missions_df['end_date'])
        except Exception as e:
            print(f"Warning: Date parsing issue: {e}")
    
    def get_pilots(self):
        """Return pilots dataframe"""
        return self.pilots_df.copy()
    
    def get_drones(self):
        """Return drones dataframe"""
        return self.drones_df.copy()
    
    def get_missions(self):
        """Return missions dataframe"""
        return self.missions_df.copy()
    
    def get_pilot_by_id(self, pilot_id):
        """Get specific pilot by ID"""
        result = self.pilots_df[self.pilots_df['pilot_id'] == pilot_id]
        return result.iloc[0] if not result.empty else None
    
    def get_drone_by_id(self, drone_id):
        """Get specific drone by ID"""
        result = self.drones_df[self.drones_df['drone_id'] == drone_id]
        return result.iloc[0] if not result.empty else None
    
    def get_mission_by_id(self, project_id):
        """Get specific mission by ID"""
        result = self.missions_df[self.missions_df['project_id'] == project_id]
        return result.iloc[0] if not result.empty else None
    
    def update_pilot_status(self, pilot_id, new_status, current_assignment=None, available_from=None):
        """Update pilot status in dataframe"""
        idx = self.pilots_df[self.pilots_df['pilot_id'] == pilot_id].index
        if len(idx) > 0:
            self.pilots_df.loc[idx[0], 'status'] = new_status
            if current_assignment:
                self.pilots_df.loc[idx[0], 'current_assignment'] = current_assignment
            if available_from:
                self.pilots_df.loc[idx[0], 'available_from'] = available_from
            return True
        return False
    
    def update_drone_status(self, drone_id, new_status, current_assignment=None):
        """Update drone status in dataframe"""
        idx = self.drones_df[self.drones_df['drone_id'] == drone_id].index
        if len(idx) > 0:
            self.drones_df.loc[idx[0], 'status'] = new_status
            if current_assignment:
                self.drones_df.loc[idx[0], 'current_assignment'] = current_assignment
            return True
        return False
    
    def update_mission_assignment(self, project_id, pilot_id=None, drone_id=None):
        """Update mission with assigned pilot and/or drone"""
        idx = self.missions_df[self.missions_df['project_id'] == project_id].index
        if len(idx) > 0:
            if pilot_id:
                self.missions_df.loc[idx[0], 'assigned_pilot'] = pilot_id
            if drone_id:
                self.missions_df.loc[idx[0], 'assigned_drone'] = drone_id
            return True
        return False
    
    # ============ SAVE METHODS ============
    
    def save_pilots(self):
        """Save pilots to appropriate backend"""
        if self.use_sheets and self.sheets_sync:
            return self._save_pilots_to_sheets()
        else:
            return self._save_pilots_to_csv()
    
    def save_drones(self):
        """Save drones to appropriate backend"""
        if self.use_sheets and self.sheets_sync:
            return self._save_drones_to_sheets()
        else:
            return self._save_drones_to_csv()
    
    def save_missions(self):
        """Save missions to appropriate backend"""
        if self.use_sheets and self.sheets_sync:
            return self._save_missions_to_sheets()
        else:
            return self._save_missions_to_csv()
    
    def save_all(self):
        """Save all data"""
        return self.save_pilots() and self.save_drones() and self.save_missions()
    
    # ============ CSV SAVE METHODS ============
    
    def _save_pilots_to_csv(self):
        """Save pilots dataframe to CSV"""
        try:
            df_to_save = self.pilots_df.copy()
            df_to_save['available_from'] = df_to_save['available_from'].dt.strftime('%Y-%m-%d')
            df_to_save.to_csv(os.path.join(self.data_dir, "pilot_roster.csv"), index=False)
            return True
        except Exception as e:
            print(f"Error saving pilots to CSV: {e}")
            return False
    
    def _save_drones_to_csv(self):
        """Save drones dataframe to CSV"""
        try:
            df_to_save = self.drones_df.copy()
            df_to_save['maintenance_due'] = df_to_save['maintenance_due'].dt.strftime('%Y-%m-%d')
            df_to_save.to_csv(os.path.join(self.data_dir, "drone_fleet.csv"), index=False)
            return True
        except Exception as e:
            print(f"Error saving drones to CSV: {e}")
            return False
    
    def _save_missions_to_csv(self):
        """Save missions dataframe to CSV"""
        try:
            df_to_save = self.missions_df.copy()
            df_to_save['start_date'] = df_to_save['start_date'].dt.strftime('%Y-%m-%d')
            df_to_save['end_date'] = df_to_save['end_date'].dt.strftime('%Y-%m-%d')
            df_to_save.to_csv(os.path.join(self.data_dir, "missions.csv"), index=False)
            return True
        except Exception as e:
            print(f"Error saving missions to CSV: {e}")
            return False
    
    # ============ GOOGLE SHEETS SAVE METHODS ============
    
    def _save_pilots_to_sheets(self):
        """Save pilots to Google Sheets"""
        try:
            df_to_save = self.pilots_df.copy()
            df_to_save['available_from'] = df_to_save['available_from'].dt.strftime('%Y-%m-%d')
            result = self.sheets_sync.sync_pilots_to_sheet(df_to_save)
            return result['success']
        except Exception as e:
            print(f"Error saving pilots to sheets: {e}")
            return False
    
    def _save_drones_to_sheets(self):
        """Save drones to Google Sheets"""
        try:
            df_to_save = self.drones_df.copy()
            df_to_save['maintenance_due'] = df_to_save['maintenance_due'].dt.strftime('%Y-%m-%d')
            result = self.sheets_sync.sync_drones_to_sheet(df_to_save)
            return result['success']
        except Exception as e:
            print(f"Error saving drones to sheets: {e}")
            return False
    
    def _save_missions_to_sheets(self):
        """Save missions to Google Sheets"""
        try:
            df_to_save = self.missions_df.copy()
            df_to_save['start_date'] = df_to_save['start_date'].dt.strftime('%Y-%m-%d')
            df_to_save['end_date'] = df_to_save['end_date'].dt.strftime('%Y-%m-%d')
            result = self.sheets_sync.sync_missions_to_sheet(df_to_save)
            return result['success']
        except Exception as e:
            print(f"Error saving missions to sheets: {e}")
            return False
