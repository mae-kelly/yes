#!/bin/bash
set -euo pipefail

PROJECT_ID=${1:-""}
if [ -z "$PROJECT_ID" ]; then
   echo "Usage: $0 <project-id>"
   exit 1
fi

pip3 install torch torchvision torchaudio
pip3 install scikit-learn pandas numpy networkx scipy

cat >> discovery_engine.py << 'EOF'

import torch
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import networkx as nx

if not torch.backends.mps.is_available():
   raise RuntimeError("M1 GPU not available - ML features disabled")

device = torch.device("mps")

class GPUFieldClassifier:
   def __init__(self):
       self.models = {}
       self.scalers = {}
       self.device = device
       
   def extract_features(self, column_name: str, samples: List[str]) -> np.ndarray:
       if not samples:
           return np.zeros(50)
       
       clean_samples = [str(s) for s in samples if s is not None][:100]
       if not clean_samples:
           return np.zeros(50)
       
       features = []
       
       lengths = [len(s) for s in clean_samples]
       features.extend([
           np.mean(lengths), np.std(lengths), np.min(lengths), np.max(lengths),
           len(set(clean_samples)) / len(clean_samples)
       ])
       
       all_text = ''.join(clean_samples)
       total_chars = len(all_text)
       if total_chars > 0:
           alpha_ratio = sum(c.isalpha() for c in all_text) / total_chars
           digit_ratio = sum(c.isdigit() for c in all_text) / total_chars
           special_ratio = sum(not c.isalnum() for c in all_text) / total_chars
           features.extend([alpha_ratio, digit_ratio, special_ratio])
       else:
           features.extend([0, 0, 0])
       
       hostname_count = sum(1 for s in clean_samples if self._is_hostname_like(s))
       ip_count = sum(1 for s in clean_samples if self._is_ip_like(s))
       mac_count = sum(1 for s in clean_samples if self._is_mac_like(s))
       features.extend([hostname_count/len(clean_samples), ip_count/len(clean_samples), mac_count/len(clean_samples)])
       
       col_lower = column_name.lower()
       keyword_groups = [
           ['host', 'hostname', 'computer', 'endpoint', 'server', 'machine'],
           ['ip', 'address', 'addr', 'inet'],
           ['mac', 'ethernet', 'physical'],
           ['os', 'operating', 'system', 'platform'],
           ['owner', 'user', 'admin', 'contact'],
           ['region', 'location', 'site', 'datacenter'],
           ['env', 'environment', 'stage', 'tier']
       ]
       
       for group in keyword_groups:
           score = sum(1 for kw in group if kw in col_lower) / len(group)
           features.append(score)
       
       while len(features) < 50:
           features.append(0)
       
       return np.array(features[:50])
   
   def _is_hostname_like(self, s: str) -> bool:
       if not s or len(s) < 2 or len(s) > 253:
           return False
       return bool(re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*[a-zA-Z0-9]$', s))
   
   def _is_ip_like(self, s: str) -> bool:
       try:
           import ipaddress
           ipaddress.ip_address(s)
           return True
       except:
           return False
   
   def _is_mac_like(self, s: str) -> bool:
       mac_patterns = [
           r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$',
           r'^([0-9A-Fa-f]{4}\.){2}([0-9A-Fa-f]{4})$'
       ]
       return any(re.match(pattern, s) for pattern in mac_patterns)
   
   def train_on_gpu(self, training_data: List[Tuple[str, List[str], str]]):
       X = []
       y = []
       
       for column_name, samples, field_type in training_data:
           features = self.extract_features(column_name, samples)
           X.append(features)
           y.append(field_type)
       
       if len(set(y)) < 2:
           raise ValueError("Need multiple field types for training")
       
       X_tensor = torch.tensor(np.array(X), device=self.device, dtype=torch.float32)
       
       X_np = X_tensor.cpu().numpy()
       scaler = StandardScaler()
       X_scaled = scaler.fit_transform(X_np)
       
       model = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=1)
       model.fit(X_scaled, y)
       
       self.models['primary'] = model
       self.scalers['primary'] = scaler
   
   def predict_on_gpu(self, column_name: str, samples: List[str]) -> Tuple[str, float]:
       if 'primary' not in self.models:
           return 'unknown', 0.0
       
       features = self.extract_features(column_name, samples)
       features_tensor = torch.tensor(features, device=self.device, dtype=torch.float32).unsqueeze(0)
       
       features_np = features_tensor.cpu().numpy()
       features_scaled = self.scalers['primary'].transform(features_np)
       
       probabilities = self.models['primary'].predict_proba(features_scaled)[0]
       classes = self.models['primary'].classes_
       
       best_idx = np.argmax(probabilities)
       return classes[best_idx], probabilities[best_idx]

class UnlimitedTableAnalyzer:
   def __init__(self):
       self.gpu_classifier = GPUFieldClassifier()
       
   async def analyze_unlimited_tables(self, client_manager, project_id: str):
       print(f"Analyzing ALL tables in {project_id}")
       
       all_tables = []
       
       with client_manager.get_client() as client:
           datasets = list(client.list_datasets(project=project_id))
           print(f"Processing {len(datasets)} datasets")
           
           for i, dataset in enumerate(datasets):
               print(f"Dataset {i+1}/{len(datasets)}: {dataset.dataset_id}")
               
               try:
                   dataset_ref = client.dataset(dataset.dataset_id)
                   tables = list(client.list_tables(dataset_ref))
                   
                   for table_ref in tables:
                       try:
                           full_table = client.get_table(table_ref)
                           
                           if not full_table.schema:
                               continue
                           
                           columns = [field.name for field in full_table.schema]
                           
                           has_potential = any(
                               any(indicator in col.lower() for indicator in 
                                   ['host', 'endpoint', 'computer', 'device', 'server', 'machine', 'asset', 'ip', 'addr'])
                               for col in columns
                           )
                           
                           if has_potential:
                               table_info = {
                                   'project_id': project_id,
                                   'dataset_id': dataset.dataset_id,
                                   'table_id': table_ref.table_id,
                                   'full_path': f"{project_id}.{dataset.dataset_id}.{table_ref.table_id}",
                                   'columns': columns,
                                   'row_count': full_table.num_rows or 0,
                                   'size_bytes': full_table.num_bytes or 0
                               }
                               
                               print(f"Adding table: {table_ref.table_id} ({full_table.num_rows:,} rows, {(full_table.num_bytes or 0)/1024/1024/1024:.1f}GB)")
                               all_tables.append(table_info)
                               
                       except Exception as e:
                           print(f"Failed to analyze table {table_ref.table_id}: {e}")
                           continue
                           
               except Exception as e:
                   print(f"Failed to process dataset {dataset.dataset_id}: {e}")
                   continue
       
       print(f"Found {len(all_tables)} tables with asset data")
       
       enhanced_tables = []
       for table in all_tables:
           enhanced = await self.enhance_unlimited_analysis(client_manager, table)
           if enhanced:
               enhanced_tables.append(enhanced)
       
       return enhanced_tables
   
   async def enhance_unlimited_analysis(self, client_manager, table_info: Dict):
       print(f"GPU analysis: {table_info['table_id']}")
       
       try:
           sample_data = await self.get_unlimited_sample(client_manager, table_info)
           if not sample_data:
               return None
           
           column_analysis = {}
           for column in table_info['columns']:
               samples = sample_data.get(column, [])
               if samples:
                   try:
                       field_type, confidence = self.gpu_classifier.predict_on_gpu(column, samples)
                       if confidence > 0.2:
                           column_analysis[column] = {
                               'field_type': field_type,
                               'confidence': confidence,
                               'sample_count': len(samples)
                           }
                   except Exception as e:
                       print(f"GPU prediction failed for {column}: {e}")
                       continue
           
           hostname_columns = [
               col for col, analysis in column_analysis.items()
               if analysis['field_type'] in ['hostname', 'fqdn'] and analysis['confidence'] > 0.3
           ]
           
           if not hostname_columns:
               return None
           
           primary_hostname = max(hostname_columns, 
                                key=lambda col: column_analysis[col]['confidence'])
           
           table_info.update({
               'sample_data': sample_data,
               'column_analysis': column_analysis,
               'hostname_columns': hostname_columns,
               'primary_hostname_column': primary_hostname,
               'analysis_score': len(column_analysis) / len(table_info['columns'])
           })
           
           return table_info
           
       except Exception as e:
           print(f"Enhancement failed for {table_info['table_id']}: {e}")
           return None
   
   async def get_unlimited_sample(self, client_manager, table_info: Dict):
       table_path = table_info['full_path']
       
       sample_query = f"SELECT * FROM `{table_path}` LIMIT 50"
       
       try:
           with client_manager.get_client() as client:
               from google.cloud import bigquery
               
               job_config = bigquery.QueryJobConfig(
                   dry_run=False,
                   use_query_cache=True
               )
               
               job = client.query(sample_query, job_config=job_config)
               results = list(job.result())
               
               sample_data = defaultdict(list)
               for row in results:
                   for i, value in enumerate(row):
                       if i < len(table_info['columns']) and value is not None:
                           column_name = table_info['columns'][i]
                           str_value = str(value).strip()
                           if str_value and len(str_value) < 500:
                               sample_data[column_name].append(str_value)
               
               return dict(sample_data)
               
       except Exception as e:
           print(f"Sample extraction failed for {table_path}: {e}")
           return {}

class FixedHostnameExtractor:
   def __init__(self, client_manager):
       self.client_manager = client_manager
       
   async def extract_all_hostnames_fixed(self, enhanced_tables: List[Dict]):
       print("Starting FIXED hostname extraction")
       
       all_hostnames = set()
       hostname_sources = defaultdict(list)
       
       for i, table_info in enumerate(enhanced_tables):
           print(f"Extracting from table {i+1}/{len(enhanced_tables)}: {table_info['table_id']}")
           
           try:
               hostnames = await self.extract_hostnames_unlimited(table_info)
               
               if hostnames:
                   table_id = table_info['table_id']
                   print(f"Extracted {len(hostnames)} hostnames from {table_id}")
                   
                   for hostname in hostnames:
                       all_hostnames.add(hostname)
                       hostname_sources[hostname].append(table_id)
                       
           except Exception as e:
               print(f"Table {table_info['table_id']} extraction failed: {e}")
               continue
       
       print(f"FIXED extraction complete: {len(all_hostnames)} unique hostnames")
       return list(all_hostnames), dict(hostname_sources)
   
   async def extract_hostnames_unlimited(self, table_info: Dict):
       hostname_column = table_info['primary_hostname_column']
       table_path = table_info['full_path']
       
       extraction_query = f"""
       SELECT DISTINCT 
           UPPER(TRIM(CAST(`{hostname_column}` AS STRING))) as hostname
       FROM `{table_path}`
       WHERE `{hostname_column}` IS NOT NULL
           AND LENGTH(TRIM(CAST(`{hostname_column}` AS STRING))) >= 2
           AND LENGTH(TRIM(CAST(`{hostname_column}` AS STRING))) <= 253
       """
       
       try:
           with self.client_manager.get_client() as client:
               from google.cloud import bigquery
               
               job_config = bigquery.QueryJobConfig(
                   dry_run=False,
                   use_query_cache=True
               )
               
               job = client.query(extraction_query, job_config=job_config)
               results = list(job.result())
               
               hostnames = set()
               for row in results:
                   hostname = str(row[0]) if row[0] else ""
                   normalized = self.normalize_hostname_fixed(hostname)
                   if normalized:
                       hostnames.add(normalized)
               
               return hostnames
               
       except Exception as e:
           print(f"Hostname extraction failed for {table_path}: {e}")
           return set()
   
   def normalize_hostname_fixed(self, hostname: str) -> str:
       if not hostname:
           return ""
       
       hostname = str(hostname).strip().upper()
       
       if len(hostname) < 2 or len(hostname) > 253:
           return ""
       
       invalid_indicators = [
           'HTTP', 'HTTPS', 'UNKNOWN', 'NULL', 'N/A', 'NONE', 'EMPTY', 
           'TEST', 'EXAMPLE', 'LOCALHOST', 'DUMMY', 'SAMPLE'
       ]
       if any(indicator in hostname for indicator in invalid_indicators):
           return ""
       
       hostname = re.sub(r'^[^A-Z0-9]+', '', hostname)
       hostname = re.sub(r'[^A-Z0-9]+$', '', hostname)
       
       return hostname if len(hostname) >= 2 else ""

class UnlimitedAO1Discovery:
   def __init__(self, project_id: str, config: Dict[str, Any] = None):
       self.project_id = project_id
       self.config = config or {}
       
       from gcp_client import BigQueryClientManager
       self.client_manager = BigQueryClientManager(project_id)
       
       self.analyzer = UnlimitedTableAnalyzer()
       self.extractor = FixedHostnameExtractor(self.client_manager)
       
       self.db_path = f"unlimited_{project_id}_cmdb.db"
       self.setup_unlimited_database()
       
   def setup_unlimited_database(self):
       self.conn = duckdb.connect(self.db_path)
       
       self.conn.execute("PRAGMA threads=8")
       self.conn.execute("PRAGMA memory_limit='8GB'")
       
       self.conn.execute("""
       CREATE TABLE IF NOT EXISTS unlimited_assets (
           hostname VARCHAR PRIMARY KEY,
           fqdn VARCHAR,
           ip_addresses TEXT,
           mac_addresses TEXT,
           operating_system VARCHAR,
           infrastructure_type VARCHAR,
           environment VARCHAR,
           business_unit VARCHAR,
           owner VARCHAR,
           cost_center VARCHAR,
           criticality VARCHAR,
           location VARCHAR,
           department VARCHAR,
           region VARCHAR,
           data_center VARCHAR,
           source_tables TEXT,
           source_count INTEGER,
           confidence_score DOUBLE,
           completeness_score DOUBLE,
           last_updated TIMESTAMP DEFAULT NOW()
       )
       """)
   
   async def execute_unlimited_discovery(self):
       start_time = time.time()
       
       try:
           print("Phase 1: UNLIMITED table analysis")
           enhanced_tables = await self.analyzer.analyze_unlimited_tables(self.client_manager, self.project_id)
           
           if not enhanced_tables:
               return {'error': 'No suitable tables found', 'total_assets': 0}, {}
           
           print("Phase 2: FIXED hostname extraction")
           hostnames, hostname_sources = await self.extractor.extract_all_hostnames_fixed(enhanced_tables)
           
           if not hostnames:
               return {'error': 'No hostnames found', 'total_assets': 0}, {}
           
           print("Phase 3: Unlimited asset building")
           total_assets = await self.build_unlimited_inventory(hostnames, hostname_sources, enhanced_tables)
           
           processing_time = time.time() - start_time
           
           return {
               'processing_time': processing_time,
               'total_assets': total_assets,
               'database_path': self.db_path,
               'engine_type': 'Unlimited_GPU',
               'discovery_method': 'unlimited_gpu_analysis',
               'tables_analyzed': len(enhanced_tables)
           }, {
               'unlimited_inventory': f"SELECT * FROM unlimited_assets ORDER BY confidence_score DESC;",
               'quality_analysis': """
               SELECT 
                   COUNT(*) as total,
                   AVG(confidence_score) as avg_confidence,
                   AVG(completeness_score) as avg_completeness,
                   COUNT(CASE WHEN operating_system != '' THEN 1 END) as has_os,
                   COUNT(CASE WHEN environment != '' THEN 1 END) as has_env,
                   COUNT(CASE WHEN source_count > 2 THEN 1 END) as multi_source
               FROM unlimited_assets;
               """
           }
           
       except Exception as e:
           print(f"Unlimited discovery failed: {e}")
           return {'error': str(e), 'total_assets': 0}, {}
   
   async def build_unlimited_inventory(self, hostnames: List[str], hostname_sources: Dict, enhanced_tables: List[Dict]):
       print(f"Building unlimited inventory for {len(hostnames)} hostnames")
       
       batch_size = 50
       hostname_batches = [hostnames[i:i + batch_size] for i in range(0, len(hostnames), batch_size)]
       
       total_assets = 0
       
       for i, batch in enumerate(hostname_batches):
           print(f"Processing batch {i+1}/{len(hostname_batches)} ({len(batch)} hostnames)")
           
           batch_assets = []
           for hostname in batch:
               asset_data = await self.build_unlimited_asset(hostname, hostname_sources, enhanced_tables)
               if asset_data:
                   batch_assets.append(asset_data)
           
           if batch_assets:
               self.insert_unlimited_assets(batch_assets)
               total_assets += len(batch_assets)
       
       print(f"Unlimited inventory complete: {total_assets} assets")
       return total_assets
   
   async def build_unlimited_asset(self, hostname: str, hostname_sources: Dict, enhanced_tables: List[Dict]):
       asset = {
           'hostname': hostname,
           'fqdn': '',
           'ip_addresses': '',
           'mac_addresses': '',
           'operating_system': '',
           'infrastructure_type': '',
           'environment': '',
           'business_unit': '',
           'owner': '',
           'cost_center': '',
           'criticality': '',
           'location': '',
           'department': '',
           'region': '',
           'data_center': '',
           'source_tables': '',
           'source_count': 0,
           'confidence_score': 0.0,
           'completeness_score': 0.0
       }
       
       source_tables = hostname_sources.get(hostname, [])
       asset['source_tables'] = ','.join(source_tables)
       asset['source_count'] = len(source_tables)
       
       for table_info in enhanced_tables:
           if table_info['table_id'] in source_tables:
               enrichment = await self.extract_unlimited_data(hostname, table_info)
               for field, value in enrichment.items():
                   if field in asset and value and not asset[field]:
                       asset[field] = value
       
       populated_fields = sum(1 for v in asset.values() if v and str(v).strip())
       total_fields = len(asset) - 1
       asset['completeness_score'] = populated_fields / total_fields
       
       confidence_factors = [
           asset['completeness_score'],
           min(asset['source_count'] / 3, 1.0),
           0.8 if asset['operating_system'] else 0.2,
           0.7 if asset['environment'] else 0.3
       ]
       asset['confidence_score'] = sum(confidence_factors) / len(confidence_factors)
       
       return asset
   
   async def extract_unlimited_data(self, hostname: str, table_info: Dict):
       hostname_column = table_info['primary_hostname_column']
       table_path = table_info['full_path']
       column_analysis = table_info.get('column_analysis', {})
       
       select_fields = [f"UPPER(TRIM(CAST(`{hostname_column}` AS STRING))) as hostname"]
       field_mappings = {}
       
       for column, analysis in column_analysis.items():
           if column != hostname_column and analysis['confidence'] > 0.4:
               field_type = analysis['field_type']
               if field_type in ['operating_system', 'environment', 'business_unit', 'owner', 'cost_center', 'criticality', 'location', 'department', 'region']:
                   safe_column = column.replace('`', '``')
                   select_fields.append(f"CAST(`{safe_column}` AS STRING) as `{safe_column}`")
                   field_mappings[safe_column] = field_type
       
       if len(select_fields) == 1:
           return {}
       
       enrichment_query = f"""
       SELECT {', '.join(select_fields)}
       FROM `{table_path}`
       WHERE UPPER(TRIM(CAST(`{hostname_column}` AS STRING))) = '{hostname}'
       LIMIT 1
       """
       
       try:
           with self.client_manager.get_client() as client:
               from google.cloud import bigquery
               
               job_config = bigquery.QueryJobConfig(
                   dry_run=False,
                   use_query_cache=True
               )
               
               job = client.query(enrichment_query, job_config=job_config)
               results = list(job.result())
               
               if not results:
                   return {}
               
               row = results[0]
               enrichment = {}
               
               for i, field_name in enumerate(select_fields[1:], 1):
                   if i < len(row) and row[i]:
                       clean_field_name = field_name.split(' as ')[-1].strip('`')
                       field_type = field_mappings.get(clean_field_name, 'unknown')
                       value = str(row[i]).strip()
                       
                       if value and value.upper() not in ['NULL', 'N/A', 'UNKNOWN', 'NONE', '']:
                           enrichment[field_type] = value
               
               return enrichment
               
       except Exception as e:
           return {}
   
   def insert_unlimited_assets(self, assets: List[Dict]):
       if not assets:
           return
       
       columns = list(assets[0].keys())
       placeholders = ', '.join(['?' for _ in columns])
       column_names = ', '.join(columns)
       
       query = f"INSERT OR REPLACE INTO unlimited_assets ({column_names}) VALUES ({placeholders})"
       
       values_list = []
       for asset in assets:
           values = [asset[col] for col in columns]
           values_list.append(values)
       
       try:
           self.conn.executemany(query, values_list)
       except Exception as e:
           print(f"Database insert failed: {e}")
   
   def close(self):
       if hasattr(self, 'conn') and self.conn:
           self.conn.close()
EOF

python3 enhanced_discovery_system.py "$PROJECT_ID"

echo "Unlimited discovery complete for $PROJECT_ID"
echo "Database: unlimited_${PROJECT_ID}_cmdb.db"