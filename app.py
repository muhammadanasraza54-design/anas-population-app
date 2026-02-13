import streamlit as st
import rasterio
import math
import numpy as np
import folium
from streamlit_folium import st_folium
import os

st.set_page_config(layout="wide", page_title="Anas TCF Tool")

# 📁 Files ke exact naam (Spaces ke sath)
FILES = {
    'total': 'pak_total_Pop FN.tif',
    'p05': 'pak_Pri_Pop FN.tif',
    'p10': 'pak_Sec_Pop FN.tif'
}

def get_pop_data(lat, lon, rad):
    results = {}
    try:
        for key, path in FILES.items():
            if not os.path.exists(path):
                return f"Error: {path} nahi mili"
            
            with rasterio.open(path) as ds:
                # Coordinate ko pixel mein badalna
                row, col = ds.index(lon, lat)
                window = ds.read(1)
                
                # Pixel ki asli value lena
                pixel_val = window[row, col]
                pixel_val = max(0, float(pixel_val)) if not np.isnan(pixel_val) else 0
                
                # 🛠️ Calculation Update:
                # Agar population bohot kam aa rahi hai, toh iska matlab hai pixel value 
                # ko area se multiply karne ki zaroorat hai. 
                # WorldPop ka 1 pixel taqreeban 100m (0.01 sq km) ka hota hai.
                # Hum radius ke hisab se circle ka area nikal kar multiply kar rahe hain.
                area_sq_km = math.pi * (rad**2)
                
                # WorldPop density ko area se multiply karein (assuming 100m resolution)
                # Hum yahan pixel value ko scale up kar rahe hain
                results[key] = int(pixel_val * area_sq_km * 100) 
        return results
    except Exception as e:
        return str(e)

# Sidebar UI
st.sidebar.title("TCF Catchment 2025")
radius = st.sidebar.slider("Select Radius (KM)", 0.5, 5.0, 2.0, step=0.5)

if 'pos' not in st.session_state:
    st.session_state.pos = [24.8607, 67.0011]

data = get_pop_data(st.session_state.pos[0], st.session_state.pos[1], radius)

if isinstance(data, dict):
    # Metrics display
    st.sidebar.metric("📊 Total Population", f"{data['total']:,}")
    st.sidebar.write(f"👶 Primary (5-9): **{data['p05']:,}**")
    st.sidebar.write(f"🏫 Secondary (10-14): **{data['p10']:,}**")
else:
    st.sidebar.error(data)

# Map
m = folium.Map(location=st.session_state.pos, zoom_start=13)
folium.TileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google', name='Satellite').add_to(m)
folium.Circle(st.session_state.pos, radius=radius*1000, color='red', fill=True, fill_opacity=0.3).add_to(m)

out = st_folium(m, width="100%", height=750)
if out['last_clicked']:
    st.session_state.pos = [out['last_clicked']['lat'], out['last_clicked']['lng']]
    st.rerun()
