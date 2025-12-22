WITH all_idn_eon AS (
    -- Collect all unique IDN_EON values from table1 with source tracking
    SELECT DISTINCT 
        CAST(IDN_EON AS VARCHAR) AS IDN_EON,
        'table1' AS source_table
    FROM table1
    WHERE IDN_EON IS NOT NULL
    
    UNION ALL
    
    -- Collect from table2
    SELECT DISTINCT 
        CAST(IDN_EON AS VARCHAR) AS IDN_EON,
        'table2' AS source_table
    FROM table2
    WHERE IDN_EON IS NOT NULL
    
    UNION ALL
    
    -- Collect from table3
    SELECT DISTINCT 
        CAST(IDN_EON AS VARCHAR) AS IDN_EON,
        'table3' AS source_table
    FROM table3
    WHERE IDN_EON IS NOT NULL
    
    UNION ALL
    
    -- Collect from table4
    SELECT DISTINCT 
        CAST(IDN_EON AS VARCHAR) AS IDN_EON,
        'table4' AS source_table
    FROM table4
    WHERE IDN_EON IS NOT NULL
    
    UNION ALL
    
    -- Collect from table5
    SELECT DISTINCT 
        CAST(IDN_EON AS VARCHAR) AS IDN_EON,
        'table5' AS source_table
    FROM table5
    WHERE IDN_EON IS NOT NULL
),

aggregated AS (
    -- Aggregate sources for each unique IDN_EON
    SELECT 
        IDN_EON,
        STRING_AGG(DISTINCT source_table, ', ') AS present_in_tables
    FROM all_idn_eon
    GROUP BY IDN_EON
)

-- Only include IDN_EON values that exist in abc123 table
SELECT 
    a.IDN_EON,
    a.present_in_tables
FROM aggregated a
WHERE EXISTS (
    SELECT 1 
    FROM abc123 
    WHERE CAST(abc123.IDN_EON AS VARCHAR) = a.IDN_EON
)
ORDER BY a.IDN_EON;
