import streamlit as st
import os
import requests
import rasterio
import math
import numpy as np
import streamlit.components.v1 as components
import folium
from streamlit_folium import st_folium

# Page Configuration
st.set_page_config(layout="wide", page_title="Anas TCF Multi-Tool")

# --- 🎨 CSS: UI Fixes (Sidebar & Full Screen Map) ---
st.markdown("""
    <style>
        [data-testid="stSidebar"] { top: 60px !important; height: calc(100vh - 60px) !important; }
        .block-container { padding-top: 0rem !important; padding-bottom: 0rem !important; }
        iframe { border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 📁 Google Drive IDs (2025 Data) ---
files_config = {
    'pak_pop_2025.tif': '1OxPhQtpWnLKgr9qyntNmbPyHo5GtSSKO',
    'pak_t_10_2025.tif': '1D7PTkPqCI9-dZ1_HLGZBw0vyobYCO0KU',
    'pak_t_05_2025.tif': '1dMtumXxkCnhduFbOOy47Ch4Ow8b0hAzB'
}

# --- 🛠️ Function: Large File Bypass Download ---
def download_large_file(file_id, output):
    if not os.path.exists(output) or os.path.getsize(output) < 1000000:
        with st.spinner(f'2025 Data Download ho raha hai: {output}... Is mein 1-2 minute lag saktay hain.'):
            session = requests.Session()
            url = "https://docs.google.com/uc?export=download"
            
            # Pehli request virus warning check karne ke liye
            response = session.get(url, params={'id': file_id}, stream=True)
            token = None
            for key, value in response.cookies.items():
                if key.startswith('download_warning'):
                    token = value
                    break
            
            # Agar token mil jaye (bari file ke liye), dobara request bhejein
            if token:
                response = session.get(url, params={'id': file_id, 'confirm': token}, stream=True)
            
            try:
                with open(output, "wb") as f:
                    for chunk in response.iter_content(32768):
                        if chunk: f.write(chunk)
            except Exception as e:
                st.error(f"Download fail: {e}")

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.image("https://www.tcf.org.pk/wp-content/uploads/2019/09/logo.svg", width=120)
    st.title("Main Menu")
    app_mode = st.radio("Go to Window:", ["📊 Population Analysis", "🌍 Advanced GIS Map"])

# --- POPULATION ENGINE ---
if app_mode == "📊 Population Analysis":
    # Automatic download check
    for name, f_id in files_config.items():
        download_large_file(f_id, name)
    
    if 'pos' not in st.session_state:
        st.session_state.pos = [24.8607, 67.0011]
    
    with st.sidebar:
        radius = st.slider("Search Radius (KM)", 0.5, 10.0, 2.0)
        
        def get_val(f_path):
            try:
                if not os.path.exists(f_path) or os.path.getsize(f_path) < 1000000:
                    return None
                with rasterio.open(f_path) as ds:
                    row, col = ds.index(st.session_state.pos[1], st.session_state.pos[0])
                    v = ds.read(1)[row, col]
                    return float(v) if v >= 0 and not np.isnan(v) else 0.0
            except:
                return 0.0

        t = get_val('pak_pop_2025.tif')
        p = get_val('pak_t_05_2025.tif')
        s = get_val('pak_t_10_2025.tif')
        area = math.pi * (radius**2)

        if t is None:
            st.warning("🔄 Data Loading... Please wait.")
        else:
            st.metric("Total Population (2025)", f"{int(t * area):,}")
            st.markdown("---")
            st.write(f"👶 **Primary (5-9):** {int(p * area):,}")
            st.write(f"🏫 **Secondary (10-14):** {int(s * area):,}")

    # Full Screen Map
    m = folium.Map(location=st.session_state.pos, zoom_start=13)
    folium.TileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google Satellite').add_to(m)
    folium.Circle(st.session_state.pos, radius=radius*1000, color='red', fill=True, fill_opacity=0.1).add_to(m)
    
    out = st_folium(m, width="100%", height=800)
    if out['last_clicked']:
        st.session_state.pos = [out['last_clicked']['lat'], out['last_clicked']['lng']]
        st.rerun()

# --- GIS MAP WINDOW ---
elif app_mode == "🌍 Advanced GIS Map":
    try:
        with open("AnasGhouri_Ultimate_GIS.html", "r", encoding='utf-8') as f:
            components.html(f.read(), height=950, scrolling=True)
    except:
        st.error("GIS HTML file not found.")
