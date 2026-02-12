import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import rasterio
import math
import os
import re
from math import radians, cos, sin, asin, sqrt

# --- 1. CONFIG ---
st.set_page_config(layout="wide", page_title="Anas Population Pro")

# Distance calculation function
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dLat, dLon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dLat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dLon/2)**2
    return 2 * asin(sqrt(a)) * R

# Population Density function using your TIF file
def get_density(lat, lon):
    try:
        # Anas, ensure 'pak_pd_2020_1km.tif' is in your GitHub folder
        with rasterio.open('pak_pd_2020_1km.tif') as ds:
            row, col = ds.index(lon, lat)
            data = ds.read(1)
            val = data[row, col]
            return float(val) if val >= 0 and not math.isnan(val) else 0.0
    except: 
        return 0.0

# --- 2. SESSION STATE ---
if 'marker_pos' not in st.session_state:
    st.session_state.marker_pos = [24.8607, 67.0011] # Karachi Default

# --- 3. SIDEBAR (Analytics) ---
with st.sidebar:
    st.image("https://www.tcf.org.pk/wp-content/uploads/2019/09/logo.svg", width=150)
    st.header("📊 Population Analytics")
    
    # Radius slider
    radius_km = st.slider("Search Radius (KM)", 0.5, 10.0, 2.0)
    
    # Calculate Results
    density = get_density(st.session_state.marker_pos[0], st.session_state.marker_pos[1])
    total_pop = int(density * (math.pi * radius_km**2))
    
    # Display Stats
    st.metric("Total Population", f"{total_pop:,}")
    st.write(f"👶 Primary Age (5-10): {int(total_pop * 0.15):,}")
    st.write(f"🏫 Secondary Age (11-16): {int(total_pop * 0.12):,}")
    
    st.markdown("---")
    st.info(f"Current Lat: {st.session_state.marker_pos[0]:.4f}\n\nLon: {st.session_state.marker_pos[1]:.4f}")

# --- 4. MAIN INTERFACE ---
st.subheader("📍 Click on Map to Check Population")

# Search Bar
search_input = st.text_input("🔍 Search Coordinates (Lat, Lon)", placeholder="e.g. 24.89, 67.15")
if search_input:
    coord_match = re.findall(r"[-+]?\d*\.\d+|\d+", search_input)
    if len(coord_match) >= 2:
        st.session_state.marker_pos = [float(coord_match[0]), float(coord_match[1])]

# --- 5. MAP CONSTRUCTION (No School Pins) ---
# Map build with satellite view
m = folium.Map(location=st.session_state.marker_pos, zoom_start=13)

folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attr='Google', name='Google Satellite', overlay=False
).add_to(m)

# Red Circle for Area
folium.Circle(
    st.session_state.marker_pos, 
    radius=radius_km*1000, 
    color='red', fill=True, fill_opacity=0.15,
    tooltip="Analysis Area"
).add_to(m)

# Single Target Marker (Center)
folium.Marker(
    st.session_state.marker_pos, 
    icon=folium.Icon(color='red', icon='crosshairs', prefix='fa')
).add_to(m)

# Display Map
map_output = st_folium(m, width="100%", height=600)

# Click to update location
if map_output['last_clicked']:
    new_lat = map_output['last_clicked']['lat']
    new_lon = map_output['last_clicked']['lng']
    if [new_lat, new_lon] != st.session_state.marker_pos:
        st.session_state.marker_pos = [new_lat, new_lon]
        st.rerun()
