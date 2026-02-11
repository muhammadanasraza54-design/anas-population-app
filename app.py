import streamlit as st
import rasterio
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import re
import math

# 1. Page Config
st.set_page_config(layout="wide", page_title="Anas Population Pro", initial_sidebar_state="collapsed")

# CSS for full-width layout
st.markdown("""
    <style>
    .main > div { padding: 0px !important; }
    .block-container { padding: 0px !important; }
    iframe { width: 100% !important; height: 80vh !important; border: none; }
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

# Sidebar Settings
selected_km = st.sidebar.slider("Radius (KM):", 0.5, 10.0, 1.0, 0.5)

# 2. FIXED SEARCH BAR (Using Form to prevent freezing)
with st.container():
    with st.form(key='search_form'):
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            search_query = st.text_input("🔍 Search Location:", placeholder="Type city or area name...", key="query_input")
        with col2:
            submit_button = st.form_submit_button(label='Search')

    if submit_button and search_query:
        try:
            loc = Nominatim(user_agent="anas_final_pro").geocode(search_query, timeout=10)
            if loc:
                st.session_state.marker_pos = [loc.latitude, loc.longitude]
                st.session_state.pop_density = get_density(loc.latitude, loc.longitude)
                st.rerun()
        except: st.error("Search Service Busy. Try again.")

# 3. Create Map
m = folium.Map(location=st.session_state.marker_pos, zoom_start=15)
folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                 attr='Google', name='Google Satellite').add_to(m)

p_lat, p_lon = st.session_state.marker_pos
folium.Marker([p_lat, p_lon], icon=folium.Icon(color='red')).add_to(m)
folium.Circle([p_lat, p_lon], radius=selected_km*1000, color='yellow', fill=True, fill_opacity=0.3).add_to(m)

# 4. Floating Stats Box
area = math.pi * (selected_km ** 2)
total_pop = int(st.session_state.pop_density * area)

stats_html = f'''
<div style="position: fixed; top: 150px; left: 20px; width: 200px; 
     background-color: rgba(255, 255, 255, 0.9); border:2px solid #d32f2f; z-index:9999; 
     padding: 10px; border-radius: 10px; font-family: sans-serif;">
     <b style="color:#d32f2f;">Anas Analytics</b><br>
     📏 Radius: {selected_km} KM<br>
     👥 <b>Total Pop: {total_pop:,}</b><br>
     📊 Density: {round(st.session_state.pop_density, 2)}/km²
</div>
'''
m.get_root().html.add_child(folium.Element(stats_html))

# 5. Display Map & Handle Click
# "key" is very important for refreshing the map component
output = st_folium(m, height=700, use_container_width=True, key=f"map_{st.session_state.marker_pos}")

if output['last_clicked']:
    new_lat, new_lon = output['last_clicked']['lat'], output['last_clicked']['lng']
    if st.session_state.marker_pos != [new_lat, new_lon]:
        st.session_state.marker_pos = [new_lat, new_lon]
        st.session_state.pop_density = get_density(new_lat, new_lon)
        st.rerun()
