import streamlit as st
import rasterio
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import math
import re

# 1. Page Config
st.set_page_config(layout="wide", page_title="Anas Population Pro")

# 2. CSS for Layout
st.markdown("""
    <style>
    .block-container { padding-top: 5rem !important; }
    [data-testid="stMetricValue"] { font-size: 24px; }
    /* Hide the button specifically if any stays */
    div.stButton { display: none; } 
    </style>
    """, unsafe_allow_html=True)

# Session States
if 'marker_pos' not in st.session_state:
    st.session_state.marker_pos = [24.8607, 67.0011]
if 'pop_density' not in st.session_state:
    st.session_state.pop_density = 0.0

def get_density(lat, lon):
    try:
        with rasterio.open('pak_pd_2020_1km.tif') as ds:
            row, col = ds.index(lon, lat)
            data = ds.read(1)
            val = data[row, col]
            return float(val) if val >= 0 and str(val) != 'nan' else 0.0
    except: return 0.0

# 3. SIDEBAR (Radius & Status)
with st.sidebar:
    st.header("📏 Settings")
    selected_km = st.slider("Radius KM", 0.5, 10.0, 1.0, 0.5)
    st.markdown("---")
    st.header("📊 Status")
    area = math.pi * (selected_km ** 2)
    total_pop = int(st.session_state.pop_density * area)
    st.metric("Total Population", f"{total_pop:,}")
    st.write(f"🎓 Primary (5-10): {int(total_pop * 0.15):,}")
    st.write(f"🏫 Secondary (11-16): {int(total_pop * 0.12):,}")
    st.info(f"Coordinates: {st.session_state.marker_pos[0]:.4f}, {st.session_state.marker_pos[1]:.4f}")

# 4. SEARCH LOGIC (Address + Coordinates)
# Label 'Location Search' ko hide rakha hai design ke liye
search_input = st.text_input("Search", placeholder="Type address or lat, lon (e.g. 24.8, 67.0) then press Enter", label_visibility="collapsed")

if search_input:
    # Check if input is Coordinates (e.g., "24.86, 67.01")
    coord_match = re.findall(r"[-+]?\d*\.\d+|\d+", search_input)
    
    if len(coord_match) >= 2:
        # Agar coordinates hain
        try:
            new_lat, new_lon = float(coord_match[0]), float(coord_match[1])
            st.session_state.marker_pos = [new_lat, new_lon]
            st.session_state.pop_density = get_density(new_lat, new_lon)
            st.rerun()
        except:
            st.error("Invalid Coordinates")
    else:
        # Agar address hai
        try:
            geolocator = Nominatim(user_agent="anas_final_app_v2")
            location = geolocator.geocode(search_input)
            if location:
                st.session_state.marker_pos = [location.latitude, location.longitude]
                st.session_state.pop_density = get_density(location.latitude, location.longitude)
                st.rerun()
            else:
                st.error("Location not found!")
        except:
            st.error("Search service busy.")

# 5. MAP AREA
m = folium.Map(location=st.session_state.marker_pos, zoom_start=14)
folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                 attr='Google', name='Google Satellite').add_to(m)

folium.Marker(st.session_state.marker_pos, icon=folium.Icon(color='red')).add_to(m)
folium.Circle(st.session_state.marker_pos, radius=selected_km*1000, color='yellow', fill=True, fill_opacity=0.2).add_to(m)

# Display Map
output = st_folium(m, height=650, use_container_width=True, key="main_map")

# 6. Click Handling
if output['last_clicked']:
    cl_lat, cl_lon = output['last_clicked']['lat'], output['last_clicked']['lng']
    if st.session_state.marker_pos != [cl_lat, cl_lon]:
        st.session_state.marker_pos = [cl_lat, cl_lon]
        st.session_state.pop_density = get_density(cl_lat, cl_lon)
        st.rerun()
