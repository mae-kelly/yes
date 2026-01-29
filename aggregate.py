/*
================================================================================
ECOMMS DETECTION AND RISK CLASSIFICATION QUERY
================================================================================

PURPOSE:
This query identifies applications and their ECOMMS-related features, then 
classifies them into risk categories based on specific criteria.

RISK DEFINITIONS:
- Risk A: Applications that appear in DLM plan responses (inconsistent plans)
- Risk B: Applications NOT found in the Risk B reference table (not archiving)

OUTPUT:
A table showing each application (EON_ID) with its detected features and 
assigned risk classification (SUB_RISK column only - no separate RISK column).

================================================================================
*/

-- ============================================================================
-- STEP 1: Create base table of all unique EON IDs from multiple sources
-- ============================================================================
-- This section gathers all distinct application IDs from various ECOMMS tables
-- to ensure we capture every application that might be relevant

WITH base_table AS (
    SELECT DISTINCT
        CAST(IDN_EON AS VARCHAR) AS IDN_EON,
        'TTAI' AS source_table
    FROM "LH_SND_DB"."WMCLOUD_PRJ166"."MAEVEPERSONAL_TTAI_SYS_Active_Owning_Filter"
    WHERE IDN_EON IS NOT NULL
),

-- ============================================================================
-- STEP 2: Get Risk B reference IDs
-- ============================================================================
-- This table contains applications that are properly onboarded to ECOMMS
-- If an application is NOT in this table, it gets flagged as Risk B

risk_b_ids AS (
    SELECT DISTINCT
        CAST(IDN_EON AS VARCHAR) AS IDN_EON
    FROM "LH_SND_DB"."WMCLOUD_PRJ166"."MAEVEPERSONAL_RISK_B_OUTPUT_2_PREPARED"
    WHERE IDN_EON IS NOT NULL
),

-- ============================================================================
-- STEP 3: Gather all EON IDs from different ECOMMS feature tables
-- ============================================================================
-- This section collects application IDs from various feature-specific tables
-- and unions them together to create a comprehensive list

all_ids AS (
    -- TTAI System data
    SELECT DISTINCT
        CAST(IDN_EON AS VARCHAR) AS IDN_EON,
        'TTAI' AS source_table
    FROM "LH_SND_DB"."WMCLOUD_PRJ166"."MAEVEPERSONAL_TTAI_SYS_prepared_filtered"
    WHERE IDN_EON IS NOT NULL

    UNION ALL
    
    -- Privacy Q data for IT50 attributes
    SELECT DISTINCT
        CAST(IDN_EON AS VARCHAR) AS IDN_EON,
        'PrivacyQ' AS source_table
    FROM "LH_SND_DB"."WMCLOUD_PRJ166"."MAEVEPERSONAL_PrivacyQ_for_IT50_Att_prepared_filtered_filtered"
    WHERE IDN_EON IS NOT NULL

    UNION ALL
    
    -- DLM Work data
    SELECT DISTINCT
        CAST(IDN_EON AS VARCHAR) AS IDN_EON,
        'SOURCE_CODE' AS source_table
    FROM "LH_SND_DB"."WMCLOUD_PRJ166"."MAEVEPERSONAL_DLM_WORM"
    WHERE IDN_EON IS NOT NULL

    UNION ALL
    
    -- MYSDM Detections for bulk email
    SELECT DISTINCT
        CAST(IDN_EON AS VARCHAR) AS IDN_EON,
        'MYSDM' AS source_table
    FROM "LH_SND_DB"."WMCLOUD_PRJ166"."MAEVEPERSONAL_MYSDM_Detections_for_Bulk_Email_prepared_filtered"
    WHERE IDN_EON IS NOT NULL

    UNION ALL
    
    -- DLM in-scope data (final)
    SELECT DISTINCT
        CAST(IDN_EON AS VARCHAR) AS IDN_EON,
        'DLM' AS source_table
    FROM "LH_SND_DB"."WMCLOUD_PRJ166"."MAEVEPERSONAL_in_scope_dlm_final"
    WHERE IDN_EON IS NOT NULL

    UNION ALL
    
    -- ECOMM Detection data
    SELECT DISTINCT
        CAST(IDN_EON AS VARCHAR) AS IDN_EON,
        'ECOMM_DETECTION' AS source_table
    FROM "LH_SND_DB"."WMCLOUD_PRJ166"."MAEVEPERSONAL_ecomm_detection_yes_filtered"
    WHERE IDN_EON IS NOT NULL

    UNION ALL
    
    -- EPR filtered data
    SELECT DISTINCT
        CAST(IDN_EON AS VARCHAR) AS IDN_EON,
        'EPR' AS source_table
    FROM "LH_SND_DB"."WMCLOUD_PRJ166"."MAEVEPERSONAL_epr_filtered"
    WHERE IDN_EON IS NOT NULL
),

-- ============================================================================
-- STEP 4: Aggregate detection types by EON ID
-- ============================================================================
-- Groups all the different source tables by application ID and creates a 
-- comma-separated list of where each application was detected

aggregated AS (
    SELECT
        IDN_EON,
        LISTAGG(source_table, ', ') WITHIN GROUP (ORDER BY source_table) AS DETECTION_TYPE
    FROM all_ids
    GROUP BY IDN_EON
),

-- ============================================================================
-- STEP 5: Detect specific ECOMMS keywords in application descriptions
-- ============================================================================
-- This section searches through application text fields to identify mentions
-- of specific ECOMMS-related features (email, chat, SMS, video, etc.)

keyword_detection AS (
    SELECT
        bt.IDN_EON AS EON_ID,
        
        -- Get the main application label/name
        MAX(t.TXT_DSPLY_LABEL) AS GRN,
        
        -- Get various descriptive text fields that might contain keywords
        MAX(d.TXT_DATA_LIFECYCL_MANG_ANSW) AS TXT_DATA_LIFECYCL_MANG_ANSW,
        MAX(t.NME_TAI_ASSET_DSPLY) AS APP_NAME,
        
        -- Get detection type from previous step
        a.DETECTION_TYPE AS DETECTION_TYPE,
        
        -- Text description fields to search for keywords
        MAX(t.TXT_RSRC_DESC) AS TXT_RSRC_DESC,
        MAX(e.TXT_APPL_DESC) AS TXT_APPL_DESC,

        -- ===================================================================
        -- EMAIL DETECTION
        -- Searches for email-related keywords in text descriptions
        -- ===================================================================
        CASE
            -- Check if 's.Email' keyword appears in text
            WHEN MAX(s.Email) = 'x' THEN 'YES'
            -- Check for various email-related terms in description fields
            WHEN POSITION('via email' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('email to' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('by email' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('email communications' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('email notification' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('secure email' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('email based' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('email communication' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('over email' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('using email' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('email notification' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('email client' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('email flow' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('outlook-based email' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('receives email' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('mailing list' IN MAX(t.TXT_APPL_DESC)) > 0 OR
                 POSITION('send email' IN MAX(e.TXT_APPL_DESC)) > 0 OR
                 POSITION('over email' IN MAX(e.TXT_APPL_DESC)) > 0 OR
                 POSITION('through emails' IN MAX(e.TXT_APPL_DESC)) > 0 OR
                 POSITION('via email' IN MAX(e.TXT_APPL_DESC)) > 0 OR
                 POSITION('bulk emails' IN MAX(e.TXT_APPL_DESC)) > 0 OR
                 POSITION('email notifications' IN MAX(e.TXT_APPL_DESC)) > 0 OR
                 POSITION('save-receipts' IN MAX(e.TXT_APPL_DESC)) > 0 OR
                 POSITION('email to' IN MAX(e.TXT_APPL_DESC)) > 0 OR
                 POSITION('send to' IN MAX(e.TXT_APPL_DESC)) > 0 OR
                 POSITION('e-comm' IN MAX(e.TXT_APPL_DESC)) > 0 OR
                 POSITION('e-comms' IN MAX(e.TXT_APPL_DESC)) > 0 OR
                 POSITION('ecomm' IN MAX(e.TXT_APPL_DESC)) > 0 OR
                 POSITION('ecomms' IN MAX(e.TXT_APPL_DESC)) > 0
            THEN 'YES'
            -- Special case: Check MYSDM table for bulk email detections
            WHEN POSITION('yes, TXT_DATA_LIFECYCL_MANG_ANSW value: true' IN d.TXT_DATA_LIFECYCL_MANG_ANSW) > 0
            THEN 'YES'
            WHEN EXISTS (
                SELECT 1
                FROM "LH_SND_DB"."WMCLOUD_PRJ166"."MAEVEPERSONAL_MYSDM_Detections_for_Bulk_Email_prepared_filtered" m2
                WHERE CAST(m2.IDN_EON AS VARCHAR) = bt.IDN_EON
            ) THEN 'YES'
        END AS EMAIL,

        -- ===================================================================
        -- COMMENTS DETECTION
        -- Searches for comment/feedback-related keywords
        -- ===================================================================
        CASE
            WHEN MAX(s.Comments) = 'x' THEN 'YES'
            WHEN POSITION('comment' IN MAX(e.TXT_APPL_DESC)) > 0 OR
                 POSITION('comment on' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('post comment' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('comment share' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('yes, TXT_DATA_LIFECYCL_MANG_ANSW value: true' IN d.TXT_DATA_LIFECYCL_MANG_QSTN_COMMENTS) > 0
            THEN 'YES'
        END AS COMMENTS,

        -- ===================================================================
        -- VIDEO DETECTION
        -- Searches for video conferencing and communication keywords
        -- ===================================================================
        CASE
            WHEN POSITION('video conferencing' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('video conferences' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('enterprise video' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('zoom video' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('video call' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('hd video' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('video interviewing' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('live video' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('video communications' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('captures video' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('video recording' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('video messaging' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('video enabled' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('enables video' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('video capture' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('video record' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('record video' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('yes, TXT_DATA_LIFECYCL_MANG_ANSW value: true' IN d.TXT_DATA_LIFECYCL_MANG_QSTN_VIDEO) > 0
            THEN 'YES'
        END AS VIDEO,

        -- ===================================================================
        -- CHAT DETECTION
        -- Searches for chat and messaging-related keywords
        -- ===================================================================
        CASE
            WHEN MAX(s.Chat) = 'x' THEN 'YES'
            WHEN POSITION('chat' IN MAX(e.TXT_APPL_DESC)) > 0 OR
                 POSITION('yes, TXT_DATA_LIFECYCL_MANG_ANSW value: true' IN d.TXT_DATA_LIFECYCL_MANG_QSTN_CHAT) > 0
            THEN 'YES'
        END AS CHAT,

        -- ===================================================================
        -- SMS DETECTION
        -- Searches for SMS and text messaging keywords
        -- ===================================================================
        CASE
            WHEN MAX(s.SMS) = 'x' THEN 'YES'
            WHEN POSITION('a message' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('chat rooms' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('via sms' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('users chat' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('swift message' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('message delivery' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('message queue' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('text to' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('chat messages' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('message exchange' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('multi-party chat' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('chat multi-party' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('individual chat' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('chat meet' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('to chat' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('helpdesk chat' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('live chat' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('chat functionality' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('chat feature' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('chat sms' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('sms messages' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('text messages' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('chat experience' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('message service' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('message gateway' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('message for' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('message from' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('enables message' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('message transfer' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('message processing' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('chat threads' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('chat function' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('chat secure' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('chat room' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('messaging chat' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('chat application' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('chat interactions' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('real time chat' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('chat window' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('sending sms' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('use sms' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('sms texting' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('sms messaging' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('provide sms' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('custom message' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('message sent' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('receive message' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('electronic message' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('chat session' IN MAX(t.TXT_RSRC_DESC)) > 0 OR
                 POSITION('sending sms' IN MAX(t.TXT_APPL_DESC)) > 0 OR
                 POSITION('yes, TXT_DATA_LIFECYCL_MANG_ANSW value: true' IN d.TXT_DATA_LIFECYCL_MANG_QSTN_SMS) > 0 OR
                 POSITION('sms' IN MAX(e.TXT_APPL_DESC)) > 0 OR
                 POSITION('via sms' IN MAX(e.TXT_APPL_DESC)) > 0 OR
                 POSITION('text' IN MAX(e.TXT_APPL_DESC)) > 0
            THEN 'YES'
        END AS SMS,

        -- ===================================================================
        -- VOICE DETECTION
        -- Searches for voice communication keywords
        -- ===================================================================
        CASE
            WHEN POSITION('yes, TXT_DATA_LIFECYCL_MANG_ANSW value: true' IN d.TXT_DATA_LIFECYCL_MANG_QSTN_VOICE) > 0 OR
                 POSITION('voice' IN MAX(t.TXT_RSRC_DESC)) > 0
            THEN 'YES'
        END AS VOICE,
        
        -- Track if application is present in archive
        MAX(d.PRESENT_IN_ARCHIVE) AS PRESENT_IN_ARCHIVE

    -- Join all the necessary tables together
    FROM base_table bt
    LEFT JOIN aggregated a
        ON bt.IDN_EON = a.IDN_EON
    LEFT JOIN "LH_SND_DB"."WMCLOUD_PRJ166"."MAEVEPERSONAL_dlm_worm" s
        ON bt.IDN_EON = CAST(s.IDN_EON AS VARCHAR)
    LEFT JOIN "LH_SND_DB"."WMCLOUD_PRJ166"."MAEVEPERSONAL_in_scope_dlm_final" d
        ON bt.IDN_EON = CAST(d.IDN_EON AS VARCHAR)
    LEFT JOIN "LH_SND_DB"."WMCLOUD_PRJ166"."MAEVEPERSONAL_PrivacyQ_for_IT50_Att_prepared_filtered_filtered" p
        ON bt.IDN_EON = CAST(p.IDN_EON AS VARCHAR)
    LEFT JOIN "LH_SND_DB"."WMCLOUD_PRJ166"."MAEVEPERSONAL_MYSDM_Detections_for_Bulk_Email_prepared_filtered" m
        ON bt.IDN_EON = CAST(m.IDN_EON AS VARCHAR)
    LEFT JOIN "LH_SND_DB"."WMCLOUD_PRJ166"."MAEVEPERSONAL_epr_filtered" e
        ON bt.IDN_EON = CAST(e.IDN_EON AS VARCHAR)
    LEFT JOIN "LH_SND_DB"."WMCLOUD_PRJ166"."MAEVEPERSONAL_TTAI_SYS_Active_Owning_Filter" t
        ON bt.IDN_EON = CAST(t.IDN_EON AS VARCHAR)
    
    -- Only include records where detection type is 'TTAI-SYS'
    WHERE a.DETECTION_TYPE IS NOT NULL
        AND a.DETECTION_TYPE <> 'TTAI-SYS'
    
    -- Group by application ID and detection type
    GROUP BY
        bt.IDN_EON,
        a.DETECTION_TYPE
),

-- ============================================================================
-- STEP 6: Create final output with risk classifications
-- ============================================================================
-- Combines all the detection data and assigns risk categories based on:
-- - Risk A: If found in DLM plan responses
-- - Risk B: If NOT found in Risk B reference table

final_output AS (
    SELECT
        kd.EON_ID,
        kd.DETECTION_TYPE,
        
        -- Get the maximum (most complete) values for each text field
        MAX(kd.GRN) AS GRN,
        MAX(kd.APP_NAME) AS APP_NAME,
        
        -- Convert YES/NO flags to user-friendly format
        -- If any value is 'YES', show 'YES', otherwise show the actual value
        MAX(CASE WHEN kd.EMAIL = 'YES' THEN 'YES' ELSE kd.EMAIL END) AS EMAIL,
        MAX(CASE WHEN kd.COMMENTS = 'YES' THEN 'YES' ELSE kd.COMMENTS END) AS COMMENTS,
        MAX(CASE WHEN kd.CHAT = 'YES' THEN 'YES' ELSE kd.CHAT END) AS CHAT,
        MAX(CASE WHEN kd.SMS = 'YES' THEN 'YES' ELSE kd.SMS END) AS SMS,
        MAX(CASE WHEN kd.VOICE = 'YES' THEN 'YES' ELSE kd.VOICE END) AS VOICE,
        
        -- Keep the text description fields
        MAX(kd.TXT_RSRC_DESC) AS TXT_RSRC_DESC,
        MAX(kd.TXT_APPL_DESC) AS TXT_APPL_DESC,
        MAX(kd.TXT_DATA_LIFECYCL_MANG_ANSW) AS TXT_DATA_LIFECYCL_MANG_ANSW,
        MAX(kd.PRESENT_IN_ARCHIVE) AS PRESENT_IN_ARCHIVE
        
    FROM keyword_detection kd
    GROUP BY kd.EON_ID, kd.DETECTION_TYPE
)

-- ============================================================================
-- FINAL SELECT: Output the complete results with risk classification
-- ============================================================================
SELECT
    fo.EON_ID,
    fo.DETECTION_TYPE,
    fo.GRN,
    fo.APP_NAME,
    fo.EMAIL,
    fo.COMMENTS,
    fo.CHAT,
    fo.SMS,
    fo.VOICE,
    fo.PRESENT_IN_ARCHIVE,
    
    -- ========================================================================
    -- ONBOARDED FLAG
    -- Shows 'YES' if application is in Risk B table, 'NO' otherwise
    -- ========================================================================
    CASE
        WHEN rb.IDN_EON IS NOT NULL THEN 'YES'
        ELSE 'NO'
    END AS ONBOARDED_TO_ECOMMS_ARCHIVE,

    -- ========================================================================
    -- SUB_RISK CLASSIFICATION (NO SEPARATE RISK COLUMN)
    -- ========================================================================
    -- Logic:
    -- 1. If application IS in DLM plan responses → Risk A (NOT LIKE means it's NOT there, so assign Risk A)
    -- 2. If application is NOT in Risk B table → Risk B
    -- 3. Otherwise → No risk assigned (NULL)
    -- ========================================================================
    CASE
        -- Check if detection type does NOT include dlm_plan_response
        -- This means it's in the DLM plan responses and has inconsistent plans
        WHEN LOWER(fo.DETECTION_TYPE) NOT LIKE '%dlm_plan_response%' THEN 
            'A: Application with inconsistent plans and assessments for ECOMMs'
        
        -- Check if NOT in Risk B table (not onboarded/not archiving properly)
        WHEN rb.IDN_EON IS NULL THEN 
            'B: Application with ECOMMs features not archiving'
        
        -- If neither condition is met, no risk is assigned
        ELSE NULL
    END AS SUB_RISK,
    
    -- ========================================================================
    -- CONFIDENCE SCORE
    -- ========================================================================
    -- This calculates a percentage score based on how many different sources
    -- detected this application. More sources = higher confidence.
    -- 
    -- Scoring logic:
    -- - Check if application exists in each of 6 possible source tables
    -- - If exists in PrivacyQ table → 100% confidence
    -- - If exists in DLM_WORM table → 100% confidence  
    -- - If exists in MYSDM table → 100% confidence
    -- - If exists in ecomm_detection table → 100% confidence
    -- - If exists in in_scope_dlm table → 100% confidence
    -- - Otherwise → 75% confidence if in TTAI table, 0% if not found
    -- ========================================================================
    CASE
        -- Full confidence if found in specific high-priority tables
        WHEN EXISTS (
            SELECT 1
            FROM "LH_SND_DB"."WMCLOUD_PRJ166"."MAEVEPERSONAL_PrivacyQ_for_IT50_Att_prepared_filtered_filtered" p
            WHERE CAST(p.IDN_EON AS VARCHAR) = fo.EON_ID
        )
        OR EXISTS (
            SELECT 1
            FROM "LH_SND_DB"."WMCLOUD_PRJ166"."MAEVEPERSONAL_DLM_WORM" w
            WHERE CAST(w.IDN_EON AS VARCHAR) = fo.EON_ID
        )
        OR EXISTS (
            SELECT 1
            FROM "LH_SND_DB"."WMCLOUD_PRJ166"."MAEVEPERSONAL_MYSDM_Detections_for_Bulk_Email_prepared_filtered" m
            WHERE CAST(m.IDN_EON AS VARCHAR) = fo.EON_ID
        )
        OR EXISTS (
            SELECT 1
            FROM "LH_SND_DB"."WMCLOUD_PRJ166"."MAEVEPERSONAL_ecomm_detection_yes_filtered" c
            WHERE CAST(c.IDN_EON AS VARCHAR) = fo.EON_ID
        )
        OR EXISTS (
            SELECT 1
            FROM "LH_SND_DB"."WMCLOUD_PRJ166"."MAEVEPERSONAL_in_scope_dlm_final" d
            WHERE CAST(d.IDN_EON AS VARCHAR) = fo.EON_ID
        )
        THEN '100%'
        
        -- Partial confidence if found in TTAI table
        WHEN EXISTS (
            SELECT 1
            FROM "LH_SND_DB"."WMCLOUD_PRJ166"."MAEVEPERSONAL_TTAI_SYS_Active_Owning_Filter" ttai
            WHERE CAST(ttai.IDN_EON AS VARCHAR) = fo.EON_ID
        )
        THEN '75%'
        
        -- Low confidence otherwise
        ELSE '0%'
    END AS CONFIDENCE

-- Join with risk_b_ids to determine onboarding status
FROM final_output fo
LEFT JOIN risk_b_ids rb
    ON rb.IDN_EON = fo.EON_ID

-- Only include records where at least one ECOMMS feature exists
WHERE EXISTS (
    SELECT 1
    FROM "LH_SND_DB"."WMCLOUD_PRJ166"."MAEVEPERSONAL_TTAI_SYS_Active_Owning_Filter" ttai
    WHERE CAST(ttai.IDN_EON AS VARCHAR) = fo.EON_ID
)

-- Sort results by application ID
ORDER BY fo.EON_ID;
