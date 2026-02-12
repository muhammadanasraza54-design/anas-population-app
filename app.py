import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
import rasterio
import math
import os
import re
from math import radians, cos, sin, asin, sqrt

# --- 1. CONFIG ---
st.set_page_config(layout="wide", page_title="Anas TCF Pro GIS")

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dLat, dLon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dLat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dLon/2)**2
    return 2 * asin(sqrt(a)) * R

def get_density(lat, lon):
    try:
        # Anas, ensure 'pak_pd_2020_1km.tif' is in your GitHub folder
        with rasterio.open('pak_pd_2020_1km.tif') as ds:
            row, col = ds.index(lon, lat)
            data = ds.read(1)
            val = data[row, col]
            return float(val) if val >= 0 and not math.isnan(val) else 0.0
    except: return 0.0

# --- 2. DATA LOADING ---
@st.cache_data
def load_excel_data():
    file_path = 'TCF_Mapp 1.xlsx' # As per your GitHub screenshot
    if os.path.exists(file_path):
        df = pd.read_excel(file_path)
        df.columns = [str(c).strip().lower() for c in df.columns]
        if 'year' in df.columns:
            df['final_year'] = pd.to_numeric(df['year'], errors='coerce').fillna(2024).astype(int)
        return df
    return None

df_all = load_excel_data()

# --- 3. SESSION STATE ---
if 'marker_pos' not in st.session_state:
    st.session_state.marker_pos = [24.8607, 67.0011]

# --- 4. SIDEBAR (Analytics & Settings) ---
with st.sidebar:
    st.image("https://www.tcf.org.pk/wp-content/uploads/2019/09/logo.svg", width=150)
    st.header("📊 Analytics")
    radius_km = st.slider("Search Radius (KM)", 0.5, 10.0, 2.0)
    
    # Population Logic
    density = get_density(st.session_state.marker_pos[0], st.session_state.marker_pos[1])
    total_pop = int(density * (math.pi * radius_km**2))
    
    st.metric("Total Population", f"{total_pop:,}")
    st.write(f"👶 Primary (5-10): {int(total_pop * 0.15):,}")
    st.write(f"🏫 Secondary (11-16): {int(total_pop * 0.12):,}")
    
    st.markdown("---")
    if df_all is not None:
        st.write(f"Total Schools in DB: {len(df_all)}")

# --- 5. SEARCH & UI ---
search_input = st.text_input("🔍 Search Coordinates (Lat, Lon)", placeholder="e.g. 24.89, 67.15")
if search_input:
    coord_match = re.findall(r"[-+]?\d*\.\d+|\d+", search_input)
    if len(coord_match) >= 2:
        st.session_state.marker_pos = [float(coord_match[0]), float(coord_match[1])]

# --- 6. MAP CONSTRUCTION ---
m = folium.Map(location=st.session_state.marker_pos, zoom_start=12, prefer_canvas=True)

# Google Satellite HD
folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attr='Google', name='Google Satellite', overlay=False
).add_to(m)

# Cluster Markers for performance
marker_cluster = MarkerCluster(name="TCF Schools").add_to(m)

if df_all is not None:
    for _, row in df_all.iterrows():
        # Lat/Lon are small letters in your Excel
        folium.Marker(
            [row['lat'], row['lon']],
            popup=f"School: {row.get('school')}<br>Year: {row.get('final_year')}",
            icon=folium.Icon(color='blue', icon='graduation-cap', prefix='fa')
        ).add_to(marker_cluster)

# Red Circle for Area
folium.Circle(
    st.session_state.marker_pos, 
    radius=radius_km*1000, 
    color='red', fill=True, fill_opacity=0.15
).add_to(m)

# Target Marker
folium.Marker(st.session_state.marker_pos, icon=folium.Icon(color='red', icon='crosshairs', prefix='fa')).add_to(m)

# Display
map_output = st_folium(m, width="100%", height=600)

if map_output['last_clicked']:
    st.session_state.marker_pos = [map_output['last_clicked']['lat'], map_output['last_clicked']['lng']]
    st.rerun()
