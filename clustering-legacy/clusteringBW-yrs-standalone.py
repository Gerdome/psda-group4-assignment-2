import numpy as np
import matplotlib.pyplot as plt

import pandas as pd
import geopandas as gpd

import sqlalchemy as db

from sklearn.cluster import DBSCAN
import scipy.spatial.distance as dist

db_URI = 'postgresql://postgres:SDAPraktikum2020@193.196.37.97:5432/postgres'
engine = db.create_engine(db_URI)
connection = engine.connect()
metadata = db.MetaData()

census = db.Table('air_temperature_stations', metadata, autoload=True, autoload_with=engine)

stations = gpd.read_postgis('air_temperature_stations', connection, geom_col='geom_station', index_col='stations_id')

stations = stations[stations['bundesland'] == 'Baden-Württemberg']
stations.to_crs(epsg=3857).plot()
#plt.savefig('stations.png')

coordinates = stations[['geobreite', 'geolaenge']].to_numpy()
clusters = DBSCAN(eps=0.5).fit(coordinates).labels_

dists = dist.pdist(coordinates)
dists = dists[dists > 0]
#plt.hist(dists)



def tdist(x, y):
  return dist.euclidean(x, y)

def flexdist(x, y):
  return dist.euclidean(x[0:2], y[0:2]) + tdist(x[2:], y[2:])

WHOLE_YEAR = "year"
SUMMER = "summer"
WINTER = "winter"

def clusterForYear(yearStr, season=WHOLE_YEAR):
    # Build query depending on season seleced
    query = "SELECT stations_id, AVG(temperature_day), stddev(temperature_day) FROM air_temperature_values as vals "
    if season == WHOLE_YEAR:
        query += "WHERE vals.messdatum_date >= date('" + yearStr + "-01-01') AND vals.messdatum_date <= date('" + yearStr + "-12-31') GROUP BY stations_id"
    elif season == SUMMER:
        query += "WHERE vals.messdatum_date >= date('" + yearStr + "-06-01') AND vals.messdatum_date <= date('" + yearStr + "-08-31') GROUP BY stations_id"
    elif season == WINTER:
        query += "WHERE vals.messdatum_date >= date('" + yearStr + "-11-01') AND vals.messdatum_date <= date('" + str(int(yearStr) + 1) + "-03-01') GROUP BY stations_id"

    # Get data
    temp_data = pd.read_sql(query, connection, parse_dates=['messdatum_date'], index_col='stations_id')

    df = stations.join(temp_data)
    df = df.dropna()
    #print(df.shape)

    coordinates = df[['geobreite', 'geolaenge']].to_numpy()
    tdata = df[['avg', 'stddev']].to_numpy()

    data = np.hstack([coordinates, tdata])

    dists = dist.pdist(data, flexdist)
    dists = dists[dists > 0]
    plt.hist(dists)

    maxClusters = 0.0
    epsToUse = -1.0
    for eps in np.arange(0.1, 1.5, 0.1):
        clusters = DBSCAN(eps=eps, metric=flexdist).fit(data).labels_
        #print("Eps: {:.2f} \t gives {} clusters".format(eps,max(clusters)))

        if max(clusters) > maxClusters:
            maxClusters = max(clusters)
            epsToUse = eps

    print("==> Using " + str(epsToUse) + " for #clusters = " + str(maxClusters))

    clusters = DBSCAN(eps=epsToUse, metric=flexdist).fit(data).labels_

    df['cluster'] = clusters


    df.to_crs(epsg=3857).plot('cluster', )

    plt.title(yearStr + ' (' + str(round(epsToUse, 2)) + ', #c=' + str(maxClusters) + ')')
    plt.savefig('output/clustersBW-' + yearStr + '.png')


# Perform clustering and save output for several years
for i in range(2010, 2019 + 1):
    clusterForYear(str(i))