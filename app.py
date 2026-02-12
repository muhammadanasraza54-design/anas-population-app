import streamlit as st
import streamlit.components.v1 as components
import folium
from streamlit_folium import st_folium
import rasterio
import math

# Page Config
st.set_page_config(layout="wide", page_title="Anas TCF Multi-Tool")

# --- 🎨 CSS: Sidebar aur Content Fix ---
st.markdown("""
    <style>
        /* Sidebar ko top patti ke nichay lane ke liye */
        [data-testid="stSidebar"] {
            top: 60px !important;
            height: calc(100vh - 60px) !important;
        }
        
        /* Main content ki padding khatam karke map ko bara karne ke liye */
        .block-container {
            padding-top: 0rem !important;
            padding-bottom: 0rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }

        /* Metrics background clean look ke liye */
        .stMetric {
            background-color: #f8f9fa;
            padding: 10px;
            border-radius: 8px;
        }
    </style>
    """, unsafe_allow_html=True)

# --- NAVIGATION SIDEBAR ---
with st.sidebar:
    st.image("https://www.tcf.org.pk/wp-content/uploads/2019/09/logo.svg", width=120)
    st.title("Main Menu")
    app_mode = st.radio("Go to Window:", ["📊 Population Analysis", "🌍 Advanced GIS Map"])
    st.markdown("---")

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
    
    st.subheader("Population Analytics Tool")
    
    # 🔍 Search bar
    search_input = st.text_input("🔍 Search Coordinates (Lat, Lon):", value=f"{st.session_state.marker_pos[0]}, {st.session_state.marker_pos[1]}")
    
    if search_input:
        try:
            coords = search_input.split(',')
            st.session_state.marker_pos = [float(coords[0].strip()), float(coords[1].strip())]
        except: pass

    # Stats in Sidebar
    with st.sidebar:
        radius_km = st.slider("Search Radius (KM)", 0.5, 10.0, 2.0)
        density = get_density(st.session_state.marker_pos[0], st.session_state.marker_pos[1])
        total_pop = int(density * (math.pi * radius_km**2))
        
        st.metric("Total Population", f"{total_pop:,}")
        st.write(f"👶 **Primary (5-10):** {int(total_pop * 0.15):,}")
        st.write(f"🏫 **Secondary (11-16):** {int(total_pop * 0.12):,}")

    # Map with increased height (800)
    m = folium.Map(location=st.session_state.marker_pos, zoom_start=13)
    folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google', name='Satellite').add_to(m)
    folium.Circle(st.session_state.marker_pos, radius=radius_km*1000, color='red', fill=True, fill_opacity=0.1).add_to(m)
    folium.Marker(st.session_state.marker_pos, icon=folium.Icon(color='red', icon='crosshairs', prefix='fa')).add_to(m)
    
    map_output = st_folium(m, width="100%", height=800)
    
    if map_output['last_clicked']:
        st.session_state.marker_pos = [map_output['last_clicked']['lat'], map_output['last_clicked']['lng']]
        st.rerun()

# --- WINDOW 2: ADVANCED GIS MAP (HTML) ---
elif app_mode == "🌍 Advanced GIS Map":
    st.subheader("TCF Advanced GIS Viewer")
    try:
        with open("AnasGhouri_Ultimate_GIS.html", "r", encoding='utf-8') as f:
            html_content = f.read()
            # Height 950 for full screen coverage
            components.html(html_content, height=950, scrolling=True)
    except Exception as e:
        st.error(f"Error: {e}")
