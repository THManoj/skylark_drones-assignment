from datetime import datetime

class RosterManager:
    """Manage pilot roster operations"""
    
    def __init__(self, data_loader):
        self.data_loader = data_loader
    
    def get_available_pilots(self):
        """Get all available pilots"""
        pilots = self.data_loader.get_pilots()
        return pilots[pilots['status'] == 'Available']
    
    def get_pilots_by_skill(self, skill):
        """Get pilots with specific skill"""
        pilots = self.data_loader.get_pilots()
        # Skills are comma-separated
        matching = []
        for idx, pilot in pilots.iterrows():
            skills = [s.strip() for s in str(pilot['skills']).split(',')]
            if skill in skills:
                matching.append(pilot)
        
        if matching:
            import pandas as pd
            return pd.DataFrame(matching)
        
        import pandas as pd
        return pd.DataFrame()
    
    def get_pilots_by_certification(self, cert):
        """Get pilots with specific certification"""
        pilots = self.data_loader.get_pilots()
        matching = []
        for idx, pilot in pilots.iterrows():
            certs = [c.strip() for c in str(pilot['certifications']).split(',')]
            if cert in certs:
                matching.append(pilot)
        
        if matching:
            import pandas as pd
            return pd.DataFrame(matching)
        
        import pandas as pd
        return pd.DataFrame()
    
    def get_pilots_by_location(self, location):
        """Get pilots in specific location"""
        pilots = self.data_loader.get_pilots()
        return pilots[pilots['location'] == location]
    
    def get_pilots_by_status(self, status):
        """Get pilots by status (Available/On Leave/Assigned/Unavailable)"""
        pilots = self.data_loader.get_pilots()
        return pilots[pilots['status'] == status]
    
    def get_pilot_details(self, pilot_id):
        """Get detailed info for a pilot"""
        pilot = self.data_loader.get_pilot_by_id(pilot_id)
        if pilot is not None:
            return {
                'id': pilot['pilot_id'],
                'name': pilot['name'],
                'skills': pilot['skills'],
                'certifications': pilot['certifications'],
                'location': pilot['location'],
                'status': pilot['status'],
                'current_assignment': pilot['current_assignment'],
                'available_from': pilot['available_from']
            }
        return None
    
    def find_best_pilot_for_mission(self, required_skills, required_certs, location):
        """Find best pilot match for mission requirements"""
        pilots = self.data_loader.get_pilots()
        available = pilots[pilots['status'] == 'Available']
        
        best_matches = []
        for idx, pilot in available.iterrows():
            # Check skills
            pilot_skills = [s.strip() for s in str(pilot['skills']).split(',')]
            pilot_certs = [c.strip() for c in str(pilot['certifications']).split(',')]
            
            required_skills_list = [s.strip() for s in str(required_skills).split(',')]
            required_certs_list = [c.strip() for c in str(required_certs).split(',')]
            
            skill_match = sum(1 for skill in required_skills_list if skill in pilot_skills)
            cert_match = sum(1 for cert in required_certs_list if cert in pilot_certs)
            location_match = 1 if pilot['location'] == location else 0
            
            if skill_match > 0 and cert_match == len(required_certs_list):
                score = skill_match * 2 + cert_match * 1.5 + location_match * 0.5
                best_matches.append({
                    'pilot_id': pilot['pilot_id'],
                    'name': pilot['name'],
                    'score': score,
                    'skills_match': skill_match,
                    'cert_match': cert_match,
                    'location_match': location_match
                })
        
        # Sort by score descending
        best_matches.sort(key=lambda x: x['score'], reverse=True)
        return best_matches
    
    def update_pilot_assignment(self, pilot_id, project_id, status='Assigned'):
        """Assign pilot to a project"""
        success = self.data_loader.update_pilot_status(pilot_id, status, project_id)
        if success:
            return {'success': True, 'message': f'Pilot {pilot_id} assigned to {project_id}'}
        return {'success': False, 'message': f'Pilot {pilot_id} not found'}
    
    def mark_pilot_on_leave(self, pilot_id, available_from_date):
        """Mark pilot as on leave"""
        success = self.data_loader.update_pilot_status(pilot_id, 'On Leave', '–', available_from_date)
        if success:
            return {'success': True, 'message': f'Pilot {pilot_id} marked on leave'}
        return {'success': False, 'message': f'Pilot {pilot_id} not found'}
    
    def mark_pilot_available(self, pilot_id):
        """Mark pilot as available"""
        success = self.data_loader.update_pilot_status(pilot_id, 'Available', '–')
        if success:
            return {'success': True, 'message': f'Pilot {pilot_id} marked available'}
        return {'success': False, 'message': f'Pilot {pilot_id} not found'}
