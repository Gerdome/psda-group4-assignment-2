import os
import time

from calendar import monthrange

import psycopg2             # For postgres

import pandas as pd
import geopandas as gpd

import folium

import selenium.webdriver   # For generating screenshots of HTML files

# Configuration
FROM_YEAR = 2010
TO_YEAR = 2019

OUT_DIR = "output"

def analyseForYear(yearStr, monthStr="", dayStr=""):
    print(yearStr)

    # Connect to database
    connection = psycopg2.connect(host="193.196.37.97", database="postgres",user="postgres", password="SDAPraktikum2020")
    cursor = connection.cursor()

    # Get all temps for stations in year
    #airtemps2010 = pd.read_sql_query("SELECT sts.stations_id, sts.stationsname, vals.temperature_day, vals.messdatum_date FROM air_temperature_values as vals LEFT JOIN air_temperature_stations as sts ON vals.stations_id = sts.stations_id WHERE vals.messdatum_date >= date('2010-01-01') AND vals.messdatum_date <= date('2010-12-31')", connection)
    #airtemps2010

    # Get all average temps for stations in year
    if monthStr != "":
        if dayStr != "":
            # query for day
            query = "SELECT sts.stationsname, AVG(vals.temperature_day) as avg_temp FROM air_temperature_values as vals LEFT JOIN air_temperature_stations as sts ON vals.stations_id = sts.stations_id WHERE vals.messdatum_date>= date('" + yearStr + "-" + monthStr + "-" + dayStr + "') GROUP BY sts.stationsname"
        else:
            # query for one month
            daysInMonth = monthrange(int(yearStr), int(monthStr))[1]
            query = "SELECT sts.stationsname, AVG(vals.temperature_day) as avg_temp FROM air_temperature_values as vals LEFT JOIN air_temperature_stations as sts ON vals.stations_id = sts.stations_id WHERE vals.messdatum_date >= date('" + yearStr + "-" + monthStr + "-01') AND vals.messdatum_date <= date('" + yearStr + "-" + monthStr + "-" + str(daysInMonth) + "') GROUP BY sts.stationsname"
    else:
        # query for whole year
        query = "SELECT sts.stationsname, AVG(vals.temperature_day) as avg_temp FROM air_temperature_values as vals LEFT JOIN air_temperature_stations as sts ON vals.stations_id = sts.stations_id WHERE vals.messdatum_date >= date('" + yearStr + "-01-01') AND vals.messdatum_date <= date('" + yearStr + "-12-31') GROUP BY sts.stationsname"

    print(query)
    avgTemps = pd.read_sql_query(query, connection)

    # Load station list with Landkreise political regions
    stationsKreise = pd.read_csv("stations+counties.csv")

    # Convert to geopandas data frame with geometry column
    geometry = gpd.points_from_xy(x=stationsKreise.geobreite_x, y=stationsKreise.geolaenge_x)
    stationsKreise = stationsKreise.drop(['stationshoehe_x', 'geobreite_x', 'geolaenge_x'], axis=1)
    stationsKreise = gpd.GeoDataFrame(stationsKreise, crs='EPSG:4326', geometry=geometry)  # "EPSG:4326" is WGS84 long-lat

    # Remove columns not needed here
    stationsKreise = stationsKreise.drop(['Unnamed: 0', 'von_datum', 'bis_datum'], axis=1)

    # Join on temperatures table with statstationsname
    joined = avgTemps.set_index('stationsname').join(stationsKreise.set_index('stationsname'))
    joined = gpd.GeoDataFrame(joined, crs='EPSG:4326', geometry='geometry')  # Re-add the geometry information

    # Search for rows without Kreis avialble
    stationsWithoutKreis = []
    for row in joined.iterrows():
        name, vals = row
        avg, kreis, geom = vals
        
        kreisname = str(kreis)
        if kreisname == "nan":
            print("No Kreis for station", name)
            stationsWithoutKreis.append(name)

    # Remove stations from list that have no kreis aka is NaN
    kreisTemps = joined.dropna()

    # Count stations per kreis
    stationsPerKreis = kreisTemps[['Landkreis', 'avg_temp']].groupby(['Landkreis']).agg('count')
    stationsPerKreis.rename(columns={'avg_temp':'Stations'}, inplace=True)
    stationsPerKreis = stationsPerKreis.sort_values(by=['Stations'])
    stationsPerKreis

    # # Visualize Stations density
    # # Create map focussed on Germany
    # densMap = folium.Map(location=[51.3, 10.1], zoom_start=6)  # This zooms the map to focus on germany (coods 51.3, 10.1)

    # # Add federal states overlay
    # germany_political = 'landkreise-in-germany.geojson'

    # folium.Choropleth(
    #     geo_data=germany_political,
    #     geo_str='choropleth',
    #     data=stationsPerKreis,
    #     columns=[stationsPerKreis.index, 'Stations'],
    #     key_on = 'feature.properties.name_2',
    #     fill_color='YlOrRd',
    #     fill_opacity=0.7,
    #     line_opacity=0.2,
    #     legend_name='Number of Stations',
    #     highlight=True
    # ).add_to(densMap)

    # densMap.save("output/densmap-" + yearStr + ".html")

    # Now group by and average on Kreise
    kreisTempsAvg = kreisTemps.groupby(['Landkreis']).mean()

    # Create map focussed on Germany
    m = folium.Map(location=[51.3, 10.1], zoom_start=6.45)  # This zooms the map to focus on germany (coods 51.3, 10.1)

    # Add federal states overlay
    germany_political = 'landkreise-in-germany.geojson'

    folium.Choropleth(
        geo_data=germany_political,
        geo_str='choropleth',
        data=kreisTempsAvg,
        columns=[kreisTempsAvg.index, 'avg_temp'],
        key_on = 'feature.properties.name_2',
        fill_color='YlOrRd',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Temperatur (Grad Celsius)',
        highlight=True,
        threshold_scale=[0, 6, 8, 10, 12, 14]
    ).add_to(m)

    # Add station markers from GeoPandas data frame
    #m.add_child(folium.features.GeoJson(stationsKreise))
    #m.add_child(folium.features.GeoJson(kreisTemps2010))

    fileName = yearStr
    if monthStr != "":
        fileName += "-" + monthStr
        if dayStr != "":
            fileName += "-" + dayStr

    m.save(OUT_DIR + "/temps-" + fileName + ".html")

def setupRenderer():
    global driver

    driver = selenium.webdriver.Safari()    # You need to set *your browser* supporting webdriver here!
    driver.set_window_size(900, 750)

def renderHTML(htmlFilePath):
    path = 'file://' + os.getcwd() + "/" + htmlFilePath
    path = path.replace(" ", "%20")

    driver.get(path)
    time.sleep(5)   # Wait for HTML to render in browser

    dirPath = os.path.dirname(htmlFilePath)
    filenameNoExt = os.path.basename(htmlFilePath).split(".")[0]   # This assumes there is only one dot in filename!
    driver.save_screenshot(dirPath + "/" + filenameNoExt + '.png')

# Analyse and save HTML files of maps
for i in range(FROM_YEAR, TO_YEAR + 1):
    analyseForYear(str(i))

# Now render the HTML files to PNGs
print("Rendering the HTML maps to PNGs...")
setupRenderer()
for fileName in os.listdir(OUT_DIR):
    if fileName.endswith(".html"):
        print(fileName)
        renderHTML(os.path.join(OUT_DIR, fileName))

    