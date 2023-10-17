import streamlit as st
import pandas as pd
from datetime import datetime 
from dateutil.relativedelta import relativedelta 
import geopandas as gpd
import pydeck as pdk


# @st.cache_data(experimental_allow_widgets=True)  # 👈 Set the parameter
def get_data():
  today = datetime.now()
  week = today + relativedelta(weeks=-1)
  max_date = (today + relativedelta(months=-3))
  d = st.date_input(
    "Select your vacation for next year",
    (week.date(),today.date()),
    max_date.date(),
    today.date(),
    
    format="MM.DD.YYYY",
  )
  
  try:
    df_raw = pd.read_csv(f"https://webservices.ingv.it/fdsnws/event/1/query?starttime={str(d[0].strftime('%Y-%m-%d'))}T00%3A00%3A00&endtime={str(d[1].strftime('%Y-%m-%d'))}T23%3A59%3A59&minmag=-1&maxmag=10&mindepth=-10&maxdepth=1000&minlat=35&maxlat=49&minlon=5&maxlon=20&minversion=100&orderby=time-asc&format=text&limit=10000",sep="|")

  except:
    st.spinner('Wait for it...')
    st.stop()
    
  df_fun = df_raw[df_raw.EventLocationName=="Campi Flegrei"][['Time', 'Latitude', 'Longitude', 'Depth/Km','Magnitude','EventLocationName']]
  
  gdf = gpd.GeoDataFrame(df_fun, geometry=gpd.points_from_xy(df_fun.Longitude, df_fun.Latitude), crs="EPSG:4326")    
  return gdf

df = get_data()

# Define a layer to display on a map
layer = pdk.Layer(
    "ScreenGridLayer",
    df,
    pickable=True,
    opacity=0.3,
    cell_size_pixels=30,
    get_position=["Longitude","Latitude"],
)

# Set the viewport location
view_state = pdk.ViewState(latitude=df.Latitude.mean(), longitude=df.Longitude.mean(), zoom=11, bearing=0, pitch=0)

# Render
r = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip={"text": "Number of earthquakes: {cellCount}"})


tab1, tab2, tab3 = st.tabs(["Cat", "Dog", "Owl"])

with tab1:
  st.pydeck_chart(pydeck_obj=r, use_container_width=True)

with tab2:
  st.table(data=df.drop("geometry",axis=1))
