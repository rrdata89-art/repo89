# RRData89 DataLake V2 - Bitcoin Extractor Pipeline

## 📋 Visão Geral

Pipeline completo de **extração, transformação e carga (ETL)** de dados de Bitcoin a partir da API CoinGecko. Implementado em **Google Cloud Platform (GCP)** com arquitetura em **camadas (RAW → TRUSTED → REFINED)**.

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                      CLOUD FUNCTION (Extract)                   │
│              Extrai dados da API CoinGecko (1 dia)               │
│                   Carrega na camada RAW                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   AIRFLOW DAG (Orchestration)                    │
│          Orquestra pipeline diário 06h00 (Brasília)              │
│              Executa procedures TRUSTED e REFINED                │
└────────────────────────────┬────────────────────────────────────┘
                             │
         ┌───────────────────┴───────────────────┐
         ▼                                       ▼
  ┌─────────────────┐             ┌──────────────────────┐
  │  TRUSTED Layer  │             │  REFINED Layer       │
  │ (Dados validados│ ──Delta──>  │  (Análise Final)     │
  │  deduplicados)  │             │  (Consumo BI)        │
  └─────────────────┘             └──────────────────────┘
```

---

## 📁 Estrutura de Arquivos

```
rrdata89-datalake_02/
├── airflow-dags/
│   └── dev/
│       └── dag_api_bitcoin_v3.py          # DAG Airflow (Orquestração)
├── apis/
│   └── bitcoin-extractor/
│       └── src/
│           ├── main.py                     # Cloud Function (Extração)
│           └── requirements.txt            # Dependências Python
├── sql/
│   ├── trusted/
│   │   └── tz_tb_bitcoin.sql              # Procedure TRUSTED (Validação)
│   └── refined/
│       └── rf_tb_bitcoin.sql              # Procedure REFINED (Análise)
└── README.md                               # Este arquivo
```
----
---

## 🔄 Fluxo de Dados

### 1️⃣ **RAW Layer** (Extração)
- **Fonte**: API CoinGecko (`/coins/bitcoin/market_chart`)
- **Frequência**: Diária (manual por enquanto)
- **Função**: `executar_pipeline()` em `main.py`
- **Saída**: Tabela `rrdata89.raw.api_bitcoin`
- **Dados**: JSON bruto + timestamp de ingestão

### 2️⃣ **TRUSTED Layer** (Transformação)
- **Entrada**: Dados brutos da camada RAW
- **Procedure**: `SP_PROCESSAR_BITCOIN_V2` em `tz_tb_bitcoin.sql`
- **Transformações**:
  - Extrai arrays JSON (preços históricos)
  - Converte timestamps de milissegundos para TIMESTAMP
  - Remove duplicatas
  - Implementa lógica **DELTA** (apenas dados novos)
  - Valida integridade dos dados
- **Saída**: Tabela `rrdata89.trusted.tb_bitcoin_historico` (série temporal)

### 3️⃣ **REFINED Layer** (Análise)
- **Entrada**: Dados processados da TRUSTED
- **Procedure**: `SP_PROCESSAR_REFINED` em `rf_tb_bitcoin.sql`
- **Transformações**:
  - Carrega dados da TRUSTED para consumo
  - Implementa lógica **DELTA** incremental
  - Adiciona timestamp de refinamento (audit)
- **Saída**: Tabela `rrdata89.refined.tb_bitcoin_analitico` (pronto para BI)

---

## 🚀 Como Usar

### Executar Manualmente

#### Opção 1: Via Cloud Console
1. Acesse [Cloud Functions](https://console.cloud.google.com/functions)
2. Selecione `cf-extract-api-bitcoin`
3. Clique em "ATIVAR" e execute a função

#### Opção 2: Via Terminal (gcloud)
```bash
gcloud functions call cf-extract-api-bitcoin \
  --region=southamerica-east1
```

#### Opção 3: Via Airflow (após ativação)
```bash
airflow trigger_dag pipeline_api_bitcoin_v3
```

---

## ⚙️ Ativar Execução Automática

Para agendar o pipeline **todos os dias às 06h00 (Brasília)**:

1. Edite o arquivo `dag_api_bitcoin_v3.py`
2. Descomente a linha:
   ```python
   # schedule_interval='0 6 * * *',  # 06h00 Brasil
   ```
3. Comente a linha:
   ```python
   schedule_interval=None,  # Execução manual
   ```
4. Atualize a DAG no Airflow
5. Aguarde próximo agendamento

---

## 📊 Monitoramento

### Logs
- **Cloud Function**: [Cloud Logging](https://console.cloud.google.com/logs)
- **Airflow**: Interface web do Airflow (Tasks > Task Logs)
- **BigQuery**: Query History

### Alertas
- ❌ Falhas na Cloud Function → Retentar (config: 1 retry / 5 min)
- ⚠️ Atraso na execução → Verificar Airflow Scheduler

---

## 📈 Métricas de Sucesso

| Métrica | Esperado | Status |
|---------|----------|--------|
| Latência extração | < 30s | ✅ |
| Ingestão diária | 1 execução | ⏳ |
| Linhas/dia TRUSTED | ~10-50 (delta) | 📊 |
| Linhas/dia REFINED | ~10-50 (delta) | 📊 |
| Erro taxa | 0% | ✅ |

---

## 🔧 Dependências

### Cloud Functions
```
functions-framework==3.0.0
requests
pandas
google-cloud-bigquery
```

### GCP Services
- ✅ Cloud Functions
- ✅ Cloud Scheduler (opcional para agendamento)
- ✅ BigQuery
- ✅ Cloud Logging
- ✅ Airflow (Cloud Composer)

---

## 🐛 Troubleshooting

| Problema | Solução |
|----------|---------|
| **RAW não recebe dados** | Verificar autenticação GCP + Internet |
| **TRUSTED com erros** | Validar formato JSON em RAW |
| **REFINED vazio** | Rodar TRUSTED primeiro |
| **Execução muito lenta** | Aumentar memória Cloud Function (512MB) |
| **Duplicatas em TRUSTED** | Lógica DELTA já previne (CHECK) |

---

## 📝 Notas Técnicas

### Por que 3 camadas?
- **RAW**: Preserva dados originais para auditoria
- **TRUSTED**: Limpeza, validação, deduplicação
- **REFINED**: Pronto para BI/Analytics (sem complexidade)

### Por que DELTA (incremental)?
- ⚡ Reduz custo BigQuery (menos dados processados)
- 🔄 Simples recuperação em caso de falha
- 📊 Histórico completo preservado

### Segurança
- Autenticação via **Google Cloud IAM**
- Dados encriptados em repouso (BigQuery)
- Acesso controlado por grupo de trabalho

---

## 👤 Responsável

**Engenheiro de Dados**: @rrdata89  
**Última atualização**: 21 de janeiro de 2026  
**Versão**: 2.0 (V2 do DataLake)

---

## 📞 Suporte

Dúvidas ou issues? Entre em contato com o time de dados rrdata89.

