import os
import json
from geopy import GoogleV3
from geopy.geocoders import Nominatim
import dotenv
import pandas as pd

if __name__ == "__main__":

    akt_wahlkreis = "Freising"

    # Liste der Gemeindeschlüssel für Bayern aus Geodaten der Vermessungsverwaltung extrahiert
    # Definiere string als Datentyp für SCH Spalte, ansonsten würde Pandas die Spalte als Zahl interpretieren
    # und damit die führende Null entfernen
    gemeinden = pd.read_csv("../data/BY_Gemeindeliste_2025.csv", dtype={'SCH': str})

    # filtere nach Wahlkreis
    gemeinden = gemeinden[gemeinden["WKR_NAME"] == akt_wahlkreis]
    gemeindeschluessel_list = gemeinden["SCH"]
    
    base_dir = f"../data/{akt_wahlkreis}"
    csv_dir = os.path.join(base_dir, "Stimmen_pro_Wahllokal")

    # create mapping
    d = {}
    for f in os.listdir(csv_dir):
        
        if f.endswith('.csv'):
            # filter über die Wahllokal ID, die bis zur 8. Stelle dem Gemeindeschlüssel entspricht
            wahllokal_id = f"{f.split('.csv')[0].split('_')[-1]}"
            row = gemeinden[gemeinden["SCH"] == wahllokal_id[:8]]
            kreis = row["BEZ_KRS"].to_numpy()[0]
            gemeinde = row["BEZ_GEM"].to_numpy()[0]

            with open(os.path.join(csv_dir, f)) as fo:
                content = fo.readlines()
                tmp = content[2].split(',')[1]
                # entferne unnötigen Text bei falsch formatierten Vorkommnissen
                if "Amtliches Endergebnis" in tmp:
                    tmp = tmp.replace('Amtliches Endergebnis"\n', '')
                d[wahllokal_id] = dict(kreis=kreis, gemeinde=gemeinde, wahllokal=tmp)

    s = json.dumps(d, ensure_ascii=False)
    with open(os.path.join(base_dir, 'Wahllokal_mapping.json'), mode='w') as f:
        f.write(s)

    # TODO auch als CSV
    # Create a geolocator instance with a user-defined app name
    #geolocator = Nominatim(user_agent="Wahlanalyse2025")

    geolocator = GoogleV3(api_key=dotenv.get_key("GOOGLE_API_KEY"), user_agent="Wahlanalyse2025")

    geo_csv = ['"WahllokalID", "Kreis", "Gemeinde", "Wahllokalname", "Gemeindeebene", "Latitude", "Longitude", "Adresse"']
    for k in list(d.keys()):
        v = d[k]

        # lasse briefwahllokale erst mal weg
        if "briefwahl" in v["wahllokal"].lower() or "BW " in v["wahllokal"]:
            continue

        # Geokodierung mit OSM - evtl. ist Google besser
        # produziert ein CSV
        try:
            # entferne dabei den ID Krempel wie 0001 - Bla bla -> Bla bla
            loc_str = ""
            # doppelte Namen ignorieren
            if v['kreis'] == v['gemeinde']:
                loc_str = f"{v['gemeinde']}, {v['wahllokal'][7:].strip()}"
            else:
                loc_str = f"{v['kreis']}, {v['gemeinde']}, {v['wahllokal'][7:].strip()}"

            print(f"Searching for {loc_str}..")
            location = geolocator.geocode(loc_str)
            if location:
                t = f""" "{k}", "{v['kreis']}", "{v['gemeinde']}", "{v['wahllokal']}", {False}, {location.latitude}, {location.longitude}, "{location.address}" """
                geo_csv.append(t)
            # fallback: Gemeindeebene in Bayern
            else:
                loc_str = f"Bayern, {v['gemeinde']}"
                print(f"Searching for {loc_str}..")
                location = geolocator.geocode(loc_str)
                if location:
                    t = f""" "{k}", "{v['kreis']}", "{v['gemeinde']}", "{v['wahllokal']}", {True}, {location.latitude}, {location.longitude}, "{location.address}" """
                    geo_csv.append(t)

        except Exception as ex:
            print(ex)

    with open(f'../data/{akt_wahlkreis}/Wahllokal_mapping_geocoded_google.csv', mode='w') as f:
        for l in geo_csv:
            f.write(l+"\n")
