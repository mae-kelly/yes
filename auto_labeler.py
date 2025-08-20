import sys
import os
sys.path.insert(0, '/Users/maeve.kelly/Downloads/logLens2')

from gcp.client import BigQueryClientManager
import json
import pickle
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
from collections import defaultdict
import numpy as np
from smart_claude_intelligence import ClaudeLevelIntelligence
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutomaticCompleteLabeler:
    def __init__(self):
        self.project_ids = ['prj-fisv-p-gcss-sas-dl9dd0f1df', 'chronicle-fisv']
        self.client_managers = {}
        self.labeled_data_path = Path('complete_labeled_columns.json')
        self.model_path = Path('complete_column_classifier.pkl')
        self.intelligence = ClaudeLevelIntelligence()
        
        self.column_types = {
            'host': ['host', 'hostname', 'host_name', 'computer_name', 'server_name', 'machine_name', 
                    'device_name', 'node_name', 'system_name', 'endpoint_name', 'asset_name'],
            'infrastructure_type': ['infrastructure_type', 'infra_type', 'platform_type', 'deployment_type', 
                                   'hosting_type', 'env_type', 'environment_type'],
            'region': ['region', 'geographic_region', 'geo_region', 'location_region', 'aws_region', 
                      'azure_region', 'gcp_region', 'cloud_region'],
            'country': ['country', 'country_code', 'nation', 'geographic_country', 'geo_country'],
            'data_center': ['data_center', 'datacenter', 'dc', 'facility', 'site', 'location'],
            'cloud_region': ['cloud_region', 'aws_region', 'azure_region', 'gcp_region', 'cloud_zone', 
                           'availability_zone', 'az'],
            'business_unit': ['business_unit', 'bu', 'org_unit', 'organization', 'division', 'department', 
                            'cost_center', 'org'],
            'cio': ['cio', 'chief_information_officer', 'it_org', 'it_organization', 'it_division'],
            'apm': ['apm', 'application_performance_monitoring', 'app_monitoring', 'performance_monitoring'],
            'app_class': ['app_class', 'application_class', 'application_type', 'app_type', 
                         'application_category', 'app_category'],
            'system_classification': ['system_classification', 'sys_class', 'system_type', 'server_type', 
                                     'os_type', 'operating_system', 'os', 'platform'],
            'edr_coverage': ['edr_coverage', 'edr', 'endpoint_detection', 'crowdstrike', 'carbon_black', 
                           'sentinel_one', 'endpoint_protection', 'edr_status'],
            'tanium_coverage': ['tanium_coverage', 'tanium', 'endpoint_platform', 'tanium_agent', 
                              'tanium_status'],
            'dlp_agent_coverage': ['dlp_agent_coverage', 'dlp_coverage', 'dlp', 'data_loss_prevention', 
                                 'forcepoint', 'symantec_dlp', 'dlp_agent', 'dlp_status'],
            'logging_in_splunk': ['logging_in_splunk', 'splunk_logging', 'splunk', 'spl_', 
                                'universal_forwarder', 'splunk_agent', 'splunk_status'],
            'logging_in_gso': ['logging_in_gso', 'gso_logging', 'gso', 'global_security_operations', 
                             'security_logging', 'gso_status'],
            'domain': ['domain', 'dns_domain', 'fqdn_domain', 'ad_domain', 'network_domain', 
                      'windows_domain', 'active_directory'],
            'ip_address': ['ip_address', 'ip', 'ipv4', 'ipv6', 'ip_addr', 'network_address', 
                         'source_ip', 'dest_ip', 'destination_ip', 'client_ip', 'server_ip'],
            'mac_address': ['mac_address', 'mac', 'mac_addr', 'physical_address', 'hardware_address'],
            'os_type': ['os_type', 'operating_system', 'os', 'platform', 'system_platform'],
            'os_version': ['os_version', 'os_ver', 'version', 'os_release', 'release'],
            'patch_level': ['patch_level', 'patch', 'patch_version', 'hotfix', 'update_level'],
            'owner': ['owner', 'owned_by', 'owner_email', 'owner_name', 'responsible_party'],
            'criticality': ['criticality', 'critical', 'priority', 'importance', 'severity'],
            'environment': ['environment', 'env', 'stage', 'deployment_env', 'env_name'],
            'last_patch_date': ['last_patch_date', 'patch_date', 'last_update', 'last_patched', 
                              'update_date', 'patch_timestamp'],
            'created_date': ['created_date', 'created', 'creation_date', 'created_at', 'created_timestamp'],
            'modified_date': ['modified_date', 'modified', 'updated_date', 'updated_at', 'last_modified'],
            'asset_id': ['asset_id', 'asset_tag', 'asset_number', 'asset_code', 'inventory_id'],
            'serial_number': ['serial_number', 'serial', 'serial_no', 'sn', 'device_serial'],
            'fqdn': ['fqdn', 'fully_qualified_domain_name', 'full_domain', 'dns_name'],
            'vpc': ['vpc', 'virtual_private_cloud', 'vpc_id', 'network_vpc'],
            'subnet': ['subnet', 'subnet_id', 'network_subnet', 'subnetwork'],
            'security_group': ['security_group', 'sg', 'firewall_group', 'security_group_id'],
            'cmdb_id': ['cmdb_id', 'cmdb', 'configuration_item', 'ci_id', 'cmdb_ci'],
            'compliance_status': ['compliance_status', 'compliance', 'compliant', 'compliance_state'],
            'backup_status': ['backup_status', 'backup', 'backup_enabled', 'backup_configured']
        }
        
        self.labeled_columns = self._load_labeled_data()
        self.statistics = {
            'total_tables': 0,
            'total_columns': 0,
            'labeled_columns': 0,
            'tables_processed': [],
            'start_time': datetime.now()
        }
        
        logger.info(f"Initializing automatic labeler for projects: {', '.join(self.project_ids)}")
        self._connect_to_projects()
    
    def _connect_to_projects(self):
        for project_id in self.project_ids:
            try:
                manager = BigQueryClientManager(project_id)
                if manager.test_connection():
                    self.client_managers[project_id] = manager
                    logger.info(f"✅ Connected to project: {project_id}")
                else:
                    logger.error(f"❌ Failed to connect to project: {project_id}")
            except Exception as e:
                logger.error(f"❌ Connection error for {project_id}: {e}")
        
        if not self.client_managers:
            raise RuntimeError("Failed to connect to any projects")
    
    def _load_labeled_data(self) -> Dict[str, Any]:
        if self.labeled_data_path.exists():
            with open(self.labeled_data_path, 'r') as f:
                return json.load(f)
        return {
            'columns': {},
            'patterns': defaultdict(list),
            'confidence_scores': {},
            'labeling_history': [],
            'statistics': {}
        }
    
    def _save_labeled_data(self):
        with open(self.labeled_data_path, 'w') as f:
            json.dump(self.labeled_columns, f, indent=2, default=str)
        logger.info(f"💾 Saved labeled data to {self.labeled_data_path}")
    
    def label_all_tables_automatically(self):
        print("\n" + "="*80)
        print("AUTOMATIC COMPLETE PROJECT LABELING")
        print("="*80)
        print(f"Projects: {', '.join(self.project_ids)}")
        print("This will label EVERY table in EVERY dataset")
        print("="*80 + "\n")
        
        total_start = time.time()
        
        for project_id, manager in self.client_managers.items():
            self._label_entire_project(project_id, manager)
        
        total_time = time.time() - total_start
        
        self._print_final_statistics(total_time)
        self._train_model()
        self._save_labeled_data()
    
    def _label_entire_project(self, project_id: str, manager):
        print(f"\n📁 PROJECT: {project_id}")
        print("-"*60)
        
        project_stats = {
            'datasets': 0,
            'tables': 0,
            'columns': 0,
            'labeled': 0
        }
        
        with manager.get_client() as client:
            datasets = list(client.list_datasets(project=project_id))
            print(f"Found {len(datasets)} datasets")
            
            for dataset in datasets:
                dataset_id = dataset.dataset_id if hasattr(dataset, 'dataset_id') else str(dataset).split('.')[-1]
                print(f"\n  📂 Dataset: {dataset_id}")
                
                try:
                    tables = list(client.list_tables(f"{project_id}.{dataset_id}"))
                    print(f"    Found {len(tables)} tables")
                    
                    for table_ref in tables:
                        table_id = table_ref.table_id if hasattr(table_ref, 'table_id') else str(table_ref).split('.')[-1]
                        table_path = f"{project_id}.{dataset_id}.{table_id}"
                        
                        labels = self._label_table_automatically(client, table_path)
                        
                        if labels:
                            project_stats['tables'] += 1
                            project_stats['columns'] += len(labels)
                            project_stats['labeled'] += len([l for l in labels.values() if l != 'unknown'])
                            
                            self.statistics['total_tables'] += 1
                            self.statistics['total_columns'] += len(labels)
                            self.statistics['labeled_columns'] += len([l for l in labels.values() if l != 'unknown'])
                            self.statistics['tables_processed'].append(table_path)
                    
                    project_stats['datasets'] += 1
                    
                except Exception as e:
                    logger.error(f"    ❌ Failed to process dataset {dataset_id}: {e}")
        
        print(f"\n📊 Project {project_id} Statistics:")
        print(f"  Datasets: {project_stats['datasets']}")
        print(f"  Tables: {project_stats['tables']}")
        print(f"  Columns: {project_stats['columns']}")
        print(f"  Labeled: {project_stats['labeled']} ({project_stats['labeled']/project_stats['columns']*100:.1f}%)")
    
    def _label_table_automatically(self, client, table_path: str) -> Dict[str, str]:
        try:
            table = client.get_table(table_path)
            
            if table.num_rows == 0:
                logger.debug(f"      Skipping empty table: {table_path}")
                return {}
            
            columns = [field.name for field in table.schema]
            
            print(f"      📊 {table_path.split('.')[-1]}: {len(columns)} columns, {table.num_rows:,} rows")
            
            query = f"""
            SELECT *
            FROM `{table_path}`
            LIMIT 10
            """
            
            try:
                query_job = client.query(query)
                results = list(query_job.result(timeout=30))
            except:
                results = []
            
            table_labels = {}
            labeled_count = 0
            
            for column in columns:
                label = self._classify_column(column, results, table_path)
                table_labels[column] = label
                
                if label != 'unknown':
                    labeled_count += 1
                    
                    self.labeled_columns['patterns'][label].append({
                        'column': column,
                        'table': table_path,
                        'sample': results[0].__dict__.get(column) if results else None
                    })
            
            self.labeled_columns['columns'][table_path] = table_labels
            
            self.labeled_columns['labeling_history'].append({
                'table': table_path,
                'labels': table_labels,
                'timestamp': datetime.now().isoformat(),
                'rows': table.num_rows,
                'labeled_ratio': labeled_count / len(columns) if columns else 0
            })
            
            print(f"        ✓ Labeled {labeled_count}/{len(columns)} columns")
            
            return table_labels
            
        except Exception as e:
            logger.error(f"      ❌ Failed to label table {table_path}: {e}")
            return {}
    
    def _classify_column(self, column_name: str, sample_rows: List[Any], table_path: str) -> str:
        column_lower = column_name.lower()
        
        for col_type, patterns in self.column_types.items():
            for pattern in patterns:
                if pattern in column_lower or column_lower == pattern:
                    return col_type
                
                if column_lower.replace('_', '') == pattern.replace('_', ''):
                    return col_type
                
                if column_lower.startswith(pattern.split('_')[0]):
                    if len(pattern.split('_')) > 1 and pattern.split('_')[1] in column_lower:
                        return col_type
        
        if sample_rows:
            samples = [getattr(row, column_name, None) for row in sample_rows[:5]]
            non_null_samples = [s for s in samples if s is not None]
            
            if non_null_samples:
                sample_str = str(non_null_samples[0])
                
                if all('.' in str(s) and str(s).count('.') == 3 for s in non_null_samples):
                    if all(self._is_valid_ip(str(s)) for s in non_null_samples):
                        return 'ip_address'
                
                if all(':' in str(s) or '-' in str(s) for s in non_null_samples):
                    if all(len(str(s).replace(':', '').replace('-', '')) == 12 for s in non_null_samples):
                        return 'mac_address'
                
                if all(self._looks_like_hostname(str(s)) for s in non_null_samples):
                    return 'host'
                
                if all(str(s).lower() in ['true', 'false', '0', '1', 'yes', 'no'] for s in non_null_samples):
                    if any(security in column_lower for security in ['edr', 'tanium', 'dlp', 'splunk', 'gso']):
                        for col_type, patterns in self.column_types.items():
                            if any(p in column_lower for p in patterns):
                                return col_type
        
        if 'timestamp' in column_lower or 'time' in column_lower or 'date' in column_lower:
            if 'created' in column_lower:
                return 'created_date'
            elif 'modified' in column_lower or 'updated' in column_lower:
                return 'modified_date'
            elif 'patch' in column_lower:
                return 'last_patch_date'
        
        return 'unknown'
    
    def _is_valid_ip(self, value: str) -> bool:
        parts = value.split('.')
        if len(parts) != 4:
            return False
        try:
            return all(0 <= int(part) <= 255 for part in parts)
        except:
            return False
    
    def _looks_like_hostname(self, value: str) -> bool:
        if not value or len(value) < 2:
            return False
        
        if '.' in value and value.count('.') >= 1:
            return True
        
        if '-' in value and any(c.isalpha() for c in value):
            return True
        
        if value.replace('-', '').replace('_', '').replace('.', '').isalnum():
            if any(c.isalpha() for c in value):
                return True
        
        return False
    
    def _train_model(self):
        print("\n🧠 Training column classification model...")
        
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import classification_report
        
        X = []
        y = []
        
        for table_path, table_labels in self.labeled_columns['columns'].items():
            for column, label in table_labels.items():
                if label != 'unknown':
                    features = self._extract_features(column)
                    X.append(features)
                    y.append(label)
        
        if len(set(y)) < 2 or len(X) < 10:
            print("Not enough labeled data to train model")
            return
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        classifier = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42)
        classifier.fit(X_train, y_train)
        
        train_score = classifier.score(X_train, y_train)
        test_score = classifier.score(X_test, y_test)
        
        print(f"✅ Model trained on {len(X_train)} examples")
        print(f"📊 Training accuracy: {train_score:.2%}")
        print(f"📊 Test accuracy: {test_score:.2%}")
        
        model_data = {
            'classifier': classifier,
            'feature_extractor': self._extract_features,
            'column_types': list(set(y)),
            'training_size': len(X_train),
            'test_score': test_score
        }
        
        with open(self.model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"💾 Model saved to {self.model_path}")
    
    def _extract_features(self, column_name: str) -> List[float]:
        features = []
        column_lower = column_name.lower()
        
        features.append(len(column_name))
        features.append(1 if '_' in column_name else 0)
        features.append(1 if '-' in column_name else 0)
        features.append(column_name.count('_'))
        features.append(1 if column_name[0].isupper() else 0)
        features.append(1 if column_name.isupper() else 0)
        features.append(1 if any(c.isdigit() for c in column_name) else 0)
        
        for keyword in ['host', 'ip', 'address', 'name', 'type', 'status', 'date', 'time', 
                       'id', 'coverage', 'logging', 'region', 'env', 'domain']:
            features.append(1 if keyword in column_lower else 0)
        
        features.append(1 if column_lower.startswith('is_') else 0)
        features.append(1 if column_lower.startswith('has_') else 0)
        features.append(1 if column_lower.endswith('_id') else 0)
        features.append(1 if column_lower.endswith('_at') else 0)
        features.append(1 if column_lower.endswith('_date') else 0)
        features.append(1 if column_lower.endswith('_time') else 0)
        
        return features
    
    def _print_final_statistics(self, total_time: float):
        print("\n" + "="*80)
        print("LABELING COMPLETE")
        print("="*80)
        print(f"Total time: {total_time:.1f} seconds")
        print(f"Tables processed: {self.statistics['total_tables']}")
        print(f"Columns analyzed: {self.statistics['total_columns']}")
        print(f"Columns labeled: {self.statistics['labeled_columns']}")
        print(f"Labeling accuracy: {self.statistics['labeled_columns']/self.statistics['total_columns']*100:.1f}%")
        
        print("\nColumn type distribution:")
        type_counts = defaultdict(int)
        for table_labels in self.labeled_columns['columns'].values():
            for label in table_labels.values():
                type_counts[label] += 1
        
        for col_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:20]:
            print(f"  {col_type:30} {count:6} ({count/self.statistics['total_columns']*100:5.1f}%)")
        
        self.labeled_columns['statistics'] = {
            'total_tables': self.statistics['total_tables'],
            'total_columns': self.statistics['total_columns'],
            'labeled_columns': self.statistics['labeled_columns'],
            'processing_time': total_time,
            'projects': self.project_ids,
            'type_distribution': dict(type_counts)
        }

def main():
    labeler = AutomaticCompleteLabeler()
    labeler.label_all_tables_automatically()
    
    print("\n✅ All tables in both projects have been labeled and saved.")
    print(f"📁 Results saved to: complete_labeled_columns.json")
    print(f"🧠 Model saved to: complete_column_classifier.pkl")

if __name__ == "__main__":
    main()