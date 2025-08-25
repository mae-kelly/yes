-- /src/database/ao1_metrics_queries.sql

SELECT 
    'Overall Coverage Totals' as metric_category,
    COUNT(*) as total_hosts,
    COUNT(CASE WHEN logging_in_splunk = 'yes' THEN 1 END) as total_splunk_logging,
    ROUND(COUNT(CASE WHEN logging_in_splunk = 'yes' THEN 1 END) * 100.0 / COUNT(*), 2) as splunk_coverage_pct,
    COUNT(CASE WHEN present_in_cmdb = 'yes' THEN 1 END) as total_cmdb_present,
    ROUND(COUNT(CASE WHEN present_in_cmdb = 'yes' THEN 1 END) * 100.0 / COUNT(*), 2) as cmdb_coverage_pct,
    COUNT(CASE WHEN LOWER(edr_coverage) LIKE '%crowdstrike agent%' THEN 1 END) as total_crowdstrike,
    ROUND(COUNT(CASE WHEN LOWER(edr_coverage) LIKE '%crowdstrike agent%' THEN 1 END) * 100.0 / COUNT(*), 2) as crowdstrike_coverage_pct,
    COUNT(CASE WHEN LOWER(tanium_coverage) LIKE '%tanium%' THEN 1 END) as total_tanium,
    ROUND(COUNT(CASE WHEN LOWER(tanium_coverage) LIKE '%tanium%' THEN 1 END) * 100.0 / COUNT(*), 2) as tanium_coverage_pct,
    COUNT(CASE WHEN LOWER(apm) LIKE '%apm%' THEN 1 END) as total_apm,
    ROUND(COUNT(CASE WHEN LOWER(apm) LIKE '%apm%' THEN 1 END) * 100.0 / COUNT(*), 2) as apm_coverage_pct
FROM universal_cmdb_copy2;

SELECT 
    '1DC Domain Analysis' as analysis_type,
    COUNT(CASE WHEN LOWER(domain) LIKE '%1dc%' THEN 1 END) as total_1dc_hosts,
    COUNT(CASE WHEN LOWER(domain) LIKE '%1dc%' AND logging_in_splunk = 'yes' THEN 1 END) as dc1_splunk_covered,
    COUNT(CASE WHEN LOWER(domain) LIKE '%1dc%' AND present_in_cmdb = 'yes' THEN 1 END) as dc1_cmdb_covered,
    COUNT(CASE WHEN LOWER(domain) LIKE '%1dc%' AND LOWER(edr_coverage) LIKE '%crowdstrike agent%' THEN 1 END) as dc1_crowdstrike_covered,
    ROUND(COUNT(CASE WHEN LOWER(domain) LIKE '%1dc%' AND logging_in_splunk = 'yes' THEN 1 END) * 100.0 / 
          NULLIF(COUNT(CASE WHEN LOWER(domain) LIKE '%1dc%' THEN 1 END), 0), 2) as dc1_splunk_pct,
    ROUND(COUNT(CASE WHEN LOWER(domain) LIKE '%1dc%' AND present_in_cmdb = 'yes' THEN 1 END) * 100.0 / 
          NULLIF(COUNT(CASE WHEN LOWER(domain) LIKE '%1dc%' THEN 1 END), 0), 2) as dc1_cmdb_pct,
    ROUND(COUNT(CASE WHEN LOWER(domain) LIKE '%1dc%' AND LOWER(edr_coverage) LIKE '%crowdstrike agent%' THEN 1 END) * 100.0 / 
          NULLIF(COUNT(CASE WHEN LOWER(domain) LIKE '%1dc%' THEN 1 END), 0), 2) as dc1_crowdstrike_pct
FROM universal_cmdb_copy2
UNION ALL
SELECT 
    'FEAD Domain Analysis' as analysis_type,
    COUNT(CASE WHEN LOWER(domain) LIKE '%fead%' THEN 1 END) as total_fead_hosts,
    COUNT(CASE WHEN LOWER(domain) LIKE '%fead%' AND logging_in_splunk = 'yes' THEN 1 END) as fead_splunk_covered,
    COUNT(CASE WHEN LOWER(domain) LIKE '%fead%' AND present_in_cmdb = 'yes' THEN 1 END) as fead_cmdb_covered,
    COUNT(CASE WHEN LOWER(domain) LIKE '%fead%' AND LOWER(edr_coverage) LIKE '%crowdstrike agent%' THEN 1 END) as fead_crowdstrike_covered,
    ROUND(COUNT(CASE WHEN LOWER(domain) LIKE '%fead%' AND logging_in_splunk = 'yes' THEN 1 END) * 100.0 / 
          NULLIF(COUNT(CASE WHEN LOWER(domain) LIKE '%fead%' THEN 1 END), 0), 2) as fead_splunk_pct,
    ROUND(COUNT(CASE WHEN LOWER(domain) LIKE '%fead%' AND present_in_cmdb = 'yes' THEN 1 END) * 100.0 / 
          NULLIF(COUNT(CASE WHEN LOWER(domain) LIKE '%fead%' THEN 1 END), 0), 2) as fead_cmdb_pct,
    ROUND(COUNT(CASE WHEN LOWER(domain) LIKE '%fead%' AND LOWER(edr_coverage) LIKE '%crowdstrike agent%' THEN 1 END) * 100.0 / 
          NULLIF(COUNT(CASE WHEN LOWER(domain) LIKE '%fead%' THEN 1 END), 0), 2) as fead_crowdstrike_pct
FROM universal_cmdb_copy2;

SELECT 
    CASE 
        WHEN LOWER(region) LIKE '%north america%' OR LOWER(region) LIKE '%usa%' OR LOWER(region) LIKE '%us%' THEN 'North America'
        WHEN LOWER(region) LIKE '%latam%' OR LOWER(region) LIKE '%latin%' OR LOWER(region) LIKE '%south america%' THEN 'LATAM'
        WHEN LOWER(region) LIKE '%emea%' OR LOWER(region) LIKE '%europe%' OR LOWER(region) LIKE '%africa%' OR LOWER(region) LIKE '%middle east%' THEN 'EMEA'
        WHEN LOWER(region) LIKE '%apac%' OR LOWER(region) LIKE '%asia%' OR LOWER(region) LIKE '%pacific%' THEN 'APAC'
        ELSE COALESCE(region, 'Unknown')
    END as standardized_region,
    COUNT(*) as total_hosts_region,
    COUNT(CASE WHEN present_in_cmdb = 'yes' THEN 1 END) as cmdb_covered_region,
    ROUND(COUNT(CASE WHEN present_in_cmdb = 'yes' THEN 1 END) * 100.0 / COUNT(*), 2) as cmdb_region_pct,
    COUNT(CASE WHEN logging_in_splunk = 'yes' THEN 1 END) as splunk_covered_region,
    ROUND(COUNT(CASE WHEN logging_in_splunk = 'yes' THEN 1 END) * 100.0 / COUNT(*), 2) as splunk_region_pct,
    COUNT(CASE WHEN LOWER(edr_coverage) LIKE '%crowdstrike agent%' THEN 1 END) as crowdstrike_covered_region,
    ROUND(COUNT(CASE WHEN LOWER(edr_coverage) LIKE '%crowdstrike agent%' THEN 1 END) * 100.0 / COUNT(*), 2) as crowdstrike_region_pct
FROM universal_cmdb_copy2
GROUP BY 
    CASE 
        WHEN LOWER(region) LIKE '%north america%' OR LOWER(region) LIKE '%usa%' OR LOWER(region) LIKE '%us%' THEN 'North America'
        WHEN LOWER(region) LIKE '%latam%' OR LOWER(region) LIKE '%latin%' OR LOWER(region) LIKE '%south america%' THEN 'LATAM'
        WHEN LOWER(region) LIKE '%emea%' OR LOWER(region) LIKE '%europe%' OR LOWER(region) LIKE '%africa%' OR LOWER(region) LIKE '%middle east%' THEN 'EMEA'
        WHEN LOWER(region) LIKE '%apac%' OR LOWER(region) LIKE '%asia%' OR LOWER(region) LIKE '%pacific%' THEN 'APAC'
        ELSE COALESCE(region, 'Unknown')
    END
ORDER BY total_hosts_region DESC;

SELECT 
    cio,
    COUNT(*) as total_hosts_cio,
    COUNT(CASE WHEN logging_in_splunk = 'yes' THEN 1 END) as splunk_coverage_cio,
    COUNT(CASE WHEN present_in_cmdb = 'yes' THEN 1 END) as cmdb_coverage_cio,
    COUNT(CASE WHEN LOWER(edr_coverage) LIKE '%crowdstrike agent%' THEN 1 END) as crowdstrike_coverage_cio,
    ROUND(COUNT(CASE WHEN logging_in_splunk = 'yes' THEN 1 END) * 100.0 / COUNT(*), 2) as splunk_cio_pct,
    ROUND(COUNT(CASE WHEN present_in_cmdb = 'yes' THEN 1 END) * 100.0 / COUNT(*), 2) as cmdb_cio_pct,
    ROUND(COUNT(CASE WHEN LOWER(edr_coverage) LIKE '%crowdstrike agent%' THEN 1 END) * 100.0 / COUNT(*), 2) as crowdstrike_cio_pct
FROM universal_cmdb_copy2
WHERE cio IS NOT NULL 
    AND TRIM(cio) != '' 
    AND cio REGEXP '^[A-Za-z ]+$'
GROUP BY cio
ORDER BY total_hosts_cio DESC;

SELECT 
    TRIM(business_unit) as business_unit_clean,
    COUNT(*) as total_hosts_bu,
    COUNT(CASE WHEN present_in_cmdb = 'yes' THEN 1 END) as cmdb_coverage_bu,
    COUNT(CASE WHEN logging_in_splunk = 'yes' THEN 1 END) as splunk_coverage_bu,
    COUNT(CASE WHEN LOWER(edr_coverage) LIKE '%crowdstrike agent%' THEN 1 END) as crowdstrike_coverage_bu,
    ROUND(COUNT(CASE WHEN present_in_cmdb = 'yes' THEN 1 END) * 100.0 / COUNT(*), 2) as cmdb_bu_pct,
    ROUND(COUNT(CASE WHEN logging_in_splunk = 'yes' THEN 1 END) * 100.0 / COUNT(*), 2) as splunk_bu_pct,
    ROUND(COUNT(CASE WHEN LOWER(edr_coverage) LIKE '%crowdstrike agent%' THEN 1 END) * 100.0 / COUNT(*), 2) as crowdstrike_bu_pct
FROM universal_cmdb_copy2
WHERE business_unit IS NOT NULL AND TRIM(business_unit) != ''
GROUP BY TRIM(business_unit)
ORDER BY total_hosts_bu DESC;

SELECT 
    TRIM(system_classification) as system_class_clean,
    COUNT(*) as total_hosts_class,
    COUNT(CASE WHEN present_in_cmdb = 'yes' THEN 1 END) as cmdb_coverage_class,
    COUNT(CASE WHEN logging_in_splunk = 'yes' THEN 1 END) as splunk_coverage_class,
    COUNT(CASE WHEN LOWER(edr_coverage) LIKE '%crowdstrike agent%' THEN 1 END) as crowdstrike_coverage_class,
    ROUND(COUNT(CASE WHEN present_in_cmdb = 'yes' THEN 1 END) * 100.0 / COUNT(*), 2) as cmdb_class_pct,
    ROUND(COUNT(CASE WHEN logging_in_splunk = 'yes' THEN 1 END) * 100.0 / COUNT(*), 2) as splunk_class_pct,
    ROUND(COUNT(CASE WHEN LOWER(edr_coverage) LIKE '%crowdstrike agent%' THEN 1 END) * 100.0 / COUNT(*), 2) as crowdstrike_class_pct
FROM universal_cmdb_copy2
WHERE system_classification IS NOT NULL AND TRIM(system_classification) != ''
GROUP BY TRIM(system_classification)
ORDER BY total_hosts_class DESC;