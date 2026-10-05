import requests
import pandas as pd
from google.cloud import bigquery
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from google.api_core.exceptions import NotFound
import os
import sys

load_dotenv()

CLIENT_ID = os.getenv("FT_CLIENT_ID")
CLIENT_SECRET = os.getenv("FT_CLIENT_SECRET")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
BQ_DATASET = "raw_france_travail"
# Historique : une ligne par offre, alimentée chaque jour avec les nouvelles offres seulement
BQ_TABLE = "offres_emploi_historique"

REQUEST_TIMEOUT = 30
# Aucun échec toléré : le prochain run repart de la dernière date chargée,
# les offres d'un département en échec sur cette période seraient perdues
MAX_FAILURE_RATIO = 0
# Recouvrement avec le run précédent pour ne rater aucune offre (doublons supprimés dans dbt)
OVERLAP = timedelta(hours=6)
# Départements récupérés en parallèle ; rester bas pour ne pas dépasser le quota de l'API (~10 appels/s)
MAX_WORKERS = 4

# Retente automatiquement sur quota dépassé (429) et erreurs serveur, en respectant Retry-After
session = requests.Session()
session.mount("https://", HTTPAdapter(max_retries=Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=frozenset({"GET", "POST"}),
)))

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
    response = session.post(
        "https://entreprise.francetravail.fr/connexion/oauth2/access_token",
        params={"realm": "/partenaire"},
        data={
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "scope": "api_offresdemploiv2 o2dsoffre"
        },
        timeout=REQUEST_TIMEOUT
    )
    response.raise_for_status()
    return response.json()["access_token"]


def fetch_offres(token, departement, debut=0, fin=150, min_creation=None):
    headers = {"Authorization": f"Bearer {token}"}
    # L'API pagine via range=premier-dernier (bornes incluses, 150 max par appel)
    params = {
        "range": f"{debut}-{fin - 1}",
        "departement": departement
    }
    if min_creation:
        # L'API exige les deux bornes ensemble
        params["minCreationDate"] = min_creation.strftime("%Y-%m-%dT%H:%M:%SZ")
        params["maxCreationDate"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    response = session.get(
        "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search",
        headers=headers,
        params=params,
        timeout=REQUEST_TIMEOUT
    )
    response.raise_for_status()
    # 204 No Content : aucune offre, corps vide
    if response.status_code == 204:
        return []
    return response.json().get("resultats", [])


def fetch_all_offres(token, departement, max_offres=3000, min_creation=None):
    all_offres = []
    batch_size = 150
    debut = 0

    while debut < max_offres:
        fin = debut + batch_size
        print(f"Récupération des offres {debut} à {fin}...")
        offres = fetch_offres(
            token, departement=departement, debut=debut, fin=fin, min_creation=min_creation)
        if not offres:
            break
        for offre in offres:
            offre["departement_recherche"] = departement
        all_offres.extend(offres)
        # Page incomplète : plus rien après
        if len(offres) < batch_size:
            break
        debut += batch_size

    # L'API ne renvoie pas plus de 3000 offres par recherche
    if len(all_offres) >= max_offres:
        print(f"⚠️ Département {departement} : plafond de {max_offres} offres atteint, offres potentiellement manquantes")
    return all_offres


def get_last_creation_date():
    """Date de création la plus récente déjà chargée, None si l'historique n'existe pas encore."""
    client = bigquery.Client(project=GCP_PROJECT_ID)
    try:
        rows = client.query(
            f"select max(timestamp(replace(dateCreation, 'Z', '+00:00'))) as last_date "
            f"from `{GCP_PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}`"
        ).result()
    except NotFound:
        return None
    return next(iter(rows)).last_date


def load_to_bigquery(offres):
    df = pd.DataFrame(offres)
    # Colonne de partitionnement : les requêtes filtrées par date ne lisent que les jours utiles
    df["date_creation"] = pd.to_datetime(df["dateCreation"], utc=True).dt.date
    client = bigquery.Client(project=GCP_PROJECT_ID)
    table_id = f"{GCP_PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}"

    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",
        autodetect=True,
        time_partitioning=bigquery.TimePartitioning(field="date_creation"),
        # Le schéma détecté varie selon les offres du jour (champs absents, nouveaux champs)
        schema_update_options=[
            bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION,
            bigquery.SchemaUpdateOption.ALLOW_FIELD_RELAXATION,
        ],
    )

    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()
    print(f"✅ {len(df)} offres chargées dans {table_id}")


def fetch_departement(dept, min_creation):
    # Un token par département : pas de risque d'expiration ni de partage entre threads
    print(f"📍 Traitement du département {dept}...")
    return fetch_all_offres(get_token(), departement=dept, min_creation=min_creation)


if __name__ == "__main__":
    all_offres = []
    failed_depts = []

    last_date = get_last_creation_date()
    if last_date is None:
        # Premier run : on initialise l'historique avec toutes les offres en ligne
        min_creation = None
        print("🆕 Historique vide : récupération de toutes les offres en ligne")
    else:
        min_creation = last_date - OVERLAP
        print(f"📅 Récupération des offres créées depuis le {min_creation:%Y-%m-%d %H:%M} UTC")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(fetch_departement, dept, min_creation): dept for dept in DEPARTEMENTS}
        for future in as_completed(futures):
            dept = futures[future]
            try:
                all_offres.extend(future.result())
            except Exception as e:
                print(f"❌ Erreur pour le département {dept} : {e}")
                failed_depts.append(dept)

    failure_ratio = len(failed_depts) / len(DEPARTEMENTS)
    if failed_depts:
        print(f"⚠️ {len(failed_depts)} département(s) en échec : {', '.join(failed_depts)}")

    # Exit non nul => la tâche Airflow échoue et le prochain run repart de la même date
    if failure_ratio > MAX_FAILURE_RATIO:
        sys.exit(f"❌ Trop d'échecs ({failure_ratio:.0%} > {MAX_FAILURE_RATIO:.0%}), chargement annulé")
    if not all_offres:
        sys.exit("❌ Aucune offre récupérée, chargement annulé")

    load_to_bigquery(all_offres)

    print(f"\n🎉 Terminé ! Total offres chargées : {len(all_offres)}")
