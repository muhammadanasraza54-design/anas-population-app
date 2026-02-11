import streamlit as st
import rasterio
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import math

# 1. Page Config
st.set_page_config(layout="wide", page_title="Anas Population Pro", initial_sidebar_state="collapsed")

# 2. Custom CSS to fix the Search Bar once and for all
st.markdown("""
    <style>
    header {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    .main > div { padding: 0px !important; }
    .block-container { padding: 0px !important; }

    /* Floating Search Bar like Image 1 */
    div[data-testid="stForm"] {
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        width: 450px !important;
        z-index: 99999;
        background-color: white;
        padding: 5px 15px;
        border-radius: 8px;
        box-shadow: 0px 2px 10px rgba(0,0,0,0.2);
        border: 1px solid #ccc !important;
    }

    /* Removing the massive white background block */
    [data-testid="stVerticalBlock"] > div:has(div[data-testid="stForm"]) {
        position: absolute;
        z-index: 99999;
    }

    /* Anas Analytics Panel (Top Left) */
    .stats-overlay {
        position: fixed;
        top: 20px;
        left: 20px;
        width: 240px;
        background: white;
        padding: 12px;
        border-radius: 8px;
        box-shadow: 0px 2px 10px rgba(0,0,0,0.2);
        z-index: 99998;
        border-left: 4px solid #d32f2f;
    }

    /* Radius Slider (Bottom Center) */
    .slider-container {
        position: fixed;
        bottom: 30px;
        left: 50%;
        transform: translateX(-50%);
        width: 300px;
        background: white;
        padding: 5px 20px;
        border-radius: 30px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.3);
        z-index: 99998;
    }
    
    label { display: none !important; } /* Hide labels to save space */
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

# 3. FLOATING SEARCH BAR (Small & Clean)
with st.form(key='search_form'):
    col1, col2 = st.columns([4, 1])
    with col1:
        search_query = st.text_input("", placeholder="Search Location...", label_visibility="collapsed")
    with col2:
        submit = st.form_submit_button("Go")

if submit and search_query:
    try:
        loc = Nominatim(user_agent="anas_final_fixed").geocode(search_query)
        if loc:
            st.session_state.marker_pos = [loc.latitude, loc.longitude]
            st.session_state.pop_density = get_density(loc.latitude, loc.longitude)
            st.rerun()
    except: st.warning("Location not found")

# 4. RADIUS SLIDER (Bottom)
st.markdown('<div class="slider-container">', unsafe_allow_html=True)
selected_km = st.slider("", 0.5, 10.0, 1.0, 0.5)
st.markdown('</div>', unsafe_allow_html=True)

# 5. STATS BOX (Top Left)
area = math.pi * (selected_km ** 2)
total_pop = int(st.session_state.pop_density * area)

st.markdown(f'''
<div class="stats-overlay">
    <b style="color:#d32f2f;">Anas Analytics</b><br>
    <small>👥 Total Pop: {total_pop:,}</small><br>
    <small>🎓 Primary: {int(total_pop * 0.15):,}</small><br>
    <small>🏫 Secondary: {int(total_pop * 0.12):,}</small><br>
    <small>📏 Radius: {selected_km} KM</small>
</div>
''', unsafe_allow_html=True)

# 6. MAP
m = folium.Map(location=st.session_state.marker_pos, zoom_start=14, zoom_control=False)
folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                 attr='Google', name='Google Satellite').add_to(m)

folium.Marker(st.session_state.marker_pos, icon=folium.Icon(color='red')).add_to(m)
folium.Circle(st.session_state.marker_pos, radius=selected_km*1000, color='yellow', fill=True, fill_opacity=0.2).add_to(m)

# 7. OUTPUT
st_folium(m, height=1200, use_container_width=True, key=f"map_{st.session_state.marker_pos}_{selected_km}")
