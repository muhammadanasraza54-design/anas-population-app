import streamlit as st
import rasterio
import math
import numpy as np
import folium
from streamlit_folium import st_folium

# Page configuration
st.set_page_config(layout="wide", page_title="Anas TCF - Pakistan 2025")

# 📁 Files ke exact naam jo aapne GitHub Desktop se upload kiye hain
FILES = {
    'total': 'pak_total_Pop_FN.tif',
    'p05': 'pak_Pri_Pop_FN.tif',
    'p10': 'pak_Sec_Pop_FN.tif'
}

def get_pop_data(lat, lon, rad):
    try:
        results = {}
        for key, path in FILES.items():
            # Local file read karna (jo GitHub repo mein hai)
            with rasterio.open(path) as ds:
                # Coordinate ko pixel mein badalna
                row, col = ds.index(lon, lat)
                # Pixel value read karna
                val = ds.read(1)[row, col]
                
                # Null values ya negative ko zero karna
                val = max(0, float(val)) if not np.isnan(val) else 0
                
                # Population Calculation: Value (Density) * Area of Circle
                # Formula: val * pi * r^2
                results[key] = int(val * math.pi * (rad**2))
        return results
    except Exception as e:
        return None

# --- SIDEBAR UI ---
st.sidebar.image("https://www.tcf.org.pk/wp-content/uploads/2019/09/logo.svg", width=150)
st.sidebar.title("TCF Catchment Tool")
st.sidebar.markdown("---")

# Radius Slider
radius = st.sidebar.slider("Select Radius (KM)", 0.5, 5.0, 2.0, step=0.5)

# Initialize position in session state
if 'pos' not in st.session_state:
    st.session_state.pos = [24.8607, 67.0011] # Default: Karachi

# Fetch Data
data = get_pop_data(st.session_state.pos[0], st.session_state.pos[1], radius)

# Display Results
if data:
    st.sidebar.metric("📊 Total Population", f"{data['total']:,}")
    st.sidebar.markdown("---")
    st.sidebar.subheader("Age Segments:")
    st.sidebar.write(f"👶 **Primary (5-9):** {data['p05']:,}")
    st.sidebar.write(f"🏫 **Secondary (10-14):** {data['p10']:,}")
else:
    st.sidebar.error("Data files read nahi ho sakein. File names check karein.")

st.sidebar.markdown("---")
st.sidebar.info(f"Coordinates: {round(st.session_state.pos[0], 4)}, {round(st.session_state.pos[1], 4)}")

# --- MAIN MAP ---
m = folium.Map(location=st.session_state.pos, zoom_start=13, control_scale=True)

# Google Satellite Layer
google_sat = folium.TileLayer(
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
    fill_opacity=0.2,
    popup=f"{radius}KM Catchment"
).add_to(m)

# Handle Map Clicks
map_data = st_folium(m, width="100%", height=750)

if map_data['last_clicked']:
    clicked_lat = map_data['last_clicked']['lat']
    clicked_lng = map_data['last_clicked']['lng']
    
    # Update position and rerun
    if [clicked_lat, clicked_lng] != st.session_state.pos:
        st.session_state.pos = [clicked_lat, clicked_lng]
        st.rerun()
