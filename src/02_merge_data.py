import pandas as pd
import os
import asyncio


async def read_csv_async(file_path, skiprows=6, column_names=None, na_values=['-']):
    # Simuliere non-blocking Laden von Dateien (pandas ist sync)
    loop = asyncio.get_running_loop()
    df = await loop.run_in_executor(
        None, lambda: pd.read_csv(
            file_path,
            skiprows=skiprows,
            names=column_names,
            na_values=na_values,
            decimal=',',
            thousands='.'
        )
    )
    return df

if __name__ == "__main__":

    akt_wahlkreis = "Landshut"

    # Führe die CSV pro Wahllokal zusammen zu einem Gesamt CSV
    l = []
    for f in os.listdir(f'../data/{akt_wahlkreis}/Stimmen_pro_Wahllokal'):
        if f.endswith('.csv'):
            df = asyncio.run(read_csv_async(os.path.join(f'../data/{akt_wahlkreis}/Stimmen_pro_Wahllokal', f), skiprows=8,
                                            na_values=['-'],
                                            column_names=[
                                                'Partei', 'Direktbewerber',
                                                'Erststimmen', 'Erststimmenanteil',
                                                'Zweitstimmen','Zweitstimmenanteil'
                                            ]))
            try:
                # Unglückliche Ausgangsformatierung der Anteile mit Prozentangaben wird als Float umgewandelt: 0-1.0 (0 bis 100%)
                df["Erststimmenanteil_2"] = df["Erststimmenanteil"].str.replace('%', '').str.replace(',', '.').astype(float) / 100
                df["Zweitstimmenanteil_2"] = df["Zweitstimmenanteil"].str.replace('%', '').str.replace(',', '.').astype(
                    float) / 100

                df.drop(columns=["Erststimmenanteil", "Zweitstimmenanteil"], inplace=True)
                df.rename(columns={"Erststimmenanteil_2": "Erststimmenanteil", "Zweitstimmenanteil_2": "Zweitstimmenanteil"}, inplace=True)

                df["Wahllokal_ID"] = f"{f.split('.csv')[0].split('_')[-1]}"
                df["Wahllokaltyp"] = f"{f.split('.csv')[0].split('_')[-2]}"
                l.append(df)
            except ValueError:
                print(f)


    total_df = pd.concat(l)
    total_df.to_excel(f'../data/{akt_wahlkreis}/Stimmen_pro_Wahllokal.xlsx', index=False)

    # Prüfe das Ergebnis
    erststimmen = total_df.groupby("Partei")["Erststimmen"].sum()
    zweitstimmen = total_df.groupby("Partei")["Zweitstimmen"].sum()

    assert erststimmen["Gültige Stimmen"] + erststimmen["Ungültige Stimmen"] == erststimmen["Wähler"]

    # Vergleich mit dem amtlichen Endergebnis 2025 Wahlkreis Freising
    # TODO: lies es aus dem amtlichen Ergebnis aus und vergleiche mit diesen Zahlen
    assert erststimmen["Wahlberechtigte"].sum() == 238829
    assert zweitstimmen["Wahlberechtigte"].sum() == 238829

    assert erststimmen["Wähler"].sum() == 204980
    assert zweitstimmen["Wähler"].sum() == 204980

    assert erststimmen["Gültige Stimmen"].sum() == 204067
    assert zweitstimmen["Gültige Stimmen"].sum() == 204429

    assert erststimmen["Ungültige Stimmen"].sum() == 913
    assert zweitstimmen["Ungültige Stimmen"].sum() == 551

    assert erststimmen["Wahlberechtigte"] == zweitstimmen["Wahlberechtigte"]
    assert erststimmen["Wähler"] == zweitstimmen["Wähler"]

    waehler = erststimmen["Wähler"]

    gueltige_erststimmen = erststimmen["Gültige Stimmen"]
    ungueltige_erststimmen = erststimmen["Ungültige Stimmen"]
    gueltige_zweitstimmen = zweitstimmen["Gültige Stimmen"]
    ungueltige_zweitstimmen = zweitstimmen["Ungültige Stimmen"]

    # Um die gültigen Stimmen pro Partei zu prüfen, müssen die
    # Gesamtangaben wie gültige Stimmen, ungültige Stimmen, Wahlberechtigte und Wähler
    # auf 0 gesetzt werden
    erststimmen["Gültige Stimmen"] = 0
    erststimmen["Ungültige Stimmen"] = 0
    erststimmen["Wahlberechtigte"] = 0
    erststimmen["Wähler"] = 0

    zweitstimmen["Gültige Stimmen"] = 0
    zweitstimmen["Ungültige Stimmen"] = 0
    zweitstimmen["Wahlberechtigte"] = 0
    zweitstimmen["Wähler"] = 0

    assert erststimmen.sum() == gueltige_erststimmen
    assert zweitstimmen.sum() == gueltige_zweitstimmen
