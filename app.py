import ipyleaflet as L
from ipyleaflet import (
    Map, basemaps, basemap_to_tiles,
    Circle, Marker, Rectangle, LayerGroup, DivIcon)
import pandas as pd
import numpy as np
from shiny import ui, render, App, reactive
from shinywidgets import output_widget, reactive_read, register_widget, render_widget
import plotly.express as px
import plotly.graph_objs as go
from pathlib import Path

# --- beginning of the calculations ---

season = 'spring'

def csv_file_procedure():
    global df

    path = Path(__file__).parent / "./data/data_2022.csv"

    df = pd.read_csv(path, sep=';' , encoding='latin-1', decimal=',')
    df['year'] = pd.DatetimeIndex(df['time']).year
    df['month'] = pd.DatetimeIndex(df['time']).month
    df['date'] = pd.DatetimeIndex(df['time']).date

    season_dict = {1: 'winter',
                2: 'winter',
                3: 'spring', 
                4: 'spring',
                5: 'spring',
                6: 'summer',
                7: 'summer',
                8: 'summer',
                9: 'fall',
                10: 'fall',
                11: 'fall',
                12: 'winter'}
    df['season'] = df['month'].apply(lambda x: season_dict[x])

def season_records():
    #high season records
    season_avg_temp_low_value = find_season_record(df, 'temp_avg', 'high', season, False)
    season_avg_temp_low_city = find_season_record(df, 'temp_avg', 'high', season, True)

    season_avg_ap_temp_low_value = find_season_record(df, 'ap_temp_avg', 'high', season, False)
    season_avg_ap_temp_low_city = find_season_record(df, 'ap_temp_avg', 'high', season, True)

    season_rainy_days_most_value = find_season_record(df, 'rainy_days', 'high', season, False)
    season_rainy_days_most_city = find_season_record(df, 'rainy_days', 'high', season, True)

    season_snow_days_most_value = find_season_record(df, 'snow_days', 'high', season, False)
    season_snow_days_most_city = find_season_record(df, 'snow_days', 'high', season, True)

    season_windy_days_most_value = find_season_record(df, 'windy_days', 'high', season, False)
    season_windy_days_most_city = find_season_record(df, 'windy_days', 'high', season, True)

    season_cloudy_days_most_value = find_season_record(df, 'cloudy_days', 'high', season, False)
    season_cloudy_days_most_city = find_season_record(df, 'cloudy_days', 'high', season, True)

    #low season records
    season_avg_temp_low_value = find_season_record(df, 'temp_avg', 'low', season, False)
    season_avg_temp_low_city = find_season_record(df, 'temp_avg', 'low', season, True)

    season_avg_ap_temp_low_value = find_season_record(df, 'ap_temp_avg', 'low', season, False)
    season_avg_ap_temp_low_city = find_season_record(df, 'ap_temp_avg', 'low', season, True)

    season_rainy_days_least_value = find_season_record(df, 'rainy_days', 'low', season, False)
    season_rainy_days_least_city = find_season_record(df, 'rainy_days', 'low', season, True)

    season_snow_days_least_value = find_season_record(df, 'snow_days', 'low', season, False)
    season_snow_days_least_city = find_season_record(df, 'snow_days', 'low', season, True)

    season_windy_days_least_value = find_season_record(df, 'windy_days', 'low', season, False)
    season_windy_days_least_city = find_season_record(df, 'windy_days', 'low', season, True)

    season_cloudy_days_least_value = find_season_record(df, 'cloudy_days', 'low', season, False)
    season_cloudy_days_least_city = find_season_record(df, 'cloudy_days', 'low', season, True)

def find_season_record(df, type: str, record: str, season: str, city: bool):
    #1: temp_avg/ap_temp_avg/rainy_days/snow_days/windy_days/cloudy_days
    #2: high/low
    #3: spring/summer/autumn/winter

    if (record == 'high'):
        asc = False
    elif (record == 'low'):
        asc = True

    match type:
        case 'temp_avg':
            column = 'temperature_2m (°C)'
        case 'ap_temp_avg':
            column = 'apparent_temperature (°C)'
        case 'rainy_days':
            column = 'rain (mm)'
        case 'snow_days':
            column = 'snowfall (cm)'
        case 'windy_days':
            column = 'windspeed_10m (km/h)'
        case 'cloudy_days':
            column = 'cloudcover (%)'

    if (type in ('temp_avg', 'ap_temp_avg')):
        result_df = df.loc[df['season'] == season].groupby(['city', 'season'], as_index = False).agg({column: np.mean}).sort_values(column, ascending = asc).head(1)
        if (city == True):
            return(result_df.city.values[0])
        else:
            return(result_df[column].values[0])
    elif (type in ('rainy_days', 'snow_days', 'windy_days', 'cloudy_days')):
        match type: #value of daily average to classify a day as a rainy or a snow day
            case 'rainy_days':
                quali = 0.1 #mm
            case 'snow_days':
                quali = 0.001 #cm
            case 'windy_days':
                quali = 17 #km/h
            case 'cloudy_days':
                quali = 60 #%
        result_df = df.loc[df['season'] == season].groupby(['city','season','date'], as_index = False).agg({column: np.mean})
        result_df = result_df.loc[result_df[column] >= quali]
        result_df = result_df.groupby(['city'], as_index = False).count().sort_values(column, ascending = asc).head(1)
        if (city == True):
            return(result_df.city.values[0])
        else:
            return(result_df[column].values[0])

def find_map_summary(df, season: str):
    global map_df
    global map_ap_temp_df

    map_filter_df = df.loc[df['season'] == season]

    map_df = map_filter_df.groupby(['city', 'season'], as_index = False).agg(lambda x:x.value_counts().index[0])
    map_df = map_df[['city', 'season', 'weathercode (wmo code)', 'apparent_temperature (°C)']]

    #TBD: use avg temp during the day only instead of day&night
    #second map df because uses different aggregation method
    map_ap_temp_df = map_filter_df.groupby(['city', 'season'], as_index = False).agg({'apparent_temperature (°C)': np.mean})
    map_ap_temp_df = map_ap_temp_df[['city', 'season', 'apparent_temperature (°C)']]
    map_ap_temp_df['apparent_temperature (°C)'] = map_ap_temp_df['apparent_temperature (°C)'].round(0)

    print (map_ap_temp_df)

    weathercode_dict = {0: 'clear',
                1: 'almost clear',
                2: 'little cloudy', 
                3: 'cloudy',
                51: 'drizzle',
                53: 'drizzle',
                55: 'drizzle',
                61: 'slight rain',
                63: 'moderate rain',
                65: 'heavy fall',
                71: 'slight snow',
                73: 'moderate snow',
                75: 'heavy snow'}
    #based on https://library.wmo.int/doc_num.php?explnum_id=10235 page 382

    #translating weathercode into weather name
    map_df['weather'] = map_df['weathercode (wmo code)'].map(weathercode_dict)
    
# --- preparation before running the server ---

csv_file_procedure()
season_records()
find_map_summary(df, season)

#print (map_df)

#print (map_df.loc[map_df['city'] == 'Warszawa']['weathercode (wmo code)'].values[0])

# --- beggining of the server & interface ---
seasons = ["spring", "summer", "fall", "winter"]
cities = df['city'].values.tolist()
parameters = df.head()

app_ui = ui.page_fluid(
    ui.a("Weather data by Open-Meteo.com", href="https://open-meteo.com/"),
    ui.input_select("season_select", "Season", seasons),
    ui.h4("Map - Most Common Weather"),
    ui.output_text("my_text"),
    output_widget("map"),
    ui.h4("Comparison"),
    ui.input_select("city1_select", "City 1", cities),
    ui.input_select("city2_select", "City 2", cities),
    ui.input_select("parameter_select", "Parameter", list(df.columns)),
    output_widget("snow_plot")
)

def server(input, output, session):
    @output
    @render.text
    def my_text():
        return "In 2022, " + str.capitalize(input.season_select()) + " in Poland was like:"
    
    @reactive.Effect
    def _():
        season = input.season_select()
        csv_file_procedure()
        season_records()
        find_map_summary(df, season)
        i_warsaw = DivIcon(html='<font size="1"><center><b>Warszawa</b><br>%s, %s&deg</center>' %((map_df.loc[map_df['city'] == 'Warszawa']['weather'].values[0]), (map_ap_temp_df.loc[map_ap_temp_df['city'] == 'Warszawa']['apparent_temperature (°C)'].values[0])), bg_pos=[0, 0], icon_size=[65, 30])
        m_warsaw = Marker(location=(52.2298, 21.0118), title = "Warsaw", draggable = False, icon = i_warsaw)

        i_bialystok = DivIcon(html='<font size="1"><center><b>Białystok</b><br>%s, %s&deg</center>' %((map_df.loc[map_df['city'] == 'Bialystok']['weather'].values[0]), (map_ap_temp_df.loc[map_ap_temp_df['city'] == 'Bialystok']['apparent_temperature (°C)'].values[0])), bg_pos=[0, 0], icon_size=[65, 30])
        m_bialystok = Marker(location=(53.1333, 23.1643), title = "Białystok", draggable = False, icon = i_bialystok)
        
        i_bielsko = DivIcon(html='<font size="1"><center><b>Bielsko-Biała</b><br>%s, %s&deg</center>' %((map_df.loc[map_df['city'] == 'BielskoBiala']['weather'].values[0]), (map_ap_temp_df.loc[map_ap_temp_df['city'] == 'BielskoBiala']['apparent_temperature (°C)'].values[0])), bg_pos=[0, 0], icon_size=[65, 30])
        m_bielsko = Marker(location=(49.8225, 19.0469), title = "Bielsko-Biała", draggable = False, icon = i_bielsko)

        i_bydgoszcz = DivIcon(html='<font size="1"> <center><b>Bydgoszcz</b><br>%s, %s&deg</center>' %((map_df.loc[map_df['city'] == 'Bydgoszcz']['weather'].values[0]), (map_ap_temp_df.loc[map_ap_temp_df['city'] == 'Bydgoszcz']['apparent_temperature (°C)'].values[0])), bg_pos=[0, 0], icon_size=[65, 30])
        m_bydgoszcz = Marker(location=(53.1235, 18.0076), title = "Bydgoszcz", draggable = False, icon = i_bydgoszcz)

        i_ciechanow = DivIcon(html='<font size="1"> <center><b>Ciechanów</b><br>%s, %s&deg</center>' %((map_df.loc[map_df['city'] == 'Ciechanow']['weather'].values[0]), (map_ap_temp_df.loc[map_ap_temp_df['city'] == 'Ciechanow']['apparent_temperature (°C)'].values[0])), bg_pos=[0, 0], icon_size=[65, 30])
        m_ciechanow = Marker(location=(52.8814, 20.62), title = "Ciechanów", draggable = False, icon = i_ciechanow)

        i_elblag = DivIcon(html='<font size="1"> <center><b>Elbląg</b><br>%s, %s&deg</center>' %((map_df.loc[map_df['city'] == 'Elblag']['weather'].values[0]), (map_ap_temp_df.loc[map_ap_temp_df['city'] == 'Elblag']['apparent_temperature (°C)'].values[0])), bg_pos=[0, 0], icon_size=[65, 30])
        m_elblag = Marker(location=(54.1522, 19.4088), title = "Elbląg", draggable = False, icon = i_elblag)

        i_gdansk = DivIcon(html='<font size="1"> <center><b>Gdańsk</b><br>%s, %s&deg</center>' %((map_df.loc[map_df['city'] == 'Gdansk']['weather'].values[0]), (map_ap_temp_df.loc[map_ap_temp_df['city'] == 'Gdansk']['apparent_temperature (°C)'].values[0])), bg_pos=[0, 0], icon_size=[65, 30])
        m_gdansk = Marker(location=(54.523, 18.6491), title = "Gdańsk", draggable = False, icon = i_gdansk)

        i_katowice = DivIcon(html='<font size="1"> <center><b>Katowice</b><br>%s, %s&deg</center>' %((map_df.loc[map_df['city'] == 'Katowice']['weather'].values[0]), (map_ap_temp_df.loc[map_ap_temp_df['city'] == 'Katowice']['apparent_temperature (°C)'].values[0])), bg_pos=[0, 0], icon_size=[65, 30])
        m_katowice = Marker(location=(50.2584, 19.0275), title = "Katowice", draggable = False, icon = i_katowice)

        i_krakow = DivIcon(html='<font size="1"> <center><b>Kraków</b><br>%s, %s&deg</center>' %((map_df.loc[map_df['city'] == 'Kraków']['weather'].values[0]), (map_ap_temp_df.loc[map_ap_temp_df['city'] == 'Kraków']['apparent_temperature (°C)'].values[0])), bg_pos=[0, 0], icon_size=[65, 30])
        m_krakow = Marker(location=(50.0614, 19.9366), title = "Kraków", draggable = False, icon = i_krakow)

        i_kielce = DivIcon(html='<font size="1"> <center><b>Kielce</b><br>%s, %s&deg</center>' %((map_df.loc[map_df['city'] == 'Kielce']['weather'].values[0]), (map_ap_temp_df.loc[map_ap_temp_df['city'] == 'Kielce']['apparent_temperature (°C)'].values[0])), bg_pos=[0, 0], icon_size=[65, 30])
        m_kielce = Marker(location=(50.8703, 20.6275), title = "Kielce", draggable = False, icon = i_kielce)

        i_koszalin = DivIcon(html='<font size="1"> <center><b>Koszalin</b><br>%s, %s&deg</center>' %((map_df.loc[map_df['city'] == 'Koszalin']['weather'].values[0]), (map_ap_temp_df.loc[map_ap_temp_df['city'] == 'Koszalin']['apparent_temperature (°C)'].values[0])), bg_pos=[0, 0], icon_size=[65, 30])
        m_koszalin = Marker(location=(54.1944, 16.1722), title = "Koszalin", draggable = False, icon = i_koszalin)

        i_krosno = DivIcon(html='<font size="1"> <center><b>Krosno</b><br>%s, %s&deg</center>' %((map_df.loc[map_df['city'] == 'Krosno']['weather'].values[0]), (map_ap_temp_df.loc[map_ap_temp_df['city'] == 'Krosno']['apparent_temperature (°C)'].values[0])), bg_pos=[0, 0], icon_size=[65, 30])
        m_krosno = Marker(location=(49.6887, 21.7706), title = "Krosno", draggable = False, icon = i_krosno)

        i_lodz = DivIcon(html='<font size="1"> <center><b>Łódź</b><br>%s, %s&deg</center>' %((map_df.loc[map_df['city'] == 'Lodz']['weather'].values[0]), (map_ap_temp_df.loc[map_ap_temp_df['city'] == 'Lodz']['apparent_temperature (°C)'].values[0])), bg_pos=[0, 0], icon_size=[65, 30])
        m_lodz = Marker(location=(51.7706, 19.4739), title = "Łódź", draggable = False, icon = i_lodz)

        i_lublin = DivIcon(html='<font size="1"> <center><b>Lublin</b><br>%s, %s&deg</center>' %((map_df.loc[map_df['city'] == 'Lublin']['weather'].values[0]), (map_ap_temp_df.loc[map_ap_temp_df['city'] == 'Lublin']['apparent_temperature (°C)'].values[0])), bg_pos=[0, 0], icon_size=[65, 30])
        m_lublin = Marker(location=(51.25, 22.5667), title = "Lublin", draggable = False, icon = i_lublin)

        i_olsztyn = DivIcon(html='<font size="1"> <center><b>Olsztyn</b><br>%s, %s&deg</center>' %((map_df.loc[map_df['city'] == 'Olsztyn']['weather'].values[0]), (map_ap_temp_df.loc[map_ap_temp_df['city'] == 'Olsztyn']['apparent_temperature (°C)'].values[0])), bg_pos=[0, 0], icon_size=[65, 30])
        m_olsztyn = Marker(location=(53,7799, 20.4942), title = "Olsztyn", draggable = False, icon = i_olsztyn)

        i_pila = DivIcon(html='<font size="1"> <center><b>Piła</b><br>%s, %s&deg</center>' %((map_df.loc[map_df['city'] == 'Pila']['weather'].values[0]), (map_ap_temp_df.loc[map_ap_temp_df['city'] == 'Pila']['apparent_temperature (°C)'].values[0])), bg_pos=[0, 0], icon_size=[65, 30])
        m_pila = Marker(location=(53.1514, 16.7378), title = "Piła", draggable = False, icon = i_pila)

        i_poznan = DivIcon(html='<font size="1"> <center><b>Poznań</b><br>%s, %s&deg</center>' %((map_df.loc[map_df['city'] == 'Poznan']['weather'].values[0]), (map_ap_temp_df.loc[map_ap_temp_df['city'] == 'Poznan']['apparent_temperature (°C)'].values[0])), bg_pos=[0, 0], icon_size=[65, 30])
        m_poznan = Marker(location=(52.4069, 16.9299), title = "Poznań", draggable = False, icon = i_poznan)

        i_rzeszow = DivIcon(html='<font size="1"> <center><b>Rzeszów</b><br>%s, %s&deg</center>' %((map_df.loc[map_df['city'] == 'Rzeszow']['weather'].values[0]), (map_ap_temp_df.loc[map_ap_temp_df['city'] == 'Rzeszow']['apparent_temperature (°C)'].values[0])), bg_pos=[0, 0], icon_size=[65, 30])
        m_rzeszow = Marker(location=(50.0413, 21.999), title = "Rzeszów", draggable = False, icon = i_rzeszow)

        i_slupsk = DivIcon(html='<font size="1"> <center><b>Słupsk</b><br>%s, %s&deg</center>' %((map_df.loc[map_df['city'] == 'Slupsk']['weather'].values[0]), (map_ap_temp_df.loc[map_ap_temp_df['city'] == 'Slupsk']['apparent_temperature (°C)'].values[0])), bg_pos=[0, 0], icon_size=[65, 30])
        m_slupsk = Marker(location=(54.4641, 17.0287), title = "Słupsk", draggable = False, icon = i_slupsk)

        i_suwalki = DivIcon(html='<font size="1"> <center><b>Suwałki</b><br>%s, %s&deg</center>' %((map_df.loc[map_df['city'] == 'Suwalki']['weather'].values[0]), (map_ap_temp_df.loc[map_ap_temp_df['city'] == 'Suwalki']['apparent_temperature (°C)'].values[0])), bg_pos=[0, 0], icon_size=[65, 30])
        m_suwalki = Marker(location=(54.1118, 22.9309), title = "Suwałki", draggable = False, icon = i_suwalki)

        i_szczecin = DivIcon(html='<font size="1"> <center><b>Szczecin</b><br>%s, %s&deg</center>' %((map_df.loc[map_df['city'] == 'Szczecin']['weather'].values[0]), (map_ap_temp_df.loc[map_ap_temp_df['city'] == 'Szczecin']['apparent_temperature (°C)'].values[0])), bg_pos=[0, 0], icon_size=[65, 30])
        m_szczecin = Marker(location=(53.4289, 14.553), title = "Szczecin", draggable = False, icon = i_szczecin)

        i_torun = DivIcon(html='<font size="1"> <center><b>Toruń</b><br>%s, %s&deg</center>' %((map_df.loc[map_df['city'] == 'Torun']['weather'].values[0]), (map_ap_temp_df.loc[map_ap_temp_df['city'] == 'Torun']['apparent_temperature (°C)'].values[0])), bg_pos=[0, 0], icon_size=[65, 30])
        m_torun = Marker(location=(53.0138, 18.5981), title = "Toruń", draggable = False, icon = i_torun)

        i_wroclaw = DivIcon(html='<font size="1"> <center><b>Wrocław</b><br>%s, %s&deg</center>' %((map_df.loc[map_df['city'] == 'Wroclaw']['weather'].values[0]), (map_ap_temp_df.loc[map_ap_temp_df['city'] == 'Wroclaw']['apparent_temperature (°C)'].values[0])), bg_pos=[0, 0], icon_size=[65, 30])
        m_wroclaw = Marker(location=(51.1, 17.0333), title = "Wrocław", draggable = False, icon = i_wroclaw)

        i_zakopane = DivIcon(html='<font size="1"> <center><b>Zakopane</b><br>%s, %s&deg</center>' %((map_df.loc[map_df['city'] == 'Zakopane']['weather'].values[0]), (map_ap_temp_df.loc[map_ap_temp_df['city'] == 'Zakopane']['apparent_temperature (°C)'].values[0])), bg_pos=[0, 0], icon_size=[65, 30])
        m_zakopane = Marker(location=(49.299, 19.9489), title = "Zakopane", draggable = False, icon = i_zakopane)

        i_zielonagora = DivIcon(html='<font size="1"> <center><b>Zielona Góra</b><br>%s, %s&deg</center>' %((map_df.loc[map_df['city'] == 'ZielonaGora']['weather'].values[0]), (map_ap_temp_df.loc[map_ap_temp_df['city'] == 'ZielonaGora']['apparent_temperature (°C)'].values[0])), bg_pos=[0, 0], icon_size=[65, 30])
        m_zielonagora = Marker(location=(51.9355, 15.5064), title = "Zielona Góra", draggable = False, icon = i_zielonagora)

        layer_group = LayerGroup(layers=(m_warsaw, m_bialystok, m_bielsko, m_bydgoszcz, m_ciechanow, m_elblag, m_gdansk, m_katowice, m_krakow, m_kielce, m_koszalin, m_krosno, m_lodz, m_lublin, m_olsztyn, m_pila, m_poznan, m_rzeszow, m_slupsk, m_suwalki, m_szczecin, m_torun, m_wroclaw, m_zakopane, m_zielonagora))
        map.add_layer(layer_group)
        
    map = L.Map(center=(51.919438, 19.14513599999998), zoom=5, scroll_wheel_zoom=True)
    map = Map(basemap=basemaps.CartoDB.Positron, center=(52.237049, 21.017532), zoom=7,
              dragging = True, zoom_control = False)
    register_widget("map", map)

    @output
    @render_widget
    def snow_plot():
        city1 = input.city1_select()
        city2 = input.city2_select()
        param = input.parameter_select()

        fig = px.line(df.loc[((df['city'] == city1) | (df['city'] == city2))], x="time", y=param, color='city', markers=True)
        fig.layout.height = 500
        return fig
        fig.show()

app = App(app_ui, server)
