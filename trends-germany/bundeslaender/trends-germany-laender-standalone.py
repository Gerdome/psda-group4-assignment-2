import os
import time

from calendar import monthrange

import psycopg2             # For postgres

import pandas as pd
import geopandas as gpd

import folium

import urllib
import selenium.webdriver   # For generating screenshots of HTML files

# Configuration
FROM_YEAR = 2019
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
            query = "SELECT sts.bundesland as bundesland, AVG(vals.temperature_day) as avg_temp FROM air_temperature_values as vals LEFT JOIN air_temperature_stations as sts ON vals.stations_id = sts.stations_id WHERE vals.messdatum_date = date('" + yearStr + "-" + monthStr + "-" + dayStr + "') GROUP BY sts.bundesland"
        else:
            # query for one month
            daysInMonth = monthrange(int(yearStr), int(monthStr))[1]
            query = "SELECT sts.bundesland as bundesland, AVG(vals.temperature_day) as avg_temp FROM air_temperature_values as vals LEFT JOIN air_temperature_stations as sts ON vals.stations_id = sts.stations_id WHERE vals.messdatum_date >= date('" + yearStr + "-" + monthStr + "-01') AND vals.messdatum_date <= date('" + yearStr + "-" + monthStr + "-" + str(daysInMonth) + "') GROUP BY sts.bundesland"
    else:
        # query for whole year
        query = "SELECT sts.bundesland as bundesland, AVG(vals.temperature_day) as avg_temp FROM air_temperature_values as vals LEFT JOIN air_temperature_stations as sts ON vals.stations_id = sts.stations_id WHERE vals.messdatum_date >= date('" + yearStr + "-01-01') AND vals.messdatum_date <= date('" + yearStr + "-12-31') GROUP BY sts.bundesland"

    print(query)
    avgTemps = pd.read_sql_query(query, connection)

    # Now group by and average on Kreise

    # Create map focussed on Germany
    m = folium.Map(location=[51.3, 10.1], zoom_start=6.45)  # This zooms the map to focus on germany (coods 51.3, 10.1)

    # Add federal states overlay
    germany_political = 'deutschlandGeoJSON/2_bundeslaender/2_hoch.geo.json'

    folium.Choropleth(
        geo_data=germany_political,
        geo_str='choropleth',
        data=avgTemps,
        columns=['bundesland', 'avg_temp'],
        key_on = 'feature.properties.name',
        fill_color='YlOrRd',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Temperatur (Grad Celsius)',
        highlight=True,
        # threshold_scale=[0, 6, 8, 10, 12, 14]         # comment out for relative dynamic scale
    ).add_to(m)

    # Add station markers from GeoPandas data frame
    #m.add_child(folium.features.GeoJson(stationsKreise))
    #m.add_child(folium.features.GeoJson(kreisTemps2010))

    fileName = yearStr
    if monthStr != "":
        fileName += "-" + monthStr.zfill(2)
        if dayStr != "":
            fileName += "-" + dayStr.zfill(2)

    m.save(OUT_DIR + "/temps-" + fileName + ".html")

def setupRenderer():
    global driver

    driver = selenium.webdriver.Safari()    # You need to set *your browser* supporting webdriver here!
    driver.set_window_size(900, 750)

def renderHTML(htmlFilePath):
    path = 'file://' + os.getcwd() + "/" + htmlFilePath
    path = path.replace(" ", "%20")
    print(path)
    driver.get(path)
    time.sleep(1)   # Wait for HTML to render in browser

    dirPath = os.path.dirname(htmlFilePath)
    filenameNoExt = os.path.basename(htmlFilePath).split(".")[0]   # This assumes there is only one dot in filename!
    driver.save_screenshot(dirPath + "/" + filenameNoExt + '.png')

# Analyse and save HTML files of maps
# for i in range(FROM_YEAR, TO_YEAR + 1):
#    for m in range(1, 12 + 1):
#         daysInMonth = monthrange(i, m)[1]
#         for d in range(1, daysInMonth + 1):
#             analyseForYear(str(i), monthStr=str(m), dayStr=str(d))

# Now render the HTML files to PNGs
print("Rendering the HTML maps to PNGs...")
setupRenderer()
for fileName in os.listdir(OUT_DIR):
    if fileName.endswith(".html"):
        print(fileName)
        renderHTML(os.path.join(OUT_DIR, fileName))

    