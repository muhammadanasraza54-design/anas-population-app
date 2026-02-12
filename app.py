import streamlit as st
import rasterio
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import math
import re

# 1. Page Config
st.set_page_config(layout="wide", page_title="Anas Population Pro")

# CSS: Design aur Button ko hide karne ke liye
st.markdown("""
    <style>
    .block-container { padding-top: 5rem !important; }
    [data-testid="stMetricValue"] { font-size: 24px; }
    /* Form ka submit button hide kiya taake sirf Enter kaam kare */
    div[data-testid="stForm"] button {
        display: none;
    }
    div[data-testid="stForm"] {
        border: none !important;
        padding: 0px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Session States
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
    st.info(f"📍 Location: {st.session_state.marker_pos[0]:.4f}, {st.session_state.marker_pos[1]:.4f}")

# 4. SEARCH SECTION (Using Form for 'Enter' key support)
with st.form(key='my_search_form', clear_on_submit=True):
    search_input = st.text_input("Search Location", placeholder="Type address or lat, lon then press Enter", label_visibility="collapsed")
    submit_button = st.form_submit_button("Search") # Ye CSS se hidden hai

if submit_button and search_input:
    # Check for Coordinates (e.g. 24.8, 67.1)
    coord_match = re.findall(r"[-+]?\d*\.\d+|\d+", search_input)
    
    if len(coord_match) >= 2:
        try:
            n_lat, n_lon = float(coord_match[0]), float(coord_match[1])
            st.session_state.marker_pos = [n_lat, n_lon]
            st.session_state.pop_density = get_density(n_lat, n_lon)
            st.rerun()
        except: st.error("Invalid Coordinates")
    else:
        # Check for Address
        try:
            geolocator = Nominatim(user_agent="anas_geo_fix")
            location = geolocator.geocode(search_input)
            if location:
                st.session_state.marker_pos = [location.latitude, location.longitude]
                st.session_state.pop_density = get_density(location.latitude, location.longitude)
                st.rerun()
            else:
                st.error("Location not found")
        except: st.error("Service busy, try again")

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
    # Sirf tab update karein agar click coordinates purane wale se different hon
    if abs(st.session_state.marker_pos[0] - cl_lat) > 0.0001:
        st.session_state.marker_pos = [cl_lat, cl_lon]
        st.session_state.pop_density = get_density(cl_lat, cl_lon)
        st.rerun()
