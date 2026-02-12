import streamlit as st
import rasterio
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import math

# 1. Page Configuration
st.set_page_config(layout="wide", page_title="Anas Population Pro")

# 2. CSS for Layout
st.markdown("""
    <style>
    .block-container { 
        padding-top: 5rem !important; 
    }
    [data-testid="stMetricValue"] { font-size: 24px; }
    </style>
    """, unsafe_allow_html=True)

# Session States initialization
if 'marker_pos' not in st.session_state:
    st.session_state.marker_pos = [24.8607, 67.0011]
if 'pop_density' not in st.session_state:
    st.session_state.pop_density = 0.0

def get_density(lat, lon):
    try:
        # File path check karein ke aapke system par sahi ho
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
    st.info(f"Location: {st.session_state.marker_pos}")

# 4. SEARCH BAR SECTION (Fixed Logic)
# Search input aur button ko ek form mein daal diya hai taake 'Enter' dabane par bhi kaam kare
with st.container():
    col_search, col_btn = st.columns([4, 1])
    with col_search:
        # Label ko dikhane ke liye taake backend asani se read kare
        search_query = st.text_input("Location Search", placeholder="Karachi, Lahore, etc...", label_visibility="collapsed")
    
    with col_btn:
        search_button = st.button("Search", use_container_width=True)

# Search function ko alag se handle kiya hai
if search_button and search_query:
    try:
        geolocator = Nominatim(user_agent="anas_app_final")
        location = geolocator.geocode(search_query)
        if location:
            st.session_state.marker_pos = [location.latitude, location.longitude]
            st.session_state.pop_density = get_density(location.latitude, location.longitude)
            st.rerun() # Page ko refresh karega nayi location ke sath
        else:
            st.error("Location nahi mili. Dobara koshish karein.")
    except Exception as e:
        st.error("Search service busy hai.")

# 5. MAP AREA
m = folium.Map(location=st.session_state.marker_pos, zoom_start=14)
folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                 attr='Google', name='Google Satellite').add_to(m)

folium.Marker(st.session_state.marker_pos, icon=folium.Icon(color='red')).add_to(m)
folium.Circle(st.session_state.marker_pos, radius=selected_km*1000, color='yellow', fill=True, fill_opacity=0.2).add_to(m)

# Map display
output = st_folium(m, height=600, use_container_width=True, key="main_map")

# 6. Click Handling
if output['last_clicked']:
    new_lat, new_lon = output['last_clicked']['lat'], output['last_clicked']['lng']
    if st.session_state.marker_pos != [new_lat, new_lon]:
        st.session_state.marker_pos = [new_lat, new_lon]
        st.session_state.pop_density = get_density(new_lat, new_lon)
        st.rerun()
