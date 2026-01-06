WITH keyword_filtered AS (
    -- Filter and extract relevant text based on keywords
    SELECT
        id_col,
        LISTAGG(DISTINCT REGEXP_SUBSTR(text_col, '[^.!?]*\b(keyword)\b[^.!?]*[.!?]', 1, 1, 'i'), ' ')
        WITHIN GROUP (ORDER BY REGEXP_SUBSTR(text_col, '[^.!?]*\b(keyword)\b[^.!?]*[.!?]', 1, 1, 'i')) AS extracted_text
    FROM (
        SELECT
            id_col,
            text_col,
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
    ) sub
    WHERE keyword IS NOT NULL
    GROUP BY id_col
)

-- Return ALL rows from table1 with extracted_text added
SELECT
    t1.*,
    kf.extracted_text
FROM "DB"."SCHEMA"."table1" t1
LEFT JOIN keyword_filtered kf
    ON CAST(t1.id_col AS VARCHAR) = kf.id_col
ORDER BY t1.id_col;
