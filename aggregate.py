-- Step 1: Create a base table with all unique IDs from the primary dataset
WITH base_table AS (
    -- Get all unique IDs from primary dataset
    -- This is our starting point - all IDs we want to analyze
    SELECT DISTINCT
        CAST(IDN_EON AS VARCHAR) AS IDN_EON,  -- Convert ID to text format for consistency
        'TTAI_SYS' AS source_table             -- Label where this ID came from
    FROM "LH_SND_DB"."WACLOUD_PRJ166"."MAEVEPERSONAL_TTAI_SYS_Active_Owning_Filter"
    WHERE IDN_EON IS NOT NULL                  -- Only include IDs that exist
),

-- Step 2: Collect all unique IDs from multiple source tables
all_ids AS (
    -- Collect ALL unique IDs from all sources
    -- This combines IDs from different tables to see which detection systems flagged each ID
    
    -- Get IDs from keyword filtering table
    SELECT DISTINCT
        CAST(IDN_EON AS VARCHAR) AS IDN_EON,
        'TTAI' AS source_table                 -- Tag this source as 'TTAI'
    FROM "LH_SND_DB"."WACLOUD_PRJ166"."MAEVEPERSONAL_TTAI_SYS_keyword_Filtering"
    WHERE IDN_EON IS NOT NULL
    
    UNION ALL  -- Combine with next table (keeps all rows, even duplicates between tables)
    
    -- Get IDs from PrivacyQ table
    SELECT DISTINCT
        CAST(IDN_EON AS VARCHAR) AS IDN_EON,
        'PrivacyQ' AS source_table             -- Tag this source as 'PrivacyQ'
    FROM "LH_SND_DB"."WACLOUD_PRJ166"."MAEVEPERSONAL_PrivacyQ_for_ITSO_Att_prepared_filtered_filtered"
    WHERE IDN_EON IS NOT NULL
    
    UNION ALL
    
    -- Get IDs from DLM WORM table
    SELECT DISTINCT
        CAST(IDN_EON AS VARCHAR) AS IDN_EON,
        'DLM' AS source_table                  -- Tag this source as 'DLM'
    FROM "LH_SND_DB"."WACLOUD_PRJ166"."MAEVEPERSONAL_DLM_WORM"
    WHERE IDN_EON IS NOT NULL
    
    UNION ALL
    
    -- Get IDs from MYSDM table
    SELECT DISTINCT
        CAST(IDN_EON AS VARCHAR) AS IDN_EON,
        'MYSDM' AS source_table                -- Tag this source as 'MYSDM'
    FROM "LH_SND_DB"."WACLOUD_PRJ166"."MAEVEPERSONAL_MYSDM_Detections_for_Bulk_Email_prepared_filtered"
    WHERE IDN_EON IS NOT NULL
    
    UNION ALL
    
    -- Get IDs from EPR table
    SELECT DISTINCT
        CAST(IDN_EON AS VARCHAR) AS IDN_EON,
        'EPR' AS source_table                  -- Tag this source as 'EPR'
    FROM "LH_SND_DB"."WACLOUD_PRJ166"."MAEVEPERSONAL_epr_filtered"
    WHERE IDN_EON IS NOT NULL
),

-- Step 3: For each unique ID, combine all the sources that flagged it
aggregated AS (
    -- Aggregate sources for each unique ID
    -- If an ID appears in multiple tables, this combines them into one comma-separated list
    -- Example: If ID "123" is in TTAI and DLM, this creates "DLM, TTAI"
    SELECT
        IDN_EON,
        LISTAGG(source_table, ', ') WITHIN GROUP (ORDER BY source_table) AS DETECTION_TYPE
        -- LISTAGG combines multiple values into one string with ', ' between them
        -- WITHIN GROUP (ORDER BY...) sorts them alphabetically
    FROM all_ids
    GROUP BY IDN_EON  -- Group by ID so we get one row per unique ID
),

-- Step 4: Detect specific keywords and capabilities for each ID
keyword_detection AS (
    -- Detect keywords and record their source
    -- This is where we analyze the actual content to determine what capabilities exist
    SELECT
        base_table.IDN_EON AS EON_ID,          -- The unique ID we're analyzing
        MAX(t.TXT_DSPLY_LABEL) AS GKN,         -- Get the display label (MAX just picks one if there are multiple)
        MAX(NME_TAI_ASSET_DSPLY) AS APP_NAME,  -- Get the app name
        a.detection_type AS DETECTION_TYPE,    -- Which detection systems flagged this ID
        'YES' AS ECOMMS_CAPABILITY,            -- All records get marked as having ecomms capability
        
        -- EMAIL DETECTION: Check multiple tables and columns for email-related keywords
        CASE
            -- First check: Does the WORM table have 'x' in the email column?
            WHEN MAX(w.Email) = 'x' THEN 'YES'
            -- Second check: Does MYSDM mention bulk email?
            WHEN MAX(m.TXT_RSRC_GAP_DESC) LIKE '%bulk email%' THEN 'YES'
            -- Third check: Search for email keywords in the description field
            -- POSITION finds if a word exists in text, returns >0 if found
            WHEN POSITION('mailing list' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('send email' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('over email' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('through emails' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('via email' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('bulk emails' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('email notifications' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('newsletters' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('email to' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('emails' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('e-comm' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('e-comms' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('ecomm' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('ecomms' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('email' IN MAX(t.TXT_RSRC_DESC)) > 0 THEN 'YES'
            -- Fourth check: Search for same keywords in a different table/column
            WHEN POSITION('mailing list' IN MAX(d.TXT_DATA_LIFECYCL_MANG_ANSW)) > 0 OR
                 POSITION('send email' IN MAX(d.TXT_DATA_LIFECYCL_MANG_ANSW)) > 0 OR
                 POSITION('over email' IN MAX(d.TXT_DATA_LIFECYCL_MANG_ANSW)) > 0 OR
                 POSITION('through emails' IN MAX(d.TXT_DATA_LIFECYCL_MANG_ANSW)) > 0 OR
                 POSITION('via email' IN MAX(d.TXT_DATA_LIFECYCL_MANG_ANSW)) > 0 OR
                 POSITION('bulk emails' IN MAX(d.TXT_DATA_LIFECYCL_MANG_ANSW)) > 0 OR
                 POSITION('email notifications' IN MAX(d.TXT_DATA_LIFECYCL_MANG_ANSW)) > 0 OR
                 POSITION('newsletters' IN MAX(d.TXT_DATA_LIFECYCL_MANG_ANSW)) > 0 OR
                 POSITION('email to' IN MAX(d.TXT_DATA_LIFECYCL_MANG_ANSW)) > 0 OR
                 POSITION('emails' IN MAX(d.TXT_DATA_LIFECYCL_MANG_ANSW)) > 0 OR
                 POSITION('e-comm' IN MAX(d.TXT_DATA_LIFECYCL_MANG_ANSW)) > 0 OR
                 POSITION('e-comms' IN MAX(d.TXT_DATA_LIFECYCL_MANG_ANSW)) > 0 OR
                 POSITION('ecomm' IN MAX(d.TXT_DATA_LIFECYCL_MANG_ANSW)) > 0 OR
                 POSITION('ecomms' IN MAX(d.TXT_DATA_LIFECYCL_MANG_ANSW)) > 0 OR
                 POSITION('email' IN MAX(d.TXT_DATA_LIFECYCL_MANG_ANSW)) > 0 THEN 'YES'
            -- If none of the above, return whatever value was in the email column
            ELSE MAX(w.Email)
        END AS EMAIL,
        
        -- COMMENTS DETECTION: Similar logic to email, but looking for comment-related keywords
        CASE
            WHEN MAX(w.Comments) = 'x' THEN 'YES'
            WHEN POSITION('commentary' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('comment' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('comments' IN MAX(t.TXT_RSRC_DESC)) > 0 THEN 'YES'
            ELSE MAX(w.Comments)
        END AS COMMENTS,
        
        -- CHAT DETECTION: Looking for chat-related keywords
        CASE
            WHEN MAX(w.Chat) = 'x' THEN 'YES'
            WHEN POSITION('live chat' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('chat' IN MAX(t.TXT_RSRC_DESC)) > 0 THEN 'YES'
            ELSE MAX(w.Chat)
        END AS CHAT,
        
        -- SMS DETECTION: Looking for SMS/text message keywords
        CASE
            WHEN MAX(w.SMS) = 'x' THEN 'YES'
            WHEN POSITION('through text messages' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('text message' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('sms' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('via sms' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('text' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('SMS' IN MAX(t.TXT_RSRC_DESC)) > 0 THEN 'YES'
            ELSE MAX(w.SMS)
        END AS SMS
        
    -- Join all the tables we need to check
    FROM base_table
    LEFT JOIN aggregated a ON base_table.IDN_EON = a.IDN_EON
    -- LEFT JOIN means: keep all rows from base_table even if no match in the other table
    LEFT JOIN "LH_SND_DB"."WACLOUD_PRJ166"."MAEVEPERSONAL_DLM_WORM" w
        ON base_table.IDN_EON = CAST(w.IDN_EON AS VARCHAR)
    LEFT JOIN "LH_SND_DB"."WACLOUD_PRJ166"."MAEVEPERSONAL_DLM_Plan_Responses22" d
        ON base_table.IDN_EON = CAST(d.IDN_EON AS VARCHAR)
    LEFT JOIN "LH_SND_DB"."WACLOUD_PRJ166"."MAEVEPERSONAL_PrivacyQ_for_ITSO_Att_prepared_filtered_filtered" p
        ON base_table.IDN_EON = CAST(p.IDN_EON AS VARCHAR)
    LEFT JOIN "LH_SND_DB"."WACLOUD_PRJ166"."MAEVEPERSONAL_MYSDM_Detections_for_Bulk_Email_prepared_filtered" m
        ON base_table.IDN_EON = CAST(m.IDN_EON AS VARCHAR)
    LEFT JOIN "LH_SND_DB"."WACLOUD_PRJ166"."MAEVEPERSONAL_epr_filtered" e
        ON base_table.IDN_EON = CAST(e.IDN_EON AS VARCHAR)
    LEFT JOIN "LH_SND_DB"."WACLOUD_PRJ166"."MAEVEPERSONAL_TTAI_SYS_Active_Owning_Filter" t
        ON base_table.IDN_EON = CAST(t.IDN_EON AS VARCHAR)
    
    -- Filter: Only include rows that have a detection type and it's not just TTAI_SYS
    WHERE a.detection_type IS NOT NULL AND a.detection_type <> 'TTAI_SYS'
    
    -- GROUP BY: Combine multiple rows for the same ID+detection_type into one row
    GROUP BY base_table.IDN_EON, a.detection_type
)

-- Step 5: Final output - add the SUB_RISK column based on risk B table
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
    
    -- SUB_RISK LOGIC: Determine if this ID should be flagged as A, B, or A,B
    CASE
        -- First check: Is this ID NOT in the risk B table?
        -- NOT EXISTS returns true if the subquery finds no matching rows
        WHEN NOT EXISTS (
            SELECT 1 
            FROM "LH_SND_DB"."WACLOUD_PRJ166"."MAEVEPERSONAL_Risk_B_Output_2_prepared" risk_b
            WHERE risk_b.IDN_EON = keyword_detection.EON_ID
        ) THEN
            -- ID is NOT in risk B table, so we need to add 'B'
            CASE 
                -- If detection type doesn't contain 'dlm_plan_responses', it gets 'A'
                -- So if it already has 'A', we add ',B' to make 'A,B'
                WHEN LOWER(DETECTION_TYPE) NOT LIKE '%dlm_plan_responses%' THEN 'A,B'
                -- If it does contain 'dlm_plan_responses', it doesn't get 'A'
                -- So we just put 'B'
                ELSE 'B'
            END
        ELSE
            -- ID IS in risk B table, so we don't add 'B'
            CASE
                -- If detection type doesn't contain 'dlm_plan_responses', it gets 'A'
                WHEN LOWER(DETECTION_TYPE) NOT LIKE '%dlm_plan_responses%' THEN 'A'
                -- If it does contain 'dlm_plan_responses', it gets nothing (NULL)
                ELSE NULL
            END
    END AS SUB_RISK
    
FROM keyword_detection
ORDER BY EON_ID;  -- Sort the final results by ID
