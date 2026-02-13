import streamlit as st
import os
import requests
import rasterio
import math
import numpy as np
import streamlit.components.v1 as components
import folium
from streamlit_folium import st_folium

# Page Setup
st.set_page_config(layout="wide", page_title="Anas TCF Multi-Tool")

# --- 🎨 UI Fixes: Full Height Map & Sidebar ---
st.markdown("""
    <style>
        /* Sidebar ko top patti ke nichay rakhne ke liye */
        [data-testid="stSidebar"] { top: 60px !important; height: calc(100vh - 60px) !important; }
        /* Map ko nichay tak phelane ke liye padding khatam */
        .block-container { padding-top: 0rem !important; padding-bottom: 0rem !important; }
        iframe { border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 📁 Google Drive Direct IDs (Verified from your links) ---
files_config = {
    'pak_pop_2025.tif': '1OxPhQtpWnLKgr9qyntNmbPyHo5GtSSKO', # Total Pop 2025
    'pak_t_10_2025.tif': '1D7PTkPqCI9-dZ1_HLGZBw0vyobYCO0KU', # Secondary (10-14)
    'pak_t_05_2025.tif': '1dMtumXxkCnhduFbOOy47Ch4Ow8b0hAzB'  # Primary (5-9)
}

def download_file(file_id, output):
    if not os.path.exists(output):
        url = f'https://drive.google.com/uc?id={file_id}&export=download'
        with st.spinner(f'Connecting 2025 Data: {output}...'):
            try:
                r = requests.get(url, allow_redirects=True)
                with open(output, 'wb') as f:
                    f.write(r.content)
            except: st.error(f"Link Error: {output}")

# Navigation Sidebar
with st.sidebar:
    st.image("https://www.tcf.org.pk/wp-content/uploads/2019/09/logo.svg", width=120)
    st.title("Main Menu")
    app_mode = st.radio("Go to Window:", ["📊 Population Analysis", "🌍 Advanced GIS Map"])

# --- Window 1: Population Analysis ---
if app_mode == "📊 Population Analysis":
    # Pehli bar files download hongi (Size: ~400MB)
    for name, f_id in files_config.items(): download_file(f_id, name)
    
    if 'pos' not in st.session_state: st.session_state.pos = [24.8607, 67.0011]
    
    with st.sidebar:
        radius = st.slider("Search Radius (KM)", 0.5, 10.0, 2.0)
        
        def get_val(f_path):
            try:
                if not os.path.exists(f_path): return None
                with rasterio.open(f_path) as ds:
                    # Point query for 100m resolution
                    row, col = ds.index(st.session_state.pos[1], st.session_state.pos[0])
                    v = ds.read(1)[row, col]
                    return float(v) if v >= 0 and not np.isnan(v) else 0.0
            except: return 0.0

        t = get_val('pak_pop_2025.tif')
        p = get_val('pak_t_05_2025.tif')
        s = get_val('pak_t_10_2025.tif')
        area = math.pi * (radius**2)

        if t is None:
            st.info("🔄 Files are being prepared. Please refresh in a minute.")
        else:
            st.metric("Total Population (2025)", f"{int(t * area):,}")
            st.write(f"👶 **Primary (5-9):** {int(p * area):,}")
            st.write(f"🏫 **Secondary (10-14):** {int(s * area):,}")

    # Map with Increased Height (800)
    m = folium.Map(location=st.session_state.pos, zoom_start=13)
    folium.TileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google Satellite').add_to(m)
    folium.Circle(st.session_state.pos, radius=radius*1000, color='red', fill=True, fill_opacity=0.1).add_to(m)
    
    out = st_folium(m, width="100%", height=800)
    if out['last_clicked']:
        st.session_state.pos = [out['last_clicked']['lat'], out['last_clicked']['lng']]
        st.rerun()

# --- Window 2: GIS Map ---
elif app_mode == "🌍 Advanced GIS Map":
    try:
        with open("AnasGhouri_Ultimate_GIS.html", "r", encoding='utf-8') as f:
            components.html(f.read(), height=950, scrolling=True)
    except: st.error("GIS HTML file not found in GitHub.")
