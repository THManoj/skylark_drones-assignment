from datetime import datetime

class AssignmentTracker:
    """Track and manage pilot/drone assignments to missions"""
    
    def __init__(self, data_loader, roster_manager, drone_inventory):
        self.data_loader = data_loader
        self.roster_manager = roster_manager
        self.drone_inventory = drone_inventory
    
    def get_active_assignments(self):
        """Get all active assignments (pilots and drones)"""
        pilots = self.data_loader.get_pilots()
        drones = self.data_loader.get_drones()
        
        pilot_assignments = []
        drone_assignments = []
        
        # Get pilot assignments
        for idx, pilot in pilots.iterrows():
            if pilot['current_assignment'] != '–':
                pilot_assignments.append({
                    'type': 'Pilot',
                    'id': pilot['pilot_id'],
                    'name': pilot['name'],
                    'assignment': pilot['current_assignment'],
                    'status': pilot['status']
                })
        
        # Get drone assignments
        for idx, drone in drones.iterrows():
            if drone['current_assignment'] != '–':
                drone_assignments.append({
                    'type': 'Drone',
                    'id': drone['drone_id'],
                    'model': drone['model'],
                    'assignment': drone['current_assignment'],
                    'status': drone['status']
                })
        
        return pilot_assignments + drone_assignments
    
    def get_mission_details_with_assignments(self, project_id):
        """Get mission details with assigned pilots and drones"""
        mission = self.data_loader.get_mission_by_id(project_id)
        if mission is None:
            return None
        
        pilots = self.data_loader.get_pilots()
        drones = self.data_loader.get_drones()
        
        assigned_pilots = pilots[pilots['current_assignment'] == project_id]
        assigned_drones = drones[drones['current_assignment'] == project_id]
        
        return {
            'project_id': mission['project_id'],
            'client': mission['client'],
            'location': mission['location'],
            'required_skills': mission['required_skills'],
            'required_certs': mission['required_certs'],
            'start_date': mission['start_date'],
            'end_date': mission['end_date'],
            'priority': mission['priority'],
            'assigned_pilots': assigned_pilots.to_dict('records'),
            'assigned_drones': assigned_drones.to_dict('records')
        }
    
    def assign_pilot_to_mission(self, pilot_id, project_id):
        """Assign pilot to a mission"""
        pilot = self.data_loader.get_pilot_by_id(pilot_id)
        mission = self.data_loader.get_mission_by_id(project_id)
        
        if pilot is None or mission is None:
            return {'success': False, 'message': 'Pilot or Mission not found'}
        
        # Check availability
        if pilot['status'] != 'Available':
            return {'success': False, 'message': f"Pilot {pilot_id} is {pilot['status']}"}
        
        # Update assignment
        result = self.roster_manager.update_pilot_assignment(pilot_id, project_id, 'Assigned')
        return result
    
    def assign_drone_to_mission(self, drone_id, project_id):
        """Assign drone to a mission"""
        drone = self.data_loader.get_drone_by_id(drone_id)
        mission = self.data_loader.get_mission_by_id(project_id)
        
        if drone is None or mission is None:
            return {'success': False, 'message': 'Drone or Mission not found'}
        
        # Check availability
        if drone['status'] != 'Available':
            return {'success': False, 'message': f"Drone {drone_id} is {drone['status']}"}
        
        # Update assignment
        result = self.drone_inventory.assign_drone(drone_id, project_id)
        return result
    
    def reassign_pilot(self, pilot_id, new_project_id):
        """Reassign pilot from current project to new project"""
        pilot = self.data_loader.get_pilot_by_id(pilot_id)
        new_mission = self.data_loader.get_mission_by_id(new_project_id)
        
        if pilot is None or new_mission is None:
            return {'success': False, 'message': 'Pilot or Mission not found'}
        
        old_assignment = pilot['current_assignment']
        
        # Update to new assignment
        result = self.roster_manager.update_pilot_assignment(pilot_id, new_project_id, 'Assigned')
        
        if result['success']:
            return {
                'success': True,
                'message': f'Pilot reassigned from {old_assignment} to {new_project_id}',
                'old_assignment': old_assignment,
                'new_assignment': new_project_id
            }
        return result
    
    def reassign_drone(self, drone_id, new_project_id):
        """Reassign drone to new project"""
        drone = self.data_loader.get_drone_by_id(drone_id)
        new_mission = self.data_loader.get_mission_by_id(new_project_id)
        
        if drone is None or new_mission is None:
            return {'success': False, 'message': 'Drone or Mission not found'}
        
        old_assignment = drone['current_assignment']
        
        # Update to new assignment
        result = self.drone_inventory.assign_drone(drone_id, new_project_id)
        
        if result['success']:
            return {
                'success': True,
                'message': f'Drone reassigned from {old_assignment} to {new_project_id}',
                'old_assignment': old_assignment,
                'new_assignment': new_project_id
            }
        return result
    
    def unassign_pilot(self, pilot_id):
        """Unassign pilot from current project"""
        result = self.roster_manager.mark_pilot_available(pilot_id)
        return result
    
    def unassign_drone(self, drone_id):
        """Unassign drone from current project"""
        result = self.drone_inventory.mark_drone_available(drone_id)
        return result
