# Smart Data Analytics Tasks, Team 4, Assignment 2

# Setup
- Zugangsdaten zur Datenbank in db.py eintragen
- Einmalig db.py setup aufrufen, um die notwendigen Views in der DB anzulegen.

# Inhalte
## Database connection
Wir haben die zugrundeliegende Daten (DWD-Daten aggregiert auf Tageslevel) auf einem separaten Cloudserver gehostet und stellen die Verbindung in den jeweiligen Skripten bzw. Notebooks her.
## Pre Processing
- Zugehörigkeit der einzelnen Wetterstationen zu Land/Stadtkreise & Bevölkerung der einzelnen Kreise bestimmen: [Pre-Processing Notebook](https://git.scc.kit.edu/ubelj/psda-group-4-assignment-2/-/blob/master/Pre-Processing.ipynb)

## Data Exploration
- Visualisierung der Wetterstationen + Landkreise in interaktiver Map mittels Folium: [Visualisierungs-Notebooks] (https://git.scc.kit.edu/ubelj/psda-group-4-assignment-2/-/tree/master/visualization-tests)
- Visualisierung der Temperaturdaten auf Landeskreisebene: [Temperature Kreise] (https://git.scc.kit.edu/ubelj/psda-group-4-assignment-2/-/tree/master/temperature-kreise)
- Visualisierung der zeitlichen Verläufe und Erstellung von Videos zur Übersicht der zeitlichen Verläufe: [Trends Notebooks] (https://git.scc.kit.edu/ubelj/psda-group-4-assignment-2/-/tree/master/trends-germany)
Anmerkung: Um Videos zu erstellen, benötigt man FFMPEG und IMAGEMAGICK.

## Data Clustering
- Clustering.ipyn enthält die Clustering-Verfahren mit Korrelation und Cosine-Distanz
- Clustering Legacy Ordner enthält ein frühes Clustering Verfahren und wurde nach der Exploration nicht weiter bearbeitet. Bitte für die aktuellen Verfahren statdessen das Notebook anschauen.