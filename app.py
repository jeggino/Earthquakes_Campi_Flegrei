import streamlit as st
import pandas as pd
from datetime import datetime 
from dateutil.relativedelta import relativedelta 
import geopandas as gpd
import pydeck as pdk
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go


img = "https://travelnostop.com/wp-content/uploads/2014/02/muqoy_campiflegrei-610x366.jpg"
st.sidebar.image(img)

today = datetime.now()
week = today + relativedelta(weeks=-1)
max_date = (today + relativedelta(months=-3))
d = st.sidebar.date_input(
  "'Select a range",
  (week.date(),today.date()),
  max_date.date(),
  today.date(),
  
  format="MM.DD.YYYY",
)

try:
  df_raw = pd.read_csv(f"https://webservices.ingv.it/fdsnws/event/1/query?starttime={str(d[0].strftime('%Y-%m-%d'))}T00%3A00%3A00&endtime={str(d[1].strftime('%Y-%m-%d'))}T23%3A59%3A59&minmag=-1&maxmag=10&mindepth=-10&maxdepth=1000&minlat=35&maxlat=49&minlon=5&maxlon=20&minversion=100&orderby=time-asc&format=text&limit=10000",sep="|")

except:
  st.stop()

magnitude_0, magnitude_1 = st.sidebar.slider(
  'Select a range of magnitude values',
  df_raw.Magnitude.min(), df_raw.Magnitude.max(), (df_raw.Magnitude.min(), df_raw.Magnitude.max())
)
MAGNITUDE = (df_raw.Magnitude>=magnitude_0) & (df_raw.Magnitude<=magnitude_1)

deep_0, deep_1 = st.sidebar.slider(
  'Select a range of depths values',
  df_raw["Depth/Km"].min(), df_raw["Depth/Km"].max(), (df_raw["Depth/Km"].min(), df_raw["Depth/Km"].max())
)
DEEP = (df_raw["Depth/Km"]>=deep_0) & (df_raw["Depth/Km"]<=deep_1)

df_fun = df_raw.loc[(df_raw.EventLocationName=="Campi Flegrei") & MAGNITUDE & DEEP]

gdf = gpd.GeoDataFrame(df_fun, geometry=gpd.points_from_xy(df_fun.Longitude, df_fun.Latitude), crs="EPSG:4326")    

df = gdf

# Set the viewport location
view_state = pdk.ViewState(latitude=df.Latitude.mean(), longitude=df.Longitude.mean(), zoom=11, bearing=0, pitch=0)

# Define a layer to display on a map
ScreenGridLayer = pdk.Layer(
    "ScreenGridLayer",
    df,
    pickable=True,
    opacity=0.3,
    cell_size_pixels=30,
    get_position=["Longitude","Latitude"],
)

# Render
r_ScreenGridLayer = pdk.Deck(layers=[ScreenGridLayer], initial_view_state=view_state, tooltip={"text": "Number of earthquakes: {cellCount}"})

HeatmapLayer = pdk.Layer(
    "HeatmapLayer",
    data=df,
    opacity=1,
    threshold=0.75,
    get_position=["Longitude","Latitude"],
)

# Render
r_HeatmapLayer = pdk.Deck(layers=[HeatmapLayer], initial_view_state=view_state)

# Define a layer to display on a map
HexagonLayer = pdk.Layer(
    "HexagonLayer",
    df,
    opacity=0.7,
    get_position=["Longitude","Latitude"],
    auto_highlight=True,
    elevation_scale=10,
    pickable=True,
    elevation_range=[0, 300],
    extruded=True,
    coverage=1,
    radius=200,
) 

# Set the viewport location
view_state_HexagonLayer = pdk.ViewState(latitude=df.Latitude.mean(), longitude=df.Longitude.mean(), zoom=13, pitch=40.5, bearing=-27.36,)

# Render
r_HexagonLayer = pdk.Deck(layers=[HexagonLayer], initial_view_state=view_state_HexagonLayer,tooltip={"text": "Number of earthquakes: {colorValue}"})



bins = 3

color_cat = dict(zip(sorted(pd.cut(df.Magnitude,bins=bins,include_lowest=True).unique().tolist()),
                     list(sns.color_palette("YlOrRd",n_colors=bins,))
                    )
                )

df["color_cat"] = pd.cut(df.Magnitude,bins=bins,include_lowest=True).tolist()
df["color_cat"] = df["color_cat"].map(color_cat)
df["color_cat"] = df["color_cat"].apply(lambda x: [round(i * 255) for i in x])

# Define a layer to display on a map
ScatterplotLayer = pdk.Layer(
    "ScatterplotLayer",
    df,
    pickable=True,
    opacity=0.6,
    stroked=False,
    filled=True,
    radius_scale=50,
    radius_min_pixels=1,
    radius_max_pixels=100000,
    get_position=["Longitude","Latitude"],
    get_radius="Magnitude",
    get_fill_color="color_cat",
)


# Render
r_ScatterplotLayer = pdk.Deck(layers=[ScatterplotLayer], initial_view_state=view_state,
            tooltip={"text": "Date: {Time} \n Magnitude: {Magnitude} \n Depth (Km): {Depth/Km}"})


df["date"] = pd.to_datetime(df.Time).dt.date

fig = px.scatter_mapbox(
    df,
    opacity=0.8,
    lat="Latitude",
    lon="Longitude",
    zoom=11,
    color="Magnitude",
    size="Depth/Km",
    animation_frame="date",
    range_color=(0,5),
    color_continuous_scale="ylorrd",
    hover_name="date",
    hover_data={
                "Depth/Km":True,
                "Longitude":False,
                "date":False,
                "Latitude":False},
    template="plotly_dark",
    
)


fig.update_layout(
    mapbox_style='carto-darkmatter',
    font_family="fantasy",
    font_size=13,
    hoverlabel=dict(font_size=12),
    sliders=[{"currentvalue":{"prefix": "","font_size":14,},
              "font_size":12,
              }]
)


tab1, tab2, tab3,  tab5 = st.tabs(["ScreenGrid", "Heatmap", "Hexagon", "Timelapse"])

with tab1:
  st.pydeck_chart(pydeck_obj=r_ScreenGridLayer, use_container_width=True)

with tab2:
  st.pydeck_chart(pydeck_obj=r_HeatmapLayer, use_container_width=True)

with tab3:
  st.pydeck_chart(pydeck_obj=r_HexagonLayer, use_container_width=True)

# with tab4:
#   st.pydeck_chart(pydeck_obj=r_ScatterplotLayer, use_container_width=True)

if st.button("update"):
    st.rerun()

with tab5:
  st.plotly_chart(fig, use_container_width=True)


