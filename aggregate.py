– Dataiku SQL Recipe
– Input datasets: lcd_in_scope, Risk_B_Output_2_prepared
– Output dataset: in_scope_vs_archive_inventory

SELECT
lcd.IDN_EON,
CASE
WHEN risk.IDN_EON IS NOT NULL THEN ‘YES’
ELSE ‘NO’
END AS PRESENT_IN_ARCHIVE_INVENTORY,
lcd.*
FROM lcd_in_scope lcd
LEFT JOIN (
SELECT DISTINCT IDN_EON
FROM Risk_B_Output_2_prepared
WHERE IDN_EON IS NOT NULL
) risk
ON lcd.IDN_EON = risk.IDN_EON