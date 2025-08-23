import json
import duckdb
import os
import re
from google.cloud import bigquery
from google.oauth2 import service_account
from typing import Dict, List, Set, Tuple, Optional
import logging
from datetime import datetime
from collections import defaultdict

# Set up pretty logging
class ColorFormatter(logging.Formatter):
    """Custom formatter to add colors to log levels"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    def format(self, record):
        # Add color to level name
        level_color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{level_color}{self.BOLD}{record.levelname:8}{self.RESET}"
        
        # Format the message
        formatted = super().format(record)
        return formatted

# Configure pretty logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)

# Create and set the color formatter
console_handler = logging.StreamHandler()
console_handler.setFormatter(ColorFormatter())
logger = logging.getLogger(__name__)
logger.handlers.clear()
logger.addHandler(console_handler)
logger.setLevel(logging.INFO)

def print_banner(title: str, width: int = 80):
    """Print a pretty banner"""
    print("\n" + "=" * width)
    print(f"{title:^{width}}")
    print("=" * width)

def print_section(title: str, width: int = 60):
    """Print a section header"""
    print(f"\n{'-' * width}")
    print(f"📋 {title}")
    print(f"{'-' * width}")

def print_progress(current: int, total: int, item: str = ""):
    """Print progress indicator"""
    percentage = (current / total * 100) if total > 0 else 0
    bar_length = 30
    filled_length = int(bar_length * current / total) if total > 0 else 0
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    print(f"\r🔄 Progress: [{bar}] {percentage:5.1f}% ({current}/{total}) {item}", end='', flush=True)

class HostDataProcessor:
    def __init__(self, json_file_path: str, duckdb_path: str = "universal_cmdb.db"):
        """Initialize the processor with BigQuery and DuckDB connections"""
        print_banner("🚀 UNIVERSAL CMDB PROCESSOR INITIALIZATION")
        
        self.json_file_path = json_file_path
        self.duckdb_path = duckdb_path
        
        # Define column name patterns that indicate specific data types
        self.column_patterns = {
            'hostname': [
                'host', 'hostname', 'fqdn', 'server_name', 'node_name', 'device_name', 
                'endpoint_name', 'splunk_host', 'app_host', 'chronicle_device_hostname',
                'device_hostname', 'endpointdomain_name', 'computer_name', 'machine_name'
            ],
            'fqdn': ['fqdn', 'full_name', 'qualified_name', 'dns_name'],
            'domain': ['domain', 'dns_domain', 'ad_domain'],
            'infrastructure_type': [
                'infrastructure_type', 'infra_type', 'server_type', 'system_type',
                'platform', 'environment', 'env_type', 'deployment_type'
            ],
            'region': [
                'region', 'location', 'site', 'datacenter_region', 'aws_region',
                'azure_region', 'gcp_region', 'geographic_region'
            ],
            'country': ['country', 'nation', 'country_code', 'geo_country'],
            'data_center': [
                'datacenter', 'data_center', 'dc', 'facility', 'site_name',
                'datacenter_name', 'center'
            ],
            'cloud_region': [
                'cloud_region', 'aws_region', 'azure_region', 'gcp_region',
                'cloud_location', 'cloud_zone'
            ],
            'ip_address': [
                'ip_address', 'ip', 'ipv4', 'ipv6', 'host_ip', 'server_ip',
                'endpoint_ip', 'device_ip', 'internal_ip', 'external_ip'
            ],
            'class': [
                'class', 'classification', 'tier', 'level', 'grade', 'category'
            ],
            'system_classification': [
                'system_classification', 'security_classification', 'data_classification',
                'classification_level', 'sensitivity'
            ],
            'business_unit': [
                'business_unit', 'bu', 'department', 'division', 'org_unit',
                'organizational_unit', 'cost_center', 'business_group'
            ],
            'apm': [
                'apm', 'monitoring', 'application_monitoring', 'performance_monitoring'
            ],
            'cio': [
                'cio', 'owner', 'responsible', 'contact', 'admin', 'administrator'
            ],
            'edr_coverage': [
                'edr_coverage', 'edr', 'endpoint_detection', 'security_agent',
                'antivirus', 'av_coverage'
            ],
            'tanium_coverage': [
                'tanium_coverage', 'tanium', 'tanium_agent', 'endpoint_management'
            ],
            'dlp_agent_coverage': [
                'dlp_agent_coverage', 'dlp', 'data_loss_prevention', 'dlp_agent'
            ],
            'logging_in_splunk': [
                'logging_in_splunk', 'splunk', 'splunk_logging', 'log_forwarding'
            ],
            'logging_in_gso': [
                'logging_in_gso', 'gso', 'gso_logging', 'security_logging'
            ]
        }
        
        # Initialize connections
        logger.info("🔌 Initializing BigQuery connection...")
        self.bq_client = self._initialize_bigquery_client()
        
        logger.info("🗄️  Initializing DuckDB connection...")
        self.duck_conn = duckdb.connect(duckdb_path)
        
        # Storage for all discovered data
        self.all_host_data = defaultdict(lambda: defaultdict(set))  # {normalized_host: {column_type: {values}}}
        self.table_host_mapping = defaultdict(set)  # {table_name: {normalized_hosts}}
        
        # Initialize database
        self._setup_database()
        
        print("✅ Initialization complete!")
    
    def _initialize_bigquery_client(self):
        """Initialize BigQuery client"""
        try:
            service_account_file = os.getenv('GCP_SERVICE_ACCOUNT_FILE', 'gcp/gcp_prod_key.json')
            
            if os.path.exists(service_account_file):
                credentials = service_account.Credentials.from_service_account_file(service_account_file)
                client = bigquery.Client(project="chronicle-fisv", credentials=credentials)
                logger.info("✅ Connected to BigQuery with service account")
            else:
                client = bigquery.Client(project="chronicle-fisv")
                logger.info("✅ Connected to BigQuery with default credentials")
            
            return client
        except Exception as e:
            logger.error(f"❌ Failed to initialize BigQuery client: {e}")
            raise
    
    def _setup_database(self):
        """Setup the database with all possible columns"""
        print_section("DATABASE SETUP")
        
        # Create base table with mandatory columns
        logger.info("🏗️  Creating base table structure...")
        self._create_base_table()
        
        # Add ALL possible columns from our patterns
        logger.info("📊 Adding all possible data columns...")
        self._ensure_all_columns_exist()
        
        # Show final table structure
        self._show_table_structure()
    
    def _create_base_table(self):
        """Create the base table with mandatory columns"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS universal_cmdb (
            normalized_host VARCHAR PRIMARY KEY,
            source_tables TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.duck_conn.execute(create_table_sql)
        
        # Create primary index
        try:
            self.duck_conn.execute("CREATE INDEX IF NOT EXISTS idx_normalized_host ON universal_cmdb(normalized_host)")
        except:
            pass
        
        logger.info("✅ Base table created")
    
    def _ensure_all_columns_exist(self):
        """Ensure ALL possible columns from our patterns exist in the table"""
        # Get all unique column types from our patterns
        all_column_types = set(self.column_patterns.keys())
        
        logger.info(f"📋 Ensuring {len(all_column_types)} columns exist...")
        
        columns_added = 0
        for column_type in sorted(all_column_types):
            if self._add_column_if_not_exists(column_type):
                columns_added += 1
        
        if columns_added > 0:
            logger.info(f"✅ Added {columns_added} new columns")
        else:
            logger.info("✅ All columns already exist")
    
    def _add_column_if_not_exists(self, column_name: str) -> bool:
        """Add a column if it doesn't exist. Returns True if column was added."""
        if not column_name or column_name in ['normalized_host', 'source_tables', 'last_updated', 'created_at']:
            return False
        
        try:
            # Check if column exists
            columns_query = "PRAGMA table_info(universal_cmdb)"
            existing_columns = {col[1] for col in self.duck_conn.execute(columns_query).fetchall()}
            
            if column_name not in existing_columns:
                # Add the column
                alter_sql = f"ALTER TABLE universal_cmdb ADD COLUMN {column_name} TEXT"
                self.duck_conn.execute(alter_sql)
                
                # Create index
                try:
                    self.duck_conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{column_name} ON universal_cmdb({column_name})")
                except:
                    pass
                
                logger.info(f"  ➕ Added column: {column_name}")
                return True
            
            return False
        except Exception as e:
            logger.error(f"❌ Error adding column {column_name}: {e}")
            return False
    
    def _show_table_structure(self):
        """Display the current table structure"""
        columns_query = "PRAGMA table_info(universal_cmdb)"
        columns_info = self.duck_conn.execute(columns_query).fetchall()
        
        print_section("FINAL TABLE STRUCTURE")
        print("📊 Table: universal_cmdb")
        print("┌─────────────────────────────────┬──────────┬─────────┐")
        print("│ Column Name                     │ Type     │ Key     │")
        print("├─────────────────────────────────┼──────────┼─────────┤")
        
        for col in columns_info:
            name = col[1][:31]  # Truncate long names
            col_type = col[2][:8]
            is_pk = "PRIMARY" if col[5] else ""
            print(f"│ {name:<31} │ {col_type:<8} │ {is_pk:<7} │")
        
        print("└─────────────────────────────────┴──────────┴─────────┘")
        print(f"📈 Total columns: {len(columns_info)}")
    
    def load_metadata(self) -> Dict:
        """Load and parse the JSON metadata file"""
        try:
            with open(self.json_file_path, 'r') as f:
                metadata = json.load(f)
            logger.info(f"📖 Loaded metadata from {self.json_file_path}")
            return metadata
        except Exception as e:
            logger.error(f"❌ Error loading metadata: {e}")
            raise
    
    def normalize_hostname(self, hostname: str) -> str:
        """Normalize hostname according to requirements"""
        if not hostname or not isinstance(hostname, str):
            return ""
        
        # Convert to lowercase and strip
        normalized = hostname.lower().strip()
        
        # Remove anything after the first dot
        if '.' in normalized:
            normalized = normalized.split('.')[0]
        
        # Remove dashes
        normalized = normalized.replace('-', '')
        
        # Remove any remaining special characters except alphanumeric
        normalized = re.sub(r'[^a-z0-9]', '', normalized)
        
        return normalized
    
    def analyze_all_columns(self, metadata: Dict):
        """Analyze ALL columns in metadata and classify them by patterns"""
        print_section("AGGRESSIVE COLUMN ANALYSIS")
        
        if 'columns' not in metadata:
            logger.error("❌ No 'columns' key found in metadata")
            return []
        
        all_columns_to_process = []
        pattern_matches = defaultdict(list)
        unmatched_columns = []
        
        # Examine EVERY column in EVERY table
        for table_name, columns in metadata['columns'].items():
            logger.info(f"🔍 Analyzing table: {table_name}")
            
            for column_name, column_type in columns.items():
                # First, try to match by the column_type value if it's useful
                matched_type = None
                if isinstance(column_type, str):
                    for pattern_type, patterns in self.column_patterns.items():
                        if column_type.lower() in [p.lower() for p in patterns]:
                            matched_type = pattern_type
                            break
                
                # If no type match, try to match by column name
                if not matched_type:
                    column_lower = column_name.lower()
                    for pattern_type, patterns in self.column_patterns.items():
                        if any(pattern in column_lower for pattern in patterns):
                            matched_type = pattern_type
                            break
                
                if matched_type:
                    all_columns_to_process.append((table_name, column_name, column_type, matched_type))
                    pattern_matches[matched_type].append(f"{table_name}.{column_name}")
                    logger.info(f"  ✅ {column_name} (type: {column_type}) → {matched_type}")
                else:
                    unmatched_columns.append((table_name, column_name, column_type))
                    logger.debug(f"  ❓ {column_name} (type: {column_type}) → unmatched")
        
        # Show comprehensive analysis results
        print("\n📊 COLUMN ANALYSIS RESULTS:")
        print(f"  📋 Total columns found: {sum(len(columns) for columns in metadata['columns'].values())}")
        print(f"  ✅ Matched columns: {len(all_columns_to_process)}")
        print(f"  ❌ Unmatched columns: {len(unmatched_columns)}")
        
        print(f"\n🎯 MATCHES BY DATA TYPE:")
        for pattern_type in sorted(pattern_matches.keys()):
            columns = pattern_matches[pattern_type]
            print(f"  • {pattern_type}: {len(columns)} columns")
            for col in columns[:3]:  # Show first 3 examples
                print(f"    - {col}")
            if len(columns) > 3:
                print(f"    - ... and {len(columns) - 3} more")
        
        if unmatched_columns:
            print(f"\n❓ UNMATCHED COLUMNS (first 10):")
            for table, col, ctype in unmatched_columns[:10]:
                print(f"  • {table}.{col} (type: {ctype})")
            if len(unmatched_columns) > 10:
                print(f"  • ... and {len(unmatched_columns) - 10} more unmatched")
        
        return all_columns_to_process
    
    def collect_all_data_aggressively(self, columns_to_process):
        """PHASE 1: Aggressively collect ALL data from BigQuery"""
        print_section("PHASE 1: AGGRESSIVE DATA COLLECTION")
        
        logger.info("🗂️  Collecting ALL data from BigQuery...")
        
        # First pass: collect all hostname data to establish hosts
        hostname_columns = [(t, c, ct, nt) for t, c, ct, nt in columns_to_process if nt == 'hostname']
        
        logger.info(f"🏠 Processing {len(hostname_columns)} hostname columns...")
        for i, (table_name, column_name, orig_type, norm_type) in enumerate(hostname_columns, 1):
            print_progress(i, len(hostname_columns), f"{table_name}.{column_name}")
            
            # Get all hostnames from this column
            hostnames = self._fetch_column_data(table_name, column_name)
            for hostname in hostnames:
                normalized_host = self.normalize_hostname(hostname)
                if normalized_host and len(normalized_host) > 2:
                    self.all_host_data[normalized_host]['source_tables'].add(table_name)
                    self.all_host_data[normalized_host][norm_type].add(hostname)
                    self.table_host_mapping[table_name].add(normalized_host)
        
        print(f"\n✅ Discovered {len(self.all_host_data)} unique hosts from hostname columns")
        
        # Second pass: collect all attribute data
        attribute_columns = [(t, c, ct, nt) for t, c, ct, nt in columns_to_process if nt != 'hostname']
        
        logger.info(f"📝 Processing {len(attribute_columns)} attribute columns...")
        attribute_data_collected = defaultdict(lambda: defaultdict(set))  # {table: {attr_type: {values}}}
        
        for i, (table_name, column_name, orig_type, norm_type) in enumerate(attribute_columns, 1):
            print_progress(i, len(attribute_columns), f"{table_name}.{column_name}")
            
            # Get all values from this column
            values = self._fetch_column_data(table_name, column_name)
            for value in values:
                if value and value.strip():
                    attribute_data_collected[table_name][norm_type].add(value.strip())
        
        print(f"\n✅ Collected attribute data from {len(attribute_columns)} columns")
        
        # Third pass: apply attribute data to hosts
        logger.info("🔗 Linking attribute data to hosts...")
        
        total_links = 0
        for table_name, attr_data in attribute_data_collected.items():
            # If this table has hosts, apply all attributes to those hosts
            if table_name in self.table_host_mapping:
                hosts_in_table = self.table_host_mapping[table_name]
                for attr_type, values in attr_data.items():
                    # Use the most common/longest value for this attribute
                    if values:
                        best_value = max(values, key=lambda x: (values.count if hasattr(values, 'count') else 1, len(x)))
                        for host in hosts_in_table:
                            self.all_host_data[host][attr_type].add(best_value)
                            total_links += 1
            else:
                # Table has no direct hosts, apply to ALL hosts (global attributes)
                for attr_type, values in attr_data.items():
                    if values and len(values) <= 10:  # Only if few unique values (likely global)
                        best_value = max(values, key=len)  # Take longest value
                        for host in list(self.all_host_data.keys()):
                            if not self.all_host_data[host][attr_type]:  # Only if not already set
                                self.all_host_data[host][attr_type].add(best_value)
                                total_links += 1
        
        logger.info(f"✅ Created {total_links:,} attribute links")
        
        # Show final collection results
        print("\n📊 FINAL COLLECTION RESULTS:")
        print(f"  🏠 Total unique hosts: {len(self.all_host_data):,}")
        print(f"  📋 Tables with hosts: {len(self.table_host_mapping)}")
        
        # Show attribute population
        attribute_counts = defaultdict(int)
        for host_data in self.all_host_data.values():
            for attr_type, values in host_data.items():
                if values and attr_type != 'source_tables':
                    attribute_counts[attr_type] += 1
        
        print(f"  🎯 Attribute population:")
        for attr_type in sorted(attribute_counts.keys()):
            count = attribute_counts[attr_type]
            percentage = (count / len(self.all_host_data) * 100) if self.all_host_data else 0
            print(f"     • {attr_type}: {count:,} hosts ({percentage:.1f}%)")
    
    def _fetch_column_data(self, table_name: str, column_name: str) -> List[str]:
        """Fetch all distinct values from a column"""
        query = f"""
        SELECT DISTINCT `{column_name}` as value
        FROM `{table_name}`
        WHERE `{column_name}` IS NOT NULL 
        AND `{column_name}` != ''
        AND `{column_name}` != 'null'
        AND `{column_name}` != 'NULL'
        AND LENGTH(`{column_name}`) > 0
        LIMIT 100000
        """
        
        try:
            query_job = self.bq_client.query(query)
            results = query_job.result()
            return [row.value for row in results if row.value and isinstance(row.value, str)]
        except Exception as e:
            logger.error(f"❌ Error fetching {table_name}.{column_name}: {e}")
            return []
    
    def write_all_to_database(self):
        """PHASE 2: Write everything to database"""
        print_section("PHASE 2: DATABASE POPULATION")
        
        logger.info("💾 Writing all collected data to database...")
        
        total_hosts = len(self.all_host_data)
        records_written = 0
        
        # Get all possible column names from our patterns
        all_column_types = set(self.column_patterns.keys())
        
        for i, (normalized_host, host_data) in enumerate(self.all_host_data.items(), 1):
            if i % 50 == 0:
                print_progress(i, total_hosts, f"Writing {normalized_host}")
            
            # Build the record data
            record_data = {
                'normalized_host': normalized_host,
                'source_tables': ', '.join(sorted(host_data['source_tables'])) if host_data['source_tables'] else ''
            }
            
            # Add all attribute data
            for attr_type in all_column_types:
                if attr_type in host_data and host_data[attr_type]:
                    # Take the best value (longest or most representative)
                    best_value = max(host_data[attr_type], key=len) if host_data[attr_type] else ''
                    record_data[attr_type] = best_value
                else:
                    record_data[attr_type] = None
            
            # Build and execute insert statement
            columns = list(record_data.keys())
            values = list(record_data.values())
            placeholders = ', '.join(['?' for _ in values])
            
            insert_sql = f"""
            INSERT OR REPLACE INTO universal_cmdb 
            ({', '.join(columns)})
            VALUES ({placeholders})
            """
            
            try:
                self.duck_conn.execute(insert_sql, values)
                records_written += 1
            except Exception as e:
                logger.error(f"❌ Error writing {normalized_host}: {e}")
        
        print()  # New line after progress bar
        logger.info(f"✅ Successfully wrote {records_written:,} records to database")
    
    def process_all_data(self):
        """Main processing function"""
        print_banner("🔄 AGGRESSIVE DATA PROCESSING")
        
        # Load and analyze metadata
        metadata = self.load_metadata()
        columns_to_process = self.analyze_all_columns(metadata)
        
        if not columns_to_process:
            logger.warning("⚠️  No columns to process!")
            return
        
        # Phase 1: Aggressively collect all data
        self.collect_all_data_aggressively(columns_to_process)
        
        # Phase 2: Write everything to database
        self.write_all_to_database()
        
        # Create summary table
        logger.info("📊 Creating summary table...")
        self._create_summary_table()
        
        print("✅ Aggressive data processing complete!")
    
    def _create_summary_table(self):
        """Create summary table"""
        try:
            drop_sql = "DROP TABLE IF EXISTS all_sources"
            self.duck_conn.execute(drop_sql)
            
            # Get all column names except system columns
            columns_query = "PRAGMA table_info(universal_cmdb)"
            all_columns = [col[1] for col in self.duck_conn.execute(columns_query).fetchall()]
            data_columns = [col for col in all_columns 
                           if col not in ['normalized_host', 'source_tables', 'last_updated', 'created_at']]
            
            column_list = ['normalized_host as host', 'source_tables'] + data_columns
            column_list.append("LENGTH(source_tables) - LENGTH(REPLACE(source_tables, ',', '')) + 1 as source_count")
            column_list.append('last_updated')
            
            create_sql = f"""
            CREATE TABLE all_sources AS (
                SELECT {', '.join(column_list)}
                FROM universal_cmdb
                WHERE normalized_host IS NOT NULL 
                ORDER BY source_count DESC, normalized_host
            )
            """
            self.duck_conn.execute(create_sql)
            logger.info("✅ Summary table created")
        except Exception as e:
            logger.error(f"❌ Error creating summary table: {e}")
    
    def print_final_summary(self):
        """Print comprehensive final summary"""
        print_banner("📊 FINAL SUMMARY")
        
        try:
            total_hosts = self.duck_conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
            
            # Get column info
            columns_query = "PRAGMA table_info(universal_cmdb)"
            columns_info = self.duck_conn.execute(columns_query).fetchall()
            
            print(f"🏠 Total unique hosts: {total_hosts:,}")
            print(f"📊 Total columns: {len(columns_info)}")
            print()
            
            # Show data population for each column
            print("📈 DATA POPULATION BY COLUMN:")
            print("┌─────────────────────────────────┬─────────────┬─────────────┐")
            print("│ Column Name                     │ Records     │ Coverage %  │")
            print("├─────────────────────────────────┼─────────────┼─────────────┤")
            
            non_empty_columns = []
            for col_info in columns_info:
                col_name = col_info[1]
                if col_name not in ['last_updated', 'created_at']:
                    try:
                        count_sql = f"SELECT COUNT(*) FROM universal_cmdb WHERE {col_name} IS NOT NULL AND {col_name} != ''"
                        count = self.duck_conn.execute(count_sql).fetchone()[0]
                        percentage = (count / total_hosts * 100) if total_hosts > 0 else 0
                        
                        display_name = col_name[:31]
                        print(f"│ {display_name:<31} │ {count:>11,} │ {percentage:>10.1f}% │")
                        
                        if count > 0 and col_name not in ['normalized_host', 'source_tables']:
                            non_empty_columns.append(col_name)
                    except Exception as e:
                        logger.debug(f"Error getting count for {col_name}: {e}")
            
            print("└─────────────────────────────────┴─────────────┴─────────────┘")
            
            print(f"\n🎉 SUCCESS! Populated {len(non_empty_columns)} data columns:")
            for col in sorted(non_empty_columns):
                print(f"   ✅ {col}")
            
            # Show sample records with most data
            print("\n📄 SAMPLE RECORDS WITH MOST DATA:")
            sample_sql = f"""
            SELECT * FROM universal_cmdb 
            WHERE normalized_host IS NOT NULL
            ORDER BY (
                {' + '.join([f"CASE WHEN {col} IS NOT NULL AND {col} != '' THEN 1 ELSE 0 END" for col in non_empty_columns[:10]])}
            ) DESC
            LIMIT 5
            """
            
            sample_results = self.duck_conn.execute(sample_sql).fetchall()
            column_names = [col[1] for col in columns_info]
            
            for i, row in enumerate(sample_results, 1):
                print(f"\n  🏠 Host {i}: {row[0]}")
                populated_fields = 0
                for j, value in enumerate(row[1:], 1):
                    if value and str(value).strip() and column_names[j] not in ['last_updated', 'created_at']:
                        display_value = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                        print(f"     • {column_names[j]}: {display_value}")
                        populated_fields += 1
                print(f"     📊 Total populated fields: {populated_fields}")
            
        except Exception as e:
            logger.error(f"❌ Error generating summary: {e}")
    
    def export_data(self, output_file: str = "universal_cmdb_export.csv"):
        """Export data to CSV"""
        try:
            export_sql = f"COPY (SELECT * FROM universal_cmdb ORDER BY normalized_host) TO '{output_file}' WITH (FORMAT CSV, HEADER)"
            self.duck_conn.execute(export_sql)
            logger.info(f"📄 Data exported to {output_file}")
        except Exception as e:
            logger.error(f"❌ Export failed: {e}")
    
    def close_connections(self):
        """Close all connections"""
        try:
            self.duck_conn.close()
            logger.info("🔌 Database connections closed")
        except:
            pass

# Main execution
if __name__ == "__main__":
    JSON_FILE_PATH = "reviewed_labeled_columns.json"
    DUCKDB_PATH = "universal_cmdb.db"
    
    processor = None
    try:
        print_banner("🌟 UNIVERSAL CMDB CREATOR - AGGRESSIVE MODE", 100)
        print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📂 Metadata file: {JSON_FILE_PATH}")
        print(f"🗄️  Database file: {DUCKDB_PATH}")
        
        # Initialize processor
        processor = HostDataProcessor(
            json_file_path=JSON_FILE_PATH,
            duckdb_path=DUCKDB_PATH
        )
        
        # Process all data aggressively
        processor.process_all_data()
        
        # Show final summary
        processor.print_final_summary()
        
        # Export results
        processor.export_data("universal_cmdb_export.csv")
        
        print_banner("🎉 AGGRESSIVE PROCESSING COMPLETE!", 100)
        print(f"📅 Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Database: {DUCKDB_PATH}")
        print(f"📊 Export: universal_cmdb_export.csv")
        print(f"✨ Query your data: SELECT * FROM universal_cmdb WHERE hostname IS NOT NULL LIMIT 10;")
        
    except KeyboardInterrupt:
        print("\n\n🛑 Processing interrupted by user")
    except Exception as e:
        logger.error(f"💥 Processing failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if processor:
            processor.close_connections()