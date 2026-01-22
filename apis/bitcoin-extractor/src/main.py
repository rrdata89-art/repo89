import functions_framework
import requests
import pandas as pd
import json
from google.cloud import bigquery
import datetime

# --- CONFIGURAÇÃO ---
# URL da API CoinGecko para extrair histórico de preços do Bitcoin em BRL (últimos 1 dia)
API_URL = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=brl&days=1"
# Tabela BigQuery onde os dados brutos serão armazenados
TABLE_ID = "rrdata89.raw.api_bitcoin"

@functions_framework.http
def executar_pipeline(request):
    """
    Função serverless executada via Google Cloud Function.
    Realiza a extração de dados de Bitcoin da API externa e carrega na camada RAW do DW.
    """
    try:
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # BLOCO 1: EXTRAÇÃO (Extract)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Realiza requisição HTTP GET para a API CoinGecko
        # Usa headers User-Agent obrigatório pela API
        # raise_for_status() lança exceção se status HTTP for 4xx ou 5xx
        response = requests.get(API_URL, headers={"User-Agent": "GCP-Function"})
        response.raise_for_status()
        data = response.json()
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # BLOCO 2: TRANSFORMAÇÃO (Transform)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Estrutura payload JSON contendo os dados brutos da API
        # Adiciona timestamp de ingestão para rastreabilidade e auditoria
        client = bigquery.Client()
        rows = [
            {
                "json_payload": json.dumps(data),  # Dados brutos da API em formato JSON
                "data_ingestao": datetime.datetime.now().isoformat()  # Timestamp UTC de quando foi inserido
            }
        ]
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # BLOCO 3: CARGA (Load)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Insere os dados na tabela RAW do BigQuery
        # insert_rows_json retorna lista vazia se sucesso, ou erros se houver problemas
        errors = client.insert_rows_json(TABLE_ID, rows)
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # BLOCO 4: TRATAMENTO DE ERROS
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Se houver erros na inserção, retorna status 500 com detalhes
        if errors:
            return f"Erro na inserção BigQuery: {errors}", 500
        
        # Sucesso: retorna status 200
        return "Sucesso na extração e carga de dados", 200
        
    except Exception as e:
        # Captura qualquer erro não esperado (conexão, timeout, etc)
        # Retorna mensagem de erro e status 500
        return f"Erro no pipeline: {str(e)}", 500