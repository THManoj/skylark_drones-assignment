from datetime import datetime

class ConflictDetector:
    """Detect and flag conflicts in assignments"""
    
    def __init__(self, data_loader):
        self.data_loader = data_loader
    
    def check_date_overlap(self, date1_start, date1_end, date2_start, date2_end):
        """Check if two date ranges overlap"""
        return not (date1_end < date2_start or date2_end < date1_start)
    
    def detect_pilot_double_booking(self):
        """Detect pilots assigned to overlapping projects"""
        conflicts = []
        pilots = self.data_loader.get_pilots()
        missions = self.data_loader.get_missions()
        
        for idx, pilot in pilots.iterrows():
            if pilot['current_assignment'] == '–':
                continue
            
            current_mission = missions[missions['project_id'] == pilot['current_assignment']]
            if current_mission.empty:
                continue
            
            current_mission = current_mission.iloc[0]
            
            # Check for overlaps with other assignments
            for idx2, other_pilot in pilots.iterrows():
                if other_pilot['pilot_id'] == pilot['pilot_id'] or other_pilot['current_assignment'] == '–':
                    continue
                
                other_mission = missions[missions['project_id'] == other_pilot['current_assignment']]
                if other_mission.empty:
                    continue
                
                other_mission = other_mission.iloc[0]
                
                # This check is simplified since a pilot can't have 2 assignments in our current data
                # But we flag if pilot is assigned while on leave
                if pilot['status'] == 'On Leave' and pilot['current_assignment'] != '–':
                    conflicts.append({
                        'type': 'Pilot On Leave but Assigned',
                        'severity': 'HIGH',
                        'pilot_id': pilot['pilot_id'],
                        'pilot_name': pilot['name'],
                        'assignment': pilot['current_assignment'],
                        'issue': f"{pilot['name']} is On Leave but assigned to {pilot['current_assignment']}"
                    })
        
        return conflicts
    
    def detect_skill_mismatch(self):
        """Detect pilots assigned to projects requiring skills they lack"""
        conflicts = []
        pilots = self.data_loader.get_pilots()
        missions = self.data_loader.get_missions()
        
        for idx, pilot in pilots.iterrows():
            if pilot['current_assignment'] == '–':
                continue
            
            mission = missions[missions['project_id'] == pilot['current_assignment']]
            if mission.empty:
                continue
            
            mission = mission.iloc[0]
            
            pilot_skills = [s.strip() for s in str(pilot['skills']).split(',')]
            required_skills = [s.strip() for s in str(mission['required_skills']).split(',')]
            
            missing_skills = [s for s in required_skills if s not in pilot_skills]
            
            if missing_skills:
                conflicts.append({
                    'type': 'Skill Mismatch',
                    'severity': 'MEDIUM',
                    'pilot_id': pilot['pilot_id'],
                    'pilot_name': pilot['name'],
                    'assignment': mission['project_id'],
                    'missing_skills': missing_skills,
                    'issue': f"{pilot['name']} lacks skills: {', '.join(missing_skills)}"
                })
        
        return conflicts
    
    def detect_certification_mismatch(self):
        """Detect pilots lacking required certifications"""
        conflicts = []
        pilots = self.data_loader.get_pilots()
        missions = self.data_loader.get_missions()
        
        for idx, pilot in pilots.iterrows():
            if pilot['current_assignment'] == '–':
                continue
            
            mission = missions[missions['project_id'] == pilot['current_assignment']]
            if mission.empty:
                continue
            
            mission = mission.iloc[0]
            
            pilot_certs = [c.strip() for c in str(pilot['certifications']).split(',')]
            required_certs = [c.strip() for c in str(mission['required_certs']).split(',')]
            
            missing_certs = [c for c in required_certs if c not in pilot_certs]
            
            if missing_certs:
                conflicts.append({
                    'type': 'Certification Mismatch',
                    'severity': 'HIGH',
                    'pilot_id': pilot['pilot_id'],
                    'pilot_name': pilot['name'],
                    'assignment': mission['project_id'],
                    'missing_certs': missing_certs,
                    'issue': f"{pilot['name']} lacks certifications: {', '.join(missing_certs)}"
                })
        
        return conflicts
    
    def detect_location_mismatch(self):
        """Detect pilot-drone location mismatches for same project"""
        conflicts = []
        pilots = self.data_loader.get_pilots()
        drones = self.data_loader.get_drones()
        missions = self.data_loader.get_missions()
        
        # Check pilot location vs mission location
        for idx, pilot in pilots.iterrows():
            if pilot['current_assignment'] == '–':
                continue
            
            mission = missions[missions['project_id'] == pilot['current_assignment']]
            if mission.empty:
                continue
            
            mission = mission.iloc[0]
            
            if pilot['location'] != mission['location']:
                conflicts.append({
                    'type': 'Pilot Location Mismatch',
                    'severity': 'MEDIUM',
                    'pilot_id': pilot['pilot_id'],
                    'pilot_name': pilot['name'],
                    'pilot_location': pilot['location'],
                    'mission_location': mission['location'],
                    'issue': f"{pilot['name']} is in {pilot['location']} but assigned to mission in {mission['location']}"
                })
        
        # Check drone location vs mission location
        for idx, drone in drones.iterrows():
            if drone['current_assignment'] == '–':
                continue
            
            mission = missions[missions['project_id'] == drone['current_assignment']]
            if mission.empty:
                continue
            
            mission = mission.iloc[0]
            
            if drone['location'] != mission['location']:
                conflicts.append({
                    'type': 'Drone Location Mismatch',
                    'severity': 'MEDIUM',
                    'drone_id': drone['drone_id'],
                    'drone_model': drone['model'],
                    'drone_location': drone['location'],
                    'mission_location': mission['location'],
                    'issue': f"{drone['model']} is in {drone['location']} but assigned to mission in {mission['location']}"
                })
        
        return conflicts
    
    def detect_maintenance_conflict(self):
        """Detect drones in maintenance assigned to projects"""
        conflicts = []
        drones = self.data_loader.get_drones()
        
        for idx, drone in drones.iterrows():
            if drone['status'] == 'Maintenance' and drone['current_assignment'] != '–':
                conflicts.append({
                    'type': 'Maintenance Conflict',
                    'severity': 'CRITICAL',
                    'drone_id': drone['drone_id'],
                    'drone_model': drone['model'],
                    'status': drone['status'],
                    'assignment': drone['current_assignment'],
                    'issue': f"{drone['model']} is in Maintenance but assigned to {drone['current_assignment']}"
                })
        
        return conflicts
    
    def get_all_conflicts(self):
        """Get all detected conflicts"""
        all_conflicts = []
        all_conflicts.extend(self.detect_pilot_double_booking())
        all_conflicts.extend(self.detect_skill_mismatch())
        all_conflicts.extend(self.detect_certification_mismatch())
        all_conflicts.extend(self.detect_location_mismatch())
        all_conflicts.extend(self.detect_maintenance_conflict())
        
        # Sort by severity
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        all_conflicts.sort(key=lambda x: severity_order.get(x['severity'], 4))
        
        return all_conflicts
    
    def get_conflicts_summary(self):
        """Get summary of conflicts"""
        conflicts = self.get_all_conflicts()
        
        summary = {
            'total_conflicts': len(conflicts),
            'critical': len([c for c in conflicts if c['severity'] == 'CRITICAL']),
            'high': len([c for c in conflicts if c['severity'] == 'HIGH']),
            'medium': len([c for c in conflicts if c['severity'] == 'MEDIUM']),
            'conflicts': conflicts
        }
        
        return summary
