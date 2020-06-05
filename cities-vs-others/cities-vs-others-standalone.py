import folium

import pandas as pd
import geopandas as gpd

import psycopg2  # For postgres

FROM_YEAR = 2010
TO_YEAR = 2019

def analyseForYear(yearStr):
    print(yearStr)

    # Connect to database
    connection = psycopg2.connect(host="193.196.37.97", database="postgres",user="postgres", password="SDAPraktikum2020")
    cursor = connection.cursor()

    # Get all temps for stations in year
    #airtemps2010 = pd.read_sql_query("SELECT sts.stations_id, sts.stationsname, vals.temperature_day, vals.messdatum_date FROM air_temperature_values as vals LEFT JOIN air_temperature_stations as sts ON vals.stations_id = sts.stations_id WHERE vals.messdatum_date >= date('2010-01-01') AND vals.messdatum_date <= date('2010-12-31')", connection)
    #airtemps2010

    # Get all average temps for stations in year
    query = "SELECT sts.stationsname, AVG(vals.temperature_day) as avg_temp_yr2010 FROM air_temperature_values as vals LEFT JOIN air_temperature_stations as sts ON vals.stations_id = sts.stations_id WHERE vals.messdatum_date >= date('" + yearStr + "-06-01') AND vals.messdatum_date <= date('" + yearStr + "-08-31') GROUP BY sts.stationsname"
    print(query)
    avgtemps2010 = pd.read_sql_query(query, connection)

    # Load station list with Landkreise political regions
    stationsKreise = pd.read_csv("stations+counties.csv")

    # Convert to geopandas data frame with geometry column
    geometry = gpd.points_from_xy(x=stationsKreise.geobreite_x, y=stationsKreise.geolaenge_x)
    stationsKreise = stationsKreise.drop(['stationshoehe_x', 'geobreite_x', 'geolaenge_x'], axis=1)
    stationsKreise = gpd.GeoDataFrame(stationsKreise, crs='EPSG:4326', geometry=geometry)  # "EPSG:4326" is WGS84 long-lat

    # Remove columns not needed here
    stationsKreise = stationsKreise.drop(['Unnamed: 0', 'von_datum', 'bis_datum'], axis=1)

    # Join on temperatures table with statstationsname
    joined = avgtemps2010.set_index('stationsname').join(stationsKreise.set_index('stationsname'))
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
    kreisTemps2010 = joined.dropna()

    # Count stations per kreis
    stationsPerKreis = kreisTemps2010[['Landkreis', 'avg_temp_yr2010']].groupby(['Landkreis']).agg('count')
    stationsPerKreis.rename(columns={'avg_temp_yr2010':'Stations'}, inplace=True)
    stationsPerKreis = stationsPerKreis.sort_values(by=['Stations'])
    stationsPerKreis

    # Visualize Stations density
    # Create map focussed on Germany
    densMap = folium.Map(location=[51.3, 10.1], zoom_start=6)  # This zooms the map to focus on germany (coods 51.3, 10.1)

    # Add federal states overlay
    germany_political = 'landkreise-in-germany.geojson'

    folium.Choropleth(
        geo_data=germany_political,
        geo_str='choropleth',
        data=stationsPerKreis,
        columns=[stationsPerKreis.index, 'Stations'],
        key_on = 'feature.properties.name_2',
        fill_color='YlOrRd',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Number of Stations',
        highlight=True
    ).add_to(densMap)

    densMap.save("output/densmap-" + yearStr + ".html")

    # Now group by and average on Kreise
    kreisTemps2010avg = kreisTemps2010.groupby(['Landkreis']).mean()

    # Create map focussed on Germany
    m = folium.Map(location=[51.3, 10.1], zoom_start=6)  # This zooms the map to focus on germany (coods 51.3, 10.1)

    # Add federal states overlay
    germany_political = 'landkreise-in-germany.geojson'

    folium.Choropleth(
        geo_data=germany_political,
        geo_str='choropleth',
        data=kreisTemps2010avg,
        columns=[kreisTemps2010avg.index, 'avg_temp_yr2010'],
        key_on = 'feature.properties.name_2',
        fill_color='YlOrRd',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Temperature (celsius)',
        highlight=True
    ).add_to(m)

    # Add station markers from GeoPandas data frame
    #m.add_child(folium.features.GeoJson(stationsKreise))
    #m.add_child(folium.features.GeoJson(kreisTemps2010))

    m.save("output/temps-" + yearStr + ".html")

    # Now filter for the major cities, down to ~500,000 population -- tmp workaround: use Bochum for Dortmund, nearest
    cities2009 = ['Berlin', 'Hamburg', 'München', 'Köln', 'Frankfurt am Main', 'Stuttgart', 'Düsseldorf', 'Bochum', 'Essen', 'Bremen', 'Region Hannover', 'Leipzig', 'Dresden', 'Nürnberg', 'Duisburg']

    # Check if they are directly available as Landkreise
    allMatched = True 
    for c in cities2009:
        if c not in kreisTemps2010avg.index:
            print("No match", c)
            allMatched = False

    if allMatched:
        print("All cities matched!")

    # Now cluster the cities together and compare them to everything else
    sumCities = 0.0
    sumOthers = 0.0

    countCities = 0
    countOthers = 0

    for row in kreisTemps2010avg.iterrows():
        kreis, val = row
        avgtemp = val['avg_temp_yr2010']
        

        if kreis in cities2009:
            sumCities += avg
            countCities += 1
        else:
            sumOthers += avg
            countOthers += 1
            
    avgCities = sumCities / float(countCities)
    avgOthers = sumOthers / float(countOthers)

    # Write to file
    file = open("output/citiesvsother-" + yearStr + ".txt", "w")
    file.write("Cities: " +  str(round(avgCities, 5)) + "\n")
    file.write("Others: " +  str(round(avgOthers, 5)) + "\n")
    file.close()

for i in range(FROM_YEAR, TO_YEAR + 1):
    analyseForYear(str(i))