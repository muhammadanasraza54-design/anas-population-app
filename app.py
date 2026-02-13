import streamlit as st
import os
import requests
import rasterio
import math
import numpy as np
import folium
from streamlit_folium import st_folium

# Page Config
st.set_page_config(layout="wide", page_title="Anas TCF Multi-Tool")

# --- 📁 Google Drive IDs (2025 Data) ---
files_config = {
    'total.tif': '1OxPhQtpWnLKgr9qyntNmbPyHo5GtSSKO',
    'p05.tif': '1dMtumXxkCnhduFbOOy47Ch4Ow8b0hAzB',
    'p10.tif': '1D7PTkPqCI9-dZ1_HLGZBw0vyobYCO0KU'
}

# --- 🛠️ Function: Bypass Virus Warning & Download ---
def download_large_file(file_id, output):
    if not os.path.exists(output) or os.path.getsize(output) < 1000000:
        session = requests.Session()
        # Direct Download Link with Token Handling
        url = "https://docs.google.com/uc?export=download"
        response = session.get(url, params={'id': file_id}, stream=True)
        
        token = None
        for key, value in response.cookies.items():
            if key.startswith('download_warning'):
                token = value
                break
        
        if token:
            response = session.get(url, params={'id': file_id, 'confirm': token}, stream=True)
        
        with st.spinner(f'Bari File Load ho rahi hai: {output}... 1-2 minute lag saktay hain.'):
            try:
                with open(output, "wb") as f:
                    for chunk in response.iter_content(32768):
                        if chunk: f.write(chunk)
                st.success(f"{output} ready!")
            except Exception as e:
                st.error(f"Download error: {e}")

# Sidebar
with st.sidebar:
    st.image("https://www.tcf.org.pk/wp-content/uploads/2019/09/logo.svg", width=100)
    st.title("TCF Analysis")
    
    # Download start
    for name, f_id in files_config.items():
        download_large_file(f_id, name)

    radius = st.slider("Radius (KM)", 0.5, 5.0, 2.0)

# Position Logic
if 'pos' not in st.session_state:
    st.session_state.pos = [24.8607, 67.0011]

# Population Calculation Engine
def get_val(f_path, lat, lon):
    try:
        if not os.path.exists(f_path) or os.path.getsize(f_path) < 1000000:
            return 0.0
        with rasterio.open(f_path) as ds:
            # Point query
            row, col = ds.index(lon, lat)
            v = ds.read(1)[row, col]
            return float(v) if v >= 0 and not np.isnan(v) else 0.0
    except:
        return 0.0

# Calculate results
area = math.pi * (radius**2)
val_total = get_val('total.tif', st.session_state.pos[0], st.session_state.pos[1])
val_p05 = get_val('p05.tif', st.session_state.pos[0], st.session_state.pos[1])
val_p10 = get_val('p10.tif', st.session_state.pos[0], st.session_state.pos[1])

# Sidebar Results
st.sidebar.metric("Total Population (2025)", f"{int(val_total * area):,}")
st.sidebar.write(f"👶 Primary (5-9): {int(val_p05 * area):,}")
st.sidebar.write(f"🏫 Secondary (10-14): {int(val_p10 * area):,}")

# Full Screen Map
m = folium.Map(location=st.session_state.pos, zoom_start=13)
folium.TileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google Satellite').add_to(m)
folium.Circle(st.session_state.pos, radius=radius*1000, color='red', fill=True, fill_opacity=0.2).add_to(m)

out = st_folium(m, width="100%", height=800)

if out['last_clicked']:
    st.session_state.pos = [out['last_clicked']['lat'], out['last_clicked']['lng']]
    st.rerun()
