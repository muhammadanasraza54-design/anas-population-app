import streamlit as st
import os
import requests
import rasterio
import math
import numpy as np
import streamlit.components.v1 as components
import folium
from streamlit_folium import st_folium

st.set_page_config(layout="wide", page_title="Anas TCF Multi-Tool")

# --- 🎨 CSS: Full Screen UI ---
st.markdown("""
    <style>
        [data-testid="stSidebar"] { top: 60px !important; height: calc(100vh - 60px) !important; }
        .block-container { padding-top: 0rem !important; padding-bottom: 0rem !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 📁 Google Drive IDs ---
files_config = {
    'pak_pop_2025.tif': '1OxPhQtpWnLKgr9qyntNmbPyHo5GtSSKO',
    'pak_t_10_2025.tif': '1D7PTkPqCI9-dZ1_HLGZBw0vyobYCO0KU',
    'pak_t_05_2025.tif': '1dMtumXxkCnhduFbOOy47Ch4Ow8b0hAzB'
}

# --- 🛠️ Download Function with Virus Bypass ---
def download_file(file_id, output):
    if not os.path.exists(output) or os.path.getsize(output) < 1000000:
        session = requests.Session()
        url = "https://docs.google.com/uc?export=download"
        response = session.get(url, params={'id': file_id}, stream=True)
        
        token = None
        for key, value in response.cookies.items():
            if key.startswith('download_warning'):
                token = value
                break
        if token:
            response = session.get(url, params={'id': file_id, 'confirm': token}, stream=True)
        
        with st.spinner(f'2025 Data: {output} download ho raha hai...'):
            with open(output, "wb") as f:
                for chunk in response.iter_content(32768):
                    if chunk: f.write(chunk)
        st.success(f"File {output} ready!")

# Sidebar Menu
with st.sidebar:
    st.image("https://www.tcf.org.pk/wp-content/uploads/2019/09/logo.svg", width=120)
    app_mode = st.radio("Go to:", ["📊 Population Analysis", "🌍 Advanced GIS Map"])

if app_mode == "📊 Population Analysis":
    # Download check
    for name, f_id in files_config.items():
        download_file(f_id, name)
    
    if 'pos' not in st.session_state: st.session_state.pos = [24.8607, 67.0011]
    
    with st.sidebar:
        radius = st.slider("Radius (KM)", 0.5, 10.0, 2.0)
        
        def get_val(f_path):
            try:
                # Agar file sahi download nahi hui to logic bypass karein
                if not os.path.exists(f_path) or os.path.getsize(f_path) < 1000000:
                    return None
                with rasterio.open(f_path) as ds:
                    row, col = ds.index(st.session_state.pos[1], st.session_state.pos[0])
                    v = ds.read(1)[row, col]
                    return float(v) if v >= 0 and not np.isnan(v) else 0.0
            except: return 0.0

        t = get_val('pak_pop_2025.tif')
        p = get_val('pak_t_05_2025.tif')
        s = get_val('pak_t_10_2025.tif')
        area = math.pi * (radius**2)

        if t is None:
            st.warning("⚠️ Files are heavy (400MB). Background mein download jari hai. 2-3 minute baad refresh karein.")
        else:
            st.metric("Total Population (2025)", f"{int(t * area):,}")
            st.write(f"👶 **Primary (5-9):** {int(p * area):,}")
            st.write(f"🏫 **Secondary (10-14):** {int(s * area):,}")

    # Map Height increased to fill screen
    m = folium.Map(location=st.session_state.pos, zoom_start=13)
    folium.TileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google Satellite').add_to(m)
    folium.Circle(st.session_state.pos, radius=radius*1000, color='red', fill=True, fill_opacity=0.1).add_to(m)
    
    out = st_folium(m, width="100%", height=800)
    if out['last_clicked']:
        st.session_state.pos = [out['last_clicked']['lat'], out['last_clicked']['lng']]
        st.rerun()

elif app_mode == "🌍 Advanced GIS Map":
    try:
        with open("AnasGhouri_Ultimate_GIS.html", "r", encoding='utf-8') as f:
            components.html(f.read(), height=950, scrolling=True)
    except: st.error("GIS File not found on GitHub.")
