import streamlit as st
import rasterio
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import re

st.set_page_config(layout="wide")
st.title("Anas Ghouri - Population Finder & Search")

# 1. Memory setup taake marker aur circle gayab na hon
if 'marker_pos' not in st.session_state:
    st.session_state.marker_pos = None

# Default location (Karachi)
start_lat, start_lon = 24.8607, 67.0011

search_query = st.text_input("Search (Place or Coordinates):")

if search_query:
    coord_match = re.findall(r"[-+]?\d*\.\d+|\d+", search_query)
    if len(coord_match) >= 2:
        start_lat, start_lon = float(coord_match[0]), float(coord_match[1])
        st.session_state.marker_pos = [start_lat, start_lon] # Search par pin set
    else:
        try:
            geolocator = Nominatim(user_agent="anas_app_final")
            location = geolocator.geocode(search_query, timeout=10)
            if location:
                start_lat, start_lon = location.latitude, location.longitude
                st.session_state.marker_pos = [start_lat, start_lon] # Search par pin set
        except:
            st.warning("Search service busy.")

# 2. Map Setup
m = folium.Map(location=[start_lat, start_lon], zoom_start=14)
folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attr='Google', name='Google Satellite'
).add_to(m)

# 3. Pin aur Circle lagana (Agar coordinate select hua ho)
if st.session_state.marker_pos:
    p_lat, p_lon = st.session_state.marker_pos
    # Red Pin
    folium.Marker([p_lat, p_lon], tooltip="Selected Location", icon=folium.Icon(color='red', icon='info-sign')).add_to(m)
    # 500 meter ka Circle
    folium.Circle(
        location=[p_lat, p_lon],
        radius=500, # 500 meters
        color='yellow',
        fill=True,
        fill_opacity=0.2
    ).add_to(m)

# Display Map
output = st_folium(m, height=600, use_container_width=True, key=f"map_{start_lat}")

# 4. Click handle karna
if output['last_clicked']:
    lat, lon = output['last_clicked']['lat'], output['last_clicked']['lng']
    st.session_state.marker_pos = [lat, lon] # Click par pin update
    
    try:
        with rasterio.open('pak_pd_2020_1km.tif') as ds:
            row, col = ds.index(lon, lat)
            data = ds.read(1)
            pop = round(float(data[row, col]), 2)
            st.success(f"📍 Coordinates: {lat}, {lon} | 👥 Population: {pop}")
            st.rerun() # Screen refresh taake marker fauran nazar aaye
    except:
        st.error("Data not available.")
