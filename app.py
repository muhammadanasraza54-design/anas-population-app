import streamlit as st
import rasterio
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import math

# 1. Page Config
st.set_page_config(layout="wide", page_title="Anas Population Pro", initial_sidebar_state="collapsed")

# Custom CSS for Side Panel and Top Search
st.markdown("""
    <style>
    header {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    .main > div { padding: 0px !important; }
    .block-container { padding: 0px !important; }
    
    /* Side Panel Container */
    .side-panel {
        position: fixed;
        top: 80px;
        left: 20px;
        width: 280px;
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0px 10px 30px rgba(0,0,0,0.1);
        z-index: 1000;
        border: 1px solid #eee;
    }

    /* Top Search Bar positioning */
    div[data-testid="stForm"] {
        position: fixed;
        top: 15px;
        left: 50%;
        transform: translateX(-50%);
        width: 500px !important;
        z-index: 1001;
        background-color: white;
        padding: 5px 20px;
        border-radius: 50px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.1);
        border: 1px solid #ddd !important;
    }

    /* Slider styling inside panel */
    .stSlider { margin-top: 20px; }
    label { font-weight: bold; color: #333; }
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

# 2. Top Search Bar
with st.form(key='search_form'):
    search_query = st.text_input("", placeholder="🔍 Search location or paste coordinates...", key="query_input")
    submit_button = st.form_submit_button(label='Search', use_container_width=True)

if submit_button and search_query:
    try:
        loc = Nominatim(user_agent="anas_pro").geocode(search_query, timeout=10)
        if loc:
            st.session_state.marker_pos = [loc.latitude, loc.longitude]
            st.session_state.pop_density = get_density(loc.latitude, loc.longitude)
            st.rerun()
    except: st.error("Search Timeout")

# 3. Calculation Logic
# (Note: Radius slider is handled inside the side panel container below)
area = math.pi * (1.0 ** 2) # Default or updated via session state

# 4. Map Setup
m = folium.Map(location=st.session_state.marker_pos, zoom_start=14)
folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                 attr='Google', name='Google Satellite').add_to(m)

p_lat, p_lon = st.session_state.marker_pos
folium.Marker([p_lat, p_lon], icon=folium.Icon(color='red', icon='info-sign')).add_to(m)

# 5. Side Panel UI (Radius + Stats)
with st.container():
    st.markdown('<div class="side-panel">', unsafe_allow_html=True)
    st.markdown("<h3 style='margin:0; color:#d32f2f;'>Anas Analytics</h3>", unsafe_allow_html=True)
    st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)
    
    # Radius Slider inside the Panel
    selected_km = st.slider("Select Radius (KM)", 0.5, 10.0, 1.0, 0.5)
    
    # Recalculate based on slider
    area_new = math.pi * (selected_km ** 2)
    total_pop = int(st.session_state.pop_density * area_new)
    
    # Dynamic Stats Display
    st.write(f"👥 **Total Pop:** {total_pop:,}")
    st.write(f"🎓 **Primary (5-10):** {int(total_pop * 0.15):,}")
    st.write(f"🏫 **Secondary (11-16):** {int(total_pop * 0.12):,}")
    st.write(f"📍 **Density:** {st.session_state.pop_density:.2f}/km²")
    st.markdown('</div>', unsafe_allow_html=True)

# Add Circle to Map
folium.Circle([p_lat, p_lon], radius=selected_km*1000, color='yellow', fill=True, fill_opacity=0.2).add_to(m)

# 6. Display Full Map
st_folium(m, height=900, use_container_width=True, key=f"map_{p_lat}_{selected_km}")
