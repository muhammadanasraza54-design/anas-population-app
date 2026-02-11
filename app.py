import streamlit as st
import rasterio
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import re
import math

# 1. Page Config
st.set_page_config(layout="wide", page_title="Anas Population Pro", initial_sidebar_state="collapsed")

# CSS: Overlap khatam karne ke liye Search Bar ko Right shift kiya hai
st.markdown("""
    <style>
    .main > div { padding: 0px !important; }
    .block-container { padding: 0px !important; }
    iframe { width: 100% !important; height: 95vh !important; border: none; }
    
    /* Search Bar ko Right side par move kiya taake box se na takraye */
    .stTextInput { 
        position: absolute; 
        top: 20px; 
        left: 350px; /* Stats box 240px ka hai, isliye isay 350px par rakha hai */
        z-index: 10000; 
        width: 400px !important; 
    }
    </style>
    """, unsafe_allow_html=True)

if 'marker_pos' not in st.session_state:
    st.session_state.marker_pos = [24.8607, 67.0011]
if 'pop_density' not in st.session_state:
    st.session_state.pop_density = 0.0

# Sidebar for Radius
selected_km = st.sidebar.slider("Radius (KM):", 0.5, 10.0, 1.0, 0.5)

# 2. Search Bar
search_query = st.text_input("", placeholder="🔍 Search Place here...", key="search_input")
if search_query:
    try:
        loc = Nominatim(user_agent="anas_fix_overlap").geocode(search_query, timeout=10)
        if loc:
            st.session_state.marker_pos = [loc.latitude, loc.longitude]
            st.session_state.pop_density = get_density(loc.latitude, loc.longitude)
            st.rerun()
    except: pass

# 3. Create Map
m = folium.Map(location=st.session_state.marker_pos, zoom_start=15)
folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                 attr='Google', name='Google Satellite').add_to(m)

# 4. Floating Stats Box (Design thora compact kiya hai)
area = math.pi * (selected_km ** 2)
total_pop = int(st.session_state.pop_density * area)

stats_html = f'''
<div style="position: fixed; top: 20px; left: 20px; width: 240px; 
     background-color: rgba(255, 255, 255, 0.95); border:2px solid #d32f2f; z-index:9999; 
     padding: 12px; border-radius: 10px; font-family: sans-serif; box-shadow: 0px 4px 15px rgba(0,0,0,0.4);">
     <b style="color:#d32f2f; font-size:16px;">Anas Analytics</b><br>
     <hr style="margin:8px 0; border:0.5px solid #ccc;">
     📏 <b>Radius:</b> {selected_km} KM<br>
     👥 <b>Total Pop:</b> <span style="font-size:16px; color:#d32f2f;">{total_pop:,}</span><br>
     📊 <b>Density:</b> {round(st.session_state.pop_density, 2)}/km²
</div>
'''
m.get_root().html.add_child(folium.Element(stats_html))

# 5. Display Map
output = st_folium(m, height=850, use_container_width=True, key=f"map_{st.session_state.marker_pos}")

# Click Handling
if output['last_clicked']:
    new_lat, new_lon = output['last_clicked']['lat'], output['last_clicked']['lng']
    if st.session_state.marker_pos != [new_lat, new_lon]:
        st.session_state.marker_pos = [new_lat, new_lon]
        st.session_state.pop_density = get_density(new_lat, new_lon)
        st.rerun()
