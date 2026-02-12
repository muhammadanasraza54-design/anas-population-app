import streamlit as st
import streamlit.components.v1 as components
import folium
from streamlit_folium import st_folium
import rasterio
import math

# Page Config - Wide mode is essential
st.set_page_config(layout="wide", page_title="Anas TCF Multi-Tool")

# --- NAVIGATION SIDEBAR ---
with st.sidebar:
    st.image("https://www.tcf.org.pk/wp-content/uploads/2019/09/logo.svg", width=150)
    st.title("Main Menu")
    app_mode = st.radio("Choose Window:", ["📊 Population Analysis", "🌍 Advanced GIS Map"])

# Population Calculation Function
def get_density(lat, lon):
    try:
        with rasterio.open('pak_pd_2020_1km.tif') as ds:
            row, col = ds.index(lon, lat)
            data = ds.read(1)
            val = data[row, col]
            return float(val) if val >= 0 and not math.isnan(val) else 0.0
    except: return 0.0

# --- WINDOW 1: POPULATION ANALYSIS ---
if app_mode == "📊 Population Analysis":
    if 'marker_pos' not in st.session_state:
        st.session_state.marker_pos = [24.8607, 67.0011]
    
    # 🔍 SEARCH BAR (Wapas add kar diya gaya hai)
    st.subheader("Population Analytics Tool")
    search_input = st.text_input("🔍 Search Coordinates (Lat, Lon):", placeholder="e.g. 24.89, 67.15")
    
    if search_input:
        try:
            new_lat, new_lon = map(float, search_input.split(','))
            st.session_state.marker_pos = [new_lat, new_lon]
        except:
            st.warning("Format: Latitude, Longitude")

    with st.sidebar:
        radius_km = st.slider("Search Radius (KM)", 0.5, 10.0, 2.0)
        density = get_density(st.session_state.marker_pos[0], st.session_state.marker_pos[1])
        total_pop = int(density * (math.pi * radius_km**2))
        st.metric("Total Population", f"{total_pop:,}")

    m = folium.Map(location=st.session_state.marker_pos, zoom_start=13)
    folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google', name='Satellite').add_to(m)
    folium.Circle(st.session_state.marker_pos, radius=radius_km*1000, color='red', fill=True, fill_opacity=0.1).add_to(m)
    folium.Marker(st.session_state.marker_pos, icon=folium.Icon(color='red', icon='crosshairs', prefix='fa')).add_to(m)
    
    map_output = st_folium(m, width="100%", height=600)
    if map_output['last_clicked']:
        st.session_state.marker_pos = [map_output['last_clicked']['lat'], map_output['last_clicked']['lng']]
        st.rerun()

# --- WINDOW 2: ADVANCED GIS MAP (HTML) ---
elif app_mode == "🌍 Advanced GIS Map":
    # Margin khatam karne ke liye CSS
    st.markdown("""
        <style>
               .block-container {
                    padding-top: 0rem;
                    padding-bottom: 0rem;
                    padding-left: 0rem;
                    padding-right: 0rem;
                }
        </style>
        """, unsafe_allow_html=True)
    
    try:
        with open("AnasGhouri_Ultimate_GIS.html", "r", encoding='utf-8') as f:
            html_content = f.read()
            # Height ko 1000 kar diya gaya hai takay screen par fit aaye
            components.html(html_content, height=1000, scrolling=True)
    except Exception as e:
        st.error(f"Error: {e}")
