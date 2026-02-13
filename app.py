import streamlit as st
import rasterio
from rasterio.windows import from_bounds
import math
import numpy as np
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import os

st.set_page_config(layout="wide", page_title="Anas TCF Pro Tool")

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

# Initialize session state
if 'pos' not in st.session_state:
    st.session_state.pos = [24.8607, 67.0011]

# --- SIDEBAR SEARCH ---
st.sidebar.title("TCF Catchment 2025")

# 🔍 Direct Search Box
search_query = st.sidebar.text_input("🔍 Search Location or Coordinates", placeholder="e.g. Orangi Town or 24.8, 67.1")

if st.sidebar.button("Search & Update"):
    if search_query:
        try:
            geolocator = Nominatim(user_agent="tcf_app")
            location = geolocator.geocode(search_query)
            if location:
                st.session_state.pos = [location.latitude, location.longitude]
                st.sidebar.success(f"Found: {location.address[:30]}...")
                st.rerun()
            else:
                st.sidebar.error("Location nahi mili!")
        except:
            st.sidebar.error("Search error!")

st.sidebar.markdown("---")
radius = st.sidebar.slider("Select Radius (KM)", 0.5, 5.0, 1.0, step=0.5)

# Calculate Data
data = get_pop_data(st.session_state.pos[0], st.session_state.pos[1], radius)

if data:
    st.sidebar.metric("📊 Total Population", f"{data['total']:,}")
    st.sidebar.write(f"👶 Primary: **{data['p05']:,}**")
    st.sidebar.write(f"🏫 Secondary: **{data['p10']:,}**")
    st.sidebar.info(f"📍 Lat: {st.session_state.pos[0]:.4f}, Lon: {st.session_state.pos[1]:.4f}")

# --- MAP ---
m = folium.Map(location=st.session_state.pos, zoom_start=14)
folium.TileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google', name='Satellite').add_to(m)

# Always show Pin and Circle at st.session_state.pos
folium.Marker(st.session_state.pos, icon=folium.Icon(color="red", icon="info-sign")).add_to(m)
folium.Circle(st.session_state.pos, radius=radius*1000, color='red', fill=True, fill_opacity=0.2).add_to(m)

out = st_folium(m, width="100%", height=700, key=f"map_{st.session_state.pos}")

# Click handling
if out.get("last_clicked"):
    new_pos = [out["last_clicked"]["lat"], out["last_clicked"]["lng"]]
    if new_pos != st.session_state.pos:
        st.session_state.pos = new_pos
        st.rerun()
