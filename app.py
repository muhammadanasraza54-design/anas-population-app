import streamlit as st
import rasterio
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import math

# 1. Page Config
st.set_page_config(layout="wide", page_title="Anas Population Pro", initial_sidebar_state="collapsed")

# 2. CSS: Aapke Sketch ke mutabiq layout fixing
st.markdown("""
    <style>
    header {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    .main > div { padding: 0px !important; }
    .block-container { padding: 0px !important; }

    /* Top Navigation Bar for Search */
    .search-bar-container {
        position: fixed;
        top: 0;
        left: 260px; /* Sidebar ki jagah chor kar */
        right: 0;
        height: 60px;
        background: white;
        display: flex;
        align-items: center;
        padding: 0 20px;
        z-index: 999999;
        border-bottom: 1px solid #ddd;
    }

    /* Left Sidebar for Radius & Status */
    .side-panel {
        position: fixed;
        top: 0;
        left: 0;
        width: 260px;
        height: 100vh;
        background: #f8f9fa;
        border-right: 1px solid #ddd;
        z-index: 1000000;
        padding: 20px;
    }

    /* Map adjustment */
    .map-frame {
        margin-left: 260px;
        margin-top: 60px;
    }

    /* Hide redundant UI */
    [data-testid="stVerticalBlock"] { gap: 0rem; }
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

# 3. LEFT SIDE PANEL (Radius & Status)
with st.sidebar:
    st.markdown("### 📏 Radius KM")
    selected_km = st.slider("", 0.5, 10.0, 1.0, 0.5, label_visibility="collapsed")
    
    st.markdown("---")
    
    st.markdown("### 📊 Status")
    area = math.pi * (selected_km ** 2)
    total_pop = int(st.session_state.pop_density * area)
    
    st.metric("Total Population", f"{total_pop:,}")
    st.write(f"🎓 Primary: {int(total_pop * 0.15):,}")
    st.write(f"🏫 Secondary: {int(total_pop * 0.12):,}")
    st.caption(f"Lat: {st.session_state.marker_pos[0]:.4f}")
    st.caption(f"Lon: {st.session_state.marker_pos[1]:.4f}")

# 4. TOP SEARCH BAR
st.markdown('<div class="search-bar-container">', unsafe_allow_html=True)
c1, c2 = st.columns([5, 1])
with c1:
    search_query = st.text_input("", placeholder="🔍 Search location here...", key="top_search", label_visibility="collapsed")
with c2:
    if st.button("Search", use_container_width=True):
        if search_query:
            try:
                loc = Nominatim(user_agent="anas_final_layout").geocode(search_query)
                if loc:
                    st.session_state.marker_pos = [loc.latitude, loc.longitude]
                    st.session_state.pop_density = get_density(loc.latitude, loc.longitude)
                    st.rerun()
            except: st.error("Error")
st.markdown('</div>', unsafe_allow_html=True)

# 5. MAIN MAP AREA
st.markdown('<div class="map-frame">', unsafe_allow_html=True)
m = folium.Map(location=st.session_state.marker_pos, zoom_start=14, zoom_control=False)
folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                 attr='Google', name='Google Satellite').add_to(m)

folium.Marker(st.session_state.marker_pos, icon=folium.Icon(color='red')).add_to(m)
folium.Circle(st.session_state.marker_pos, radius=selected_km*1000, color='yellow', fill=True, fill_opacity=0.2).add_to(m)

output = st_folium(m, height=900, use_container_width=True, key=f"map_{st.session_state.marker_pos}_{selected_km}")
st.markdown('</div>', unsafe_allow_html=True)

# Click logic
if output['last_clicked']:
    new_lat, new_lon = output['last_clicked']['lat'], output['last_clicked']['lng']
    if st.session_state.marker_pos != [new_lat, new_lon]:
        st.session_state.marker_pos = [new_lat, new_lon]
        st.session_state.pop_density = get_density(new_lat, new_lon)
        st.rerun()
