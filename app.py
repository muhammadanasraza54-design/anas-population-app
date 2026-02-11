import streamlit as st
import rasterio
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import math

# 1. Page Config
st.set_page_config(layout="wide", page_title="Anas Population Pro", initial_sidebar_state="collapsed")

# 2. CSS: Search Bar ko Header mein fit karne ke liye
st.markdown("""
    <style>
    header {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    .main > div { padding: 0px !important; }
    .block-container { padding: 0px !important; }
    
    /* Search Bar: Top Header Style */
    .search-container {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 60px;
        background: white;
        z-index: 999999;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.1);
        padding: 0 20px;
    }
    
    /* Input box width fix */
    div[data-testid="stTextInput"] {
        width: 500px !important;
        margin-bottom: 0px !important;
    }

    /* Anas Analytics Panel (Left side) */
    .stats-card {
        position: fixed;
        top: 80px;
        left: 20px;
        width: 220px;
        background: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.2);
        z-index: 99999;
        border-top: 4px solid #d32f2f;
    }

    /* Hide redundant elements */
    [data-testid="stVerticalBlock"] { gap: 0rem; }
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

# 3. TOP SEARCH BAR (Fixed at very top)
st.markdown('<div class="search-container">', unsafe_allow_html=True)
col1, col2 = st.columns([4, 1])
with col1:
    search_query = st.text_input("", placeholder="🔍 Search Place (e.g. Karachi)...", key="nav_search", label_visibility="collapsed")
with col2:
    if st.button("Search Location"):
        if search_query:
            try:
                loc = Nominatim(user_agent="anas_v3").geocode(search_query)
                if loc:
                    st.session_state.marker_pos = [loc.latitude, loc.longitude]
                    st.session_state.pop_density = get_density(loc.latitude, loc.longitude)
                    st.rerun()
            except: st.error("Error")
st.markdown('</div>', unsafe_allow_html=True)

# 4. STATS & RADIUS (Left Side Floating)
area = math.pi * (1.0 ** 2) # Default 1km for display
total_pop = int(st.session_state.pop_density * area)

st.markdown(f'''
<div class="stats-card">
    <b style="color:#d32f2f; font-size:16px;">Anas Analytics</b>
    <hr style="margin:8px 0;">
    <p style="margin:5px 0; font-size:14px;">👥 <b>Pop:</b> {total_pop:,}</p>
    <p style="margin:5px 0; font-size:14px;">🎓 <b>Primary:</b> {int(total_pop * 0.15):,}</p>
    <p style="margin:5px 0; font-size:14px;">🏫 <b>Secondary:</b> {int(total_pop * 0.12):,}</p>
    <p style="margin:5px 0; font-size:14px;">📍 <b>Radius:</b> 1.0 KM</p>
</div>
''', unsafe_allow_html=True)

# 5. FULL SCREEN MAP
m = folium.Map(location=st.session_state.marker_pos, zoom_start=14, zoom_control=False)
folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                 attr='Google', name='Google Satellite').add_to(m)

folium.Marker(st.session_state.marker_pos, icon=folium.Icon(color='red')).add_to(m)
folium.Circle(st.session_state.marker_pos, radius=1000, color='yellow', fill=True, fill_opacity=0.2).add_to(m)

# Display Map (Full Height)
output = st_folium(m, height=1200, use_container_width=True, key="main_map")

# Click Logic
if output['last_clicked']:
    new_lat, new_lon = output['last_clicked']['lat'], output['last_clicked']['lng']
    if st.session_state.marker_pos != [new_lat, new_lon]:
        st.session_state.marker_pos = [new_lat, new_lon]
        st.session_state.pop_density = get_density(new_lat, new_lon)
        st.rerun()
