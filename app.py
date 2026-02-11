import streamlit as st
import rasterio
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import re
import math

# 1. Page Configuration
st.set_page_config(layout="wide", page_title="Anas Ghouri - Population Analyzer")

st.title("🌍 Anas Ghouri - Population Finder & Area Analyzer")

# 2. State Management
if 'marker_pos' not in st.session_state:
    st.session_state.marker_pos = None
if 'pop_density' not in st.session_state:
    st.session_state.pop_density = 0.0
if 'zoom_level' not in st.session_state:
    st.session_state.zoom_level = 13 # Default zoom

# Sidebar Settings
st.sidebar.header("Settings")
selected_km = st.sidebar.slider("Select Radius (KM):", min_value=0.5, max_value=10.0, value=1.0, step=0.5)
radius_meters = selected_km * 1000

def get_density(lat, lon):
    try:
        with rasterio.open('pak_pd_2020_1km.tif') as ds:
            row, col = ds.index(lon, lat)
            data = ds.read(1)
            val = data[row, col]
            return float(val) if val >= 0 and str(val) != 'nan' else 0.0
    except:
        return 0.0

# 3. Search Logic
search_query = st.text_input("Search Place or Coordinates:")
start_lat, start_lon = 24.8607, 67.0011

if search_query:
    coord_match = re.findall(r"[-+]?\d*\.\d+|\d+", search_query)
    if len(coord_match) >= 2:
        s_lat, s_lon = float(coord_match[0]), float(coord_match[1])
        st.session_state.marker_pos = [s_lat, s_lon]
        st.session_state.zoom_level = 16 # Search par zoom barhayein
        st.session_state.pop_density = get_density(s_lat, s_lon)
    else:
        try:
            geolocator = Nominatim(user_agent="anas_final_app")
            location = geolocator.geocode(search_query, timeout=10)
            if location:
                st.session_state.marker_pos = [location.latitude, location.longitude]
                st.session_state.zoom_level = 16
                st.session_state.pop_density = get_density(location.latitude, location.longitude)
        except:
            st.sidebar.warning("Search service busy.")

# 4. Map Setup
if st.session_state.marker_pos:
    start_lat, start_lon = st.session_state.marker_pos

m = folium.Map(location=[start_lat, start_lon], zoom_start=st.session_state.zoom_level)

# Feature 1: Full Screen Button
from folium.plugins import Fullscreen
Fullscreen(position='topright', title='Full Screen', title_cancel='Exit', force_separate_button=True).add_to(m)

folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attr='Google', name='Google Satellite'
).add_to(m)

if st.session_state.marker_pos:
    p_lat, p_lon = st.session_state.marker_pos
    folium.Marker([p_lat, p_lon], icon=folium.Icon(color='red')).add_to(m)
    folium.Circle([p_lat, p_lon], radius=radius_meters, color='yellow', fill=True, fill_opacity=0.3).add_to(m)

# 5. Map Display
output = st_folium(m, height=650, use_container_width=True, key=f"map_{start_lat}_{st.session_state.zoom_level}")

# Feature 2: Click to Zoom Logic
if output['last_clicked']:
    c_lat, c_lon = output['last_clicked']['lat'], output['last_clicked']['lng']
    if st.session_state.marker_pos != [c_lat, c_lon]:
        st.session_state.marker_pos = [c_lat, c_lon]
        st.session_state.zoom_level = 16 # Click karne par zoom level 16 kar dein
        st.session_state.pop_density = get_density(c_lat, c_lon)
        st.rerun()

# 6. Stats Display
if st.session_state.marker_pos:
    area_sq_km = math.pi * (selected_km ** 2)
    total_est_pop = int(st.session_state.pop_density * area_sq_km)
    
    st.write("---")
    col1, col2, col3 = st.columns(3)
    col1.metric("Selected Radius", f"{selected_km} KM")
    col2.metric("Avg. Density", f"{round(st.session_state.pop_density, 2)} /km²")
    col3.metric("Est. Total Population", f"{total_est_pop:,}")
