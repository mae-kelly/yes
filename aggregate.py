WITH base_table AS (
    -- Get all unique IDs from primary dataset
    SELECT DISTINCT 
        CAST(id_col AS VARCHAR) AS id_col
    FROM "DB"."SCHEMA"."table1"
    WHERE id_col IS NOT NULL
),

all_ids AS (
    -- Collect ALL unique IDs from all sources
    SELECT DISTINCT
        CAST(id_col AS VARCHAR) AS id_col,
        'table1' AS source_table
    FROM "DB"."SCHEMA"."table1"
    WHERE id_col IS NOT NULL
    
    UNION ALL
    
    SELECT DISTINCT
        CAST(id_col AS VARCHAR) AS id_col,
        'table2' AS source_table
    FROM "DB"."SCHEMA"."table2"
    WHERE id_col IS NOT NULL
    
    UNION ALL
    
    SELECT DISTINCT
        CAST(id_col AS VARCHAR) AS id_col,
        'table3' AS source_table
    FROM "DB"."SCHEMA"."table3"
    WHERE id_col IS NOT NULL
    
    UNION ALL
    
    SELECT DISTINCT
        CAST(id_col AS VARCHAR) AS id_col,
        'table4' AS source_table
    FROM "DB"."SCHEMA"."table4"
    WHERE id_col IS NOT NULL
    
    UNION ALL
    
    SELECT DISTINCT
        CAST(id_col AS VARCHAR) AS id_col,
        'table5' AS source_table
    FROM "DB"."SCHEMA"."table5"
    WHERE id_col IS NOT NULL
),

aggregated AS (
    -- Aggregate sources for each unique ID
    SELECT
        id_col,
        LISTAGG(source_table, ', ') WITHIN GROUP (ORDER BY source_table) AS present_in_tables
    FROM all_ids
    GROUP BY id_col
),

ids_only_in_table1 AS (
    -- Identify IDs that ONLY appear in table1 dataset
    SELECT id_col
    FROM aggregated
    WHERE present_in_tables = 'table1'
),

filtered_data AS (
    -- ONLY extract keywords for IDs that are ONLY in table1
    SELECT
        id_col,
        col_a,
        LISTAGG(DISTINCT REGEXP_SUBSTR(text_col, '[^.!?]*\b(keyword)\b[^.!?]*[.!?]', 1, 1, 'i'), ' ')
        WITHIN GROUP (ORDER BY REGEXP_SUBSTR(text_col, '[^.!?]*\b(keyword)\b[^.!?]*[.!?]', 1, 1, 'i')) AS extracted_text
    FROM (
        SELECT
            id_col,
            text_col,
            col_a,
            CASE
                WHEN LOWER(text_col) LIKE '%connect with%' THEN 'connect with'
                WHEN LOWER(text_col) LIKE '%communicate with%' THEN 'communicate with'
                WHEN LOWER(text_col) LIKE '%mailing list%' THEN 'mailing list'
                WHEN LOWER(text_col) LIKE '%send email%' THEN 'send emails'
                WHEN LOWER(text_col) LIKE '%over email%' THEN 'over email'
                WHEN LOWER(text_col) LIKE '%through emails%' THEN 'through emails'
                WHEN LOWER(text_col) LIKE '%messaging%' THEN 'messaging'
                WHEN LOWER(text_col) LIKE '%through text messages%' THEN 'through text messages'
                WHEN LOWER(text_col) LIKE '%text messages%' THEN 'text messages'
                WHEN LOWER(text_col) LIKE '%via email%' THEN 'via email'
                WHEN LOWER(text_col) LIKE '%live chat%' THEN 'live chat'
                WHEN LOWER(text_col) LIKE '%bulk emails%' THEN 'bulk emails'
                WHEN LOWER(text_col) LIKE '%email notifications%' THEN 'email notifications'
                WHEN LOWER(text_col) LIKE '%newsletters%' THEN 'newsletters'
                WHEN LOWER(text_col) LIKE '%sms%' THEN 'sms'
                WHEN LOWER(text_col) LIKE '%email to%' THEN 'email to'
                WHEN LOWER(text_col) LIKE '%receive a message%' THEN 'receive a message'
                WHEN LOWER(text_col) LIKE '%commentary%' THEN 'commentary'
                WHEN LOWER(text_col) LIKE '%chat%' THEN 'chat'
                WHEN LOWER(text_col) LIKE '%meet with%' THEN 'meet with'
                WHEN LOWER(text_col) LIKE '%via sms%' THEN 'via sms'
                WHEN LOWER(text_col) LIKE '%secure communication%' THEN 'secure communication'
                WHEN LOWER(text_col) LIKE '%send%' THEN 'send'
                WHEN LOWER(text_col) LIKE '%to an individual%' THEN 'to an individual'
                WHEN LOWER(text_col) LIKE '%communicate%' THEN 'communicate'
                WHEN LOWER(text_col) LIKE '%email%' THEN 'email'
                ELSE NULL
            END AS keyword
        FROM "DB"."SCHEMA"."table1"
        WHERE id_col IN (SELECT id_col FROM ids_only_in_table1)
    ) sub
    WHERE keyword IS NOT NULL
    GROUP BY id_col, col_a
)

-- Final SELECT - all IDs from table1, but keyword extraction only for exclusive IDs
SELECT
    base_table.id_col,
    a.present_in_tables,
    MAX(d.col_b) AS col_b,
    MAX(d.col_c) AS col_c,
    MAX(d.col_d) AS col_d,
    MAX(p.col_e) AS col_e,
    MAX(f.extracted_text) AS extracted_text,
    MAX(f.col_a) AS col_a,
    MAX(m.col_f) AS col_f
FROM base_table
LEFT JOIN aggregated a ON base_table.id_col = a.id_col
LEFT JOIN "DB"."SCHEMA"."table3" d
    ON base_table.id_col = CAST(d.id_col AS VARCHAR)
LEFT JOIN "DB"."SCHEMA"."table2" p
    ON base_table.id_col = CAST(p.id_col AS VARCHAR)
LEFT JOIN filtered_data f
    ON base_table.id_col = f.id_col
LEFT JOIN "DB"."SCHEMA"."table4" m
    ON base_table.id_col = CAST(m.id_col AS VARCHAR)
LEFT JOIN "DB"."SCHEMA"."table5" e
    ON base_table.id_col = CAST(e.id_col AS VARCHAR)
GROUP BY base_table.id_col, a.present_in_tables
ORDER BY base_table.id_col;
