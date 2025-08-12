#!/bin/bash
set -euo pipefail

PROJECT_ID=${1:-""}
if [ -z "$PROJECT_ID" ]; then
    echo "Usage: $0 <project-id>"
    exit 1
fi

DB_PATH="unlimited_${PROJECT_ID}_cmdb.db"

if [ ! -f "$DB_PATH" ]; then
    echo "Database not found: $DB_PATH"
    echo "Run unlimited discovery first"
    exit 1
fi

echo "Unlimited Asset Analysis for $PROJECT_ID"
echo "======================================="

python3 -c "
import duckdb
conn = duckdb.connect('$DB_PATH')

print('Total Assets:')
result = conn.execute('SELECT COUNT(*) FROM unlimited_assets').fetchone()
print(f'  {result[0]:,} assets discovered')

print('\nQuality Metrics:')
result = conn.execute('SELECT AVG(confidence_score), AVG(completeness_score) FROM unlimited_assets').fetchone()
print(f'  Average confidence: {result[0]:.3f}')
print(f'  Average completeness: {result[1]:.3f}')

print('\nField Population:')
for field in ['operating_system', 'environment', 'business_unit', 'owner', 'criticality']:
    result = conn.execute(f\"SELECT COUNT(*) FROM unlimited_assets WHERE {field} != ''\").fetchone()
    total = conn.execute('SELECT COUNT(*) FROM unlimited_assets').fetchone()[0]
    pct = (result[0] / total * 100) if total > 0 else 0
    print(f'  {field}: {result[0]:,} ({pct:.1f}%)')

print('\nTop Quality Assets:')
results = conn.execute('SELECT hostname, confidence_score, completeness_score FROM unlimited_assets ORDER BY confidence_score DESC LIMIT 10').fetchall()
for row in results:
    print(f'  {row[0]} - Confidence: {row[1]:.3f}, Completeness: {row[2]:.3f}')
"

echo ""
echo "Database location: $DB_PATH"