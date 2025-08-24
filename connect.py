import json
import duckdb
import os
import re
import time
import threading
from google.cloud import bigquery
from google.oauth2 import service_account
from typing import Dict, List, Set, Tuple
import logging
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)

class KeepAliveManager:
    def __init__(self):
        self.running = True
        self.thread = None
        self.start_time = time.time()
        
    def start(self):
        """Start the keep-alive thread"""
        if self.thread is None or not self.thread.is_alive():
            self.running = True
            self.thread = threading.Thread(target=self._keep_alive_loop, daemon=True)
            self.thread.start()
            print("🤍 Keep-alive system activated - preventing computer sleep ☁️")
    
    def _keep_alive_loop(self):
        """Keep the system active with periodic updates"""
        emoji_cycle = ["🤍", "🦢", "🎧", "☁️", "🪞", "‧₊˚🖇️✩", "₊˚🎧⊹", "♡", "༘˚⋆𐙚｡⋆", "𖦹.✧˚", "🤍ྀི"]
        emoji_index = 0
        
        while self.running:
            elapsed = time.time() - self.start_time
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            
            current_emoji = emoji_cycle[emoji_index % len(emoji_cycle)]
            print(f"{current_emoji} System active - Runtime: {hours:02d}:{minutes:02d}:{seconds:02d} ☁️")
            
            # Prevent system sleep by creating tiny file activity
            try:
                with open('.keep_alive_marker', 'w') as f:
                    f.write(f"active_{int(time.time())}")
            except:
                pass
            
            emoji_index += 1
            time.sleep(30)  # Update every 30 seconds
    
    def stop(self):
        """Stop the keep-alive system"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
        
        # Clean up marker file
        try:
            if os.path.exists('.keep_alive_marker'):
                os.remove('.keep_alive_marker')
        except:
            pass
        
        elapsed = time.time() - self.start_time
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        print(f"🦢 Keep-alive system deactivated - Total runtime: {hours:02d}:{minutes:02d} 🤍")

class HostDataProcessor:
    def __init__(self, json_file_path: str, duckdb_path: str = "universal_cmdb.db"):
        self.json_file_path = json_file_path
        self.duckdb_path = duckdb_path
        self.keep_alive = KeepAliveManager()
        self.table_row_counts = {}
        
        self.column_mapping = {
            'fqdn': 'fqdn',
            'domain': 'domain',
            'host': 'hostname',
            'hostname': 'hostname',
            'infrastructure_type': 'infrastructure_type',
            'infra_type': 'infrastructure_type',
            'region': 'region',
            'country': 'country',
            'data_center': 'data_center',
            'cloud_region': 'cloud_region',
            'ip_address': 'ip_address',
            'class': 'class',
            'system_classification': 'system_classification',
            'business_unit': 'business_unit',
            'apm': 'apm',
            'cio': 'cio',
            'edr_coverage': 'edr_coverage',
            'tanium_coverage': 'tanium_coverage',
            'dlp_agent_coverage': 'dlp_agent_coverage',
            'logging_in_splunk': 'logging_in_splunk',
            'logging_in_gso': 'logging_in_gso'
        }
        
        self.hostname_patterns = ['host', 'hostname', 'fqdn', 'server_name', 'node_name', 'device_name', 
                                 'endpoint_name', 'splunk_host', 'app_host', 'computer_name']
        
        self.attribute_patterns = {
            'business_unit': ['business_unit', 'bu', 'business', 'department', 'division', 'org_unit', 'cost_center'],
            'region': ['region', 'location', 'site', 'area', 'zone', 'geographic', 'geo_region'],
            'country': ['country', 'nation', 'country_code'],
            'infrastructure_type': ['infrastructure_type', 'infra_type', 'server_type', 'platform', 'environment', 'env'],
            'data_center': ['datacenter', 'data_center', 'dc', 'facility', 'center'],
            'cloud_region': ['cloud_region', 'aws_region', 'azure_region', 'gcp_region'],
            'ip_address': ['ip_address', 'ip', 'ipv4', 'host_ip', 'server_ip'],
            'class': ['class', 'classification', 'tier', 'level', 'grade'],
            'system_classification': ['system_classification', 'security_classification', 'sensitivity'],
            'apm': ['apm', 'monitoring', 'application_monitoring'],
            'cio': ['cio', 'owner', 'responsible', 'contact', 'admin', 'administrator'],
            'edr_coverage': ['edr_coverage', 'edr', 'endpoint_detection', 'security_agent', 'antivirus'],
            'tanium_coverage': ['tanium_coverage', 'tanium', 'tanium_agent'],
            'dlp_agent_coverage': ['dlp_agent_coverage', 'dlp', 'data_loss_prevention'],
            'logging_in_splunk': ['logging_in_splunk', 'splunk', 'splunk_logging'],
            'logging_in_gso': ['logging_in_gso', 'gso', 'gso_logging'],
            'domain': ['domain', 'dns_domain', 'ad_domain'],
            'fqdn': ['fqdn', 'full_name', 'qualified_name']
        }
        
        service_account_file = os.getenv('GCP_SERVICE_ACCOUNT_FILE', 'gcp/gcp_prod_key.json')
        
        if os.path.exists(service_account_file):
            credentials = service_account.Credentials.from_service_account_file(service_account_file)
            self.bq_client = bigquery.Client(project="chronicle-fisv", credentials=credentials)
        else:
            self.bq_client = bigquery.Client(project="chronicle-fisv")
        
        self.duck_conn = duckdb.connect(duckdb_path)
        
        self._create_table()
        
    def _create_table(self):
        sql = """
        CREATE TABLE IF NOT EXISTS universal_cmdb (
            normalized_host VARCHAR PRIMARY KEY,
            source_tables TEXT,
            hostname TEXT,
            fqdn TEXT,
            domain TEXT,
            infrastructure_type TEXT,
            region TEXT,
            country TEXT,
            data_center TEXT,
            cloud_region TEXT,
            ip_address TEXT,
            class TEXT,
            system_classification TEXT,
            business_unit TEXT,
            apm TEXT,
            cio TEXT,
            edr_coverage TEXT,
            tanium_coverage TEXT,
            dlp_agent_coverage TEXT,
            logging_in_splunk TEXT,
            logging_in_gso TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.duck_conn.execute(sql)
        
        try:
            self.duck_conn.execute("CREATE INDEX IF NOT EXISTS idx_normalized_host ON universal_cmdb(normalized_host)")
        except:
            pass
    
    def get_table_row_count(self, table_name: str) -> int:
        """Get the row count for a BigQuery table"""
        try:
            print(f"🪞 Counting rows in {table_name}...")
            count_query = f"SELECT COUNT(*) FROM `{table_name}`"
            query_job = self.bq_client.query(count_query)
            result = query_job.result()
            row_count = next(iter(result))[0]
            self.table_row_counts[table_name] = row_count
            print(f"‧₊˚🖇️✩ Table {table_name}: {row_count:,} rows")
            return row_count
        except Exception as e:
            print(f"𖦹.✧˚ Error counting rows in {table_name}: {e}")
            self.table_row_counts[table_name] = 0
            return 0
            
    def normalize_hostname(self, hostname: str) -> str:
        if not hostname or not isinstance(hostname, str):
            return ""
        
        normalized = hostname.lower().strip()
        
        if '.' in normalized:
            normalized = normalized.split('.')[0]
        
        normalized = normalized.replace('-', '')
        normalized = re.sub(r'[^a-z0-9]', '', normalized)
        
        return normalized
    
    def load_metadata(self) -> Dict:
        print("🤍 Loading metadata configuration...")
        with open(self.json_file_path, 'r') as f:
            return json.load(f)
    
    def identify_columns(self, metadata):
        all_columns = []
        
        print("\n☁️ === COLUMN DISCOVERY ANALYSIS === 🦢")
        
        for table_name, columns in metadata['columns'].items():
            print(f"\n🪞 Analyzing table: {table_name}")
            
            # Get row count for this table
            row_count = self.get_table_row_count(table_name)
            
            for column_name, column_type in columns.items():
                mapped_type = None
                
                # First: exact match on column_type
                if isinstance(column_type, str) and column_type.lower() in self.column_mapping:
                    mapped_type = self.column_mapping[column_type.lower()]
                    print(f"  ♡ EXACT TYPE MATCH: {column_name} ({column_type}) -> {mapped_type}")
                
                # Second: check hostname patterns
                if not mapped_type:
                    column_lower = column_name.lower()
                    for pattern in self.hostname_patterns:
                        if pattern in column_lower:
                            mapped_type = 'hostname'
                            print(f"  ₊˚🎧⊹ HOSTNAME PATTERN: {column_name} -> {mapped_type}")
                            break
                
                # Third: check ALL attribute patterns
                if not mapped_type:
                    column_lower = column_name.lower()
                    for attr_type, patterns in self.attribute_patterns.items():
                        for pattern in patterns:
                            if pattern in column_lower:
                                mapped_type = attr_type
                                print(f"  ‧₊˚🖇️✩ ATTRIBUTE PATTERN: {column_name} -> {mapped_type} (matched '{pattern}')")
                                break
                        if mapped_type:
                            break
                
                # Fourth: check if column_type itself matches attribute patterns
                if not mapped_type and isinstance(column_type, str):
                    type_lower = column_type.lower()
                    for attr_type, patterns in self.attribute_patterns.items():
                        for pattern in patterns:
                            if pattern in type_lower:
                                mapped_type = attr_type
                                print(f"  𖦹.✧˚ TYPE PATTERN: {column_name} ({column_type}) -> {mapped_type} (matched '{pattern}')")
                                break
                        if mapped_type:
                            break
                
                if mapped_type:
                    all_columns.append((table_name, column_name, mapped_type))
                    print(f"  🤍ྀི SUCCESS: {table_name}.{column_name} -> {mapped_type}")
                else:
                    print(f"  ༘˚⋆𐙚｡⋆ NO MATCH: {column_name} ({column_type})")
        
        print(f"\n🦢 === DISCOVERY SUMMARY: Found {len(all_columns)} mappable columns === ☁️")
        return all_columns
    
    def process_table_completely(self, table_name, all_columns_for_table):
        hostname_cols = [c for c in all_columns_for_table if c[2] == 'hostname']
        attribute_cols = [c for c in all_columns_for_table if c[2] != 'hostname']
        
        row_count = self.table_row_counts.get(table_name, 0)
        
        print(f"\n🪞 === PROCESSING TABLE: {table_name} === 🤍")
        print(f"‧₊˚🖇️✩ Total rows in table: {row_count:,}")
        print(f"₊˚🎧⊹ Hostname columns: {len(hostname_cols)}")
        print(f"♡ Attribute columns: {len(attribute_cols)}")
        
        for col in hostname_cols:
            print(f"  🦢 Hostname: {col[1]} -> {col[2]}")
        for col in attribute_cols:
            print(f"  ☁️ Attribute: {col[1]} -> {col[2]}")
        
        if not hostname_cols:
            print(f"  𖦹.✧˚ SKIPPING {table_name} - No hostname columns found")
            return
        
        hostname_col = hostname_cols[0][1]
        
        column_names = [hostname_col] + [c[1] for c in attribute_cols]
        attribute_types = [c[2] for c in attribute_cols]
        
        print(f"  🤍 Query columns: {column_names}")
        print(f"  🪞 Target types: ['hostname'] + {attribute_types}")
        
        query = f"""
        SELECT {', '.join([f'`{col}`' for col in column_names])}
        FROM `{table_name}`
        WHERE `{hostname_col}` IS NOT NULL 
        AND `{hostname_col}` != ''
        AND LENGTH(`{hostname_col}`) > 0
        LIMIT 50000
        """
        
        try:
            print(f"  ‧₊˚🖇️✩ Executing BigQuery for {table_name}...")
            query_job = self.bq_client.query(query)
            results = query_job.result()
            
            records = []
            attribute_data_found = {attr_type: 0 for attr_type in attribute_types}
            
            for row in results:
                if row[0] and isinstance(row[0], str):
                    normalized_host = self.normalize_hostname(row[0])
                    if normalized_host and len(normalized_host) > 2:
                        record = {'normalized_host': normalized_host, 'hostname': row[0]}
                        
                        for i, attr_type in enumerate(attribute_types, 1):
                            if i < len(row) and row[i] and str(row[i]).strip():
                                record[attr_type] = str(row[i]).strip()
                                attribute_data_found[attr_type] += 1
                        
                        records.append(record)
            
            print(f"  ₊˚🎧⊹ Data extraction results:")
            print(f"    🤍ྀི Total records extracted: {len(records)}")
            for attr_type, count in attribute_data_found.items():
                print(f"    ♡ {attr_type}: {count} non-empty values")
            
            records_written = 0
            for record in records:
                self._insert_or_update_host(record, table_name)
                records_written += 1
                
            print(f"  🦢 Successfully processed {records_written} records from {table_name}")
            
            # VERIFICATION: Check if data actually made it to the database
            print(f"  ☁️ VERIFICATION - Checking database storage...")
            for attr_type in attribute_types:
                count_query = f"SELECT COUNT(*) FROM universal_cmdb WHERE {attr_type} IS NOT NULL AND {attr_type} != ''"
                db_count = self.duck_conn.execute(count_query).fetchone()[0]
                print(f"    🪞 {attr_type}: {db_count} records in database")
            
        except Exception as e:
            print(f"  𖦹.✧˚ Error processing {table_name}: {e}")
            import traceback
            traceback.print_exc()
    
    def _insert_or_update_host(self, record, table_name):
        normalized_host = record['normalized_host']
        
        existing_query = "SELECT * FROM universal_cmdb WHERE normalized_host = ?"
        existing = self.duck_conn.execute(existing_query, [normalized_host]).fetchone()
        
        if existing:
            columns_query = "PRAGMA table_info(universal_cmdb)"
            column_info = self.duck_conn.execute(columns_query).fetchall()
            column_names = [col[1] for col in column_info]
            
            updates = []
            values = []
            
            current_tables = existing[1] if existing[1] else ""
            if table_name not in current_tables:
                new_tables = f"{current_tables}, {table_name}" if current_tables else table_name
                updates.append("source_tables = ?")
                values.append(new_tables)
            
            for key, new_value in record.items():
                if key != 'normalized_host' and new_value and key in column_names:
                    col_index = column_names.index(key)
                    existing_value = existing[col_index] if col_index < len(existing) else None
                    
                    if existing_value and existing_value.strip():
                        existing_values = set(v.strip() for v in existing_value.split(' | '))
                        new_values = existing_values.copy()
                        new_values.add(new_value.strip())
                        
                        if len(new_values) > 1:
                            final_value = ' | '.join(sorted(new_values))
                        else:
                            final_value = new_value.strip()
                    else:
                        final_value = new_value.strip()
                    
                    updates.append(f"{key} = ?")
                    values.append(final_value)
            
            if updates:
                values.append(normalized_host)
                update_sql = f"UPDATE universal_cmdb SET {', '.join(updates)}, last_updated = CURRENT_TIMESTAMP WHERE normalized_host = ?"
                self.duck_conn.execute(update_sql, values)
        else:
            columns = ['normalized_host', 'source_tables'] + [k for k in record.keys() if k != 'normalized_host']
            values = [normalized_host, table_name] + [record.get(k) for k in columns[2:]]
            placeholders = ', '.join(['?'] * len(columns))
            
            insert_sql = f"INSERT INTO universal_cmdb ({', '.join(columns)}) VALUES ({placeholders})"
            self.duck_conn.execute(insert_sql, values)
    
    def process_all(self):
        print("🤍 === STARTING HOST DATA PROCESSING === 🦢")
        
        # Start keep-alive system
        self.keep_alive.start()
        
        try:
            metadata = self.load_metadata()
            all_columns = self.identify_columns(metadata)
            
            columns_by_table = defaultdict(list)
            for table_name, column_name, mapped_type in all_columns:
                columns_by_table[table_name].append((table_name, column_name, mapped_type))
            
            print(f"\n☁️ Processing {len(columns_by_table)} tables...")
            
            for i, (table_name, table_columns) in enumerate(columns_by_table.items(), 1):
                print(f"\n🪞 Progress: {i}/{len(columns_by_table)} tables")
                self.process_table_completely(table_name, table_columns)
            
            self._create_summary()
            self._show_results()
            
        except Exception as e:
            print(f"𖦹.✧˚ Error during processing: {e}")
            raise
        finally:
            # Stop keep-alive system
            self.keep_alive.stop()
    
    def _create_summary(self):
        try:
            print("‧₊˚🖇️✩ Creating summary table...")
            self.duck_conn.execute("DROP TABLE IF EXISTS all_sources")
            
            create_sql = """
            CREATE TABLE all_sources AS (
                SELECT 
                    normalized_host as host,
                    source_tables,
                    hostname, fqdn, domain, infrastructure_type, region, country,
                    data_center, cloud_region, ip_address, class, system_classification,
                    business_unit, apm, cio, edr_coverage, tanium_coverage, 
                    dlp_agent_coverage, logging_in_splunk, logging_in_gso,
                    LENGTH(source_tables) - LENGTH(REPLACE(source_tables, ',', '')) + 1 as source_count,
                    last_updated
                FROM universal_cmdb
                WHERE normalized_host IS NOT NULL 
                ORDER BY source_count DESC, normalized_host
            )
            """
            self.duck_conn.execute(create_sql)
            print("₊˚🎧⊹ Summary table created successfully")
        except Exception as e:
            print(f"𖦹.✧˚ Error creating summary: {e}")
    
    def _show_results(self):
        total = self.duck_conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
        print(f"\n🤍ྀི Total hosts in database: {total:,}")
        
        # Show table processing summary
        print(f"\n♡ === TABLE PROCESSING SUMMARY === 🦢")
        total_source_rows = sum(self.table_row_counts.values())
        print(f"☁️ Total source table rows processed: {total_source_rows:,}")
        
        for table_name, row_count in self.table_row_counts.items():
            print(f"  🪞 {table_name}: {row_count:,} rows")
        
        columns = ['hostname', 'fqdn', 'domain', 'infrastructure_type', 'region', 'country',
                  'data_center', 'cloud_region', 'ip_address', 'class', 'system_classification',
                  'business_unit', 'apm', 'cio', 'edr_coverage', 'tanium_coverage', 
                  'dlp_agent_coverage', 'logging_in_splunk', 'logging_in_gso']
        
        print("\n‧₊˚🖇️✩ === COLUMN VERIFICATION === ₊˚🎧⊹")
        populated_columns = []
        empty_columns = []
        
        for col in columns:
            count = self.duck_conn.execute(f"SELECT COUNT(*) FROM universal_cmdb WHERE {col} IS NOT NULL AND {col} != ''").fetchone()[0]
            pct = (count / total * 100) if total > 0 else 0
            
            if count > 0:
                populated_columns.append(col)
                print(f"🤍ྀི DATA FOUND: {col} has {count:,} records ({pct:.1f}%)")
                
                # Show sample values
                sample_query = f"SELECT DISTINCT {col} FROM universal_cmdb WHERE {col} IS NOT NULL AND {col} != '' LIMIT 3"
                samples = self.duck_conn.execute(sample_query).fetchall()
                sample_values = [str(s[0])[:30] for s in samples]
                print(f"   ♡ Sample values: {', '.join(sample_values)}")
            else:
                empty_columns.append(col)
                print(f"༘˚⋆𐙚｡⋆ EMPTY: {col} has no data")
        
        print(f"\n🦢 === VERIFICATION SUMMARY === ☁️")
        print(f"   🤍 Columns with data: {len(populated_columns)}")
        print(f"   🪞 Empty columns: {len(empty_columns)}")
        
        if populated_columns:
            print(f"   ‧₊˚🖇️✩ SUCCESS: Data verified in: {', '.join(populated_columns)}")
        
        if empty_columns:
            print(f"   𖦹.✧˚ WARNING: No data found in: {', '.join(empty_columns)}")
        
        print("\n₊˚🎧⊹ Sample complete records:")
        sample_query = """
        SELECT * FROM universal_cmdb 
        WHERE normalized_host IS NOT NULL
        ORDER BY (
            CASE WHEN hostname IS NOT NULL AND hostname != '' THEN 1 ELSE 0 END +
            CASE WHEN business_unit IS NOT NULL AND business_unit != '' THEN 1 ELSE 0 END +
            CASE WHEN region IS NOT NULL AND region != '' THEN 1 ELSE 0 END +
            CASE WHEN infrastructure_type IS NOT NULL AND infrastructure_type != '' THEN 1 ELSE 0 END
        ) DESC
        LIMIT 3
        """
        samples = self.duck_conn.execute(sample_query).fetchall()
        
        column_names = ['normalized_host', 'source_tables'] + columns + ['last_updated', 'created_at']
        
        for i, sample in enumerate(samples, 1):
            print(f"\n♡ Record {i}: {sample[0]}")
            fields_with_data = 0
            for j, col_name in enumerate(column_names[1:], 1):
                if j < len(sample) and sample[j] and str(sample[j]).strip() and col_name not in ['last_updated', 'created_at']:
                    print(f"  🤍ྀི {col_name}: {str(sample[j])[:50]}")
                    fields_with_data += 1
            print(f"  🦢 Total fields populated: {fields_with_data}")
    
    def export(self, filename="universal_cmdb_export.csv"):
        print(f"☁️ Exporting data to {filename}...")
        self.duck_conn.execute(f"COPY (SELECT * FROM universal_cmdb ORDER BY normalized_host) TO '{filename}' WITH (FORMAT CSV, HEADER)")
        
        # Get file size for confirmation
        try:
            file_size = os.path.getsize(filename)
            file_size_mb = file_size / (1024 * 1024)
            print(f"🪞 Export completed: {filename} ({file_size_mb:.2f} MB)")
        except:
            print(f"🤍 Export completed: {filename}")
    
    def close(self):
        print("‧₊˚🖇️✩ Closing database connections...")
        self.keep_alive.stop()
        self.duck_conn.close()
        print("₊˚🎧⊹ Database connections closed")

if __name__ == "__main__":
    print("🤍 === HOST DATA PROCESSOR STARTING === 🦢")
    processor = HostDataProcessor("reviewed_labeled_columns.json", "universal_cmdb.db")
    
    try:
        processor.process_all()
        processor.export()
        print("\n♡ === PROCESSING COMPLETE === 🤍ྀི")
        print("☁️ All data has been successfully processed and exported! 🦢")
    except KeyboardInterrupt:
        print("\n𖦹.✧˚ Process interrupted by user")
    except Exception as e:
        print(f"༘˚⋆𐙚｡⋆ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        processor.close()
        print("🪞 Session ended gracefully ♡")