import streamlit as st
import rasterio
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import re

st.set_page_config(layout="wide")
st.title("Anas Ghouri - Population Finder & Search")

# Default location (Karachi)
start_lat, start_lon = 24.8607, 67.0011

search_query = st.text_input("Koi bhi jagah ya Coordinates likhein (e.g. 'Lahore' ya '24.8, 67.0'):")

if search_query:
    # Check if input is coordinates (e.g., "24.8, 67.1")
    coord_match = re.findall(r"[-+]?\d*\.\d+|\d+", search_query)
    if len(coord_match) >= 2:
        start_lat, start_lon = float(coord_match[0]), float(coord_match[1])
        st.success(f"Moving to Coordinates: {start_lat}, {start_lon}")
    else:
        # If not coordinates, try searching by name
        try:
            geolocator = Nominatim(user_agent="anas_population_app_v2")
            location = geolocator.geocode(search_query, timeout=10)
            if location:
                start_lat, start_lon = location.latitude, location.longitude
                st.success(f"Found: {location.address}")
            else:
                st.error("Jagah nahi mili, dobara koshish karein.")
        except:
            st.warning("Search service busy hai. Please coordinates (lat, lon) use karein.")

# Map Setup
m = folium.Map(location=[start_lat, start_lon], zoom_start=14)
folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attr='Google', name='Google Satellite'
).add_to(m)

# Map Display
output = st_folium(m, height=600, use_container_width=True, key=f"map_{start_lat}_{start_lon}")

# Click logic
if output['last_clicked']:
    lat, lon = output['last_clicked']['lat'], output['last_clicked']['lng']
    try:
        with rasterio.open('pak_pd_2020_1km.tif') as ds:
            row, col = ds.index(lon, lat)
            data = ds.read(1)
            pop = round(float(data[row, col]), 2)
            st.success(f"📍 Coordinates: {lat}, {lon} | 👥 Population: {pop}")
    except:
        st.error("Is jagah ka data majood nahi hai.")
