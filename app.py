import streamlit as st
import rasterio
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import math

# 1. Page Config
st.set_page_config(layout="wide", page_title="Anas Population Pro", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* White Header aur Toolbar ko hide kiya */
    header {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    footer {visibility: hidden;}
    
    .main > div { padding: 0px !important; }
    .block-container { padding: 0px !important; margin: 0px !important; }
    iframe { width: 100% !important; height: 100vh !important; border: none; margin-top: -60px; }

    /* Search Bar: Ab ye TOP CENTER mein hai */
    div[data-testid="stForm"] {
        position: fixed;
        top: 15px;
        left: 50%;
        transform: translateX(-50%);
        width: 450px !important;
        z-index: 10001;
        background-color: white;
        padding: 5px 15px;
        border-radius: 30px; /* Modern Rounded Look */
        box-shadow: 0px 4px 15px rgba(0,0,0,0.3);
        border: none !important;
    }

    /* Anas Analytics Box: Isko thora NICHE (top: 80px) kar diya */
    .stats-box {
        position: fixed; 
        top: 80px; 
        left: 20px; 
        width: 240px; 
        background-color: rgba(255, 255, 255, 0.95); 
        border: 2px solid #d32f2f; 
        z-index: 9999; 
        padding: 12px; 
        border-radius: 10px; 
        font-family: sans-serif; 
        box-shadow: 0px 4px 15px rgba(0,0,0,0.4);
    }

    /* Radius Slider: Bottom Center */
    .stSlider {
        position: fixed;
        bottom: 30px;
        left: 50%;
        transform: translateX(-50%);
        width: 300px !important;
        z-index: 10002;
        background: rgba(255, 255, 255, 0.9);
        padding: 5px 20px;
        border-radius: 20px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.2);
    }
    label { display: none !important; } /* Label hide kiya taake space bache */
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

# Radius Slider
selected_km = st.slider("", 0.5, 10.0, 1.0, 0.5)

# 2. Search Bar (Top Center)
with st.form(key='search_form'):
    col_input, col_btn = st.columns([0.8, 0.2])
    with col_input:
        search_query = st.text_input("", placeholder="🔍 Search Place or Coordinates...", key="query_input")
    with col_btn:
        submit_button = st.form_submit_button(label='Go')

if submit_button and search_query:
    try:
        loc = Nominatim(user_agent="anas_pro_final").geocode(search_query, timeout=10)
        if loc:
            st.session_state.marker_pos = [loc.latitude, loc.longitude]
            st.session_state.pop_density = get_density(loc.latitude, loc.longitude)
            st.rerun()
    except: st.error("Search Busy")

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

# 5. Stats Box (Ab ye thora niche hai)
stats_html = f'''
<div class="stats-box">
     <b style="color:#d32f2f; font-size:15px;">Anas Analytics</b><br>
     <hr style="margin:8px 0; border:0.1px solid #eee;">
     👥 <b>Total Pop:</b> {total_pop:,}<br>
     🎓 <b>Primary (5-10):</b> {primary_pop:,}<br>
     🏫 <b>Secondary (11-16):</b> {secondary_pop:,}<br>
     <hr style="margin:8px 0; border:0.1px solid #eee;">
     📏 <b>Radius:</b> {selected_km} KM
</div>
'''
m.get_root().html.add_child(folium.Element(stats_html))

# 6. Output
output = st_folium(m, height=900, use_container_width=True, key=f"map_{st.session_state.marker_pos}_{selected_km}")

if output['last_clicked']:
    new_lat, new_lon = output['last_clicked']['lat'], output['last_clicked']['lng']
    if st.session_state.marker_pos != [new_lat, new_lon]:
        st.session_state.marker_pos = [new_lat, new_lon]
        st.session_state.pop_density = get_density(new_lat, new_lon)
        st.rerun()
