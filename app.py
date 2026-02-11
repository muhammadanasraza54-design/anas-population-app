import streamlit as st
import rasterio
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from folium.plugins import Fullscreen
import re
import math

# 1. Page Config
st.set_page_config(layout="wide", page_title="Anas Population Pro")

# CSS: Map ko poori screen par phailane ke liye
st.markdown("""
    <style>
    .main > div { padding: 0px !important; }
    iframe { width: 100% !important; height: 90vh !important; border: none; }
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

# Sidebar sirf radius control ke liye
selected_km = st.sidebar.slider("Radius (KM):", 0.5, 10.0, 1.0, 0.5)

# 2. Map Setup
m = folium.Map(location=st.session_state.marker_pos, zoom_start=15, control_scale=True)
folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                 attr='Google', name='Google Satellite').add_to(m)

# Fullscreen button (Top Right)
Fullscreen(position='topright', force_separate_button=True).add_to(m)

# Marker & Circle
p_lat, p_lon = st.session_state.marker_pos
folium.Marker([p_lat, p_lon], icon=folium.Icon(color='red')).add_to(m)
folium.Circle([p_lat, p_lon], radius=selected_km*1000, color='yellow', fill=True, fill_opacity=0.3).add_to(m)

# 3. Floating Stats Box (Map ke andar)
area = math.pi * (selected_km ** 2)
total_pop = int(st.session_state.pop_density * area)

# Ye Box Full Screen mein bhi nazar ayega
stats_html = f'''
<div style="position: fixed; top: 10px; left: 50px; width: 220px; 
     background-color: rgba(255, 255, 255, 0.9); border:2px solid #333; z-index:9999; 
     padding: 10px; border-radius: 8px; font-family: sans-serif; box-shadow: 2px 2px 5px rgba(0,0,0,0.5);">
     <b style="color:#d32f2f;">Anas Ghouri Analytics</b><br>
     📏 Radius: {selected_km} KM<br>
     👥 <b>Total Pop: {total_pop:,}</b><br>
     📊 Density: {round(st.session_state.pop_density, 2)}/km²
</div>
'''
m.get_root().html.add_child(folium.Element(stats_html))

# 4. Search bar (Map ke oopar Streamlit wala)
search_query = st.text_input("🔍 Search Place (Type and press Enter):")
if search_query:
    try:
        loc = Nominatim(user_agent="anas_final").geocode(search_query, timeout=10)
        if loc:
            st.session_state.marker_pos = [loc.latitude, loc.longitude]
            st.session_state.pop_density = get_density(loc.latitude, loc.longitude)
            st.rerun()
    except: pass

# 5. Display Map
output = st_folium(m, height=750, use_container_width=True, key=f"map_{st.session_state.marker_pos}")

# Click Handling
if output['last_clicked']:
    new_lat, new_lon = output['last_clicked']['lat'], output['last_clicked']['lng']
    if st.session_state.marker_pos != [new_lat, new_lon]:
        st.session_state.marker_pos = [new_lat, new_lon]
        st.session_state.pop_density = get_density(new_lat, new_lon)
        st.rerun()
