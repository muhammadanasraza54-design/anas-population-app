import streamlit as st
import rasterio
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from folium.plugins import Fullscreen
import re
import math

# 1. Page Config - Is se sidebars aur margins khatam ho jayenge
st.set_page_config(layout="wide", page_title="Anas Population Pro", initial_sidebar_state="collapsed")

# CSS for "Full Screen Look" without pressing the button
st.markdown("""
    <style>
    /* Main container ki padding khatam karne ke liye */
    .main > div { padding: 0px !important; }
    .block-container { padding: 0px !important; }
    /* Map ki height maximum karne ke liye */
    iframe { width: 100% !important; height: 95vh !important; border: none; }
    /* Search bar ko thora style dene ke liye */
    .stTextInput { position: absolute; top: 10px; left: 50px; z-index: 10000; width: 300px !important; }
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

# Radius slider sidebar mein rakha hai (taake screen saaf rahe)
selected_km = st.sidebar.slider("Radius (KM):", 0.5, 10.0, 1.0, 0.5)

# 2. Search Bar - Isay humne CSS se map ke oopar "Float" karwaya hai
search_query = st.text_input("", placeholder="🔍 Search Place here...", key="search_input")
if search_query:
    try:
        loc = Nominatim(user_agent="anas_final_fixed").geocode(search_query, timeout=10)
        if loc:
            st.session_state.marker_pos = [loc.latitude, loc.longitude]
            st.session_state.pop_density = get_density(loc.latitude, loc.longitude)
            st.rerun()
    except: pass

# 3. Create Map
m = folium.Map(location=st.session_state.marker_pos, zoom_start=15, zoom_control=True)
folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                 attr='Google', name='Google Satellite').add_to(m)

# Marker & Circle
p_lat, p_lon = st.session_state.marker_pos
folium.Marker([p_lat, p_lon], icon=folium.Icon(color='red', icon='info-sign')).add_to(m)
folium.Circle([p_lat, p_lon], radius=selected_km*1000, color='yellow', fill=True, fill_opacity=0.3).add_to(m)

# 4. Floating Results Box (Ab ye hamesha map ke andar rahega)
area = math.pi * (selected_km ** 2)
total_pop = int(st.session_state.pop_density * area)

stats_html = f'''
<div style="position: fixed; top: 70px; left: 50px; width: 220px; 
     background-color: rgba(255, 255, 255, 0.9); border:2px solid #d32f2f; z-index:9999; 
     padding: 15px; border-radius: 12px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
     box-shadow: 0px 4px 10px rgba(0,0,0,0.3);">
     <b style="color:#d32f2f; font-size:18px;">Anas Analytics</b><br>
     <hr style="margin:10px 0;">
     📏 <b>Radius:</b> {selected_km} KM<br>
     👥 <b>Total Pop:</b> <span style="font-size:18px; color:#d32f2f;">{total_pop:,}</span><br>
     📊 <b>Density:</b> {round(st.session_state.pop_density, 2)}/km²
</div>
'''
m.get_root().html.add_child(folium.Element(stats_html))

# 5. Display Map - Height barha di hai taake full screen jaisa lage
output = st_folium(m, height=850, use_container_width=True, key=f"map_{st.session_state.marker_pos}")

# Click Handling
if output['last_clicked']:
    new_lat, new_lon = output['last_clicked']['lat'], output['last_clicked']['lng']
    if st.session_state.marker_pos != [new_lat, new_lon]:
        st.session_state.marker_pos = [new_lat, new_lon]
        st.session_state.pop_density = get_density(new_lat, new_lon)
        st.rerun()
