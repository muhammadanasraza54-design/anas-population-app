import streamlit as st
import rasterio
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import re
import math

# 1. Page Config
st.set_page_config(layout="wide", page_title="Anas Population Pro", initial_sidebar_state="collapsed")

# CSS: Search Bar ko chota aur center mein karne ke liye
st.markdown("""
    <style>
    .main > div { padding: 0px !important; }
    .block-container { padding: 0px !important; }
    iframe { width: 100% !important; height: 82vh !important; border: none; }
    
    /* Search Bar Layout Fix */
    div[data-testid="stForm"] {
        width: 40% !important; /* Width kam kar di */
        margin: auto !important; /* Center mein kar diya */
        border: none !important;
        padding: 10px 0px 0px 0px !important;
    }
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

# 2. Centered Search Bar (Is se overlap khatam ho jayega)
with st.form(key='search_form'):
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        search_query = st.text_input("", placeholder="🔍 Search Place (e.g. Korangi)...", key="query_input")
    with col2:
        st.markdown('<div style="padding-top:10px;">', unsafe_allow_html=True)
        submit_button = st.form_submit_button(label='Search')
        st.markdown('</div>', unsafe_allow_html=True)

if submit_button and search_query:
    try:
        loc = Nominatim(user_agent="anas_final_pro").geocode(search_query, timeout=10)
        if loc:
            st.session_state.marker_pos = [loc.latitude, loc.longitude]
            st.session_state.pop_density = get_density(loc.latitude, loc.longitude)
            st.rerun()
    except: st.error("Search Service Busy.")

# 3. Map Setup
m = folium.Map(location=st.session_state.marker_pos, zoom_start=15)
folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                 attr='Google', name='Google Satellite').add_to(m)

p_lat, p_lon = st.session_state.marker_pos
folium.Marker([p_lat, p_lon], icon=folium.Icon(color='red')).add_to(m)
folium.Circle([p_lat, p_lon], radius=selected_km*1000, color='yellow', fill=True, fill_opacity=0.3).add_to(m)

# 4. Stats Calculation
area = math.pi * (selected_km ** 2)
total_pop = int(st.session_state.pop_density * area)
primary_pop = int(total_pop * 0.15)
secondary_pop = int(total_pop * 0.12)

# 5. Floating Stats Box (Top Left)
stats_html = f'''
<div style="position: fixed; top: 20px; left: 20px; width: 250px; 
     background-color: rgba(255, 255, 255, 0.95); border:2px solid #d32f2f; z-index:9999; 
     padding: 15px; border-radius: 12px; font-family: sans-serif; box-shadow: 0px 4px 15px rgba(0,0,0,0.4);">
     <b style="color:#d32f2f; font-size:16px;">Anas Age-Wise Analytics</b><br>
     <hr style="margin:10px 0; border:0.5px solid #ccc;">
     👥 <b>Total Pop:</b> {total_pop:,}<br>
     🎓 <b>Primary (5-10):</b> {primary_pop:,}<br>
     🏫 <b>Secondary (11-16):</b> {secondary_pop:,}<br>
     <hr style="margin:10px 0; border:0.5px solid #ccc;">
     📏 <b>Radius:</b> {selected_km} KM
</div>
'''
m.get_root().html.add_child(folium.Element(stats_html))

# 6. Map Display
output = st_folium(m, height=750, use_container_width=True, key=f"map_{st.session_state.marker_pos}")

if output['last_clicked']:
    new_lat, new_lon = output['last_clicked']['lat'], output['last_clicked']['lng']
    if st.session_state.marker_pos != [new_lat, new_lon]:
        st.session_state.marker_pos = [new_lat, new_lon]
        st.session_state.pop_density = get_density(new_lat, new_lon)
        st.rerun()
