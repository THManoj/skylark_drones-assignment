import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# Import custom modules
from modules.data_loader import DataLoader
from modules.cloud_data_loader import CloudDataLoader
from modules.roster_manager import RosterManager
from modules.drone_inventory import DroneInventory
from modules.assignment_tracker import AssignmentTracker
from modules.conflict_detector import ConflictDetector
from utils.llm_handler import LLMHandler
from utils.sheets_sync import GoogleSheetsSync

# Page configuration
st.set_page_config(
    page_title="Skylark Drones - Operations Coordinator",
    page_icon="🚁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============ DEPLOYMENT MODE DETECTION ============
# Set USE_GOOGLE_SHEETS=true in Replit Secrets to use Google Sheets as backend
USE_GOOGLE_SHEETS = os.environ.get('USE_GOOGLE_SHEETS', 'false').lower() == 'true'
GOOGLE_SHEETS_CREDS = os.environ.get('GOOGLE_SHEETS_CREDENTIALS', '')
SPREADSHEET_ID = os.environ.get('GOOGLE_SPREADSHEET_ID', '')

# Initialize session state
if 'data_loader' not in st.session_state:
    sheets_sync = None
    
    # Try to set up Google Sheets if enabled
    if USE_GOOGLE_SHEETS and GOOGLE_SHEETS_CREDS and SPREADSHEET_ID:
        try:
            sheets_sync = GoogleSheetsSync(GOOGLE_SHEETS_CREDS)
            if sheets_sync.open_spreadsheet(SPREADSHEET_ID):
                st.session_state.sheets_sync = sheets_sync
                st.session_state.data_loader = CloudDataLoader(use_sheets=True, sheets_sync=sheets_sync)
                st.session_state.using_sheets = True
            else:
                raise Exception("Could not open spreadsheet")
        except Exception as e:
            print(f"Google Sheets setup failed: {e}, falling back to CSV")
            st.session_state.data_loader = DataLoader()
            st.session_state.using_sheets = False
    else:
        # Local development - use CSV files
        st.session_state.data_loader = DataLoader()
        st.session_state.sheets_sync = None
        st.session_state.using_sheets = False
    
    st.session_state.roster_manager = RosterManager(st.session_state.data_loader)
    st.session_state.drone_inventory = DroneInventory(st.session_state.data_loader)
    st.session_state.assignment_tracker = AssignmentTracker(
        st.session_state.data_loader,
        st.session_state.roster_manager,
        st.session_state.drone_inventory
    )
    st.session_state.conflict_detector = ConflictDetector(st.session_state.data_loader)
    st.session_state.llm_handler = LLMHandler()

# Sidebar
with st.sidebar:
    st.title("🚁 Skylark Drones")
    st.subheader("Operations Coordinator")
    
    # Show data storage mode
    if st.session_state.get('using_sheets', False):
        st.success("☁️ Cloud Mode (Google Sheets)")
    else:
        st.info("💾 Local Mode (CSV Files)")
    
    page = st.radio(
        "Navigate",
        ["Dashboard", "Roster", "Inventory", "Assignments", "Conflicts", "Chat Assistant", "Settings"]
    )
    
    st.divider()
    st.subheader("Quick Stats")
    
    pilots = st.session_state.data_loader.get_pilots()
    drones = st.session_state.data_loader.get_drones()
    missions = st.session_state.data_loader.get_missions()
    
    available_pilots = len(pilots[pilots['status'] == 'Available'])
    available_drones = len(drones[drones['status'] == 'Available'])
    active_missions = len(missions)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Available Pilots", available_pilots)
        st.metric("Available Drones", available_drones)
    with col2:
        st.metric("Active Missions", active_missions)
        conflicts = st.session_state.conflict_detector.get_conflicts_summary()
        st.metric("Conflicts", conflicts['total_conflicts'])

# Define all page functions
def show_dashboard():
    st.title("📊 Operations Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    
    pilots = st.session_state.data_loader.get_pilots()
    drones = st.session_state.data_loader.get_drones()
    missions = st.session_state.data_loader.get_missions()
    
    with col1:
        st.metric("Total Pilots", len(pilots))
        st.metric("Available", len(pilots[pilots['status'] == 'Available']))
    
    with col2:
        st.metric("Total Drones", len(drones))
        st.metric("Available", len(drones[drones['status'] == 'Available']))
    
    with col3:
        st.metric("Active Missions", len(missions))
        st.metric("Urgent Priority", len(missions[missions['priority'] == 'Urgent']))
    
    with col4:
        conflicts = st.session_state.conflict_detector.get_conflicts_summary()
        st.metric("Total Conflicts", conflicts['total_conflicts'])
        st.metric("Critical Issues", conflicts['critical'])
    
    st.divider()
    
    # Active Assignments
    st.subheader("🔗 Active Assignments")
    assignments = st.session_state.assignment_tracker.get_active_assignments()
    if assignments:
        df = pd.DataFrame(assignments)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No active assignments")
    
    # Recent Conflicts
    st.subheader("⚠️ Detected Conflicts")
    conflicts = st.session_state.conflict_detector.get_all_conflicts()
    if conflicts:
        for conflict in conflicts[:5]:  # Show top 5
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{conflict['type']}**: {conflict['issue']}")
                with col2:
                    severity_color = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🟢'}
                    st.write(f"{severity_color.get(conflict['severity'], '⚪')} {conflict['severity']}")
    else:
        st.success("✅ No conflicts detected!")

def show_roster():
    st.title("👨‍✈️ Pilot Roster Management")
    
    tab1, tab2, tab3 = st.tabs(["View Roster", "Find Pilots", "Update Status"])
    
    with tab1:
        st.subheader("All Pilots")
        pilots = st.session_state.data_loader.get_pilots()
        st.dataframe(pilots, use_container_width=True)
    
    with tab2:
        st.subheader("Find Pilots by Criteria")
        
        search_type = st.selectbox("Search by", ["Skill", "Certification", "Location", "Status"])
        
        if search_type == "Skill":
            skills = ['Mapping', 'Inspection', 'Survey', 'Thermal']
            selected_skill = st.selectbox("Select Skill", skills)
            results = st.session_state.roster_manager.get_pilots_by_skill(selected_skill)
            st.dataframe(results, use_container_width=True)
        
        elif search_type == "Certification":
            certs = ['DGCA', 'Night Ops']
            selected_cert = st.selectbox("Select Certification", certs)
            results = st.session_state.roster_manager.get_pilots_by_certification(selected_cert)
            st.dataframe(results, use_container_width=True)
        
        elif search_type == "Location":
            locations = pilots['location'].unique()
            selected_location = st.selectbox("Select Location", locations)
            results = st.session_state.roster_manager.get_pilots_by_location(selected_location)
            st.dataframe(results, use_container_width=True)
        
        elif search_type == "Status":
            statuses = pilots['status'].unique()
            selected_status = st.selectbox("Select Status", statuses)
            results = st.session_state.roster_manager.get_pilots_by_status(selected_status)
            st.dataframe(results, use_container_width=True)
    
    with tab3:
        st.subheader("Update Pilot Status")
        
        pilots = st.session_state.data_loader.get_pilots()
        pilot_names = {row['name']: row['pilot_id'] for _, row in pilots.iterrows()}
        
        selected_pilot = st.selectbox("Select Pilot", list(pilot_names.keys()))
        pilot_id = pilot_names[selected_pilot]
        
        new_status = st.selectbox("New Status", ["Available", "On Leave", "Assigned", "Unavailable"])
        
        if new_status == "Assigned":
            missions = st.session_state.data_loader.get_missions()
            mission_options = {row['project_id']: row['client'] for _, row in missions.iterrows()}
            selected_mission = st.selectbox("Assign to Mission", list(mission_options.keys()))
            
            if st.button("✅ Update Assignment"):
                result = st.session_state.assignment_tracker.assign_pilot_to_mission(pilot_id, selected_mission)
                if result['success']:
                    st.session_state.data_loader.save_pilots()
                    st.session_state.data_loader.save_missions()
                    st.success(result['message'])
                else:
                    st.error(result['message'])
        
        elif new_status == "On Leave":
            available_from = st.date_input("Available From")
            if st.button("✅ Mark On Leave"):
                result = st.session_state.roster_manager.mark_pilot_on_leave(pilot_id, available_from)
                if result['success']:
                    st.session_state.data_loader.save_pilots()
                    st.success(result['message'])
                else:
                    st.error(result['message'])
        
        else:
            if st.button(f"✅ Mark {new_status}"):
                result = st.session_state.roster_manager.mark_pilot_available(pilot_id)
                if result['success']:
                    st.session_state.data_loader.save_pilots()
                    st.success(result['message'])
                else:
                    st.error(result['message'])

def show_inventory():
    st.title("🚁 Drone Inventory Management")
    
    tab1, tab2, tab3 = st.tabs(["View Fleet", "Find Drones", "Update Status"])
    
    with tab1:
        st.subheader("All Drones")
        drones = st.session_state.data_loader.get_drones()
        st.dataframe(drones, use_container_width=True)
    
    with tab2:
        st.subheader("Find Drones by Criteria")
        
        search_type = st.selectbox("Search by", ["Capability", "Location", "Status", "Maintenance Due"])
        
        if search_type == "Capability":
            capabilities = ['LiDAR', 'RGB', 'Thermal']
            selected_cap = st.selectbox("Select Capability", capabilities)
            results = st.session_state.drone_inventory.get_drones_by_capability(selected_cap)
            st.dataframe(results, use_container_width=True)
        
        elif search_type == "Location":
            drones = st.session_state.data_loader.get_drones()
            locations = drones['location'].unique()
            selected_location = st.selectbox("Select Location", locations)
            results = st.session_state.drone_inventory.get_drones_by_location(selected_location)
            st.dataframe(results, use_container_width=True)
        
        elif search_type == "Status":
            drones = st.session_state.data_loader.get_drones()
            statuses = drones['status'].unique()
            selected_status = st.selectbox("Select Status", statuses)
            results = st.session_state.drone_inventory.get_drones_by_status(selected_status)
            st.dataframe(results, use_container_width=True)
        
        elif search_type == "Maintenance Due":
            maintenance = st.session_state.drone_inventory.get_maintenance_due_soon(30)
            if maintenance:
                df = pd.DataFrame(maintenance)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No maintenance due in next 30 days")
    
    with tab3:
        st.subheader("Update Drone Status")
        
        drones = st.session_state.data_loader.get_drones()
        drone_options = {row['drone_id']: f"{row['model']} ({row['drone_id']})" for _, row in drones.iterrows()}
        
        selected_drone = st.selectbox("Select Drone", list(drone_options.values()))
        drone_id = selected_drone.split('(')[-1].rstrip(')')
        
        new_status = st.selectbox("New Status", ["Available", "Deployed", "Maintenance"])
        
        if new_status == "Deployed":
            missions = st.session_state.data_loader.get_missions()
            mission_options = {row['project_id']: row['client'] for _, row in missions.iterrows()}
            selected_mission = st.selectbox("Deploy to Mission", list(mission_options.keys()))
            
            if st.button("✅ Deploy Drone"):
                result = st.session_state.assignment_tracker.assign_drone_to_mission(drone_id, selected_mission)
                if result['success']:
                    st.session_state.data_loader.save_drones()
                    st.session_state.data_loader.save_missions()
                    st.success(result['message'])
                else:
                    st.error(result['message'])
        
        else:
            if st.button(f"✅ Mark {new_status}"):
                if new_status == "Maintenance":
                    result = st.session_state.drone_inventory.mark_drone_maintenance(drone_id)
                else:
                    result = st.session_state.drone_inventory.mark_drone_available(drone_id)
                if result['success']:
                    st.session_state.data_loader.save_drones()
                    st.success(result['message'])
                else:
                    st.error(result['message'])

def show_assignments():
    st.title("🔗 Assignment Tracking")
    
    tab1, tab2, tab3 = st.tabs(["Active Assignments", "Mission Details", "Reassignments"])
    
    with tab1:
        st.subheader("All Active Assignments")
        assignments = st.session_state.assignment_tracker.get_active_assignments()
        if assignments:
            df = pd.DataFrame(assignments)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No active assignments")
    
    with tab2:
        st.subheader("Mission Details")
        missions = st.session_state.data_loader.get_missions()
        project_options = {row['project_id']: f"{row['client']} ({row['project_id']})" for _, row in missions.iterrows()}
        
        selected_mission = st.selectbox("Select Mission", list(project_options.values()))
        project_id = selected_mission.split('(')[-1].rstrip(')')
        
        details = st.session_state.assignment_tracker.get_mission_details_with_assignments(project_id)
        
        if details:
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Client**: {details['client']}")
                st.write(f"**Location**: {details['location']}")
                st.write(f"**Priority**: {details['priority']}")
            with col2:
                st.write(f"**Start**: {details['start_date']}")
                st.write(f"**End**: {details['end_date']}")
                st.write(f"**Required Skills**: {details['required_skills']}")
                st.write(f"**Required Certifications**: {details['required_certs']}")
            
            st.divider()
            
            if details['assigned_pilots']:
                st.subheader("Assigned Pilots")
                st.dataframe(pd.DataFrame(details['assigned_pilots']), use_container_width=True)
            else:
                st.info("No pilots assigned")
            
            if details['assigned_drones']:
                st.subheader("Assigned Drones")
                st.dataframe(pd.DataFrame(details['assigned_drones']), use_container_width=True)
            else:
                st.info("No drones assigned")
    
    with tab3:
        st.subheader("Reassign Resources")
        
        resource_type = st.selectbox("Resource Type", ["Pilot", "Drone"])
        
        if resource_type == "Pilot":
            pilots = st.session_state.data_loader.get_pilots()
            pilot_options = {row['pilot_id']: f"{row['name']} ({row['pilot_id']})" for _, row in pilots.iterrows()}
            selected_pilot = st.selectbox("Select Pilot", list(pilot_options.values()))
            pilot_id = selected_pilot.split('(')[-1].rstrip(')')
            
            missions = st.session_state.data_loader.get_missions()
            project_options = {row['project_id']: f"{row['client']} ({row['project_id']})" for _, row in missions.iterrows()}
            new_mission = st.selectbox("Reassign to Mission", list(project_options.keys()))
            
            if st.button("✅ Reassign Pilot"):
                result = st.session_state.assignment_tracker.reassign_pilot(pilot_id, new_mission)
                if result['success']:
                    st.session_state.data_loader.save_pilots()
                    st.session_state.data_loader.save_missions()
                    st.success(result['message'])
                else:
                    st.error(result['message'])
        
        else:
            drones = st.session_state.data_loader.get_drones()
            drone_options = {row['drone_id']: f"{row['model']} ({row['drone_id']})" for _, row in drones.iterrows()}
            selected_drone = st.selectbox("Select Drone", list(drone_options.values()))
            drone_id = selected_drone.split('(')[-1].rstrip(')')
            
            missions = st.session_state.data_loader.get_missions()
            project_options = {row['project_id']: f"{row['client']} ({row['project_id']})" for _, row in missions.iterrows()}
            new_mission = st.selectbox("Reassign to Mission", list(project_options.keys()))
            
            if st.button("✅ Reassign Drone"):
                result = st.session_state.assignment_tracker.reassign_drone(drone_id, new_mission)
                if result['success']:
                    st.session_state.data_loader.save_drones()
                    st.session_state.data_loader.save_missions()
                    st.success(result['message'])
                else:
                    st.error(result['message'])

def show_conflicts():
    st.title("⚠️ Conflict Detection & Resolution")
    
    tab1, tab2, tab3 = st.tabs(["All Conflicts", "By Type", "Urgent Reassignments"])
    
    with tab1:
        st.subheader("Detected Conflicts")
        conflicts = st.session_state.conflict_detector.get_all_conflicts()
        
        if conflicts:
            summary = st.session_state.conflict_detector.get_conflicts_summary()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Conflicts", summary['total_conflicts'])
            with col2:
                st.metric("🔴 Critical", summary['critical'])
            with col3:
                st.metric("🟠 High", summary['high'])
            with col4:
                st.metric("🟡 Medium", summary['medium'])
            
            st.divider()
            
            for conflict in conflicts:
                severity_color = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🟢'}
                with st.container(border=True):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"**{conflict['type']}** - {conflict['issue']}")
                    with col2:
                        st.write(f"{severity_color.get(conflict['severity'], '⚪')} {conflict['severity']}")
        else:
            st.success("✅ No conflicts detected!")
    
    with tab2:
        st.subheader("Filter by Conflict Type")
        
        conflict_types = set()
        for conflict in st.session_state.conflict_detector.get_all_conflicts():
            conflict_types.add(conflict['type'])
        
        selected_type = st.selectbox("Conflict Type", sorted(conflict_types))
        
        filtered = [c for c in st.session_state.conflict_detector.get_all_conflicts() if c['type'] == selected_type]
        
        if filtered:
            st.dataframe(pd.DataFrame(filtered), use_container_width=True)
        else:
            st.info(f"No {selected_type} conflicts")
    
    with tab3:
        st.subheader("🚨 Urgent Reassignments")
        
        conflicts = st.session_state.conflict_detector.get_all_conflicts()
        critical_conflicts = [c for c in conflicts if c['severity'] in ['CRITICAL', 'HIGH']]
        
        if critical_conflicts:
            st.warning(f"**{len(critical_conflicts)} critical issues require urgent attention**")
            
            for conflict in critical_conflicts:
                with st.expander(f"{conflict['type']}: {conflict['issue']}", expanded=False):
                    if 'pilot_id' in conflict:
                        pilot_id = conflict['pilot_id']
                        current_mission = conflict.get('assignment', 'Unknown')
                        
                        st.write(f"**Current Assignment**: {current_mission}")
                        
                        # Get available alternatives
                        available_pilots = st.session_state.roster_manager.get_available_pilots()
                        if len(available_pilots) > 0:
                            st.write("**Available Pilots to Reassign**:")
                            st.dataframe(available_pilots[['pilot_id', 'name', 'skills', 'location']], use_container_width=True)
                    
                    if 'drone_id' in conflict:
                        drone_id = conflict['drone_id']
                        current_mission = conflict.get('assignment', 'Unknown')
                        
                        st.write(f"**Current Assignment**: {current_mission}")
                        
                        # Get available alternatives
                        available_drones = st.session_state.drone_inventory.get_available_drones()
                        if len(available_drones) > 0:
                            st.write("**Available Drones to Reassign**:")
                            st.dataframe(available_drones[['drone_id', 'model', 'capabilities', 'location']], use_container_width=True)
        else:
            st.success("✅ No critical issues requiring urgent action")

def show_chat():
    st.title("💬 Chat Assistant")
    st.write("Ask questions about pilot availability, drone status, assignments, conflicts, and more!")
    
    # Display conversation history
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # User input
    user_input = st.chat_input("Ask me anything about drone operations...")
    
    if user_input:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Get context for LLM
        pilots = st.session_state.data_loader.get_pilots()
        drones = st.session_state.data_loader.get_drones()
        
        context = f"""
Current System State:
- Total Pilots: {len(pilots)} ({len(pilots[pilots['status'] == 'Available'])} available)
- Total Drones: {len(drones)} ({len(drones[drones['status'] == 'Available'])} available)
- Active Assignments: {len(st.session_state.assignment_tracker.get_active_assignments())}
- Detected Conflicts: {st.session_state.conflict_detector.get_conflicts_summary()['total_conflicts']}
"""
        
        # Get response from Claude
        with st.chat_message("assistant"):
            response = st.session_state.llm_handler.chat(user_input, context)
            st.markdown(response)
        
        # Add assistant message
        st.session_state.messages.append({"role": "assistant", "content": response})

def show_settings():
    st.title("⚙️ Settings")
    
    tab1, tab2 = st.tabs(["General", "Google Sheets Sync"])
    
    with tab1:
        st.subheader("Application Settings")
        st.info("Settings for Skylark Drone Operations Coordinator")
        
        if st.button("🔄 Reload Data"):
            st.session_state.data_loader = DataLoader()
            st.success("Data reloaded!")
    
    with tab2:
        st.subheader("Google Sheets Integration")
        
        st.write("Set up 2-way sync with Google Sheets to automatically update pilot and drone status.")
        
        spreadsheet_id = st.text_input("Google Spreadsheet ID", placeholder="Paste your spreadsheet ID here")
        
        credentials_json = st.text_area("Google Service Account JSON", placeholder="Paste your service account JSON here")
        
        if st.button("🔗 Connect to Google Sheets"):
            if spreadsheet_id and credentials_json:
                sheets_sync = GoogleSheetsSync(credentials_json)
                if sheets_sync.authenticate(credentials_json):
                    if sheets_sync.open_spreadsheet(spreadsheet_id):
                        st.session_state.sheets_sync = sheets_sync
                        st.success("✅ Connected to Google Sheets!")
                        
                        # Sync data
                        pilots = st.session_state.data_loader.get_pilots()
                        drones = st.session_state.data_loader.get_drones()
                        
                        result1 = sheets_sync.sync_pilots_to_sheet(pilots)
                        result2 = sheets_sync.sync_drones_to_sheet(drones)
                        
                        st.info(f"{result1['message']}\n{result2['message']}")
                    else:
                        st.error("Could not open spreadsheet")
                else:
                    st.error("Authentication failed")
            else:
                st.warning("Please provide both Spreadsheet ID and credentials")

# Page routing - Execute after all functions are defined
if page == "Dashboard":
    show_dashboard()
elif page == "Roster":
    show_roster()
elif page == "Inventory":
    show_inventory()
elif page == "Assignments":
    show_assignments()
elif page == "Conflicts":
    show_conflicts()
elif page == "Chat Assistant":
    show_chat()
elif page == "Settings":
    show_settings()
