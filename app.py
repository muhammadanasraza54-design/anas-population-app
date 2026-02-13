import streamlit as st
import os
import requests
import rasterio
import math
import numpy as np
import folium
from streamlit_folium import st_folium

st.set_page_config(layout="wide", page_title="Anas TCF Multi-Tool")

# --- 📁 Google Drive IDs ---
files_config = {
    'pak_pop_2025.tif': '1OxPhQtpWnLKgr9qyntNmbPyHo5GtSSKO',
    'pak_t_10_2025.tif': '1D7PTkPqCI9-dZ1_HLGZBw0vyobYCO0KU',
    'pak_t_05_2025.tif': '1dMtumXxkCnhduFbOOy47Ch4Ow8b0hAzB'
}

def download_with_progress(file_id, output):
    if not os.path.exists(output) or os.path.getsize(output) < 1000000:
        url = f'https://drive.google.com/uc?id={file_id}&export=download'
        session = requests.Session()
        response = session.get(url, stream=True)
        
        # Virus warning bypass
        token = None
        for key, value in response.cookies.items():
            if key.startswith('download_warning'):
                token = value
                break
        if token:
            response = session.get(url, params={'id': file_id, 'confirm': token}, stream=True)

        total_size = int(response.headers.get('content-length', 0))
        progress_bar = st.progress(0)
        st.write(f"Downloading {output}...")
        
        with open(output, "wb") as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=1024*1024): # 1MB chunks
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress_bar.progress(min(downloaded / total_size, 1.0))
        st.success(f"{output} Downloaded!")

# Sidebar Navigation
with st.sidebar:
    st.image("https://www.tcf.org.pk/wp-content/uploads/2019/09/logo.svg", width=100)
    app_mode = st.radio("Menu", ["📊 Population", "🌍 GIS Map"])

if app_mode == "📊 Population":
    # Debug: Check if files exist
    for name, f_id in files_config.items():
        download_with_progress(f_id, name)
    
    # Population Calculation Logic
    if 'pos' not in st.session_state: st.session_state.pos = [24.8607, 67.0011]
    
    radius = st.sidebar.slider("Radius (KM)", 0.5, 10.0, 2.0)
    
    def get_val(f_path):
        try:
            if os.path.exists(f_path) and os.path.getsize(f_path) > 100000000:
                with rasterio.open(f_path) as ds:
                    row, col = ds.index(st.session_state.pos[1], st.session_state.pos[0])
                    v = ds.read(1)[row, col]
                    return float(v) if v >= 0 else 0.0
            return 0.0
        except: return 0.0

    t_pop = get_val('pak_pop_2025.tif')
    area = math.pi * (radius**2)
    
    # Display Result
    st.sidebar.metric("Total Population", f"{int(t_pop * area):,}")
    
    m = folium.Map(location=st.session_state.pos, zoom_start=12)
    folium.TileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google').add_to(m)
    folium.Circle(st.session_state.pos, radius=radius*1000, color='red', fill=True).add_to(m)
    
    out = st_folium(m, width="100%", height=700)
    if out['last_clicked']:
        st.session_state.pos = [out['last_clicked']['lat'], out['last_clicked']['lng']]
        st.rerun()
