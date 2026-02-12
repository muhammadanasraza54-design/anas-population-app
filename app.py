import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
import rasterio
import math
import os
from math import radians, cos, sin, asin, sqrt

# --- 1. CONFIG ---
st.set_page_config(layout="wide", page_title="Anas TCF Pro GIS")

# Fast Distance Calc
def fast_haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dLat, dLon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dLat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dLon/2)**2
    return 2 * asin(sqrt(a)) * R

# --- 2. DATA LOADING (CACHED) ---
@st.cache_data
def load_excel_data():
    file_path = 'TCF_Mapp 1.xlsx' 
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

# --- 4. SIDEBAR & ANALYTICS ---
with st.sidebar:
    st.header("⚙️ Settings")
    radius_km = st.slider("Search Radius (KM)", 0.5, 10.0, 2.0)
    
    # Filter schools nearby (Speed Boost!)
    nearby_df = pd.DataFrame()
    if df_all is not None:
        # Sirf wahi schools filter karein jo radius mein hain
        df_all['dist'] = df_all.apply(lambda x: fast_haversine(st.session_state.marker_pos[0], st.session_state.marker_pos[1], x['lat'], x['lon']), axis=1)
        nearby_df = df_all[df_all['dist'] <= radius_km]

    st.metric("Nearby Schools", len(nearby_df))
    st.write(f"Total Schools in DB: {len(df_all) if df_all is not None else 0}")

# --- 5. MAP CONSTRUCTION (OPTIMIZED) ---
st.subheader(f"📍 Analysis for Lat: {st.session_state.marker_pos[0]:.4f}, Lon: {st.session_state.marker_pos[1]:.4f}")

m = folium.Map(location=st.session_state.marker_pos, zoom_start=13, prefer_canvas=True)

# Satellite Layer
folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attr='Google', name='Google Satellite', overlay=False
).add_to(m)

# 1. Cluster nearby schools only (Hazaar markers ke bajaye sirf kareeb wale)
marker_cluster = MarkerCluster(name="TCF Schools").add_to(m)

for _, row in nearby_df.iterrows():
    folium.Marker(
        [row['lat'], row['lon']],
        popup=f"School: {row.get('school')}<br>Year: {row.get('final_year')}",
        icon=folium.Icon(color='blue', icon='graduation-cap', prefix='fa')
    ).add_to(marker_cluster)

# 2. Search Area Circle
folium.Circle(
    st.session_state.marker_pos, 
    radius=radius_km*1000, 
    color='red', fill=True, fill_opacity=0.1
).add_to(m)

# 3. Center Crosshair
folium.Marker(st.session_state.marker_pos, icon=folium.Icon(color='red', icon='crosshairs', prefix='fa')).add_to(m)

# Render Map
map_output = st_folium(m, width="100%", height=550, key="main_map")

# Click Update
if map_output['last_clicked']:
    new_pos = [map_output['last_clicked']['lat'], map_output['last_clicked']['lng']]
    if new_pos != st.session_state.marker_pos:
        st.session_state.marker_pos = new_pos
        st.rerun()
