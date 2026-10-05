from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.python import PythonOperator


def fetch_offres():
    import subprocess
    subprocess.run(
        ['python', '-u', '/opt/airflow/repo/repo/API/fetch_offres.py'], check=True
    )


# gitsync recrée le dossier du repo à chaque commit (sans dbt_packages, ignoré par git) :
# chaque tâche réinstalle les packages pour pouvoir être relancée seule
DBT_CMD = 'cd /opt/airflow/repo/repo/dbt_project && dbt deps --quiet && dbt '

default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='france_travail_pipeline',
    schedule='0 8 * * *',
    start_date=datetime(2026, 3, 1),
    catchup=False,
    # Un seul run à la fois : deux ingestions en parallèle saturent la RAM de Docker (OOM)
    max_active_runs=1,
    default_args=default_args
) as dag:

    ingestion = PythonOperator(
        task_id='fetch_offres',
        python_callable=fetch_offres
    )

    dbt_run = BashOperator(
        task_id='run_dbt',
        bash_command=DBT_CMD + 'seed && dbt run'
    )

    dbt_test = BashOperator(
        task_id='dbt_test',
        bash_command=DBT_CMD + 'test',
    )

    dbt_run_prod = BashOperator(
        task_id='run_dbt_prod',
        bash_command=DBT_CMD + 'seed --target prod && dbt run --target prod'
    )

    dbt_test_prod = BashOperator(
        task_id='dbt_test_prod',
        bash_command=DBT_CMD + 'test --target prod',
    )

    ingestion >> dbt_run >> dbt_test >> dbt_run_prod >> dbt_test_prod
