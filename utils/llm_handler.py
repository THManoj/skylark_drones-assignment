import os

def get_groq_api_key():
    """Get Groq API key from Streamlit secrets or environment"""
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and 'GROQ_API_KEY' in st.secrets:
            return st.secrets['GROQ_API_KEY']
    except:
        pass
    return os.getenv('GROQ_API_KEY')

class LLMHandler:
    """Handle conversational interface with Groq LLM"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or get_groq_api_key()
        self.client = None
        self.conversation_history = []
        
        # Try to initialize Groq client
        try:
            from groq import Groq
            if self.api_key:
                self.client = Groq(api_key=self.api_key)
            else:
                self.client = None
        except Exception as e:
            print(f"Warning: Could not initialize Groq client: {e}")
            self.client = None
    
    def get_system_prompt(self):
        """Get system prompt for the conversational agent"""
        return """You are a Drone Operations Coordinator AI Assistant. You help manage a drone operations fleet coordinating pilots, drones, missions, and resource allocation.

Your capabilities include:
1. **Roster Management**: Query pilot availability by skill, certification, location. View/update pilot status.
2. **Assignment Tracking**: Match pilots/drones to projects, track active assignments, handle reassignments.
3. **Drone Inventory**: Query fleet by capability, track deployment status, flag maintenance issues.
4. **Conflict Detection**: Identify double-bookings, skill mismatches, location issues, maintenance conflicts.
5. **Urgent Reassignments**: Help coordinate urgent resource reallocations when conflicts arise.

When users ask about operations, provide helpful analysis and suggestions. Be concise but thorough.

Always maintain context about the operational state and provide actionable recommendations.

Available commands you can reference:
- "Show available pilots"
- "Show available drones"
- "Find pilot for [skill/location]"
- "Find drone for [capability/location]"
- "Assign [pilot/drone] to [mission]"
- "Check conflicts"
- "Suggest reassignments for [issue]"
- "Update [pilot/drone] status"

Format your responses clearly with sections when needed."""
    
    def chat(self, user_message, context_data=None):
        """Send a message and get a response from Groq"""
        # Check if client is available
        if self.client is None:
            return "⚠️ **AI Assistant Unavailable**\n\nThe Groq AI assistant is not configured. Please set your `GROQ_API_KEY` environment variable to enable the chat feature.\n\nYou can still use all other features of the application through the sidebar navigation."
        
        try:
            # Add context if available
            if context_data:
                context_prompt = f"\n\n[Current System State]\n{context_data}"
                full_message = user_message + context_prompt
            else:
                full_message = user_message
            
            # Build messages with system prompt
            messages = [
                {"role": "system", "content": self.get_system_prompt()}
            ]
            
            # Add conversation history
            for msg in self.conversation_history:
                messages.append(msg)
            
            # Add current user message
            messages.append({
                "role": "user",
                "content": full_message
            })
            
            # Get response from Groq (using Llama 3.3 70B)
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                max_tokens=1024,
                temperature=0.7
            )
            
            assistant_message = response.choices[0].message.content
            
            # Add to conversation history
            self.conversation_history.append({
                "role": "user",
                "content": full_message
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })
            
            return assistant_message
        
        except Exception as e:
            return f"Error communicating with AI: {str(e)}"
    
    def reset_conversation(self):
        """Reset conversation history"""
        self.conversation_history = []
    
    def parse_intent(self, user_message):
        """Parse user intent to route to appropriate handler"""
        intents = {
            'roster': ['pilot', 'available', 'skill', 'certification', 'location'],
            'inventory': ['drone', 'fleet', 'capability', 'maintenance', 'model'],
            'assignment': ['assign', 'match', 'project', 'mission', 'reassign'],
            'conflict': ['conflict', 'overlap', 'mismatch', 'issue', 'problem'],
            'status': ['status', 'update', 'change', 'mark']
        }
        
        message_lower = user_message.lower()
        detected_intents = []
        
        for intent, keywords in intents.items():
            if any(keyword in message_lower for keyword in keywords):
                detected_intents.append(intent)
        
        return detected_intents if detected_intents else ['general']
    
    def format_context_for_chat(self, roster_summary, inventory_summary, assignment_summary, conflict_summary):
        """Format operational context for the LLM"""
        context = f"""
Current Operational State:
- Available Pilots: {roster_summary.get('available_count', 0)}
- Pilots on Leave: {roster_summary.get('on_leave_count', 0)}
- Available Drones: {inventory_summary.get('available_count', 0)}
- Drones in Maintenance: {inventory_summary.get('maintenance_count', 0)}
- Active Assignments: {assignment_summary.get('total_assignments', 0)}
- Detected Conflicts: {conflict_summary.get('total_conflicts', 0)} ({conflict_summary.get('critical', 0)} critical, {conflict_summary.get('high', 0)} high)
"""
        return context
