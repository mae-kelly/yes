WITH keyword_filtered_raw AS (
    -- Apply keyword filtering to ALL rows BEFORE doing distinct
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
    WHERE LOWER(text_col) LIKE '%connect with%'
        OR LOWER(text_col) LIKE '%communicate with%'
        OR LOWER(text_col) LIKE '%mailing list%'
        OR LOWER(text_col) LIKE '%send email%'
        OR LOWER(text_col) LIKE '%over email%'
        OR LOWER(text_col) LIKE '%through emails%'
        OR LOWER(text_col) LIKE '%messaging%'
        OR LOWER(text_col) LIKE '%through text messages%'
        OR LOWER(text_col) LIKE '%text messages%'
        OR LOWER(text_col) LIKE '%via email%'
        OR LOWER(text_col) LIKE '%live chat%'
        OR LOWER(text_col) LIKE '%bulk emails%'
        OR LOWER(text_col) LIKE '%email notifications%'
        OR LOWER(text_col) LIKE '%newsletters%'
        OR LOWER(text_col) LIKE '%sms%'
        OR LOWER(text_col) LIKE '%email to%'
        OR LOWER(text_col) LIKE '%receive a message%'
        OR LOWER(text_col) LIKE '%commentary%'
        OR LOWER(text_col) LIKE '%chat%'
        OR LOWER(text_col) LIKE '%meet with%'
        OR LOWER(text_col) LIKE '%via sms%'
        OR LOWER(text_col) LIKE '%secure communication%'
        OR LOWER(text_col) LIKE '%send%'
        OR LOWER(text_col) LIKE '%to an individual%'
        OR LOWER(text_col) LIKE '%communicate%'
        OR LOWER(text_col) LIKE '%email%'
),

keyword_aggregated AS (
    -- Aggregate extracted text for each id_col
    SELECT
        id_col,
        col_a,
        LISTAGG(DISTINCT REGEXP_SUBSTR(text_col, '[^.!?]*\b(keyword)\b[^.!?]*[.!?]', 1, 1, 'i'), ' ')
        WITHIN GROUP (ORDER BY REGEXP_SUBSTR(text_col, '[^.!?]*\b(keyword)\b[^.!?]*[.!?]', 1, 1, 'i')) AS extracted_text
    FROM keyword_filtered_raw
    WHERE keyword IS NOT NULL
    GROUP BY id_col, col_a
),

distinct_ids AS (
    -- Get all distinct id_cols from table1
    SELECT DISTINCT 
        CAST(id_col AS VARCHAR) AS id_col
    FROM "DB"."SCHEMA"."table1"
    WHERE id_col IS NOT NULL
)

-- Return all distinct IDs with their keyword-filtered data
SELECT
    d.id_col,
    MAX(k.col_a) AS col_a,
    MAX(k.extracted_text) AS extracted_text
FROM distinct_ids d
LEFT JOIN keyword_aggregated k
    ON d.id_col = CAST(k.id_col AS VARCHAR)
GROUP BY d.id_col
ORDER BY d.id_col;
