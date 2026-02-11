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

# Custom CSS taake UI map ke oopar floating nazar aaye
st.markdown("""
    <style>
    .reportview-container .main .block-container { padding-top: 0rem; }
    iframe { width: 100%; height: 85vh !important; }
    </style>
    """, unsafe_allow_html=True)

if 'marker_pos' not in st.session_state:
    st.session_state.marker_pos = [24.8607, 67.0011]
if 'pop_density' not in st.session_state:
    st.session_state.pop_density = 0.0

# Sidebar for controls (Will stay hidden in Fullscreen but accessible)
st.sidebar.header("Settings")
selected_km = st.sidebar.slider("Radius (KM):", 0.5, 10.0, 1.0, 0.5)

def get_density(lat, lon):
    try:
        with rasterio.open('pak_pd_2020_1km.tif') as ds:
            row, col = ds.index(lon, lat)
            data = ds.read(1)
            val = data[row, col]
            return float(val) if val >= 0 and str(val) != 'nan' else 0.0
    except: return 0.0

# 2. Main Search Bar (Top of Map)
search_query = st.text_input("🔍 Search Place or Coordinates (e.g. Lahore):")
if search_query:
    coord_match = re.findall(r"[-+]?\d*\.\d+|\d+", search_query)
    if len(coord_match) >= 2:
        st.session_state.marker_pos = [float(coord_match[0]), float(coord_match[1])]
    else:
        try:
            loc = Nominatim(user_agent="anas_pro").geocode(search_query, timeout=10)
            if loc: st.session_state.marker_pos = [loc.latitude, loc.longitude]
        except: st.warning("Search busy...")
    st.session_state.pop_density = get_density(st.session_state.marker_pos[0], st.session_state.marker_pos[1])

# 3. Create Map
m = folium.Map(location=st.session_state.marker_pos, zoom_start=15, control_scale=True)

# Google Satellite Layer
folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attr='Google', name='Google Satellite'
).add_to(m)

# Feature: Fullscreen Plugin
Fullscreen(position='topright', force_separate_button=True).add_to(m)

# Marker & Circle
p_lat, p_lon = st.session_state.marker_pos
folium.Marker([p_lat, p_lon], icon=folium.Icon(color='red')).add_to(m)
folium.Circle([p_lat, p_lon], radius=selected_km*1000, color='yellow', fill=True, fill_opacity=0.3).add_to(m)

# Feature: Map ke andar Results Box (Floating Popup)
area = math.pi * (selected_km ** 2)
total_pop = int(st.session_state.pop_density * area)

html_box = f'''
<div style="position: fixed; bottom: 50px; left: 50px; width: 250px; height: 110px; 
     background-color: white; border:2px solid grey; z-index:9999; font-size:14px;
     padding: 10px; border-radius: 10px; opacity: 0.9;">
     <b>Anas Analytics</b><br>
     📍 Lat: {round(p_lat,4)}, Lon: {round(p_lon,4)}<br>
     📏 Radius: {selected_km} KM<br>
     👥 <b>Total Pop: {total_pop:,}</b>
</div>
'''
m.get_root().html.add_child(folium.Element(html_box))

# 4. Display Map
output = st_folium(m, height=700, use_container_width=True, key=f"map_{st.session_state.marker_pos}")

# 5. Handle Click & Auto-Zoom
if output['last_clicked']:
    new_lat, new_lon = output['last_clicked']['lat'], output['last_clicked']['lng']
    if st.session_state.marker_pos != [new_lat, new_lon]:
        st.session_state.marker_pos = [new_lat, new_lon]
        st.session_state.pop_density = get_density(new_lat, new_lon)
        st.rerun()

# Stats display niche bhi rahay ga backup ke liye
st.write(f"### 👥 Estimated Population in {selected_km}km: {total_pop:,}")
