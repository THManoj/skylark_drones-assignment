from datetime import datetime

class DroneInventory:
    """Manage drone fleet inventory"""
    
    def __init__(self, data_loader):
        self.data_loader = data_loader
    
    def get_available_drones(self):
        """Get all available drones"""
        drones = self.data_loader.get_drones()
        return drones[drones['status'] == 'Available']
    
    def get_drones_by_capability(self, capability):
        """Get drones with specific capability"""
        drones = self.data_loader.get_drones()
        matching = []
        for idx, drone in drones.iterrows():
            capabilities = [c.strip() for c in str(drone['capabilities']).split(',')]
            if capability in capabilities:
                matching.append(drone)
        
        if matching:
            import pandas as pd
            return pd.DataFrame(matching)
        
        import pandas as pd
        return pd.DataFrame()
    
    def get_drones_by_location(self, location):
        """Get drones in specific location"""
        drones = self.data_loader.get_drones()
        return drones[drones['location'] == location]
    
    def get_drones_by_status(self, status):
        """Get drones by status"""
        drones = self.data_loader.get_drones()
        return drones[drones['status'] == status]
    
    def get_drone_details(self, drone_id):
        """Get detailed info for a drone"""
        drone = self.data_loader.get_drone_by_id(drone_id)
        if drone is not None:
            return {
                'id': drone['drone_id'],
                'model': drone['model'],
                'capabilities': drone['capabilities'],
                'status': drone['status'],
                'location': drone['location'],
                'current_assignment': drone['current_assignment'],
                'maintenance_due': drone['maintenance_due']
            }
        return None
    
    def get_maintenance_due_soon(self, days=30):
        """Get drones with maintenance due soon"""
        from datetime import datetime, timedelta
        drones = self.data_loader.get_drones()
        today = datetime.now()
        threshold = today + timedelta(days=days)
        
        maintenance_due = []
        for idx, drone in drones.iterrows():
            maint_date = drone['maintenance_due']
            if maint_date < threshold:
                maintenance_due.append({
                    'drone_id': drone['drone_id'],
                    'model': drone['model'],
                    'maintenance_due': maint_date,
                    'days_until': (maint_date - today).days
                })
        
        return maintenance_due
    
    def find_best_drone_for_mission(self, required_capabilities, location):
        """Find best drone match for mission requirements"""
        drones = self.data_loader.get_drones()
        available = drones[drones['status'] == 'Available']
        
        best_matches = []
        for idx, drone in available.iterrows():
            drone_caps = [c.strip() for c in str(drone['capabilities']).split(',')]
            required_caps = [c.strip() for c in str(required_capabilities).split(',')]
            
            cap_match = sum(1 for cap in required_caps if cap in drone_caps)
            location_match = 1 if drone['location'] == location else 0
            
            if cap_match > 0:
                score = cap_match * 2 + location_match * 0.5
                best_matches.append({
                    'drone_id': drone['drone_id'],
                    'model': drone['model'],
                    'score': score,
                    'cap_match': cap_match,
                    'location_match': location_match
                })
        
        best_matches.sort(key=lambda x: x['score'], reverse=True)
        return best_matches
    
    def assign_drone(self, drone_id, project_id):
        """Assign drone to project"""
        success = self.data_loader.update_drone_status(drone_id, 'Deployed', project_id)
        if success:
            return {'success': True, 'message': f'Drone {drone_id} assigned to {project_id}'}
        return {'success': False, 'message': f'Drone {drone_id} not found'}
    
    def mark_drone_available(self, drone_id):
        """Mark drone as available"""
        success = self.data_loader.update_drone_status(drone_id, 'Available', '–')
        if success:
            return {'success': True, 'message': f'Drone {drone_id} marked available'}
        return {'success': False, 'message': f'Drone {drone_id} not found'}
    
    def mark_drone_maintenance(self, drone_id):
        """Mark drone as in maintenance"""
        success = self.data_loader.update_drone_status(drone_id, 'Maintenance', '–')
        if success:
            return {'success': True, 'message': f'Drone {drone_id} marked for maintenance'}
        return {'success': False, 'message': f'Drone {drone_id} not found'}
