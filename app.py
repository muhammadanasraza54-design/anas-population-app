import streamlit as st
import rasterio
import folium
from streamlit_folium import st_folium

st.title("Anas Ghouri - Population Finder")

# Map setup
m = folium.Map(location=[24.8607, 67.0011], zoom_start=12)
folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attr='Google', name='Google Satellite'
).add_to(m)

# Map display
output = st_folium(m, width=800, height=500)

# Click logic
if output['last_clicked']:
    lat = output['last_clicked']['lat']
    lon = output['last_clicked']['lng']
    try:
        with rasterio.open('pak_pd_2020_1km.tif') as ds:
            row, col = ds.index(lon, lat)
            data = ds.read(1)
            pop = round(float(data[row, col]), 2)
            st.success(f"Coordinates: {lat}, {lon} | Population: {pop}")
    except:
        st.error("Data not found for this location.")
