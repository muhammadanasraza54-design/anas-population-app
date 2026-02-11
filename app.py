import streamlit as st
import rasterio
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import math

# 1. Page Configuration
st.set_page_config(layout="wide", page_title="Anas Population Pro")

# 2. CSS: Search bar ki mazeed neechay adjustment
st.markdown("""
    <style>
    /* Page ke top se mazeed gap (4rem) */
    .block-container { 
        padding-top: 4rem !important; 
        padding-bottom: 0rem; 
    }
    
    /* Search row ke darmian gap */
    .stTextInput {
        margin-top: 10px;
    }
    
    /* Metric text size fix */
    [data-testid="stMetricValue"] { font-size: 24px; }
    
    /* Map ko thora sa frame mein laane ke liye */
    iframe { border-radius: 15px; box-shadow: 0px 4px 10px rgba(0,0,0,0.1); }
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

# 3. SIDEBAR (Radius & Status)
with st.sidebar:
    st.header("📏 Settings")
    selected_km = st.slider("Radius KM", 0.5, 10.0, 1.0, 0.5)
    
    st.markdown("---")
    
    st.header("📊 Status")
    area = math.pi * (selected_km ** 2)
    total_pop = int(st.session_state.pop_density * area)
    
    st.metric("Total Population", f"{total_pop:,}")
    st.write(f"🎓 Primary (5-10): {int(total_pop * 0.15):,}")
    st.write(f"🏫 Secondary (11-16): {int(total_pop * 0.12):,}")
    st.info(f"📍 Location: {st.session_state.marker_pos[0]:.4f}, {st.session_state.marker_pos[1]:.4f}")

# 4. SEARCH BAR SECTION (Mazeed niche adjusted)
col_search, col_btn = st.columns([4, 1])
with col_search:
    search_query = st.text_input("Search Location", placeholder="Search for a city or area...", label_visibility="collapsed")
with col_btn:
    # Button ko input ke sath perfectly align kiya
    search_clicked = st.button("Search", use_container_width=True)

if search_clicked:
    if search_query:
        try:
            loc = Nominatim(user_agent="anas_pro_final_v10").geocode(search_query)
            if loc:
                st.session_state.marker_pos = [loc.latitude, loc.longitude]
                st.session_state.pop_density = get_density(loc.latitude, loc.longitude)
                st.rerun()
        except: st.error("Search error. Please try again.")

# 5. MAP SECTION
m = folium.Map(location=st.session_state.marker_pos, zoom_start=14)
folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                 attr='Google', name='Google Satellite').add_to(m)

folium.Marker(st.session_state.marker_pos, icon=folium.Icon(color='red')).add_to(m)
folium.Circle(st.session_state.marker_pos, radius=selected_km*1000, color='yellow', fill=True, fill_opacity=0.2).add_to(m)

# Map output
output = st_folium(m, height=650, use_container_width=True, key="main_map")

# 6. Click Handling
if output['last_clicked']:
    new_lat, new_lon = output['last_clicked']['lat'], output['last_clicked']['lng']
    if st.session_state.marker_pos != [new_lat, new_lon]:
        st.session_state.marker_pos = [new_lat, new_lon]
        st.session_state.pop_density = get_density(new_lat, new_lon)
        st.rerun()
