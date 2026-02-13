import streamlit as st
import rasterio
import math
import numpy as np
import folium
from streamlit_folium import st_folium

st.set_page_config(layout="wide", page_title="Anas TCF Tool")

# 📁 Files configuration - Aapki nayi files ke naam
FILES = {
    'total': 'pak_total_Pop_FN.tif',
    'p05': 'pak_Pri_Pop_FN.tif',
    'p10': 'pak_Sec_Pop_FN.tif'
}

def get_pop_data(lat, lon, rad):
    try:
        results = {}
        for key, path in FILES.items():
            with rasterio.open(path) as ds:
                row, col = ds.index(lon, lat)
                val = ds.read(1)[row, col]
                # Filter null/negative values
                val = max(0, float(val)) if not np.isnan(val) else 0
                # Integration for density across area
                results[key] = int(val * math.pi * (rad**2))
        return results
    except Exception as e:
        return None

# Sidebar Setup
st.sidebar.title("TCF Population 2025")
radius = st.sidebar.slider("Radius (KM)", 0.5, 5.0, 2.0, step=0.5)

if 'pos' not in st.session_state:
    st.session_state.pos = [24.8607, 67.0011] # Karachi Start

data = get_pop_data(st.session_state.pos[0], st.session_state.pos[1], radius)

if data:
    st.sidebar.metric("Total Population", f"{data['total']:,}")
    st.sidebar.write(f"👶 Primary (5-9): **{data['p05']:,}**")
    st.sidebar.write(f"🏫 Secondary (10-14): **{data['p10']:,}**")

# Interactive Map
m = folium.Map(location=st.session_state.pos, zoom_start=12)
folium.TileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google', name='Satellite').add_to(m)
folium.Circle(st.session_state.pos, radius=radius*1000, color='red', fill=True, fill_opacity=0.3).add_to(m)

out = st_folium(m, width="100%", height=700)
if out['last_clicked']:
    st.session_state.pos = [out['last_clicked']['lat'], out['last_clicked']['lng']]
    st.rerun()
