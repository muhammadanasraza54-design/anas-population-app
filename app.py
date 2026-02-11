import streamlit as st
import rasterio
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import math

# 1. Page Config
st.set_page_config(layout="wide", page_title="Anas Population Pro", initial_sidebar_state="collapsed")

# 2. Custom CSS: Top Header for Search & Radius
st.markdown("""
    <style>
    header {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    .main > div { padding: 0px !important; }
    .block-container { padding: 0px !important; }
    
    /* Top Header Bar */
    .top-nav {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 70px;
        background: white;
        z-index: 999999;
        display: flex;
        align-items: center;
        padding: 0 20px;
        box-shadow: 0px 2px 10px rgba(0,0,0,0.1);
    }
    
    /* Stats Box (Left Side) */
    .stats-card {
        position: fixed;
        top: 90px;
        left: 20px;
        width: 240px;
        background: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.2);
        z-index: 99999;
        border-top: 4px solid #d32f2f;
    }

    /* Map Height Adjustment */
    iframe { width: 100% !important; height: 100vh !important; border: none; margin-top: 70px; }
    
    /* Hide Default Streamlit Labels */
    label { display: none !important; }
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

# 3. TOP NAVIGATION BAR (Search + Radius)
st.markdown('<div class="top-nav">', unsafe_allow_html=True)
col1, col2, col3 = st.columns([0.4, 0.4, 0.2])

with col1:
    search_query = st.text_input("Search", placeholder="🔍 Search Place...", key="nav_search")

with col2:
    # Radius slider directly in the header
    selected_km = st.slider("Radius", 0.5, 10.0, 1.0, 0.5, key="nav_radius")

with col3:
    st.markdown('<div style="padding-top:25px;">', unsafe_allow_html=True)
    if st.button("Update Map", use_container_width=True):
        if search_query:
            try:
                loc = Nominatim(user_agent="anas_final_v5").geocode(search_query)
                if loc:
                    st.session_state.marker_pos = [loc.latitude, loc.longitude]
                    st.session_state.pop_density = get_density(loc.latitude, loc.longitude)
                    st.rerun()
            except: st.warning("Location Error")
    st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# 4. STATS DISPLAY (Left Side)
area = math.pi * (selected_km ** 2)
total_pop = int(st.session_state.pop_density * area)

st.markdown(f'''
<div class="stats-card">
    <b style="color:#d32f2f; font-size:16px;">Anas Analytics</b>
    <hr style="margin:8px 0;">
    <p style="margin:5px 0;">👥 <b>Pop:</b> {total_pop:,}</p>
    <p style="margin:5px 0;">🎓 <b>Primary:</b> {int(total_pop * 0.15):,}</p>
    <p style="margin:5px 0;">🏫 <b>Secondary:</b> {int(total_pop * 0.12):,}</p>
    <p style="margin:5px 0; color:gray; font-size:12px;">📍 {st.session_state.marker_pos[0]:.4f}, {st.session_state.marker_pos[1]:.4f}</p>
</div>
''', unsafe_allow_html=True)

# 5. MAP DISPLAY
m = folium.Map(location=st.session_state.marker_pos, zoom_start=14, zoom_control=False)
folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                 attr='Google', name='Google Satellite').add_to(m)

folium.Marker(st.session_state.marker_pos, icon=folium.Icon(color='red')).add_to(m)
folium.Circle(st.session_state.marker_pos, radius=selected_km*1000, color='yellow', fill=True, fill_opacity=0.2).add_to(m)

output = st_folium(m, height=1000, use_container_width=True, key=f"map_{st.session_state.marker_pos}_{selected_km}")

# 6. Click Handling
if output['last_clicked']:
    new_lat, new_lon = output['last_clicked']['lat'], output['last_clicked']['lng']
    if st.session_state.marker_pos != [new_lat, new_lon]:
        st.session_state.marker_pos = [new_lat, new_lon]
        st.session_state.pop_density = get_density(new_lat, new_lon)
        st.rerun()
