import gspread
import pandas as pd
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
import os
import json

class GoogleSheetsSync:
    """Handle 2-way sync with Google Sheets"""
    
    def __init__(self, credentials_json=None):
        self.credentials = None
        self.client = None
        self.spreadsheet = None
        self.pilot_sheet = None
        self.drone_sheet = None
        
        if credentials_json:
            self.authenticate(credentials_json)
    
    def authenticate(self, credentials_json):
        """Authenticate with Google Sheets API"""
        try:
            # Support both file path and JSON string
            if os.path.exists(credentials_json):
                with open(credentials_json, 'r') as f:
                    creds_dict = json.load(f)
            else:
                creds_dict = json.loads(credentials_json)
            
            self.credentials = service_account.Credentials.from_service_account_info(
                creds_dict,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            self.client = gspread.authorize(self.credentials)
            return True
        except Exception as e:
            print(f"Authentication failed: {e}")
            return False
    
    def open_spreadsheet(self, spreadsheet_id):
        """Open a spreadsheet by ID"""
        try:
            self.spreadsheet = self.client.open_by_key(spreadsheet_id)
            return True
        except Exception as e:
            print(f"Error opening spreadsheet: {e}")
            return False
    
    def get_pilot_sheet(self):
        """Get pilot roster worksheet"""
        if self.spreadsheet:
            try:
                self.pilot_sheet = self.spreadsheet.worksheet('Pilot Roster')
                return self.pilot_sheet
            except:
                # Create if doesn't exist
                self.pilot_sheet = self.spreadsheet.add_worksheet(title='Pilot Roster', rows=100, cols=10)
                return self.pilot_sheet
        return None
    
    def get_drone_sheet(self):
        """Get drone fleet worksheet"""
        if self.spreadsheet:
            try:
                self.drone_sheet = self.spreadsheet.worksheet('Drone Fleet')
                return self.drone_sheet
            except:
                # Create if doesn't exist
                self.drone_sheet = self.spreadsheet.add_worksheet(title='Drone Fleet', rows=100, cols=10)
                return self.drone_sheet
        return None
    
    def get_mission_sheet(self):
        """Get missions worksheet"""
        if self.spreadsheet:
            try:
                return self.spreadsheet.worksheet('Missions')
            except:
                # Create if doesn't exist
                return self.spreadsheet.add_worksheet(title='Missions', rows=100, cols=15)
        return None
    
    def sync_pilots_to_sheet(self, pilots_df):
        """Sync pilot data to Google Sheet"""
        try:
            sheet = self.get_pilot_sheet()
            if not sheet:
                return {'success': False, 'message': 'Could not access Pilot Roster sheet'}
            
            # Clear existing data (keep headers)
            sheet.clear()
            
            # Write headers
            headers = list(pilots_df.columns)
            sheet.append_row(headers)
            
            # Write data
            for idx, row in pilots_df.iterrows():
                row_data = [str(val) for val in row.values]
                sheet.append_row(row_data)
            
            return {'success': True, 'message': f'Synced {len(pilots_df)} pilots to Google Sheet'}
        except Exception as e:
            return {'success': False, 'message': f'Error syncing pilots: {e}'}
    
    def sync_drones_to_sheet(self, drones_df):
        """Sync drone data to Google Sheet"""
        try:
            sheet = self.get_drone_sheet()
            if not sheet:
                return {'success': False, 'message': 'Could not access Drone Fleet sheet'}
            
            # Clear existing data
            sheet.clear()
            
            # Write headers
            headers = list(drones_df.columns)
            sheet.append_row(headers)
            
            # Write data
            for idx, row in drones_df.iterrows():
                row_data = [str(val) for val in row.values]
                sheet.append_row(row_data)
            
            return {'success': True, 'message': f'Synced {len(drones_df)} drones to Google Sheet'}
        except Exception as e:
            return {'success': False, 'message': f'Error syncing drones: {e}'}
    
    def read_pilots_from_sheet(self):
        """Read pilot data from Google Sheet"""
        try:
            sheet = self.get_pilot_sheet()
            if not sheet:
                return None
            
            data = sheet.get_all_records()
            return pd.DataFrame(data)
        except Exception as e:
            print(f"Error reading pilots from sheet: {e}")
            return None
    
    def read_drones_from_sheet(self):
        """Read drone data from Google Sheet"""
        try:
            sheet = self.get_drone_sheet()
            if not sheet:
                return None
            
            data = sheet.get_all_records()
            return pd.DataFrame(data)
        except Exception as e:
            print(f"Error reading drones from sheet: {e}")
            return None
    
    def read_missions_from_sheet(self):
        """Read mission data from Google Sheet"""
        try:
            sheet = self.get_mission_sheet()
            if not sheet:
                return None
            
            data = sheet.get_all_records()
            return pd.DataFrame(data)
        except Exception as e:
            print(f"Error reading missions from sheet: {e}")
            return None
    
    def sync_missions_to_sheet(self, missions_df):
        """Sync mission data to Google Sheet"""
        try:
            sheet = self.get_mission_sheet()
            if not sheet:
                return {'success': False, 'message': 'Could not access Missions sheet'}
            
            # Clear existing data
            sheet.clear()
            
            # Write headers
            headers = list(missions_df.columns)
            sheet.append_row(headers)
            
            # Write data
            for idx, row in missions_df.iterrows():
                row_data = [str(val) for val in row.values]
                sheet.append_row(row_data)
            
            return {'success': True, 'message': f'Synced {len(missions_df)} missions to Google Sheet'}
        except Exception as e:
            return {'success': False, 'message': f'Error syncing missions: {e}'}
    
    def update_pilot_status(self, pilot_id, new_status, current_assignment=None):
        """Update specific pilot status in Google Sheet"""
        try:
            sheet = self.get_pilot_sheet()
            if not sheet:
                return False
            
            all_records = sheet.get_all_records()
            
            for idx, record in enumerate(all_records, start=2):  # Start at 2 due to header
                if record['pilot_id'] == pilot_id:
                    sheet.update_cell(idx, 6, new_status)  # status column
                    if current_assignment:
                        sheet.update_cell(idx, 7, current_assignment)  # current_assignment column
                    return True
            
            return False
        except Exception as e:
            print(f"Error updating pilot status: {e}")
            return False
    
    def update_drone_status(self, drone_id, new_status, current_assignment=None):
        """Update specific drone status in Google Sheet"""
        try:
            sheet = self.get_drone_sheet()
            if not sheet:
                return False
            
            all_records = sheet.get_all_records()
            
            for idx, record in enumerate(all_records, start=2):  # Start at 2 due to header
                if record['drone_id'] == drone_id:
                    sheet.update_cell(idx, 4, new_status)  # status column
                    if current_assignment:
                        sheet.update_cell(idx, 6, current_assignment)  # current_assignment column
                    return True
            
            return False
        except Exception as e:
            print(f"Error updating drone status: {e}")
            return False
