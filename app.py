import streamlit as st
import rasterio
from rasterio.windows import from_bounds
import math
import numpy as np
import folium
from streamlit_folium import st_folium
import os

st.set_page_config(layout="wide", page_title="Anas TCF Tool")

# 📁 Exact File Names from your folder
FILES = {
    'total': 'pak_total_Pop FN.tif',
    'p05': 'pak_Pri_Pop FN.tif',
    'p10': 'pak_Sec_Pop FN.tif'
}

def get_pop_data(lat, lon, rad_km):
    results = {}
    # Approximation for lat/lon bounding box
    deg_lat = rad_km / 111.0
    deg_lon = rad_km / (111.0 * math.cos(math.radians(lat)))
    
    left, bottom, right, top = (lon - deg_lon, lat - deg_lat, lon + deg_lon, lat + deg_lat)

    try:
        for key, path in FILES.items():
            if not os.path.exists(path):
                return f"File '{path}' nahi mili."
            
            with rasterio.open(path) as ds:
                # Sirf utna hissa read karna jitna radius hai
                window = from_bounds(left, bottom, right, top, ds.transform)
                data = ds.read(1, window=window)
                
                # Filter out null/NaN and sum all pixels in the area
                valid_data = data[data > 0]
                total_val = np.nansum(valid_data)
                
                # WorldPop accuracy adjustment
                results[key] = int(total_val)
        return results
    except Exception as e:
        return f"Error: {str(e)}"

# Sidebar
st.sidebar.title("TCF Catchment 2025")
radius = st.sidebar.slider("Select Radius (KM)", 0.5, 5.0, 1.0, step=0.5)

if 'pos' not in st.session_state:
    st.session_state.pos = [24.8058, 67.1515] # Current view location

data = get_pop_data(st.session_state.pos[0], st.session_state.pos[1], radius)

if isinstance(data, dict):
    st.sidebar.metric("📊 Total Population", f"{data['total']:,}")
    st.sidebar.write(f"👶 Primary (5-9): **{data['p05']:,}**")
    st.sidebar.write(f"🏫 Secondary (10-14): **{data['p10']:,}**")
else:
    st.sidebar.error(data)

# Map View
m = folium.Map(location=st.session_state.pos, zoom_start=14)
folium.TileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google', name='Satellite').add_to(m)
folium.Circle(st.session_state.pos, radius=radius*1000, color='red', fill=True, fill_opacity=0.3).add_to(m)

out = st_folium(m, width="100%", height=700)
if out['last_clicked']:
    st.session_state.pos = [out['last_clicked']['lat'], out['last_clicked']['lng']]
    st.rerun()
