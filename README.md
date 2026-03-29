# 🇫🇷 Analyse du marché de l'emploi en France — Projet Portfolio Analytics Engineering

Projet end-to-end d'analytics engineering visant à analyser le marché de l'emploi en France par région, à partir des données temps réel de l'API France Travail.

---

## 🎯 Question métier

> **Comment se répartissent les offres d'emploi en France selon les régions, les secteurs d'activité et les types de contrat ?**

Ce projet permet d'identifier les dynamiques régionales du marché de l'emploi, les secteurs en tension, et les types de contrats dominants — des informations utiles pour les demandeurs d'emploi, les recruteurs et les acteurs des politiques publiques.

---

## 🏗️ Architecture

```
API France Travail
       │
       ▼
  Python Script               ← Ingestion via OAuth2 (300 000 lignes)
       │
       ▼
  BigQuery (raw)              ← raw_france_travail.offres_emploi
       │
       ▼
  dbt Core                    ← Transformations : staging → fact/dim → marts → metrics
       │
       ▼
  BigQuery (marts/metrics)    ← Modèles prêts pour la BI
       │
       ▼
  Looker Studio               ← Dashboard interactif (à venir)
```

---

## 🛠️ Stack technique

| Composant      | Outil                                |
| -------------- | ------------------------------------ |
| Ingestion      | Python + API France Travail (OAuth2) |
| Data Warehouse | Google BigQuery                      |
| Transformation | dbt Core                             |
| Orchestration  | Apache Airflow _(à venir)_           |
| Visualisation  | Looker Studio _(à venir)_            |
| Versionning    | Git / GitHub                         |

---

## 📁 Structure du projet

```
portfolio-france-travail/
├── API/
│   └── fetch_offres.py         # Script d'ingestion des offres via l'API France Travail
├── dbt_project/
│   ├── models/
│   │   ├── staging/            # Nettoyage et typage des données brutes
│   │   ├── intermediate/       # Logique métier intermédiaire
│   │   └── marts/              # Modèles "business ready"
│   │   └── metrics/            # Variables alimentants les dashboards
│   ├── macros/                 # Macros dbt réutilisables
│   ├── tests/                  # Tests génériques et singuliers
│   ├── dbt_project.yml
│   └── profiles.yml            # (non versionné — voir .gitignore)
├── .env                        # Credentials API (non versionné)
├── .gitignore
└── README.md
```

---

## 🔄 Pipeline dbt

Le projet suit la convention de layering **staging → intermediate → marts** :

- **Staging** (`stg_offres_emploi`) — Cast des types, renommage des colonnes, suppression des doublons. Une ligne = une offre brute nettoyée.
- **Intermediate** — Enrichissements et jointures métier (ex. mapping codes NAF → libellés secteurs, normalisation des régions).
- **Marts** (`mart_offres_by_region`, `mart_offres_by_secteur`, ...) — Agrégats prêts à consommer par Looker. Testés avec des contraintes `not_null`, `unique` et `accepted_values`.
- **Modèle de métriques** — Modèle final exposé à Looker Studio, construit via un CROSS JOIN pour garantir la continuité temporelle (zéro offre = 0, pas de ligne manquante).

### Compétences dbt illustrées

- Modularité et séparation des responsabilités par layer
- Tests natifs (`not_null`, `unique`, `relationships`, `accepted_values`)
- Documentation inline via fichiers `.yml` et blocs `{% docs %}`
- Macros pour la réutilisabilité
- Sources déclarées avec freshness checks

---

## 🚀 Reproduire le projet

### Prérequis

- Python 3.10+
- Un projet Google Cloud Platform avec BigQuery activé
- Un compte développeur France Travail ([francetravail.io](https://francetravail.io))
- dbt Core avec le connecteur BigQuery : `pip install dbt-bigquery`

### Installation

```bash
git clone https://github.com/<ton-user>/portfolio-france-travail.git
cd portfolio-france-travail

# Créer et activer un environnement virtuel
python -m venv portfolio_env
source portfolio_env/bin/activate  # ou portfolio_env\Scripts\Activate.ps1 sur Windows

pip install -r requirements.txt
```

### Configuration

Créer un fichier `.env` à la racine :

```env
CLIENT_ID=<ton_client_id_france_travail>
CLIENT_SECRET=<ton_client_secret_france_travail>
```

Configurer `dbt_project/profiles.yml` avec les credentials BigQuery (voir [documentation dbt](https://docs.getdbt.com/docs/core/connect-data-platform/bigquery-setup)).

### Lancer le pipeline

```bash
# 1. Ingestion des données
python API/fetch_offres.py

# 2. Transformations dbt
cd dbt_project
dbt deps
dbt run
dbt test
dbt docs generate && dbt docs serve
```

---

## 📊 Dashboard _(à venir)_

Un rapport Looker Studio sera connecté aux marts BigQuery pour visualiser :

- Carte de France — nombre d'offres par région
- Top secteurs d'activité par volume d'offres
- Métiers les plus tendus

---

## 👤 Auteur

**Benoit Ricart** — Analytics Engineer  
[LinkedIn](https://www.linkedin.com/in/benoît-ricart-08961112a/) · [GitHub](https://github.com/Ricart95/porfolio_AE_ricart)

---

## 📄 Source

Les données proviennent de l'[API France Travail](https://francetravail.io)
