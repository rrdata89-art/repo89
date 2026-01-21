import functions_framework
import requests
import pandas as pd
import json
from google.cloud import bigquery
import datetime

# --- CONFIG ---
API_URL = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=brl&days=1"
TABLE_ID = "rrdata89.raw.api_bitcoin"

@functions_framework.http
def executar_pipeline(request):
    try:
        # Extract
        response = requests.get(API_URL, headers={"User-Agent": "GCP-Function"})
        response.raise_for_status()
        data = response.json()
        
        # Load Raw
        client = bigquery.Client()
        rows = [{"json_payload": json.dumps(data), "data_ingestao": datetime.datetime.now().isoformat()}]
        errors = client.insert_rows_json(TABLE_ID, rows)
        
        if errors: return f"Erro BQ: {errors}", 500
        return "Sucesso", 200
    except Exception as e:
        return f"Erro: {str(e)}", 500