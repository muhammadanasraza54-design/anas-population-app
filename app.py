import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import rasterio
import math
import re
import json
import os
from math import radians, cos, sin, asin, sqrt

# --- 1. CONFIG & CSS ---
st.set_page_config(layout="wide", page_title="Anas TCF Pro GIS")

st.markdown("""
    <style>
    .block-container { padding-top: 2rem !important; max-width: 100% !important; }
    .stMetric { background: #f0f2f6; padding: 10px; border-radius: 10px; }
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. CORE FUNCTIONS ---
def haversine(lat1, lon1, lat2, lon2):
    R = 6371 # km
    dLat, dLon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dLat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dLon/2)**2
    return 2 * asin(sqrt(a)) * R

def get_density(lat, lon):
    try:
        # Anas, make sure 'pak_pd_2020_1km.tif' is in your GitHub folder
        with rasterio.open('pak_pd_2020_1km.tif') as ds:
            row, col = ds.index(lon, lat)
            data = ds.read(1)
            val = data[row, col]
            return float(val) if val >= 0 and str(val) != 'nan' else 0.0
    except: return 0.0

# --- 3. DATA LOADING (EXCEL) ---
@st.cache_data
def load_excel_data():
    file_path = 'TCF_Mapp 1.xlsx'
    if os.path.exists(file_path):
        df = pd.read_excel(file_path)
        df.columns = [c.strip() for c in df.columns]
        # Level Logic
        df['level'] = df.apply(lambda x: 'Secondary' if 'secondary' in str(x).lower() else 'Primary', axis=1)
        # Year Logic
        df['final_year'] = pd.to_numeric(df.get('Year', 2024), errors='coerce').fillna(2024).astype(int)
        return df
    return None

df = load_excel_data()

# --- 4. SESSION STATE FOR POPULATION ---
if 'marker_pos' not in st.session_state:
    st.session_state.marker_pos = [24.8607, 67.0011]
if 'pop_density' not in st.session_state:
    st.session_state.pop_density = 0.0

# --- 5. SIDEBAR (Population & Stats) ---
with st.sidebar:
    st.image("https://www.tcf.org.pk/wp-content/uploads/2019/09/logo.svg", width=150)
    st.header("📊 Population Analytics")
    radius_km = st.slider("Population Radius (KM)", 0.5, 5.0, 1.0, 0.5)
    
    area = math.pi * (radius_km ** 2)
    density = get_density(st.session_state.marker_pos[0], st.session_state.marker_pos[1])
    total_pop = int(density * area)
    
    st.metric("Estimated Population", f"{total_pop:,}")
    st.write(f"👶 Primary Age (5-10): {int(total_pop * 0.15):,}")
    st.write(f"🏫 Secondary Age (11-16): {int(total_pop * 0.12):,}")
    
    st.markdown("---")
    if df is not None:
        st.header("🏫 School Stats")
        st.write(f"Total Schools: {len(df)}")
        st.write(f"Primary: {len(df[df['level']=='Primary'])}")
        st.write(f"Secondary: {len(df[df['level']=='Secondary'])}")

# --- 6. SEARCH BAR ---
search_input = st.text_input("🔍 Search Campus or Coordinates (Lat, Lon)", placeholder="e.g. 24.8, 67.1")

if search_input:
    coord_match = re.findall(r"[-+]?\d*\.\d+|\d+", search_input)
    if len(coord_match) >= 2:
        st.session_state.marker_pos = [float(coord_match[0]), float(coord_match[1])]

# --- 7. MAP CONSTRUCTION ---
m = folium.Map(location=st.session_state.marker_pos, zoom_start=13, tiles=None)

# Layers
folium.TileLayer('openstreetmap', name='Open Street Map').add_to(m)
folium.TileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                 attr='Google', name='Google Satellite (HD)', max_zoom=20).add_to(m)

# TCF School Markers
if df is not None:
    for _, row in df.iterrows():
        folium.Marker(
            [row['Latitude'], row['Longitude']],
            popup=f"<b>{row.get('Campus Name', 'School')}</b><br>Year: {row.get('final_year')}",
            icon=folium.Icon(color='blue' if row['level']=='Primary' else 'orange', icon='graduation-cap', prefix='fa')
        ).add_to(m)

# Selected Population Circle
folium.Circle(
    st.session_state.marker_pos, 
    radius=radius_km * 1000, 
    color='red', 
    fill=True, 
    fill_opacity=0.2,
    tooltip="Population Calculation Area"
).add_to(m)

folium.Marker(st.session_state.marker_pos, icon=folium.Icon(color='red', icon='crosshairs', prefix='fa')).add_to(m)

# Map Display
output = st_folium(m, width="100%", height=700)

# --- 8. CLICK HANDLING ---
if output['last_clicked']:
    cl_lat, cl_lon = output['last_clicked']['lat'], output['last_clicked']['lng']
    st.session_state.marker_pos = [cl_lat, cl_lon]
    st.rerun()
