CREATE OR REPLACE PROCEDURE `rrdata89.refined.SP_PROCESSAR_REFINED`()
BEGIN
/***********************************************************************************************
  PROCEDURE: SP_PROCESSAR_REFINED
  OBJETIVO: Carga Delta da Trusted para a Refined (Consumo Final)
***********************************************************************************************/

    DECLARE MAX_DATA_REF TIMESTAMP DEFAULT NULL;

    BEGIN
        -- 1) Cria a tabela se não existir (para facilitar seu primeiro run)
        CREATE TABLE IF NOT EXISTS `rrdata89.refined.tb_bitcoin_analitico` (
            data_referencia TIMESTAMP,
            valor_brl FLOAT64,
            data_processamento TIMESTAMP,
            data_refino TIMESTAMP
        );

        -- 2) Descobre até onde já processamos na Refined
        SET MAX_DATA_REF = (
            SELECT IFNULL(MAX(data_referencia), TIMESTAMP('1970-01-01'))
            FROM `rrdata89.refined.tb_bitcoin_analitico`
        );

        -- 3) Insere apenas o que é novo (Delta) vindo da Trusted
        INSERT INTO `rrdata89.refined.tb_bitcoin_analitico`
        SELECT
            data_referencia,
            valor_brl,
            data_processamento,
            CURRENT_TIMESTAMP() as data_refino
        FROM `rrdata89.trusted.tb_bitcoin_historico`
        WHERE data_referencia > MAX_DATA_REF;

    EXCEPTION WHEN ERROR THEN
        RAISE USING MESSAGE = FORMAT("Erro na Refined: %s", @@error.message);
    END;
END;