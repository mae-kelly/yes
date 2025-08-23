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
        
        # Define ALL expected column types and their normalized names
        self.column_type_mapping = {
            # Hostname related
            'host': 'hostname',
            'hostname': 'hostname', 
            'fqdn': 'fqdn',
            'domain': 'domain',
            # Infrastructure
            'infrastructure_type': 'infrastructure_type',
            'infra_type': 'infrastructure_type',  # Merge with infrastructure_type
            'region': 'region',
            'country': 'country',
            'data_center': 'data_center',
            'cloud_region': 'cloud_region',
            # Network
            'ip_address': 'ip_address',
            # Classification
            'class': 'class',
            'system_classification': 'system_classification',
            'business_unit': 'business_unit',
            # Management
            'apm': 'apm',
            'cio': 'cio',
            # Security & Monitoring
            'edr_coverage': 'edr_coverage',
            'tanium_coverage': 'tanium_coverage',
            'dlp_agent_coverage': 'dlp_agent_coverage',
            'logging_in_splunk': 'logging_in_splunk',
            'logging_in_gso': 'logging_in_gso'
        }
        
        # Track which column types contain hostnames (used to create normalized_host)
        self.hostname_types = {'host', 'hostname', 'fqdn'}
        
        # Storage for all collected data - this is key to the new approach
        self.all_host_data = defaultdict(lambda: defaultdict(set))  # {normalized_host: {column_type: {values}}}
        self.all_attribute_data = defaultdict(lambda: defaultdict(set))  # {table_name: {column_type: {values}}}
        self.table_to_hosts = defaultdict(set)  # {table_name: {normalized_hosts}}
        
        # Initialize connections
        logger.info("🔌 Initializing BigQuery connection...")
        self.bq_client = self._initialize_bigquery_client()
        
        logger.info("🗄️  Initializing DuckDB connection...")
        self.duck_conn = duckdb.connect(duckdb_path)
        
        # Storage for discovered data
        self.all_columns_info = []
        self.existing_hosts_cache = set()
        
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
        
        # Add ALL possible columns from our mapping
        logger.info("📊 Adding all possible data columns...")
        self._ensure_all_columns_exist()
        
        # Load existing hosts
        logger.info("📥 Loading existing hosts cache...")
        self.existing_hosts_cache = self._load_existing_hosts()
        
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
        """Ensure ALL possible columns from our mapping exist in the table"""
        # Get all unique normalized column types
        all_possible_columns = set(self.column_type_mapping.values())
        
        logger.info(f"📋 Ensuring {len(all_possible_columns)} columns exist...")
        
        columns_added = 0
        for column_type in sorted(all_possible_columns):
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
    
    def _load_existing_hosts(self) -> Set[str]:
        """Load existing normalized hosts into memory"""
        try:
            query = "SELECT DISTINCT normalized_host FROM universal_cmdb WHERE normalized_host IS NOT NULL"
            results = self.duck_conn.execute(query).fetchall()
            existing_hosts = {row[0] for row in results}
            logger.info(f"📥 Loaded {len(existing_hosts)} existing hosts")
            return existing_hosts
        except Exception as e:
            logger.warning(f"⚠️  Could not load existing hosts: {e}")
            return set()
    
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
    
    def analyze_metadata(self, metadata: Dict):
        """Analyze metadata and discover all column types"""
        print_section("METADATA ANALYSIS")
        
        if 'columns' not in metadata:
            logger.error("❌ No 'columns' key found in metadata")
            return []
        
        # First pass: collect all column types
        all_found_types = set()
        all_columns_info = []
        
        for table_name, columns in metadata['columns'].items():
            for column_name, column_type in columns.items():
                if isinstance(column_type, str):
                    all_found_types.add(column_type.lower())
                    
                    # Check if we recognize this type
                    normalized_type = self.column_type_mapping.get(column_type.lower())
                    if normalized_type:
                        all_columns_info.append((table_name, column_name, column_type, normalized_type))
                    elif self._is_host_column_name(column_name):
                        all_columns_info.append((table_name, column_name, 'hostname', 'hostname'))
        
        # Show analysis results
        recognized_types = set(self.column_type_mapping.keys())
        mapped_types = {info[2].lower() for info in all_columns_info}
        unmapped_types = all_found_types - recognized_types
        
        print("📊 Column Type Analysis:")
        print(f"  🔍 Total unique column types found: {len(all_found_types)}")
        print(f"  ✅ Recognized and mapped: {len(mapped_types)}")
        print(f"  ❌ Unrecognized (will be skipped): {len(unmapped_types)}")
        
        if unmapped_types:
            print("  🚫 Unrecognized types:")
            for utype in sorted(unmapped_types):
                print(f"     • {utype}")
        
        # Show what we found for each column type
        type_counts = defaultdict(int)
        for _, _, _, norm_type in all_columns_info:
            type_counts[norm_type] += 1
        
        print(f"  📋 Columns found by type:")
        for col_type in sorted(type_counts.keys()):
            print(f"     • {col_type}: {type_counts[col_type]} columns")
        
        print(f"  📋 Total columns to process: {len(all_columns_info)}")
        
        self.all_columns_info = all_columns_info
        return all_columns_info
    
    def _is_host_column_name(self, column_name: str) -> bool:
        """Check if column name indicates host data"""
        host_patterns = [
            'host', 'hostname', 'endpoint_name', 'endpointdomain_name',
            'splunk_host', 'app_host', 'chronicle_device_hostname',
            'server_name', 'node_name', 'device_name', 'device_hostname'
        ]
        
        column_lower = column_name.lower()
        return any(pattern in column_lower for pattern in host_patterns)
    
    def collect_all_data(self):
        """PHASE 1: Collect ALL data from BigQuery into memory structures"""
        print_section("PHASE 1: DATA COLLECTION")
        
        logger.info("🗂️  Collecting all data from BigQuery...")
        
        for i, (table_name, column_name, orig_type, norm_type) in enumerate(self.all_columns_info, 1):
            print_progress(i, len(self.all_columns_info), f"{table_name}.{column_name}")
            
            # Get all data from this column
            data = self._fetch_column_data(table_name, column_name)
            
            # Check if this is a hostname column
            is_hostname_col = (orig_type.lower() in self.hostname_types or 
                             self._is_host_column_name(column_name))
            
            if is_hostname_col:
                # Process hostname data
                for value in data:
                    normalized_host = self.normalize_hostname(value)
                    if normalized_host and len(normalized_host) > 2:
                        self.all_host_data[normalized_host]['source_tables'].add(table_name)
                        self.all_host_data[normalized_host][norm_type].add(value)
                        self.table_to_hosts[table_name].add(normalized_host)
            else:
                # Store attribute data by table
                for value in data:
                    if value and value.strip():
                        self.all_attribute_data[table_name][norm_type].add(value.strip())
        
        print()  # New line after progress bar
        
        # Show collection results
        print("📊 Collection Results:")
        print(f"  🏠 Unique hosts discovered: {len(self.all_host_data):,}")
        print(f"  📋 Tables with hosts: {len(self.table_to_hosts)}")
        print(f"  📝 Tables with attributes: {len(self.all_attribute_data)}")
        
        # Show attribute data by type
        attribute_type_counts = defaultdict(int)
        for table_data in self.all_attribute_data.values():
            for attr_type, values in table_data.items():
                attribute_type_counts[attr_type] += len(values)
        
        if attribute_type_counts:
            print("  🎯 Attribute data collected:")
            for attr_type in sorted(attribute_type_counts.keys()):
                print(f"     • {attr_type}: {attribute_type_counts[attr_type]:,} unique values")
    
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
        LIMIT 50000
        """
        
        try:
            query_job = self.bq_client.query(query)
            results = query_job.result()
            return [row.value for row in results if row.value and isinstance(row.value, str)]
        except Exception as e:
            logger.error(f"❌ Error fetching {table_name}.{column_name}: {e}")
            return []
    
    def smart_attribute_linking(self):
        """PHASE 2: Intelligently link attribute data to hosts"""
        print_section("PHASE 2: SMART ATTRIBUTE LINKING")
        
        logger.info("🧠 Applying intelligent attribute linking...")
        
        # Strategy 1: Direct table linking - if hosts and attributes come from same table
        direct_links = 0
        for table_name, hosts in self.table_to_hosts.items():
            if table_name in self.all_attribute_data:
                for host in hosts:
                    for attr_type, values in self.all_attribute_data[table_name].items():
                        # Take the most common value for this attribute type
                        if values:
                            most_common_value = max(values, key=lambda x: len(x)) if len(values) > 1 else next(iter(values))
                            self.all_host_data[host][attr_type].add(most_common_value)
                            direct_links += 1
        
        logger.info(f"✅ Direct table links: {direct_links:,}")
        
        # Strategy 2: Pattern-based linking - match attributes to hosts by patterns
        pattern_links = 0
        for table_name, attr_data in self.all_attribute_data.items():
            for attr_type, values in attr_data.items():
                for value in values:
                    # Try to extract hostname patterns from attribute values
                    potential_hosts = self._extract_hostnames_from_value(value)
                    for potential_host in potential_hosts:
                        if potential_host in self.all_host_data:
                            self.all_host_data[potential_host][attr_type].add(value)
                            pattern_links += 1
        
        logger.info(f"✅ Pattern-based links: {pattern_links:,}")
        
        # Strategy 3: Global application - apply common attributes globally
        global_links = 0
        for table_name, attr_data in self.all_attribute_data.items():
            for attr_type, values in attr_data.items():
                # If we have very few unique values for an attribute type, apply globally
                if len(values) <= 5:  # Configurable threshold
                    most_common_value = max(values, key=lambda x: len(x)) if len(values) > 1 else next(iter(values))
                    for host in self.all_host_data.keys():
                        # Only apply if the host doesn't already have this attribute
                        if not self.all_host_data[host][attr_type]:
                            self.all_host_data[host][attr_type].add(most_common_value)
                            global_links += 1
        
        logger.info(f"✅ Global attribute applications: {global_links:,}")
        
        # Show final linking results
        populated_attributes = defaultdict(int)
        for host_data in self.all_host_data.values():
            for attr_type, values in host_data.items():
                if values and attr_type != 'source_tables':
                    populated_attributes[attr_type] += 1
        
        print("🎯 Final attribute population:")
        for attr_type in sorted(populated_attributes.keys()):
            percentage = (populated_attributes[attr_type] / len(self.all_host_data) * 100) if self.all_host_data else 0
            print(f"  • {attr_type}: {populated_attributes[attr_type]:,} hosts ({percentage:.1f}%)")
    
    def _extract_hostnames_from_value(self, value: str) -> List[str]:
        """Try to extract potential hostnames from an attribute value"""
        potential_hosts = []
        
        # Look for hostname patterns in the value
        if '.' in value:
            # Might be FQDN or contain hostname
            parts = value.lower().split('.')
            for part in parts:
                normalized = self.normalize_hostname(part)
                if normalized and len(normalized) > 2:
                    potential_hosts.append(normalized)
        
        # Try the whole value as hostname
        normalized = self.normalize_hostname(value)
        if normalized and len(normalized) > 2:
            potential_hosts.append(normalized)
        
        return potential_hosts
    
    def write_to_database(self):
        """PHASE 3: Write all collected and linked data to database"""
        print_section("PHASE 3: DATABASE POPULATION")
        
        logger.info("💾 Writing all data to database...")
        
        total_hosts = len(self.all_host_data)
        records_written = 0
        
        for i, (normalized_host, host_data) in enumerate(self.all_host_data.items(), 1):
            if i % 100 == 0:
                print_progress(i, total_hosts, f"Writing host {normalized_host}")
            
            # Prepare data for insertion
            source_tables = ', '.join(sorted(host_data['source_tables'])) if host_data['source_tables'] else ''
            
            # Build the insert/update statement
            columns = ['normalized_host', 'source_tables']
            values = [normalized_host, source_tables]
            
            # Add all attribute columns
            for attr_type in sorted(self.column_type_mapping.values()):
                if attr_type in host_data and host_data[attr_type]:
                    # Take the most representative value (longest string or most common)
                    value = max(host_data[attr_type], key=len) if host_data[attr_type] else ''
                    columns.append(attr_type)
                    values.append(value)
                else:
                    columns.append(attr_type)
                    values.append(None)
            
            # Insert or replace the record
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
                logger.error(f"❌ Error writing host {normalized_host}: {e}")
        
        print()  # New line after progress bar
        logger.info(f"✅ Successfully wrote {records_written:,} host records")
        
        # Update existing hosts cache
        self.existing_hosts_cache = set(self.all_host_data.keys())
    
    def process_all_data(self):
        """Main processing function with new 3-phase approach"""
        print_banner("🔄 DATA PROCESSING - 3 PHASE APPROACH")
        
        # Load and analyze metadata
        metadata = self.load_metadata()
        columns_info = self.analyze_metadata(metadata)
        
        if not columns_info:
            logger.warning("⚠️  No columns to process!")
            return
        
        # Phase 1: Collect all data from BigQuery
        self.collect_all_data()
        
        # Phase 2: Apply intelligent attribute linking
        self.smart_attribute_linking()
        
        # Phase 3: Write everything to database
        self.write_to_database()
        
        # Create summary table
        logger.info("📊 Creating summary tables...")
        self._create_summary_table()
        
        print("✅ Data processing complete!")
    
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
        
        # Get basic stats
        try:
            total_hosts = self.duck_conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
            
            # Get column info
            columns_query = "PRAGMA table_info(universal_cmdb)"
            columns_info = self.duck_conn.execute(columns_query).fetchall()
            
            print(f"🏠 Total unique hosts: {total_hosts:,}")
            print(f"📊 Total columns: {len(columns_info)}")
            print()
            
            # Show data population for each column
            print("📈 Data Population by Column:")
            print("┌─────────────────────────────────┬─────────────┬─────────────┐")
            print("│ Column Name                     │ Records     │ Coverage %  │")
            print("├─────────────────────────────────┼─────────────┼─────────────┤")
            
            for col_info in columns_info:
                col_name = col_info[1]
                if col_name not in ['last_updated', 'created_at']:
                    try:
                        count_sql = f"SELECT COUNT(*) FROM universal_cmdb WHERE {col_name} IS NOT NULL AND {col_name} != ''"
                        count = self.duck_conn.execute(count_sql).fetchone()[0]
                        percentage = (count / total_hosts * 100) if total_hosts > 0 else 0
                        
                        display_name = col_name[:31]
                        print(f"│ {display_name:<31} │ {count:>11,} │ {percentage:>10.1f}% │")
                    except:
                        pass
            
            print("└─────────────────────────────────┴─────────────┴─────────────┘")
            
            # Show top hosts by source count
            print("\n🏆 Top 10 Hosts by Source Coverage:")
            top_hosts_sql = """
            SELECT normalized_host, 
                   LENGTH(source_tables) - LENGTH(REPLACE(source_tables, ',', '')) + 1 as source_count,
                   source_tables
            FROM universal_cmdb
            ORDER BY source_count DESC, normalized_host
            LIMIT 10
            """
            
            top_hosts = self.duck_conn.execute(top_hosts_sql).fetchall()
            for i, (host, count, tables) in enumerate(top_hosts, 1):
                tables_display = tables[:50] + "..." if len(tables) > 50 else tables
                print(f"  {i:2d}. {host:<20} ({count} sources): {tables_display}")
            
            # Show sample complete records
            print("\n📄 Sample Complete Records:")
            sample_sql = """
            SELECT * FROM universal_cmdb 
            WHERE normalized_host IS NOT NULL
            ORDER BY (
                CASE WHEN hostname IS NOT NULL THEN 1 ELSE 0 END +
                CASE WHEN fqdn IS NOT NULL THEN 1 ELSE 0 END +
                CASE WHEN domain IS NOT NULL THEN 1 ELSE 0 END +
                CASE WHEN region IS NOT NULL THEN 1 ELSE 0 END +
                CASE WHEN business_unit IS NOT NULL THEN 1 ELSE 0 END +
                CASE WHEN infrastructure_type IS NOT NULL THEN 1 ELSE 0 END
            ) DESC
            LIMIT 5
            """
            sample_results = self.duck_conn.execute(sample_sql).fetchall()
            column_names = [col[1] for col in columns_info]
            
            for i, row in enumerate(sample_results, 1):
                print(f"\n  Record {i}: {row[0]}")
                non_empty_fields = 0
                for j, value in enumerate(row[1:], 1):
                    if value and str(value).strip() and column_names[j] not in ['last_updated', 'created_at']:
                        print(f"    • {column_names[j]}: {value}")
                        non_empty_fields += 1
                print(f"    📊 Total populated fields: {non_empty_fields}")
            
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
        print_banner("🌟 UNIVERSAL CMDB CREATOR", 100)
        print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📂 Metadata file: {JSON_FILE_PATH}")
        print(f"🗄️  Database file: {DUCKDB_PATH}")
        
        # Initialize processor
        processor = HostDataProcessor(
            json_file_path=JSON_FILE_PATH,
            duckdb_path=DUCKDB_PATH
        )
        
        # Process all data with new 3-phase approach
        processor.process_all_data()
        
        # Show final summary
        processor.print_final_summary()
        
        # Export results
        processor.export_data("universal_cmdb_export.csv")
        
        print_banner("🎉 PROCESSING COMPLETE!", 100)
        print(f"📅 Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Database: {DUCKDB_PATH}")
        print(f"📊 Export: universal_cmdb_export.csv")
        print(f"✨ Query your data: SELECT * FROM universal_cmdb LIMIT 10;")
        
    except KeyboardInterrupt:
        print("\n\n🛑 Processing interrupted by user")
    except Exception as e:
        logger.error(f"💥 Processing failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if processor:
            processor.close_connections()