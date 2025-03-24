# Analyse der Bundestagswahl 2025 auf Wahllokalebene am Beispiel des Landkreises Freising

## Motivation
Wahlergebnisse sind bei den Landeswahlleitungen bzw. der Bundeswahlleitung in der Regel auf Wahlkreisebene bis maximal zur Gemeindeebene verfügbar.
Eine noch detailliertere Analyse auf Wahllokalebene ist jedoch auch interessant, da Wahlkreise bzw. Gemeinden mitunter ziemlich heterogen hinsichtlich der Ergebnisse sein können.

## Installation
Die Installation der benötigten Pythonmodule erfolgt am besten in einer virtuellen Pythonumgebung wie virtualenv.

```shell
python3 -m venv .venv 
source .venv/bin/activate
pip install -r requirements.txt
```

## Übersicht und Anwendung
Zunächst werden die Daten für den Wahlkreis mit dem Webscraper pro Wahllokal als CSV heruntergeladen.

```shell
cd src
python3 01_webscraper.py 
```

Im zweiten Schritt werden alle Einzeldateien pro Wahllokal zu einem Gesamt CSV zusammengefasst.
```shell
cd src
python3 02_merge_data.py 
```

Anschließend wird versucht, die Bezeichnung der Wahllokale mit einem Geokodierer räumlich zu verorten. Für die Google Geokodierungs API muss ein gültiger API Key erstellt werden.
Die Geokodierung durch Google scheint mehr und bessere Treffer zu liefern als die OSM Nominatim Geokodierung in diesem Fall.
```shell
cd src
python3 03_locator.py 
```
