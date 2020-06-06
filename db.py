import sqlalchemy as db

HOST = "193.196.37.97"
PORT = "5432"
PASS = "SDAPraktikum2020"

def connect():
    db_URI = 'postgresql://postgres:{}@{}:{}/postgres'.format(PASS, HOST, PORT)
    engine = db.create_engine(db_URI)
    connection = engine.connect()
    #metadata = db.MetaData()
    #census = db.Table('air_temperature_stations', metadata, autoload=True, autoload_with=engine)
    return connection



def __createViews():
    connection = connect()
    try:
        connection.execute("CREATE VIEW air_temperature_values_bw AS SELECT air_temperature_stations.stations_id, temperature_day, messdatum_date FROM air_temperature_values LEFT JOIN air_temperature_stations ON air_temperature_values.stations_id = air_temperature_stations.stations_id WHERE bundesland='Baden-Württemberg'")
        print('Created View air_temperature_values_bw')
    except:
        pass
    try:
        connection.execute("CREATE VIEW air_temperature_stations_active AS SELECT * FROM air_temperature_stations WHERE bis_datum >= date('2010-01-01')")
        print('Created View air_temperature_stations_active')
    except:
        pass
    connection.close


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        print("DB Setup start...")
        __createViews()
        print("DB Setup done!")
