"""
DAG: Pipeline Bitcoin V3
Estrutura: Monorepo rrdata89
"""
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from airflow.utils.dates import days_ago
from datetime import timedelta

# --- CONSTANTES ---
PROJECT_ID = "rrdata89"
REGION_BR = "southamerica-east1"
# URL fixa da function (Deployada via Cloud Console ou CI/CD separado)
FUNCTION_URL = "https://cf-extract-api-bitcoin-1013772993221.southamerica-east1.run.app"

PROC_TRUSTED = f"{PROJECT_ID}.trusted.SP_PROCESSAR_BITCOIN_V2"
PROC_REFINED = f"{PROJECT_ID}.refined.SP_PROCESSAR_REFINED"

default_args = {
    'owner': 'rrdata89',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'pipeline_api_bitcoin_v3',
    default_args=default_args,
    description='Pipeline V3: Raw -> Trusted -> Refined',
    schedule_interval='0 9 * * *',
    start_date=days_ago(1),
    catchup=False,
    tags=['bitcoin', 'prod', 'refined'],
) as dag:

    t1_raw = BashOperator(
        task_id='cf_extract_api-raw',
        bash_command=f"""
        curl -m 300 -X POST {FUNCTION_URL} \
        -H "Authorization: bearer $(gcloud auth print-identity-token)" \
        -H "Content-Type: application/json" \
        -d '{{}}'
        """
    )

    t2_trusted = BigQueryInsertJobOperator(
        task_id='sp_proc-trusted',
        configuration={"query": {"query": f"CALL `{PROC_TRUSTED}`();", "useLegacySql": False}},
        location=REGION_BR,
    )

    t3_refined = BigQueryInsertJobOperator(
        task_id='sp_proc-refined',
        configuration={"query": {"query": f"CALL `{PROC_REFINED}`();", "useLegacySql": False}},
        location=REGION_BR,
    )

    t1_raw >> t2_trusted >> t3_refined