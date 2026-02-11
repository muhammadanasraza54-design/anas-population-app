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

# 2. State Management (Memory)
if 'marker_pos' not in st.session_state:
    st.session_state.marker_pos = None
if 'pop_density' not in st.session_state:
    st.session_state.pop_density = 0.0

# 3. Sidebar for Manual Settings
st.sidebar.header("Settings")
# User yahan se radius select kar sakta hai (0.5 KM se 10 KM tak)
selected_km = st.sidebar.slider("Select Radius (KM):", min_value=0.5, max_value=10.0, value=1.0, step=0.5)
radius_meters = selected_km * 1000

# Function to get population density
def get_density(lat, lon):
    try:
        with rasterio.open('pak_pd_2020_1km.tif') as ds:
            row, col = ds.index(lon, lat)
            data = ds.read(1)
            val = data[row, col]
            if val < 0 or str(val) == 'nan':
                return 0.0
            return float(val)
    except:
        return 0.0

# 4. Search Bar Logic
search_query = st.text_input("Search Place or Coordinates (e.g., Lahore or 24.8, 67.0):")
start_lat, start_lon = 24.8607, 67.0011 # Default

if search_query:
    coord_match = re.findall(r"[-+]?\d*\.\d+|\d+", search_query)
    if len(coord_match) >= 2:
        s_lat, s_lon = float(coord_match[0]), float(coord_match[1])
        st.session_state.marker_pos = [s_lat, s_lon]
        st.session_state.pop_density = get_density(s_lat, s_lon)
    else:
        try:
            geolocator = Nominatim(user_agent="anas_advanced_app")
            location = geolocator.geocode(search_query, timeout=10)
            if location:
                st.session_state.marker_pos = [location.latitude, location.longitude]
                st.session_state.pop_density = get_density(location.latitude, location.longitude)
        except:
            st.sidebar.error("Search service busy.")

# 5. Map Setup
if st.session_state.marker_pos:
    start_lat, start_lon = st.session_state.marker_pos

m = folium.Map(location=[start_lat, start_lon], zoom_start=13)
folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attr='Google', name='Google Satellite'
).add_to(m)

# 6. Marker & Dynamic Circle
if st.session_state.marker_pos:
    p_lat, p_lon = st.session_state.marker_pos
    folium.Marker([p_lat, p_lon], icon=folium.Icon(color='red', icon='info-sign')).add_to(m)
    
    # Circle jo user ke select kiye huay KM ke mutabiq banega
    folium.Circle(
        location=[p_lat, p_lon],
        radius=radius_meters,
        color='yellow',
        fill=True,
        fill_opacity=0.3
    ).add_to(m)

# 7. Map Display
output = st_folium(m, height=550, use_container_width=True, key=f"map_{start_lat}_{selected_km}")

# 8. Click Handling
if output['last_clicked']:
    c_lat, c_lon = output['last_clicked']['lat'], output['last_clicked']['lng']
    if st.session_state.marker_pos != [c_lat, c_lon]:
        st.session_state.marker_pos = [c_lat, c_lon]
        st.session_state.pop_density = get_density(c_lat, c_lon)
        st.rerun()

# 9. Automatic Calculation & Display
if st.session_state.marker_pos:
    # Area of circle = π * r²
    area_sq_km = math.pi * (selected_km ** 2)
    # Total Population = Density * Area
    total_est_pop = int(st.session_state.pop_density * area_sq_km)
    
    st.write("---")
    col1, col2, col3 = st.columns(3)
    col1.metric("Selected Radius", f"{selected_km} KM")
    col2.metric("Avg. Density", f"{round(st.session_state.pop_density, 2)} /km²")
    col3.metric("Est. Total Population", f"{total_est_pop:,}")
    
    st.info(f"💡 Is {selected_km} KM ke circle mein takreeban {total_est_pop:,} log maujood hain.")
