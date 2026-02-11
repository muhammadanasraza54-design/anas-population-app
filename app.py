import streamlit as st
import rasterio
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import re
import math

# 1. Page Config
st.set_page_config(layout="wide", page_title="Anas Population Pro", initial_sidebar_state="collapsed")

# CSS: Design ko clean aur full-screen banane ke liye
st.markdown("""
    <style>
    .main > div { padding: 0px !important; }
    .block-container { padding: 0px !important; }
    /* Search bar ki jagah fix karne ke liye */
    .stTextInput { 
        padding: 10px 50px 0px 50px !important;
    }
    iframe { width: 100% !important; height: 85vh !important; border: none; }
    </style>
    """, unsafe_allow_html=True)

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

# Sidebar Radius Control
selected_km = st.sidebar.slider("Radius (KM):", 0.5, 10.0, 1.0, 0.5)

# 2. Search Bar (Isay top par rakha hai taake block na ho)
search_query = st.text_input("🔍 Search Place:", placeholder="Type city or area name...", key="search_bar")
if search_query:
    try:
        loc = Nominatim(user_agent="anas_final_fix").geocode(search_query, timeout=10)
        if loc:
            st.session_state.marker_pos = [loc.latitude, loc.longitude]
            st.session_state.pop_density = get_density(loc.latitude, loc.longitude)
            # Rerun ki zaroorat nahi, niche map update ho jayega
    except: pass

# 3. Create Map
m = folium.Map(location=st.session_state.marker_pos, zoom_start=15)
folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                 attr='Google', name='Google Satellite').add_to(m)

# Marker & Circle
p_lat, p_lon = st.session_state.marker_pos
folium.Marker([p_lat, p_lon], icon=folium.Icon(color='red')).add_to(m)
folium.Circle([p_lat, p_lon], radius=selected_km*1000, color='yellow', fill=True, fill_opacity=0.3).add_to(m)

# 4. Floating Stats Box inside Map
area = math.pi * (selected_km ** 2)
total_pop = int(st.session_state.pop_density * area)

stats_html = f'''
<div style="position: fixed; top: 20px; left: 20px; width: 220px; 
     background-color: rgba(255, 255, 255, 0.9); border:2px solid #d32f2f; z-index:9999; 
     padding: 12px; border-radius: 10px; font-family: sans-serif; box-shadow: 2px 2px 10px rgba(0,0,0,0.3);">
     <b style="color:#d32f2f;">Anas Analytics</b><br>
     📏 Radius: {selected_km} KM<br>
     👥 <b>Total Pop: {total_pop:,}</b><br>
     📊 Density: {round(st.session_state.pop_density, 2)}/km²
</div>
'''
m.get_root().html.add_child(folium.Element(stats_html))

# 5. Display Map & Handle Click
# Humne key mein marker_pos dala hai taake map click par update ho sake
output = st_folium(m, height=750, use_container_width=True, key=f"map_v1_{st.session_state.marker_pos}")

if output['last_clicked']:
    new_lat, new_lon = output['last_clicked']['lat'], output['last_clicked']['lng']
    if st.session_state.marker_pos != [new_lat, new_lon]:
        st.session_state.marker_pos = [new_lat, new_lon]
        st.session_state.pop_density = get_density(new_lat, new_lon)
        st.rerun()
