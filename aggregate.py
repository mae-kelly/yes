WITH base_table AS (
    -- Get all unique IDs from primary dataset
    SELECT DISTINCT
        CAST(IDN_EON AS VARCHAR) AS IDN_EON,
        'TTAI_SYS' AS source_table
    FROM "[SCHEMA_1]"."[PROJECT_1]"."[TABLE_1]"
    WHERE IDN_EON IS NOT NULL
),

all_ids AS (
    -- Collect ALL unique IDs from all sources
    SELECT DISTINCT
        CAST(IDN_EON AS VARCHAR) AS IDN_EON,
        'TTAI' AS source_table
    FROM "[SCHEMA_1]"."[PROJECT_1]"."[TABLE_2]"
    WHERE IDN_EON IS NOT NULL
    
    UNION ALL
    
    SELECT DISTINCT
        CAST(IDN_EON AS VARCHAR) AS IDN_EON,
        'PrivacyQ' AS source_table
    FROM "[SCHEMA_1]"."[PROJECT_1]"."[TABLE_3]"
    WHERE IDN_EON IS NOT NULL
    
    UNION ALL
    
    SELECT DISTINCT
        CAST(IDN_EON AS VARCHAR) AS IDN_EON,
        'DLM' AS source_table
    FROM "[SCHEMA_1]"."[PROJECT_1]"."[TABLE_4]"
    WHERE IDN_EON IS NOT NULL
    
    UNION ALL
    
    SELECT DISTINCT
        CAST(IDN_EON AS VARCHAR) AS IDN_EON,
        'MYSDM' AS source_table
    FROM "[SCHEMA_1]"."[PROJECT_1]"."[TABLE_5]"
    WHERE IDN_EON IS NOT NULL
    
    UNION ALL
    
    SELECT DISTINCT
        CAST(IDN_EON AS VARCHAR) AS IDN_EON,
        'EPR' AS source_table
    FROM "[SCHEMA_1]"."[PROJECT_1]"."[TABLE_6]"
    WHERE IDN_EON IS NOT NULL
),

aggregated AS (
    -- Aggregate sources for each unique ID
    SELECT
        IDN_EON,
        LISTAGG(source_table, ', ') WITHIN GROUP (ORDER BY source_table) AS DETECTION_TYPE
    FROM all_ids
    GROUP BY IDN_EON
),

keyword_detection AS (
    -- Detect keywords and record their source
    SELECT
        base_table.IDN_EON AS EON_ID,
        MAX(t.[COLUMN_1]) AS GKN,
        MAX([COLUMN_2]) AS APP_NAME,
        a.detection_type AS DETECTION_TYPE,
        'YES' AS ECOMMS_CAPABILITY,
        CASE
            WHEN MAX(w.[COLUMN_3]) = 'x' THEN 'YES'
            WHEN MAX(m.[COLUMN_4]) LIKE '%bulk email%' THEN 'YES'
            WHEN POSITION('mailing list' IN MAX(t.[COLUMN_5])) > 0 OR
                 POSITION('send email' IN MAX(t.[COLUMN_5])) > 0 OR
                 POSITION('over email' IN MAX(t.[COLUMN_5])) > 0 OR
                 POSITION('through emails' IN MAX(t.[COLUMN_5])) > 0 OR
                 POSITION('via email' IN MAX(t.[COLUMN_5])) > 0 OR
                 POSITION('bulk emails' IN MAX(t.[COLUMN_5])) > 0 OR
                 POSITION('email notifications' IN MAX(t.[COLUMN_5])) > 0 OR
                 POSITION('newsletters' IN MAX(t.[COLUMN_5])) > 0 OR
                 POSITION('email to' IN MAX(t.[COLUMN_5])) > 0 OR
                 POSITION('emails' IN MAX(t.[COLUMN_5])) > 0 OR
                 POSITION('e-comm' IN MAX(t.[COLUMN_5])) > 0 OR
                 POSITION('e-comms' IN MAX(t.[COLUMN_5])) > 0 OR
                 POSITION('ecomm' IN MAX(t.[COLUMN_5])) > 0 OR
                 POSITION('ecomms' IN MAX(t.[COLUMN_5])) > 0 OR
                 POSITION('email' IN MAX(t.[COLUMN_5])) > 0 THEN 'YES'
            WHEN POSITION('mailing list' IN MAX(d.[COLUMN_6])) > 0 OR
                 POSITION('send email' IN MAX(d.[COLUMN_6])) > 0 OR
                 POSITION('over email' IN MAX(d.[COLUMN_6])) > 0 OR
                 POSITION('through emails' IN MAX(d.[COLUMN_6])) > 0 OR
                 POSITION('via email' IN MAX(d.[COLUMN_6])) > 0 OR
                 POSITION('bulk emails' IN MAX(d.[COLUMN_6])) > 0 OR
                 POSITION('email notifications' IN MAX(d.[COLUMN_6])) > 0 OR
                 POSITION('newsletters' IN MAX(d.[COLUMN_6])) > 0 OR
                 POSITION('email to' IN MAX(d.[COLUMN_6])) > 0 OR
                 POSITION('emails' IN MAX(d.[COLUMN_6])) > 0 OR
                 POSITION('e-comm' IN MAX(d.[COLUMN_6])) > 0 OR
                 POSITION('e-comms' IN MAX(d.[COLUMN_6])) > 0 OR
                 POSITION('ecomm' IN MAX(d.[COLUMN_6])) > 0 OR
                 POSITION('ecomms' IN MAX(d.[COLUMN_6])) > 0 OR
                 POSITION('email' IN MAX(d.[COLUMN_6])) > 0 THEN 'YES'
            ELSE MAX(w.[COLUMN_3])
        END AS EMAIL,
        CASE
            WHEN MAX(w.[COLUMN_7]) = 'x' THEN 'YES'
            WHEN POSITION('commentary' IN MAX(t.[COLUMN_5])) > 0 OR
                 POSITION('comment' IN MAX(t.[COLUMN_5])) > 0 OR
                 POSITION('comments' IN MAX(t.[COLUMN_5])) > 0 THEN 'YES'
            ELSE MAX(w.[COLUMN_7])
        END AS COMMENTS,
        CASE
            WHEN MAX(w.[COLUMN_8]) = 'x' THEN 'YES'
            WHEN POSITION('live chat' IN MAX(t.[COLUMN_5])) > 0 OR
                 POSITION('chat' IN MAX(t.[COLUMN_5])) > 0 THEN 'YES'
            ELSE MAX(w.[COLUMN_8])
        END AS CHAT,
        CASE
            WHEN MAX(w.[COLUMN_9]) = 'x' THEN 'YES'
            WHEN POSITION('through text messages' IN MAX(t.[COLUMN_5])) > 0 OR
                 POSITION('text message' IN MAX(t.[COLUMN_5])) > 0 OR
                 POSITION('sms' IN MAX(t.[COLUMN_5])) > 0 OR
                 POSITION('via sms' IN MAX(t.[COLUMN_5])) > 0 OR
                 POSITION('text' IN MAX(t.[COLUMN_5])) > 0 OR
                 POSITION('SMS' IN MAX(t.[COLUMN_5])) > 0 THEN 'YES'
            ELSE MAX(w.[COLUMN_9])
        END AS SMS,
        CASE
            WHEN risk_b.IDN_EON IS NULL THEN 
                CASE 
                    WHEN LOWER(a.detection_type) NOT LIKE '%dlm_plan_responses%' THEN 'A,B'
                    ELSE 'B'
                END
            ELSE 
                CASE
                    WHEN LOWER(a.detection_type) NOT LIKE '%dlm_plan_responses%' THEN 'A'
                    ELSE NULL
                END
        END AS SUB_RISK
    FROM base_table
    LEFT JOIN aggregated a ON base_table.IDN_EON = a.IDN_EON
    LEFT JOIN "[SCHEMA_1]"."[PROJECT_1]"."[TABLE_4]" w
        ON base_table.IDN_EON = CAST(w.IDN_EON AS VARCHAR)
    LEFT JOIN "[SCHEMA_1]"."[PROJECT_1]"."[TABLE_7]" d
        ON base_table.IDN_EON = CAST(d.IDN_EON AS VARCHAR)
    LEFT JOIN "[SCHEMA_1]"."[PROJECT_1]"."[TABLE_3]" p
        ON base_table.IDN_EON = CAST(p.IDN_EON AS VARCHAR)
    LEFT JOIN "[SCHEMA_1]"."[PROJECT_1]"."[TABLE_5]" m
        ON base_table.IDN_EON = CAST(m.IDN_EON AS VARCHAR)
    LEFT JOIN "[SCHEMA_1]"."[PROJECT_1]"."[TABLE_6]" e
        ON base_table.IDN_EON = CAST(e.IDN_EON AS VARCHAR)
    LEFT JOIN "[SCHEMA_1]"."[PROJECT_1]"."[TABLE_1]" t
        ON base_table.IDN_EON = CAST(t.IDN_EON AS VARCHAR)
    LEFT JOIN "[SCHEMA_2]"."[PROJECT_2]"."[TABLE_8]" risk_b
        ON base_table.IDN_EON = risk_b.IDN_EON
    WHERE a.detection_type IS NOT NULL AND a.detection_type <> 'TTAI_SYS'
    GROUP BY base_table.IDN_EON, a.detection_type, risk_b.IDN_EON
)

SELECT 
    EON_ID,
    DETECTION_TYPE,
    GKN,
    APP_NAME,
    ECOMMS_CAPABILITY,
    EMAIL,
    COMMENTS,
    CHAT,
    SMS,
    SUB_RISK
FROM keyword_detection
ORDER BY EON_ID;
