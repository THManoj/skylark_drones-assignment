from datetime import datetime

class ConflictDetector:
    """Detect and flag conflicts in assignments"""
    
    def __init__(self, data_loader):
        self.data_loader = data_loader
    
    def check_date_overlap(self, date1_start, date1_end, date2_start, date2_end):
        """Check if two date ranges overlap"""
        return not (date1_end < date2_start or date2_end < date1_start)
    
    def detect_pilot_double_booking(self):
        """Detect pilots on leave but assigned, or other booking conflicts"""
        conflicts = []
        pilots = self.data_loader.get_pilots()
        missions = self.data_loader.get_missions()
        
        for idx, pilot in pilots.iterrows():
            # Check if pilot is On Leave but has an assignment
            if pilot['status'] == 'On Leave' and pilot['current_assignment'] != '–':
                conflicts.append({
                    'type': 'Pilot On Leave but Assigned',
                    'severity': 'CRITICAL',
                    'pilot_id': pilot['pilot_id'],
                    'pilot_name': pilot['name'],
                    'pilot_status': pilot['status'],
                    'assignment': pilot['current_assignment'],
                    'issue': f"{pilot['name']} is On Leave but assigned to {pilot['current_assignment']}"
                })
            
            # Check if pilot is Unavailable but has an assignment
            if pilot['status'] == 'Unavailable' and pilot['current_assignment'] != '–':
                conflicts.append({
                    'type': 'Pilot Unavailable but Assigned',
                    'severity': 'HIGH',
                    'pilot_id': pilot['pilot_id'],
                    'pilot_name': pilot['name'],
                    'pilot_status': pilot['status'],
                    'assignment': pilot['current_assignment'],
                    'issue': f"{pilot['name']} is Unavailable but assigned to {pilot['current_assignment']}"
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
        all_conflicts.extend(self.detect_urgent_mission_conflicts())
        
        # Remove duplicates based on issue
        seen_issues = set()
        unique_conflicts = []
        for conflict in all_conflicts:
            if conflict['issue'] not in seen_issues:
                seen_issues.add(conflict['issue'])
                unique_conflicts.append(conflict)
        
        # Sort by severity
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        unique_conflicts.sort(key=lambda x: severity_order.get(x['severity'], 4))
        
        return unique_conflicts
    
    def detect_urgent_mission_conflicts(self):
        """Detect urgent/high priority missions with issues"""
        conflicts = []
        missions = self.data_loader.get_missions()
        pilots = self.data_loader.get_pilots()
        
        for idx, mission in missions.iterrows():
            if mission['priority'] in ['Urgent', 'High']:
                # Check if any pilot assigned to this mission is on leave
                assigned_pilots = pilots[pilots['current_assignment'] == mission['project_id']]
                
                for _, pilot in assigned_pilots.iterrows():
                    if pilot['status'] == 'On Leave':
                        conflicts.append({
                            'type': 'Urgent Mission - Pilot On Leave',
                            'severity': 'CRITICAL',
                            'pilot_id': pilot['pilot_id'],
                            'pilot_name': pilot['name'],
                            'pilot_status': pilot['status'],
                            'assignment': mission['project_id'],
                            'priority': mission['priority'],
                            'issue': f"URGENT: {pilot['name']} is On Leave but assigned to {mission['priority']} priority mission {mission['project_id']}"
                        })
        
        return conflicts
    
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
    
    def find_best_replacement_pilot(self, mission_id):
        """Find the best available pilot for a mission"""
        mission = self.data_loader.get_mission_by_id(mission_id)
        if mission is None:
            return None
        
        pilots = self.data_loader.get_pilots()
        available_pilots = pilots[pilots['status'] == 'Available']
        
        # Filter by location
        location_match = available_pilots[available_pilots['location'] == mission['location']]
        
        if location_match.empty:
            return None
        
        required_skills = [s.strip().lower() for s in str(mission['required_skills']).split(',')]
        required_certs = [c.strip().lower() for c in str(mission['required_certs']).split(',')]
        
        best_pilot = None
        best_score = -1
        
        for idx, pilot in location_match.iterrows():
            pilot_skills = [s.strip().lower() for s in str(pilot['skills']).split(',')]
            pilot_certs = [c.strip().lower() for c in str(pilot['certifications']).split(',')]
            
            # Calculate match score
            skill_matches = sum(1 for s in required_skills if s in pilot_skills)
            cert_matches = sum(1 for c in required_certs if c in pilot_certs)
            
            # Require at least base DGCA certification
            if 'dgca' not in pilot_certs:
                continue
            
            score = skill_matches * 2 + cert_matches  # Skills weighted higher
            
            if score > best_score:
                best_score = score
                best_pilot = pilot
        
        return best_pilot
    
    def auto_reassign_urgent_conflicts(self, roster_manager):
        """Automatically reassign for CRITICAL and HIGH severity conflicts"""
        conflicts = self.get_all_conflicts()
        urgent_conflicts = [c for c in conflicts if c['severity'] in ['CRITICAL', 'HIGH']]
        
        reassignments = []
        
        for conflict in urgent_conflicts:
            if 'pilot_id' in conflict and 'assignment' in conflict:
                mission_id = conflict['assignment']
                old_pilot_id = conflict['pilot_id']
                
                # Find replacement
                replacement = self.find_best_replacement_pilot(mission_id)
                
                if replacement is not None:
                    # Perform reassignment
                    new_pilot_id = replacement['pilot_id']
                    
                    # Clear old pilot assignment
                    self.data_loader.update_pilot_status(old_pilot_id, conflict.get('pilot_status', 'On Leave'), '–')
                    
                    # Assign new pilot
                    self.data_loader.update_pilot_status(new_pilot_id, 'Assigned', mission_id)
                    
                    reassignments.append({
                        'conflict': conflict['issue'],
                        'old_pilot': conflict.get('pilot_name', old_pilot_id),
                        'new_pilot': replacement['name'],
                        'new_pilot_id': new_pilot_id,
                        'mission': mission_id,
                        'status': 'SUCCESS',
                        'message': f"✅ Auto-reassigned {mission_id}: {conflict.get('pilot_name', old_pilot_id)} → {replacement['name']}"
                    })
                else:
                    reassignments.append({
                        'conflict': conflict['issue'],
                        'old_pilot': conflict.get('pilot_name', old_pilot_id),
                        'new_pilot': None,
                        'mission': mission_id,
                        'status': 'FAILED',
                        'message': f"❌ No suitable replacement found for {mission_id}"
                    })
        
        return reassignments
