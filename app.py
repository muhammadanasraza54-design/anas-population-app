import streamlit as st
import rasterio
from rasterio.windows import from_bounds
import math
import numpy as np
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import os

# Page config to use full width and hide extra padding
st.set_page_config(layout="wide", page_title="Anas TCF Pro Tool", initial_sidebar_state="expanded")

# 📁 Files configuration
FILES = {
    'total': 'pak_total_Pop FN.tif',
    'p05': 'pak_Pri_Pop FN.tif',
    'p10': 'pak_Sec_Pop FN.tif'
}

def get_pop_data(lat, lon, rad_km):
    results = {}
    deg_lat = rad_km / 111.0
    deg_lon = rad_km / (111.0 * math.cos(math.radians(lat)))
    left, bottom, right, top = (lon - deg_lon, lat - deg_lat, lon + deg_lon, lat + deg_lat)
    try:
        for key, path in FILES.items():
            if not os.path.exists(path): return None
            with rasterio.open(path) as ds:
                window = from_bounds(left, bottom, right, top, ds.transform)
                data = ds.read(1, window=window)
                results[key] = int(np.nansum(data[data > 0]))
        return results
    except: return None

if 'pos' not in st.session_state:
    st.session_state.pos = [24.8607, 67.0011]

# --- SIDEBAR ---
st.sidebar.title("TCF Catchment 2026")

search_query = st.sidebar.text_input("🔍 Search Location or Coordinates")
if st.sidebar.button("Search & Update"):
    if search_query:
        try:
            geolocator = Nominatim(user_agent="tcf_app_anas")
            location = geolocator.geocode(search_query)
            if location:
                st.session_state.pos = [location.latitude, location.longitude]
                st.rerun()
        except: st.sidebar.error("Search Error!")

st.sidebar.markdown("---")
st.sidebar.subheader("Range Settings")
radius = st.sidebar.number_input("Enter Radius (KM)", min_value=0.1, max_value=500.0, value=1.0, step=0.1)
diameter = radius * 2
st.sidebar.info(f"📏 **Diameter:** {diameter:.2f} KM")

data = get_pop_data(st.session_state.pos[0], st.session_state.pos[1], radius)

if data:
    st.sidebar.metric("📊 Total Population", f"{data['total']:,}")
    st.sidebar.write(f"👶 Primary (5-9): **{data['p05']:,}**")
    st.sidebar.write(f"🏫 Secondary (10-14): **{data['p10']:,}**")
    st.sidebar.markdown("---")
    st.sidebar.caption(f"📍 {st.session_state.pos[0]:.4f}, {st.session_state.pos[1]:.4f}")

# --- MAP SECTION ---
# CSS to remove top padding and make it look cleaner
st.markdown("""
    <style>
    .main > div { padding-top: 0rem; }
    iframe { margin-bottom: 0px !important; }
    </style>
    """, unsafe_allow_html=True)

m = folium.Map(location=st.session_state.pos, zoom_start=13, control_scale=True)
folium.TileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google', name='Satellite').add_to(m)

folium.Marker(st.session_state.pos, icon=folium.Icon(color="red", icon="info-sign")).add_to(m)
folium.Circle(st.session_state.pos, radius=radius*1000, color='red', fill=True, fill_opacity=0.2).add_to(m)

# ⬆️ Increased Height to 850 to cover the bottom space
out = st_folium(m, width="100%", height=850, key=f"map_{st.session_state.pos}_{radius}")

if out.get("last_clicked"):
    new_pos = [out["last_clicked"]["lat"], out["last_clicked"]["lng"]]
    if new_pos != st.session_state.pos:
        st.session_state.pos = new_pos
        st.rerun()
