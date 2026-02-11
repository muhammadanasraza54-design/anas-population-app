import streamlit as st
import rasterio
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import re

# 1. Page Configuration
st.set_page_config(layout="wide", page_title="Anas Ghouri - Population Finder")

st.title("🌍 Anas Ghouri - Population Finder & Search")

# 2. State Management (Memory)
if 'marker_pos' not in st.session_state:
    st.session_state.marker_pos = None
if 'pop_result' not in st.session_state:
    st.session_state.pop_result = ""

# Function to get population from TIF file
def get_pop(lat, lon):
    try:
        with rasterio.open('pak_pd_2020_1km.tif') as ds:
            row, col = ds.index(lon, lat)
            data = ds.read(1)
            val = data[row, col]
            if val < 0 or str(val) == 'nan':
                return "Data not available here (Water/Empty)."
            return f"Coordinates: {round(lat, 4)}, {round(lon, 4)} | 👥 Population: {round(float(val), 2)}"
    except:
        return "Outside data coverage."

# 3. Search Bar Logic
search_query = st.text_input("Search Location (City or Coordinates):")

start_lat, start_lon = 24.8607, 67.0011 # Default Karachi

if search_query:
    coord_match = re.findall(r"[-+]?\d*\.\d+|\d+", search_query)
    if len(coord_match) >= 2:
        s_lat, s_lon = float(coord_match[0]), float(coord_match[1])
        st.session_state.marker_pos = [s_lat, s_lon]
        st.session_state.pop_result = get_pop(s_lat, s_lon)
    else:
        try:
            geolocator = Nominatim(user_agent="anas_app_final")
            location = geolocator.geocode(search_query, timeout=10)
            if location:
                st.session_state.marker_pos = [location.latitude, location.longitude]
                st.session_state.pop_result = get_pop(location.latitude, location.longitude)
        except:
            st.warning("Search service busy.")

# 4. Map Setup
if st.session_state.marker_pos:
    start_lat, start_lon = st.session_state.marker_pos

m = folium.Map(location=[start_lat, start_lon], zoom_start=14)
folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attr='Google', name='Google Satellite'
).add_to(m)

if st.session_state.marker_pos:
    p_lat, p_lon = st.session_state.marker_pos
    folium.Marker([p_lat, p_lon], icon=folium.Icon(color='red')).add_to(m)
    folium.Circle([p_lat, p_lon], radius=500, color='yellow', fill=True, fill_opacity=0.3).add_to(m)

# 5. Map Display
# Note: dynamic key used to force map movement on search
output = st_folium(m, height=600, use_container_width=True, key=f"map_{start_lat}_{start_lon}")

# 6. Click Handling - Update result when clicking
if output['last_clicked']:
    c_lat, c_lon = output['last_clicked']['lat'], output['last_clicked']['lng']
    # Check if this is a NEW click (to avoid infinite refresh)
    if st.session_state.marker_pos != [c_lat, c_lon]:
        st.session_state.marker_pos = [c_lat, c_lon]
        st.session_state.pop_result = get_pop(c_lat, c_lon)
        st.rerun()

# 7. Final Result Display
if st.session_state.pop_result:
    if "Data not available" in st.session_state.pop_result:
        st.warning(st.session_state.pop_result)
    else:
        st.success(st.session_state.pop_result)
