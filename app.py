import streamlit as st
import rasterio
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import math

# 1. Page Config
st.set_page_config(layout="wide", page_title="Anas Population Pro", initial_sidebar_state="collapsed")

# 2. Strong CSS for Clean UI (Fixing the Giant Search Bar)
st.markdown("""
    <style>
    header {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    .main > div { padding: 0px !important; }
    .block-container { padding: 0px !important; margin: 0px !important; }
    
    /* Search Bar: Chota aur Top-Center mein fix */
    div[data-testid="stForm"] {
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        width: 400px !important; /* Fixed width taake dabba bada na ho */
        z-index: 10001;
        background-color: white;
        padding: 5px 15px;
        border-radius: 10px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.2);
        border: 1px solid #ddd !important;
    }
    
    /* Stats Box: Top-Left mein clean look */
    .stats-box {
        position: fixed;
        top: 20px;
        left: 20px;
        width: 250px;
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.2);
        z-index: 10000;
        border-left: 5px solid #d32f2f;
    }

    /* Slider: Bottom Center */
    .stSlider {
        position: fixed;
        bottom: 30px;
        left: 50%;
        transform: translateX(-50%);
        width: 300px !important;
        z-index: 10000;
        background: white;
        padding: 5px 15px;
        border-radius: 50px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.2);
    }
    
    /* Hide labels to save space */
    label { display: none !important; }
    iframe { width: 100% !important; height: 100vh !important; border: none; }
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

# 3. Radius Slider (Bottom Center)
selected_km = st.slider("", 0.5, 10.0, 1.0, 0.5)

# 4. Floating Search Bar (Now Fixed Width)
with st.form(key='search_form'):
    search_query = st.text_input("", placeholder="🔍 Search Place...", key="query_input")
    submit_button = st.form_submit_button(label='Search', use_container_width=True)

if submit_button and search_query:
    try:
        loc = Nominatim(user_agent="anas_final_pro").geocode(search_query)
        if loc:
            st.session_state.marker_pos = [loc.latitude, loc.longitude]
            st.session_state.pop_density = get_density(loc.latitude, loc.longitude)
            st.rerun()
    except: st.error("Busy")

# 5. Stats Calculation & Display
area = math.pi * (selected_km ** 2)
total_pop = int(st.session_state.pop_density * area)

st.markdown(f'''
<div class="stats-box">
    <h3 style="margin:0; color:#d32f2f; font-size:18px;">Anas Analytics</h3>
    <hr style="margin:8px 0; border:0.5px solid #eee;">
    <p style="margin:4px 0;">👥 <b>Total Pop:</b> {total_pop:,}</p>
    <p style="margin:4px 0;">🎓 <b>Primary:</b> {int(total_pop * 0.15):,}</p>
    <p style="margin:4px 0;">🏫 <b>Secondary:</b> {int(total_pop * 0.12):,}</p>
    <p style="margin:4px 0;">📏 <b>Radius:</b> {selected_km} KM</p>
</div>
''', unsafe_allow_html=True)

# 6. Map Setup
m = folium.Map(location=st.session_state.marker_pos, zoom_start=14, zoom_control=False)
folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                 attr='Google', name='Google Satellite').add_to(m)

folium.Marker(st.session_state.marker_pos, icon=folium.Icon(color='red')).add_to(m)
folium.Circle(st.session_state.marker_pos, radius=selected_km*1000, color='yellow', fill=True, fill_opacity=0.2).add_to(m)

# 7. Output
output = st_folium(m, height=1000, use_container_width=True, key=f"map_{st.session_state.marker_pos}_{selected_km}")

if output['last_clicked']:
    new_lat, new_lon = output['last_clicked']['lat'], output['last_clicked']['lng']
    if st.session_state.marker_pos != [new_lat, new_lon]:
        st.session_state.marker_pos = [new_lat, new_lon]
        st.session_state.pop_density = get_density(new_lat, new_lon)
        st.rerun()
