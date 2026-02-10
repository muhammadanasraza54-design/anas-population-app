import streamlit as st
import rasterio
import folium
from streamlit_folium import st_folium

# 1. Ye sab se zaroori line hai full screen ke liye
st.set_page_config(layout="wide")

# CSS ke zariye padding khatam karna taake map kinaro tak jaye
st.markdown("""
    <style>
    .main > div { padding-top: 2rem; }
    iframe { width: 100% !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("Anas Ghouri - Population Finder")

# 2. Map Setup
m = folium.Map(location=[24.8607, 67.0011], zoom_start=12)
folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attr='Google', name='Google Satellite'
).add_to(m)

# 3. Map Display (use_container_width=True se ye poori screen cover karega)
output = st_folium(m, height=600, use_container_width=True)

# 4. Click Logic
if output['last_clicked']:
    lat = output['last_clicked']['lat']
    lon = output['last_clicked']['lng']
    try:
        with rasterio.open('pak_pd_2020_1km.tif') as ds:
            row, col = ds.index(lon, lat)
            data = ds.read(1)
            pop = round(float(data[row, col]), 2)
            st.success(f"📍 Coordinates: {lat}, {lon} | 👥 Population: {pop}")
    except:
        st.error("Data not found.")
