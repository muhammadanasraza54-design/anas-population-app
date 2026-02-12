import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import rasterio
import math
import re
import os
from math import radians, cos, sin, asin, sqrt

# --- 1. CONFIG & CSS ---
st.set_page_config(layout="wide", page_title="Anas TCF Pro GIS")

st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; max-width: 100% !important; }
    .stMetric { background: #f0f2f6; padding: 10px; border-radius: 10px; }
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. CORE FUNCTIONS ---
def get_density(lat, lon):
    try:
        # Anas, 'pak_pd_2020_1km.tif' must be in your GitHub root
        with rasterio.open('pak_pd_2020_1km.tif') as ds:
            row, col = ds.index(lon, lat)
            data = ds.read(1)
            val = data[row, col]
            return float(val) if val >= 0 and not math.isnan(val) else 0.0
    except: 
        return 0.0

# --- 3. DATA LOADING ---
@st.cache_data
def load_excel_data():
    # --- FIXED FILE NAME ACCORDING TO YOUR SCREENSHOT ---
    file_path = 'TCF_Mapp 1.xlsx' 
    
    if os.path.exists(file_path):
        df = pd.read_excel(file_path)
        # Column names clean karein (lowercase aur no spaces)
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        # School Level Logic
        if 'school' in df.columns:
            df['level_display'] = df['school'].apply(lambda x: 'Secondary' if 'secondary' in str(x).lower() else 'Primary')
        else:
            df['level_display'] = 'Primary'

        # Year Logic (Fixing the AttributeError from your screenshot)
        if 'year' in df.columns:
            df['final_year'] = pd.to_numeric(df['year'], errors='coerce').fillna(2024).astype(int)
        else:
            df['final_year'] = 2024
            
        return df
    return None

df = load_excel_data()

# --- 4. SESSION STATE ---
if 'marker_pos' not in st.session_state:
    st.session_state.marker_pos = [24.8607, 67.0011]

# --- 5. SIDEBAR ---
with st.sidebar:
    st.image("https://www.tcf.org.pk/wp-content/uploads/2019/09/logo.svg", width=150)
    st.header("📊 Analytics")
    radius_km = st.slider("Radius (KM)", 0.5, 5.0, 1.5, 0.5)
    
    density = get_density(st.session_state.marker_pos[0], st.session_state.marker_pos[1])
    total_pop = int(density * (math.pi * radius_km**2))
    
    st.metric("Total Population", f"{total_pop:,}")
    if df is not None:
        st.write(f"Schools Found: {len(df)}")
    else:
        st.error(f"File '{file_path}' not found on GitHub!")

# --- 6. MAP & UI ---
search_input = st.text_input("🔍 Search Coordinates or School", placeholder="e.g. 24.89, 67.15")
if search_input:
    coord_match = re.findall(r"[-+]?\d*\.\d+|\d+", search_input)
    if len(coord_match) >= 2:
        st.session_state.marker_pos = [float(coord_match[0]), float(coord_match[1])]

m = folium.Map(location=st.session_state.marker_pos, zoom_start=12)

# Google Satellite Layer
folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attr='Google', name='Google Satellite', overlay=False
).add_to(m)

# Plot Schools
if df is not None and 'lat' in df.columns and 'lon' in df.columns:
    for _, row in df.iterrows():
        folium.Marker(
            [row['lat'], row['lon']],
            popup=f"School: {row.get('school')}<br>Year: {row.get('final_year')}",
            icon=folium.Icon(color='blue' if row['level_display']=='Primary' else 'orange', icon='graduation-cap', prefix='fa')
        ).add_to(m)

folium.Circle(st.session_state.marker_pos, radius=radius_km*1000, color='red', fill=True, fill_opacity=0.2).add_to(m)
folium.Marker(st.session_state.marker_pos, icon=folium.Icon(color='red', icon='crosshairs', prefix='fa')).add_to(m)

map_output = st_folium(m, width="100%", height=600)

if map_output['last_clicked']:
    st.session_state.marker_pos = [map_output['last_clicked']['lat'], map_output['last_clicked']['lng']]
    st.rerun()
