import streamlit as st
import rasterio
import folium
from streamlit_folium import st_folium

# Ye line app ko wide (chaura) kar degi
st.set_page_config(layout="wide")

st.title("Anas Ghouri - Population Finder")

# Map setup - Zoom thora behtar kiya hai
m = folium.Map(location=[24.8607, 67.0011], zoom_start=12)
folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attr='Google', name='Google Satellite'
).add_to(m)

# Map display - Width aur Height badha di gayi hai
output = st_folium(m, width=1400, height=700, use_container_width=True)

# Click logic
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
        st.error("Is jagah ka data majood nahi hai.")
