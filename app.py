import streamlit as st

st.set_page_config(page_title="Skylark Drones", page_icon="🚁", layout="wide")

st.title("🚁 Skylark Drones - Operations Coordinator")
st.success("App is running!")

# Simple test
try:
    import pandas as pd
    st.write("✅ Pandas loaded")
    
    from modules.data_loader import DataLoader
    st.write("✅ DataLoader imported")
    
    data_loader = DataLoader()
    st.write("✅ DataLoader initialized")
    
    pilots = data_loader.get_pilots()
    st.write(f"✅ Loaded {len(pilots)} pilots")
    st.dataframe(pilots)
    
except Exception as e:
    st.error(f"Error: {e}")
    import traceback
    st.code(traceback.format_exc())
