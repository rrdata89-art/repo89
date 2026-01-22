CREATE OR REPLACE PROCEDURE `rrdata89.trusted.SP_PROCESSAR_BITCOIN_V2`()
BEGIN
/*****************************************************************************************************************************************
  PROCEDURE: SP_PROCESSAR_BITCOIN_V2
  OBJETIVO: Carga DELTA na rrdata89.trusted.tb_bitcoin_historico
*****************************************************************************************************************************************/

    -- Declaração de variáveis
    DECLARE MAX_DATA_REF TIMESTAMP DEFAULT NULL;
    DECLARE DELTA_START TIMESTAMP DEFAULT NULL;

    BEGIN
        -- 1) Descobre a última data que temos na Trusted
        SET MAX_DATA_REF = (
            SELECT IFNULL(MAX(data_referencia), TIMESTAMP('1970-01-01 00:00:00+00'))
            FROM `rrdata89.trusted.tb_bitcoin_historico`
        );

        -- 2) Define o início da leitura (Volta 3 dias por segurança)
        SET DELTA_START = TIMESTAMP_SUB(MAX_DATA_REF, INTERVAL 3 DAY);

        -- 3) Inserção Inteligente
        INSERT INTO `rrdata89.trusted.tb_bitcoin_historico` (
            data_referencia,
            valor_brl,
            data_processamento
        )
        WITH SRC AS (
            SELECT
                TIMESTAMP_MILLIS(CAST(JSON_EXTRACT_SCALAR(json_payload, '$.prices[0][0]') AS INT64)) as data_referencia,
                CAST(JSON_EXTRACT_SCALAR(json_payload, '$.prices[0][1]') AS FLOAT64) as valor_brl,
                CURRENT_TIMESTAMP() as data_processamento
            FROM `rrdata89.raw.api_bitcoin`
            WHERE json_payload IS NOT NULL
        ),
        FILTERED AS (
            SELECT * FROM SRC WHERE data_referencia >= DELTA_START
        ),
        DEDUP AS (
            SELECT * FROM FILTERED
            QUALIFY ROW_NUMBER() OVER (
                PARTITION BY data_referencia ORDER BY data_processamento DESC
            ) = 1
        )
        SELECT
            D.data_referencia,
            D.valor_brl,
            D.data_processamento
        FROM DEDUP D
        WHERE NOT EXISTS (
            SELECT 1 FROM `rrdata89.trusted.tb_bitcoin_historico` T
            WHERE T.data_referencia = D.data_referencia
        );

    -- Tratamento de Erro
    EXCEPTION WHEN ERROR THEN
        RAISE USING MESSAGE = FORMAT(
            "ERRO NA PROCEDURE SP_PROCESSAR_BITCOIN_V2! Query: %s. Erro: %s.",
            @@error.statement_text, @@error.message
        );
    END;
END;