import streamlit as st
import rasterio
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import math

# 1. Page Setup
st.set_page_config(layout="wide", page_title="Anas Population Pro", initial_sidebar_state="collapsed")

# 2. CSS: Sab kuch screen se hata kar sirf chote floating boxes rakhe hain
st.markdown("""
    <style>
    header {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    .main > div { padding: 0px !important; }
    .block-container { padding: 0px !important; margin: 0px !important; }
    
    /* Search & Radius Box (Top Left) */
    .floating-controls {
        position: fixed;
        top: 20px;
        left: 20px;
        width: 320px;
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0px 4px 20px rgba(0,0,0,0.3);
        z-index: 100000;
        border: 1px solid #eee;
    }

    /* Input Fields Styling */
    .stTextInput input { border-radius: 8px !important; }
    
    /* Map display fix */
    .stFoliumRender { position: absolute; top: 0; left: 0; z-index: 1; }
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

# 3. FLOATING PANEL (Search + Radius + Stats)
with st.container():
    st.markdown('<div class="floating-controls">', unsafe_allow_html=True)
    
    st.subheader("Anas Analytics")
    
    # Search Input
    search_query = st.text_input("Search Location", placeholder="e.g. Karachi", key="f_search")
    if st.button("Search", use_container_width=True):
        if search_query:
            try:
                loc = Nominatim(user_agent="anas_final_fixed").geocode(search_query)
                if loc:
                    st.session_state.marker_pos = [loc.latitude, loc.longitude]
                    st.session_state.pop_density = get_density(loc.latitude, loc.longitude)
                    st.rerun()
            except: st.error("Service Busy")

    st.markdown("---")
    
    # Radius Slider
    selected_km = st.slider("Select Radius (KM)", 0.5, 10.0, 1.0, 0.5)
    
    # Calculation
    area = math.pi * (selected_km ** 2)
    total_pop = int(st.session_state.pop_density * area)
    
    # Stats
    st.write(f"👥 **Total Pop:** {total_pop:,}")
    st.write(f"🎓 **Primary:** {int(total_pop * 0.15):,}")
    st.write(f"🏫 **Secondary:** {int(total_pop * 0.12):,}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# 4. FULL SCREEN MAP
m = folium.Map(location=st.session_state.marker_pos, zoom_start=14, zoom_control=False)
folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                 attr='Google', name='Google Satellite').add_to(m)

folium.Marker(st.session_state.marker_pos, icon=folium.Icon(color='red')).add_to(m)
folium.Circle(st.session_state.marker_pos, radius=selected_km*1000, color='yellow', fill=True, fill_opacity=0.2).add_to(m)

# Map output
output = st_folium(m, height=1000, width=2000, key=f"map_{st.session_state.marker_pos}_{selected_km}")

# Click Handling
if output['last_clicked']:
    new_lat, new_lon = output['last_clicked']['lat'], output['last_clicked']['lng']
    if st.session_state.marker_pos != [new_lat, new_lon]:
        st.session_state.marker_pos = [new_lat, new_lon]
        st.session_state.pop_density = get_density(new_lat, new_lon)
        st.rerun()
