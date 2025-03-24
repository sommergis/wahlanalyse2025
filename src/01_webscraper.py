import asyncio
import os.path
from inspect import walktree

import pandas as pd
from playwright.async_api import async_playwright

# Basis URLs
wahlkreise = {
    "Freising": "https://wahl.kreis-freising.de/upload/2025-bundestag/ergebnisse",
    "Landshut" : "https://landshut.de/wahlen/Bundestagswahl-2025/ergebnisse",
    "München-Land" : "https://memo.landkreis-muenchen.de/wahlen/bundestagswahl_2025/ergebnisse",
    "Weiden": "https://www1.wahlen.weiden.de/20250223/ergebnisse",
    "Würzburg": "https://wahlen.wuerzburg.de/Wahl-2025-02-23/Bundestagswahl/ergebnisse"
}

async def download_csv(page, akt_wahlkreis, gem_sch):
    """ Klickt auf den CSV-Download-Button """
    try:
        # muss evtl. gar nicht sein - zur Sicherheit etwas Zeit zum Laden der Seite gegeben
        #await asyncio.sleep(3)

        # erster Download button
        await page.click("button:has(i) >> text='file_download'")
        #
        # await page.screenshot(path="screenshot.png", type='jpeg', scale='css', animations='disabled')

        # Auf den Download warten nach dem Klick auf den zweiten Button
        async with page.expect_download() as download_info:
            await page.click("button >> text='Download als CSV'")

        download = await download_info.value

        # Speichere die Datei
        download_path = f"../data/{akt_wahlkreis}/Stimmen_pro_Wahllokal/{download.suggested_filename.split('.csv')[0]}_{gem_sch}.csv"
        await download.save_as(download_path)

        print("CSV Download abgeschlossen")

    except Exception as e:
        print(f"Fehler beim Download: {e}")

async def scrape_websites(base_url, akt_wahlkreis):
    """Extrahiere Daten mit Hilfe von Playwright """

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, timeout=1000)
        context = await browser.new_context()
        page = await context.new_page()

        # 2 Varianten beim Wahllokaltyp
        for wahllokaltyp in ["stimmbezirk", "briefwahlbezirk"]:
            _url = f"{base_url}_{wahllokaltyp}_"

            for gemeindeschluessel in gemeindeschluessel_list:
                # mehr als 100 Wahllokale sind nicht wahrscheinlich..
                # aber besser wäre natürlich mehr Logik zum Erkennen der "Untergeordneten Gebiete"
                for laufende_nr in range(101):
                    url = f"{_url}{gemeindeschluessel}{laufende_nr:04}.html"

                    csv_path = f"../data/{akt_wahlkreis}/Stimmen_pro_Wahllokal/Ergebnisübersicht_{wahllokaltyp}_{gemeindeschluessel}{laufende_nr:04}.csv"
                    if os.path.exists(csv_path):
                        print("Überspringe - CSV existiert bereits!")
                        continue

                    print(f"Prüfe URL: {url}")

                    response = await page.goto(url)

                    if response.status == 200:
                        csv_path = f"../data/{akt_wahlkreis}/Stimmen_pro_Wahllokal/Ergebnisübersicht_{wahllokaltyp}_{gemeindeschluessel}{laufende_nr:04}.csv"
                        if os.path.exists(csv_path):
                            print("Überspringe - CSV existiert bereits!")
                            continue

                        await download_csv(page, akt_wahlkreis=akt_wahlkreis, gem_sch=f"{wahllokaltyp}_{gemeindeschluessel}{laufende_nr:04}")
                    else:
                        print(f"Seite nicht gefunden: {url} (Status: {response.status})")

        await browser.close()

if __name__ == "__main__":

    # Freising, Landshut, München-Land
    akt_wahlkreis = "Landshut"
    base_url = wahlkreise[akt_wahlkreis]

    # Liste der Gemeindeschlüssel für Bayern aus Geodaten der Vermessungsverwaltung extrahiert
    # Definiere string als Datentyp für SCH Spalte, ansonsten würde Pandas die Spalte als Zahl interpretieren
    # und damit die führende Null entfernen
    gemeinden = pd.read_csv("../data/BY_Gemeindeliste_2025.csv", dtype={'SCH': str})

    # filtere nach Wahlkreis
    gemeinden = gemeinden[gemeinden["WKR_NAME"] == akt_wahlkreis]
    gemeindeschluessel_list = gemeinden["SCH"]

    asyncio.run(scrape_websites(base_url, akt_wahlkreis))

