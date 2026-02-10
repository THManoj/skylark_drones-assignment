import pandas as pd
from datetime import datetime
import os

class DataLoader:
    """Load and manage data from CSV files"""
    
    def __init__(self, data_dir="."):
        self.data_dir = data_dir
        self.pilots_df = None
        self.drones_df = None
        self.missions_df = None
        self.load_all_data()
    
    def load_all_data(self):
        """Load all CSV files"""
        try:
            self.pilots_df = pd.read_csv(os.path.join(self.data_dir, "pilot_roster.csv"))
            self.drones_df = pd.read_csv(os.path.join(self.data_dir, "drone_fleet.csv"))
            self.missions_df = pd.read_csv(os.path.join(self.data_dir, "missions.csv"))
            
            # Parse date columns
            self.pilots_df['available_from'] = pd.to_datetime(self.pilots_df['available_from'])
            self.drones_df['maintenance_due'] = pd.to_datetime(self.drones_df['maintenance_due'])
            self.missions_df['start_date'] = pd.to_datetime(self.missions_df['start_date'])
            self.missions_df['end_date'] = pd.to_datetime(self.missions_df['end_date'])
            
        except FileNotFoundError as e:
            raise Exception(f"Data file not found: {e}")
        except Exception as e:
            raise Exception(f"Error loading data: {e}")
    
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
    
    # ============ SAVE METHODS - Persist to CSV ============
    
    def save_pilots(self):
        """Save pilots dataframe back to CSV"""
        try:
            # Create a copy for saving
            df_to_save = self.pilots_df.copy()
            # Convert datetime back to string format
            df_to_save['available_from'] = df_to_save['available_from'].dt.strftime('%Y-%m-%d')
            df_to_save.to_csv(os.path.join(self.data_dir, "pilot_roster.csv"), index=False)
            return True
        except Exception as e:
            print(f"Error saving pilots: {e}")
            return False
    
    def save_drones(self):
        """Save drones dataframe back to CSV"""
        try:
            df_to_save = self.drones_df.copy()
            df_to_save['maintenance_due'] = df_to_save['maintenance_due'].dt.strftime('%Y-%m-%d')
            df_to_save.to_csv(os.path.join(self.data_dir, "drone_fleet.csv"), index=False)
            return True
        except Exception as e:
            print(f"Error saving drones: {e}")
            return False
    
    def save_missions(self):
        """Save missions dataframe back to CSV"""
        try:
            df_to_save = self.missions_df.copy()
            df_to_save['start_date'] = df_to_save['start_date'].dt.strftime('%Y-%m-%d')
            df_to_save['end_date'] = df_to_save['end_date'].dt.strftime('%Y-%m-%d')
            df_to_save.to_csv(os.path.join(self.data_dir, "missions.csv"), index=False)
            return True
        except Exception as e:
            print(f"Error saving missions: {e}")
            return False
    
    def save_all(self):
        """Save all dataframes to CSV"""
        return self.save_pilots() and self.save_drones() and self.save_missions()
    
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
