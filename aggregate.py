WITH src AS (
    SELECT DISTINCT
        CAST(IDN_EON AS VARCHAR) AS IDN_EON,
        'table1' AS table_name
    FROM table1
    WHERE IDN_EON IS NOT NULL

    UNION ALL

    SELECT DISTINCT
        CAST(IDN_EON AS VARCHAR) AS IDN_EON,
        'table2' AS table_name
    FROM table2
    WHERE IDN_EON IS NOT NULL

    UNION ALL

    SELECT DISTINCT
        CAST(IDN_EON AS VARCHAR) AS IDN_EON,
        'table3' AS table_name
    FROM table3
    WHERE IDN_EON IS NOT NULL

    UNION ALL

    SELECT DISTINCT
        CAST(IDN_EON AS VARCHAR) AS IDN_EON,
        'table4' AS table_name
    FROM table4
    WHERE IDN_EON IS NOT NULL
),
ref AS (
    SELECT DISTINCT
        CAST(IDN_EON AS VARCHAR) AS IDN_EON
    FROM abc123
    WHERE IDN_EON IS NOT NULL
),
filtered AS (
    SELECT
        s.IDN_EON,
        s.table_name
    FROM src s
    INNER JOIN ref r
        ON s.IDN_EON = r.IDN_EON
)
SELECT
    IDN_EON,
    STRING_AGG(DISTINCT table_name, ', ' ORDER BY table_name) AS present_in_tables
FROM filtered
GROUP BY IDN_EON
ORDER BY IDN_EON;