import streamlit as st
import rasterio
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import re

# 1. Page Configuration
st.set_page_config(layout="wide", page_title="Anas Ghouri - Population Finder")

# CSS for better styling
st.markdown("""
    <style>
    .main > div { padding-top: 2rem; }
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

st.title("🌍 Anas Ghouri - Population Finder & Search")

# 2. State Management (Pin aur Circle ki memory ke liye)
if 'marker_pos' not in st.session_state:
    st.session_state.marker_pos = None

# Default Start Location (Karachi)
start_lat, start_lon = 24.8607, 67.0011

# 3. Search Bar
search_query = st.text_input("Search Location (Place name or Coordinates like 24.8, 67.0):")

if search_query:
    # Pehle check karein ke kya ye coordinates hain
    coord_match = re.findall(r"[-+]?\d*\.\d+|\d+", search_query)
    if len(coord_match) >= 2:
        start_lat, start_lon = float(coord_match[0]), float(coord_match[1])
        st.session_state.marker_pos = [start_lat, start_lon]
    else:
        # Agar coordinates nahi hain toh naam se search karein
        try:
            geolocator = Nominatim(user_agent="anas_explorer_app")
            location = geolocator.geocode(search_query, timeout=10)
            if location:
                start_lat, start_lon = location.latitude, location.longitude
                st.session_state.marker_pos = [start_lat, start_lon]
                st.success(f"📍 Found: {location.address}")
            else:
                st.error("Location not found. Please try again.")
        except:
            st.warning("Search service busy. Try using coordinates directly.")

# 4. Map Setup
m = folium.Map(location=[start_lat, start_lon], zoom_start=14)
folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attr='Google', name='Google Satellite'
).add_to(m)

# 5. Marker aur Circle add karna
if st.session_state.marker_pos:
    p_lat, p_lon = st.session_state.marker_pos
    folium.Marker(
        [p_lat, p_lon], 
        popup="Selected Point", 
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(m)
    
    folium.Circle(
        location=[p_lat, p_lon],
        radius=500, # 500 meters
        color='yellow',
        fill=True,
        fill_opacity=0.3
    ).add_to(m)

# 6. Display Map
# Key mein start_lat is liye dala hai taake search karte hi map jump kare
output = st_folium(m, height=600, use_container_width=True, key=f"map_{start_lat}")

# 7. Click & Population Logic
if output['last_clicked']:
    lat, lon = output['last_clicked']['lat'], output['last_clicked']['lng']
    st.session_state.marker_pos = [lat, lon]
    
    try:
        with rasterio.open('pak_pd_2020_1km.tif') as ds:
            row, col = ds.index(lon, lat)
            data = ds.read(1)
            pop_value = data[row, col]
            
            # Error check for water or out of bounds
            if pop_value < 0 or str(pop_value) == 'nan':
                st.warning(f"📍 Coordinates: {lat}, {lon} | 👥 Data not available here (Likely water or empty land).")
            else:
                pop = round(float(pop_value), 2)
                st.success(f"📍 Coordinates: {lat}, {lon} | 👥 Population Density: {pop} per sq km")
        
        # UI refresh for marker update
        st.rerun()
        
    except Exception as e:
        st.error("Point is outside the data coverage area.")
