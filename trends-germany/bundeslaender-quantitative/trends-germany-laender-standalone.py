import os
import time

from calendar import monthrange

import psycopg2             # For postgres

import pandas as pd
import geopandas as gpd

import matplotlib.pyplot as plt

import statistics

# Configuration
FROM_YEAR = 2010
TO_YEAR = 2019

xAxis = []  # e.g. the dates
seriesNames = []
series = [] # List of lists
averagedSeries = []     # Only a list, contains averages of all series
medianSeries = []       # Only a list, contains medians of all series
maxSeries = []          # "
minSeries = []          # "
stdDev = []             # "

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

    # Add all bundesländer to the seriesNames on the first call to this function
    if len(seriesNames) == 0:
        for row in avgTemps.iterrows():
            index, vals = row
            name = vals['bundesland']
            
            seriesNames.append(name)
            series.append(list())   # Also append an empty list for series data

    # Save the time reference for the current query
    if monthStr != "":
        if dayStr != "":
            # Specific day
            xAxis.append(yearStr + "-" + monthStr + "-" + dayStr)
        else:
            # Month, use last day as reference
            daysInMonth = monthrange(int(yearStr), int(monthStr))[1]
            xAxis.append(yearStr + "-" + monthStr + "-" + str(daysInMonth))
    else:
        # Just use the year
        xAxis.append(int(yearStr))            

    # Add the results to the time series for each bundesland
    for row in avgTemps.iterrows():
        index, vals = row
        name = vals['bundesland']
        avgTemp = vals['avg_temp']

        # Append the average temperatur to the series
        seriesIndex = seriesNames.index(name)
        series[seriesIndex].append(avgTemp)

def plotAnalysis():
    i = 0
    for s in series:
        plt.plot(xAxis, s, label=seriesNames[i])
        i += 1

    plt.title("Durchschnittliche Temperatur in den Bundesländern [°C]")
    plt.legend(loc="lower right", fontsize="small")
    plt.show()

    plt.plot(xAxis, averagedSeries, label="Durchschnitt aller Bundesländer")
    plt.plot(xAxis, medianSeries, label="Median aller Bundesländer")
    plt.plot(xAxis, minSeries, label="Minimum aller Bundesländer", linestyle='--')
    plt.plot(xAxis, maxSeries, label="Maximum aller Bundesländer", linestyle='--')
    #plt.plot(xAxis, stdDev, label="Standardabweichung", linestyle=':')
    plt.title("Aggergierte Temperatur aller Bundesländer [°C]")
    plt.legend(loc="lower right", fontsize="small")
    plt.show()

# Analyse and save results for each time slice
for i in range(FROM_YEAR, TO_YEAR + 1):
    #for m in range(1, 12 + 1):
        #daysInMonth = monthrange(i, m)[1]
        #for d in range(1, daysInMonth + 1):
    analyseForYear(str(i))

# Calculate average and median
for i in range(len(series[0])):
    sum = 0.0
    vals = []
    for s in series:
        sum += s[i]
        vals.append(s[i])
    averagedSeries.append(sum / float(len(series)))
    medianSeries.append(statistics.median(vals))
    minSeries.append(min(vals))
    maxSeries.append(max(vals))
    stdDev.append(statistics.stdev(vals))

# Now plot all results
plotAnalysis()

# Perform ranking regarding max and min temperature
rankingWinners = [] # List of lists for the years, may be more than one winner!
rankingLosers = []
for i in range(len(series[0])):
    rankingWinners.append(list())
    rankingLosers.append(list())

    for j in range(len(series)):
        s = series[j]
        if s[i] == maxSeries[i]:
            rankingWinners[-1].append((seriesNames[j], maxSeries[i]))

        if s[i] == minSeries[i]:
            rankingLosers[-1].append((seriesNames[j], maxSeries[i]))

print(rankingWinners)
print(rankingLosers)

rankingWinnerCounts = []
rankingLoserCounts = []
for s in seriesNames:
    rankingWinnerCounts.append(0)
    rankingLoserCounts.append(0)

for l in rankingWinners:
    for p in l:
        name = p[0]
        temp = p[1]

        index = seriesNames.index(name)
        rankingWinnerCounts[index] += 1

for l in rankingLosers:
    for p in l:
        name = p[0]
        temp = p[1]

        index = seriesNames.index(name)
        rankingLoserCounts[index] += 1

# Remove zero entries
seriesNamesWinners = []
countWinners = []

seriesNamesLosers = []
countLosers = []
for i in range(len(seriesNames)):
    if rankingWinnerCounts[i] != 0:
        seriesNamesWinners.append(seriesNames[i])
        countWinners.append(rankingWinnerCounts[i])

    if rankingLoserCounts[i] != 0:
        seriesNamesLosers.append(seriesNames[i])
        countLosers.append(rankingLoserCounts[i])

# Plot as histograms
plt.bar(seriesNamesWinners, countWinners)
plt.title("Ranking der höchsten durchschnittlichen Temperaturen von 2010 bis 2019")
plt.show()

# Plot as histograms
plt.bar(seriesNamesLosers, countLosers)
plt.title("Ranking der niedrigsten durchschnittlichen Temperaturen von 2010 bis 2019")
plt.show()

    