import streamlit as st
import rasterio
import math
import numpy as np
import folium
from streamlit_folium import st_folium
import os

# Page configuration
st.set_page_config(layout="wide", page_title="Anas TCF Population Tool")

# 📁 Files ke exact naam (Spaces confirm karein jo aapke GitHub par hain)
FILES = {
    'total': 'pak_total_Pop FN.tif',
    'p05': 'pak_Pri_Pop FN.tif',
    'p10': 'pak_Sec_Pop FN.tif'
}

def get_pop_data(lat, lon, rad):
    results = {}
    try:
        for key, path in FILES.items():
            if not os.path.exists(path):
                return f"Error: File '{path}' nahi mili."
            
            with rasterio.open(path) as ds:
                # Coordinate ko pixel index mein badalna
                row, col = ds.index(lon, lat)
                
                # Check if click is inside the map bounds
                if 0 <= row < ds.height and 0 <= col < ds.width:
                    # Sirf click wala pixel read karna
                    window = ds.read(1, window=((row, row+1), (col, col+1)))
                    val = window[0, 0]
                    val = max(0, float(val)) if not np.isnan(val) else 0
                    
                    # Area-based calculation (Scaling for Karachi/Urban density)
                    area_sq_km = math.pi * (rad**2)
                    # Note: WorldPop pixels are approx 100m. 
                    # Scaling by 100 helps align with urban density expectations.
                    results[key] = int(val * area_sq_km * 100)
                else:
                    results[key] = 0
        return results
    except Exception as e:
        return f"Technical Error: {str(e)}"

# --- SIDEBAR UI ---
st.sidebar.title("TCF Catchment 2025")
st.sidebar.markdown("---")

# Radius Slider
radius = st.sidebar.slider("Select Radius (KM)", 0.5, 5.0, 2.0, step=0.5)

# Initialize location
if 'pos' not in st.session_state:
    st.session_state.pos = [24.8607, 67.0011] # Karachi default

# Get Data
data = get_pop_data(st.session_state.pos[0], st.session_state.pos[1], radius)

# Display Results
if isinstance(data, dict):
    st.sidebar.metric("📊 Total Population", f"{data['total']:,}")
    st.sidebar.markdown("---")
    st.sidebar.subheader("Age Segments:")
    st.sidebar.write(f"👶 **Primary (5-9):** {data['p05']:,}")
    st.sidebar.write(f"🏫 **Secondary (10-14):** {data['p10']:,}")
else:
    st.sidebar.error(data)

st.sidebar.markdown("---")
st.sidebar.info(f"Lat: {round(st.session_state.pos[0], 4)}, Lon: {round(st.session_state.pos[1], 4)}")

# --- MAP SECTION ---
m = folium.Map(location=st.session_state.pos, zoom_start=13)

# Google Satellite Layer
folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attr='Google',
    name='Google Satellite',
    overlay=False,
    control=True
).add_to(m)

# Circle on Map
folium.Circle(
    location=st.session_state.pos,
    radius=radius * 1000,
    color='red',
    fill=True,
    fill_opacity=0.2
).add_to(m)

# Map click handler
map_output = st_folium(m, width="100%", height=750)

if map_output['last_clicked']:
    new_lat = map_output['last_clicked']['lat']
    new_lng = map_output['last_clicked']['lng']
    
    if [new_lat, new_lng] != st.session_state.pos:
        st.session_state.pos = [new_lat, new_lng]
        st.rerun()
