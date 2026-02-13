import streamlit as st
import rasterio
from rasterio.windows import from_bounds
import math
import numpy as np
import folium
from streamlit_folium import st_folium
from folium.plugins import Geocoder
import os

st.set_page_config(layout="wide", page_title="Anas TCF Tool - Search Enabled")

# 📁 Files Configuration
FILES = {
    'total': 'pak_total_Pop FN.tif',
    'p05': 'pak_Pri_Pop FN.tif',
    'p10': 'pak_Sec_Pop FN.tif'
}

def get_pop_data(lat, lon, rad_km):
    results = {}
    deg_lat = rad_km / 111.0
    deg_lon = rad_km / (111.0 * math.cos(math.radians(lat)))
    left, bottom, right, top = (lon - deg_lon, lat - deg_lat, lon + deg_lon, lat + deg_lat)
    try:
        for key, path in FILES.items():
            if not os.path.exists(path): return None
            with rasterio.open(path) as ds:
                window = from_bounds(left, bottom, right, top, ds.transform)
                data = ds.read(1, window=window)
                results[key] = int(np.nansum(data[data > 0]))
        return results
    except: return None

# Sidebar Setup
st.sidebar.title("TCF Catchment 2025")
radius = st.sidebar.slider("Select Radius (KM)", 0.5, 5.0, 1.0, step=0.5)

if 'pos' not in st.session_state:
    st.session_state.pos = [24.8607, 67.0011] # Default Karachi

data = get_pop_data(st.session_state.pos[0], st.session_state.pos[1], radius)

if data:
    st.sidebar.metric("📊 Total Population", f"{data['total']:,}")
    st.sidebar.write(f"👶 Primary (5-9): **{data['p05']:,}**")
    st.sidebar.write(f"🏫 Secondary (10-14): **{data['p10']:,}**")

# --- MAP SECTION ---
m = folium.Map(location=st.session_state.pos, zoom_start=13)

# Google Satellite Layer
folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attr='Google', name='Satellite', overlay=False
).add_to(m)

# 🔍 Search Bar (Geocoder)
Geocoder(add_marker=True).add_to(m)

# 📍 Red Pin Marker at current position
folium.Marker(
    location=st.session_state.pos,
    icon=folium.Icon(color="red", icon="info-sign")
).add_to(m)

# ⭕ Coverage Circle
folium.Circle(
    location=st.session_state.pos,
    radius=radius * 1000,
    color='red', fill=True, fill_opacity=0.2
).add_to(m)

# Handle interactions
out = st_folium(m, width="100%", height=700)

if out['last_clicked']:
    new_pos = [out['last_clicked']['lat'], out['last_clicked']['lng']]
    if new_pos != st.session_state.pos:
        st.session_state.pos = new_pos
        st.rerun()
