import streamlit as st
import folium
from streamlit_folium import st_folium
import rasterio
import math

# --- POPULATION FUNCTION ---
def get_density(lat, lon):
    try:
        # TIF file must be in your GitHub
        with rasterio.open('pak_pd_2020_1km.tif') as ds:
            row, col = ds.index(lon, lat)
            data = ds.read(1)
            val = data[row, col]
            return float(val) if val >= 0 and not math.isnan(val) else 0.0
    except: return 0.0

st.set_page_config(layout="wide", page_title="Population Pro")

if 'marker_pos' not in st.session_state:
    st.session_state.marker_pos = [24.8607, 67.0011]

# --- SIDEBAR (ONLY POPULATION) ---
with st.sidebar:
    st.header("📊 Population Analytics")
    radius_km = st.slider("Radius (KM)", 0.5, 10.0, 2.0)
    density = get_density(st.session_state.marker_pos[0], st.session_state.marker_pos[1])
    total_pop = int(density * (math.pi * radius_km**2))
    
    st.metric("Total Population", f"{total_pop:,}")
    st.write(f"👶 Primary: {int(total_pop * 0.15):,}")
    st.write(f"🏫 Secondary: {int(total_pop * 0.12):,}")

# --- CLEAN MAP (NO PINS) ---
m = folium.Map(location=st.session_state.marker_pos, zoom_start=13)
folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google', name='Satellite').add_to(m)

# Selection Circle
folium.Circle(st.session_state.marker_pos, radius=radius_km*1000, color='red', fill=True, fill_opacity=0.15).add_to(m)

# Center Point Only
folium.Marker(st.session_state.marker_pos, icon=folium.Icon(color='red', icon='crosshairs', prefix='fa')).add_to(m)

map_output = st_folium(m, width="100%", height=600)

if map_output['last_clicked']:
    st.session_state.marker_pos = [map_output['last_clicked']['lat'], map_output['last_clicked']['lng']]
    st.rerun()
