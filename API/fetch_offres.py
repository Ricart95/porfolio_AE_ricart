import requests
import pandas as pd
from google.cloud import bigquery
from dotenv import load_dotenv
import os
import time

load_dotenv()

CLIENT_ID = os.getenv(
    "FT_CLIENT_ID")
CLIENT_SECRET = os.getenv(
    "FT_CLIENT_SECRET")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
BQ_DATASET = "raw_france_travail"
BQ_TABLE = "offres_emploi"

DEPARTEMENTS = [
    "01", "02", "03", "04", "05", "06", "07", "08", "09", "10",
    "11", "12", "13", "14", "15", "16", "17", "18", "19", "21",
    "22", "23", "24", "25", "26", "27", "28", "29", "2A", "2B",
    "30", "31", "32", "33", "34", "35", "36", "37", "38", "39",
    "40", "41", "42", "43", "44", "45", "46", "47", "48", "49",
    "50", "51", "52", "53", "54", "55", "56", "57", "58", "59",
    "60", "61", "62", "63", "64", "65", "66", "67", "68", "69",
    "70", "71", "72", "73", "74", "75", "76", "77", "78", "79",
    "80", "81", "82", "83", "84", "85", "86", "87", "88", "89",
    "90", "91", "92", "93", "94", "95", "971", "972", "973", "974"
]


def get_token():
    response = requests.post(
        "https://entreprise.francetravail.fr/connexion/oauth2/access_token",
        params={"realm": "/partenaire"},
        data={
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "scope": "api_offresdemploiv2 o2dsoffre"
        }
    )
    response.raise_for_status()
    return response.json()["access_token"]


def fetch_offres(token, departement, debut=0, fin=150):
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "debut": debut,
        "fin": fin,
        "departement": departement
    }
    response = requests.get(
        "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search",
        headers=headers,
        params=params
    )
    response.raise_for_status()
    return response.json().get("resultats", [])


def fetch_all_offres(token, departement, max_offres=3000):
    all_offres = []
    batch_size = 150
    debut = 0

    while debut < max_offres:
        fin = debut + batch_size
        print(f"Récupération des offres {debut} à {fin}...")
        offres = fetch_offres(
            token, departement=departement, debut=debut, fin=fin)
        if not offres:
            break
        for offre in offres:
            offre["departement_recherche"] = departement
        all_offres.extend(offres)
        debut += batch_size
        time.sleep(0.5)

    print(f"Total offres récupérées : {len(all_offres)}")
    return all_offres


def load_to_bigquery(offres, first_load=False):
    df = pd.DataFrame(offres)
    client = bigquery.Client(project=GCP_PROJECT_ID)
    table_id = f"{GCP_PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}"

    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE" if first_load else "WRITE_APPEND",
        autodetect=True,
    )

    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()
    print(f"✅ {len(df)} offres chargées dans {table_id}")


if __name__ == "__main__":
    token = get_token()
    total = 0
    first_load = True

    for i, dept in enumerate(DEPARTEMENTS):
        if i > 0 and i % 20 == 0:
            print("🔄 Renouvellement du token...")
            token = get_token()

        print(f"📍 Traitement du département {dept}...")
        try:
            offres = fetch_all_offres(token, departement=dept)
            if offres:
                load_to_bigquery(offres, first_load=first_load)
                first_load = False
                total += len(offres)
        except Exception as e:
            print(f"❌ Erreur pour le département {dept} : {e}")
            continue

    print(f"\n🎉 Terminé ! Total offres chargées : {total}")
