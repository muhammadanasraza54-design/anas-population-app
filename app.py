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

# --- 🎨 CSS: Header aur Sidebar Fix (Patti ke nichay se start) ---
st.markdown("""
    <style>
        [data-testid="stSidebar"] { 
            top: 60px !important; 
            height: calc(100vh - 60px) !important; 
        }
        .block-container { 
            padding-top: 0rem !important; 
            padding-bottom: 0rem !important; 
        }
        iframe { border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 📁 Drive IDs: In ko apni sahi IDs se badalna hai ---
# Har file ke share link se ID nikal kar yahan paste karein
files_config = {
    'pak_pop_2025.tif': '1PbWVI5Iw2x1c1JC0-XFKYKxiFdWEFppD', 
    'pak_t_05_2025.tif': '1PbWVI5Iw2x1c1JC0-XFKYKxiFdWEFppD', 
    'pak_t_10_2025.tif': '1PbWVI5Iw2x1c1JC0-XFKYKxiFdWEFppD'
}

def download_file(file_id, output):
    if not os.path.exists(output):
        # Direct download link format
        url = f'https://drive.google.com/uc?id={file_id}&export=download'
        with st.spinner(f'2025 Data connect ho raha hai: {output}...'):
            try:
                r = requests.get(url, allow_redirects=True)
                with open(output, 'wb') as f:
                    f.write(r.content)
            except Exception as e:
                st.error(f"Download Error for {output}: {e}")

# Navigation
with st.sidebar:
    st.image("https://www.tcf.org.pk/wp-content/uploads/2019/09/logo.svg", width=120)
    st.title("Main Menu")
    app_mode = st.radio("Go to Window:", ["📊 Population Analysis", "🌍 Advanced GIS Map"])

# Population Window
if app_mode == "📊 Population Analysis":
    # Sirf naye 2025 data ko download aur use karega
    for name, f_id in files_config.items(): 
        download_file(f_id, name)
    
    if 'pos' not in st.session_state: 
        st.session_state.pos = [24.8607, 67.0011]
    
    st.subheader("2025 Population Analytics (100m Precision)")
    
    with st.sidebar:
        radius = st.slider("Radius (KM)", 0.5, 10.0, 2.0)
        area = math.pi * (radius**2)
        
        def get_val(f_path):
            try:
                if not os.path.exists(f_path): return 0.0
                with rasterio.open(f_path) as ds:
                    # Lat/Lon ko coordinates mein badalna
                    row, col = ds.index(st.session_state.pos[1], st.session_state.pos[0])
                    v = ds.read(1)[row, col]
                    return float(v) if v >= 0 and not np.isnan(v) else 0.0
            except: return 0.0

        # Nayi files se data lena
        t = get_val('pak_pop_2025.tif')
        p = get_val('pak_t_05_2025.tif')
        s = get_val('pak_t_10_2025.tif')

        st.metric("Total Population (2025)", f"{int(t * area):,}")
        st.markdown("---")
        st.write(f"👶 **Primary (Age 5-9):** {int(p * area):,}")
        st.write(f"🏫 **Secondary (Age 10-14):** {int(s * area):,}")

    # Map height barha di gayi hai
    m = folium.Map(location=st.session_state.pos, zoom_start=13)
    folium.TileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google Satellite').add_to(m)
    folium.Circle(st.session_state.pos, radius=radius*1000, color='red', fill=True, fill_opacity=0.1).add_to(m)
    
    out = st_folium(m, width="100%", height=800)
    if out['last_clicked']:
        st.session_state.pos = [out['last_clicked']['lat'], out['last_clicked']['lng']]
        st.rerun()

elif app_mode == "🌍 Advanced GIS Map":
    # GIS Map Window
    st.markdown("<style>.block-container {padding: 0rem;}</style>", unsafe_allow_html=True)
    try:
        with open("AnasGhouri_Ultimate_GIS.html", "r", encoding='utf-8') as f:
            components.html(f.read(), height=950, scrolling=True)
    except: 
        st.error("GIS HTML file (AnasGhouri_Ultimate_GIS.html) nahi mili.")
