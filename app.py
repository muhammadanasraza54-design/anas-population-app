import streamlit as st
import rasterio
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

st.set_page_config(layout="wide")
st.title("Anas Ghouri - Population Finder & Search")

# Search Logic
geolocator = Nominatim(user_agent="anas_app")
search_query = st.text_input("Koi bhi jagah ya Coordinates likhein (e.g. 'Lahore' ya '24.8, 67.0'):")

# Default location (Karachi)
start_lat, start_lon = 24.8607, 67.0011

if search_query:
    location = geolocator.geocode(search_query)
    if location:
        start_lat, start_lon = location.latitude, location.longitude
        st.success(f"Found: {location.address}")
    else:
        st.error("Jagah nahi mili, dobara koshish karein.")

# Map Setup
m = folium.Map(location=[start_lat, start_lon], zoom_start=14)
folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attr='Google', name='Google Satellite'
).add_to(m)

# Click logic function
def get_population(lat, lon):
    try:
        with rasterio.open('pak_pd_2020_1km.tif') as ds:
            row, col = ds.index(lon, lat)
            data = ds.read(1)
            return round(float(data[row, col]), 2)
    except:
        return None

# Map Display
output = st_folium(m, height=600, use_container_width=True, key="map")

# Population result display
if output['last_clicked']:
    lat = output['last_clicked']['lat']
    lon = output['last_clicked']['lng']
    pop = get_population(lat, lon)
    if pop is not None:
        st.success(f"📍 Coordinates: {lat}, {lon} | 👥 Population: {pop}")
    else:
        st.warning("Is area ka data available nahi hai.")
