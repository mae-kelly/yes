WITH base_table AS (
    -- Get all unique IDs from primary dataset
    SELECT DISTINCT 
        CAST(ID_FIELD AS VARCHAR) AS ID_FIELD
    FROM dataset1
    WHERE ID_FIELD IS NOT NULL
),

all_ids AS (
    -- Collect ALL unique IDs from all sources
    SELECT DISTINCT
        CAST(ID_FIELD AS VARCHAR) AS ID_FIELD,
        'dataset1' AS source_table
    FROM dataset1
    WHERE ID_FIELD IS NOT NULL
    
    UNION ALL
    
    SELECT DISTINCT
        CAST(ID_FIELD AS VARCHAR) AS ID_FIELD,
        'dataset2' AS source_table
    FROM dataset2
    WHERE ID_FIELD IS NOT NULL
    
    UNION ALL
    
    SELECT DISTINCT
        CAST(ID_FIELD AS VARCHAR) AS ID_FIELD,
        'dataset3' AS source_table
    FROM dataset3
    WHERE ID_FIELD IS NOT NULL
    
    UNION ALL
    
    SELECT DISTINCT
        CAST(ID_FIELD AS VARCHAR) AS ID_FIELD,
        'dataset4' AS source_table
    FROM dataset4
    WHERE ID_FIELD IS NOT NULL
    
    UNION ALL
    
    SELECT DISTINCT
        CAST(ID_FIELD AS VARCHAR) AS ID_FIELD,
        'dataset5' AS source_table
    FROM dataset5
    WHERE ID_FIELD IS NOT NULL
),

aggregated AS (
    -- Aggregate sources for each unique ID
    SELECT
        ID_FIELD,
        LISTAGG(source_table, ', ') WITHIN GROUP (ORDER BY source_table) AS present_in_tables
    FROM all_ids
    GROUP BY ID_FIELD
),

ids_only_in_dataset1 AS (
    -- Identify IDs that ONLY appear in dataset1
    SELECT ID_FIELD
    FROM aggregated
    WHERE present_in_tables = 'dataset1'
),

filtered_data AS (
    -- ONLY extract keywords for IDs that are ONLY in dataset1
    SELECT
        ID_FIELD,
        FIELD_A,
        LISTAGG(DISTINCT REGEXP_SUBSTR(TEXT_FIELD, '[^.!?]*\b(keyword)\b[^.!?]*[.!?]', 1, 1, 'i'), ' ')
        WITHIN GROUP (ORDER BY REGEXP_SUBSTR(TEXT_FIELD, '[^.!?]*\b(keyword)\b[^.!?]*[.!?]', 1, 1, 'i')) AS extracted_text
    FROM (
        SELECT
            ID_FIELD,
            TEXT_FIELD,
            FIELD_A,
            CASE
                WHEN LOWER(TEXT_FIELD) LIKE '%connect with%' THEN 'connect with'
                WHEN LOWER(TEXT_FIELD) LIKE '%communicate with%' THEN 'communicate with'
                WHEN LOWER(TEXT_FIELD) LIKE '%mailing list%' THEN 'mailing list'
                WHEN LOWER(TEXT_FIELD) LIKE '%send email%' THEN 'send emails'
                WHEN LOWER(TEXT_FIELD) LIKE '%over email%' THEN 'over email'
                WHEN LOWER(TEXT_FIELD) LIKE '%through emails%' THEN 'through emails'
                WHEN LOWER(TEXT_FIELD) LIKE '%messaging%' THEN 'messaging'
                WHEN LOWER(TEXT_FIELD) LIKE '%through text messages%' THEN 'through text messages'
                WHEN LOWER(TEXT_FIELD) LIKE '%text messages%' THEN 'text messages'
                WHEN LOWER(TEXT_FIELD) LIKE '%via email%' THEN 'via email'
                WHEN LOWER(TEXT_FIELD) LIKE '%live chat%' THEN 'live chat'
                WHEN LOWER(TEXT_FIELD) LIKE '%bulk emails%' THEN 'bulk emails'
                WHEN LOWER(TEXT_FIELD) LIKE '%email notifications%' THEN 'email notifications'
                WHEN LOWER(TEXT_FIELD) LIKE '%newsletters%' THEN 'newsletters'
                WHEN LOWER(TEXT_FIELD) LIKE '%sms%' THEN 'sms'
                WHEN LOWER(TEXT_FIELD) LIKE '%email to%' THEN 'email to'
                WHEN LOWER(TEXT_FIELD) LIKE '%receive a message%' THEN 'receive a message'
                WHEN LOWER(TEXT_FIELD) LIKE '%commentary%' THEN 'commentary'
                WHEN LOWER(TEXT_FIELD) LIKE '%chat%' THEN 'chat'
                WHEN LOWER(TEXT_FIELD) LIKE '%meet with%' THEN 'meet with'
                WHEN LOWER(TEXT_FIELD) LIKE '%via sms%' THEN 'via sms'
                WHEN LOWER(TEXT_FIELD) LIKE '%secure communication%' THEN 'secure communication'
                WHEN LOWER(TEXT_FIELD) LIKE '%send%' THEN 'send'
                WHEN LOWER(TEXT_FIELD) LIKE '%to an individual%' THEN 'to an individual'
                WHEN LOWER(TEXT_FIELD) LIKE '%communicate%' THEN 'communicate'
                WHEN LOWER(TEXT_FIELD) LIKE '%email%' THEN 'email'
                ELSE NULL
            END AS keyword
        FROM dataset1
        WHERE ID_FIELD IN (SELECT ID_FIELD FROM ids_only_in_dataset1)  -- ONLY process IDs exclusive to dataset1
    ) sub
    WHERE keyword IS NOT NULL
    GROUP BY ID_FIELD, FIELD_A
)

-- Final SELECT - all IDs from dataset1, but keyword extraction only for exclusive IDs
SELECT
    base_table.ID_FIELD,
    a.present_in_tables,
    MAX(d.FIELD_B) AS FIELD_B,
    MAX(d.FIELD_C) AS FIELD_C,
    MAX(d.FIELD_D) AS FIELD_D,
    MAX(p.FIELD_E) AS FIELD_E,
    f.extracted_text,
    f.FIELD_A,
    MAX(m.FIELD_F) AS FIELD_F
FROM base_table
LEFT JOIN aggregated a ON base_table.ID_FIELD = a.ID_FIELD
LEFT JOIN dataset3 d
    ON base_table.ID_FIELD = CAST(d.ID_FIELD AS VARCHAR)
LEFT JOIN dataset2 p
    ON base_table.ID_FIELD = CAST(p.ID_FIELD AS VARCHAR)
LEFT JOIN filtered_data f
    ON base_table.ID_FIELD = f.ID_FIELD
LEFT JOIN dataset4 m
    ON base_table.ID_FIELD = CAST(m.ID_FIELD AS VARCHAR)
LEFT JOIN dataset5 e
    ON base_table.ID_FIELD = CAST(e.ID_FIELD AS VARCHAR)
GROUP BY base_table.ID_FIELD, a.present_in_tables, f.extracted_text, f.FIELD_A
ORDER BY base_table.ID_FIELD;
