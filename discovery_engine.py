# discovery_engine.py
"""
intelligent discovery engine that reads bigquery tables and identifies all column meanings
uses trained ml models to understand data and build comprehensive asset visibility database
designed specifically for ao1 log visibility measurement requirements
"""

import os
import sys
import logging
import json
import asyncio
import duckdb
import pandas as pd
import numpy as np
from google.cloud import bigquery
from google.auth import default
from google.auth.transport.requests import Request
import google.auth.transport.urllib3
import urllib3
import certifi
from typing import Dict, List, Tuple, Optional, Any, Set
from datetime import datetime
from pathlib import Path
import hashlib
import joblib
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
import re
from tqdm import tqdm
import torch
from sentence_transformers import SentenceTransformer

# configure for corporate proxy
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
os.environ['CURL_CA_BUNDLE'] = certifi.where()

logger = logging.getLogger(__name__)

@dataclass
class AssetRecord:
    """
    represents a unique asset with all 17 required visibility attributes
    maps directly to ao1 measurement requirements
    """
    # requirement 1: unique hostname identifier
    hostname: str
    
    # requirement 2: infrastructure type
    infrastructure_type: str = ""  # on_premise, cloud, saas, api
    
    # requirement 3: region
    region: str = ""  # na, latam, apac, europe
    
    # requirement 4: country
    country: str = ""
    
    # requirement 5: business unit
    business_unit: str = ""  # fig, bank solutions, credit union solutions
    
    # requirement 6: data center
    datacenter: str = ""
    
    # requirement 7: cloud region
    cloud_region: str = ""
    
    # requirement 8: cio organization
    cio: str = ""
    
    # requirement 9: apm
    apm: str = ""
    
    # requirement 10: application class
    application_class: str = ""
    
    # requirement 11: system classification
    system_classification: str = ""  # web server, windows, linux, nix, mainframe
    
    # requirement 12: edr coverage
    edr_coverage: bool = False
    
    # requirement 13: tanium coverage  
    tanium_coverage: bool = False
    
    # requirement 14: dlp agent coverage
    dlp_coverage: bool = False
    
    # requirement 15: splunk logging verification
    splunk_coverage: bool = False
    
    # requirement 16: domain
    domain: str = ""
    
    # additional visibility attributes
    chronicle_coverage: bool = False
    crowdstrike_coverage: bool = False
    ip_address: str = ""
    mac_address: str = ""
    owner: str = ""
    criticality: str = ""
    environment: str = ""
    
    # metadata for tracking
    source_tables: Set[str] = field(default_factory=set)
    confidence_score: float = 0.0
    last_seen: datetime = field(default_factory=datetime.now)
    data_quality_score: float = 0.0

class BigQueryIntelligentReader:
    """
    reads bigquery tables intelligently using ml to understand column meanings
    core component for meeting visibility measurement requirements
    """
    
    def __init__(self, project_id: str, model_dir: str = "trained_models"):
        """
        initialize with bigquery client and trained ml models
        uses corporate proxy configuration for connectivity
        """
        self.project_id = project_id
        self.model_dir = Path(model_dir)
        
        # initialize bigquery client with proxy support
        self.client = self._init_bigquery_client()
        
        # load trained ml models for column identification
        self.models = self._load_trained_models()
        
        # initialize sentence transformer for semantic understanding
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # cache for processed tables
        self.table_cache = {}
        self.column_mappings = {}
        
        logger.info(f"initialized bigquery reader for project: {project_id}")
    
    def _init_bigquery_client(self) -> bigquery.Client:
        """
        initializes bigquery client with corporate proxy configuration
        handles authentication and network settings for enterprise environment
        """
        try:
            # get default credentials
            credentials, project = default()
            
            # configure http client with proxy
            http = urllib3.PoolManager(
                cert_reqs='CERT_REQUIRED',
                ca_certs=certifi.where(),
                timeout=urllib3.Timeout(connect=10.0, read=30.0)
            )
            
            # check for proxy environment variables
            http_proxy = os.environ.get('HTTP_PROXY', os.environ.get('http_proxy'))
            https_proxy = os.environ.get('HTTPS_PROXY', os.environ.get('https_proxy'))
            
            if http_proxy or https_proxy:
                # create proxy-aware http client
                proxy_url = https_proxy or http_proxy
                http = urllib3.ProxyManager(
                    proxy_url,
                    cert_reqs='CERT_REQUIRED',
                    ca_certs=certifi.where()
                )
                logger.info(f"using proxy: {proxy_url}")
            
            # create authenticated http client
            authed_http = google.auth.transport.urllib3.AuthorizedHttp(
                credentials, http=http
            )
            
            # create bigquery client
            client = bigquery.Client(
                project=self.project_id,
                credentials=credentials,
                _http=authed_http
            )
            
            logger.info("bigquery client initialized successfully")
            return client
            
        except Exception as e:
            logger.error(f"failed to initialize bigquery client: {e}")
            # try without proxy as fallback
            return bigquery.Client(project=self.project_id)
    
    def _load_trained_models(self) -> Dict[str, Any]:
        """
        loads ml models trained on infrastructure datasets
        these models understand what each column type means
        """
        models = {}
        
        if not self.model_dir.exists():
            logger.warning(f"model directory not found: {self.model_dir}")
            return models
        
        # load models for each column requirement
        model_files = [
            'hostname_model.pkl',
            'infrastructure_type_model.pkl',
            'region_model.pkl',
            'business_unit_model.pkl',
            'system_classification_model.pkl',
            'edr_coverage_model.pkl',
            'tanium_coverage_model.pkl',
            'dlp_coverage_model.pkl',
            'splunk_coverage_model.pkl',
            'domain_model.pkl'
        ]
        
        for model_file in model_files:
            model_path = self.model_dir / model_file
            if model_path.exists():
                try:
                    model = joblib.load(model_path)
                    model_name = model_file.replace('_model.pkl', '')
                    models[model_name] = model
                    logger.info(f"loaded model: {model_name}")
                except Exception as e:
                    logger.warning(f"failed to load model {model_file}: {e}")
        
        return models
    
    async def discover_all_assets(self) -> Dict[str, AssetRecord]:
        """
        discovers all unique assets across all bigquery tables
        main function for building comprehensive visibility database
        """
        logger.info("starting comprehensive asset discovery across bigquery")
        
        all_assets = {}
        
        # get all datasets in project
        datasets = list(self.client.list_datasets())
        logger.info(f"found {len(datasets)} datasets to analyze")
        
        # process each dataset
        for dataset in tqdm(datasets, desc="analyzing datasets"):
            try:
                assets = await self._process_dataset(dataset)
                
                # merge discovered assets
                for hostname, asset in assets.items():
                    if hostname in all_assets:
                        # merge data from multiple sources
                        all_assets[hostname] = self._merge_assets(all_assets[hostname], asset)
                    else:
                        all_assets[hostname] = asset
                        
            except Exception as e:
                logger.error(f"failed to process dataset {dataset.dataset_id}: {e}")
        
        logger.info(f"discovered {len(all_assets)} unique assets")
        return all_assets
    
    async def _process_dataset(self, dataset) -> Dict[str, AssetRecord]:
        """
        processes all tables in a dataset to find assets
        uses ml to understand what each column contains
        """
        assets = {}
        
        # get all tables in dataset
        tables = list(self.client.list_tables(dataset))
        logger.info(f"processing {len(tables)} tables in {dataset.dataset_id}")
        
        # process tables in parallel for speed
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            
            for table in tables:
                future = executor.submit(
                    self._analyze_table,
                    f"{self.project_id}.{dataset.dataset_id}.{table.table_id}"
                )
                futures.append(future)
            
            # collect results
            for future in as_completed(futures):
                try:
                    table_assets = future.result()
                    
                    # merge table assets
                    for hostname, asset in table_assets.items():
                        if hostname in assets:
                            assets[hostname] = self._merge_assets(assets[hostname], asset)
                        else:
                            assets[hostname] = asset
                            
                except Exception as e:
                    logger.error(f"table analysis failed: {e}")
        
        return assets
    
    def _analyze_table(self, table_path: str) -> Dict[str, AssetRecord]:
        """
        analyzes a single table to extract asset information
        uses ml models to identify what each column represents
        """
        assets = {}
        
        try:
            # get table schema
            table = self.client.get_table(table_path)
            
            if table.num_rows == 0:
                return assets
            
            # identify column types using ml
            column_mappings = self._identify_column_types(table)
            
            # check if table has hostname column (requirement 1)
            if 'hostname' not in column_mappings:
                logger.debug(f"no hostname column found in {table_path}")
                return assets
            
            # query table to extract assets
            hostname_col = column_mappings['hostname']
            
            # build query to get all relevant columns
            select_columns = [f"`{hostname_col}` as hostname"]
            
            # add other identified columns
            column_mapping_reverse = {}
            for col_type, col_name in column_mappings.items():
                if col_type != 'hostname':
                    safe_alias = col_type.replace(' ', '_')
                    select_columns.append(f"`{col_name}` as {safe_alias}")
                    column_mapping_reverse[safe_alias] = col_type
            
            # query with sampling for large tables
            if table.num_rows > 1000000:
                query = f"""
                select distinct {', '.join(select_columns)}
                from `{table_path}`
                where `{hostname_col}` is not null
                and rand() < 0.1
                limit 100000
                """
            else:
                query = f"""
                select distinct {', '.join(select_columns)}
                from `{table_path}`
                where `{hostname_col}` is not null
                limit 500000
                """
            
            # execute query
            query_job = self.client.query(query)
            results = query_job.result()
            
            # process results into assets
            for row in results:
                hostname = row.hostname
                
                if not hostname or not self._is_valid_hostname(hostname):
                    continue
                
                # create or update asset record
                if hostname not in assets:
                    assets[hostname] = AssetRecord(hostname=hostname)
                
                asset = assets[hostname]
                
                # update asset fields based on identified columns
                for field_name in column_mapping_reverse:
                    value = getattr(row, field_name, None)
                    if value:
                        self._update_asset_field(asset, column_mapping_reverse[field_name], value)
                
                # track source table
                asset.source_tables.add(table_path)
                
                # determine coverage flags based on table name
                self._infer_coverage_from_table(asset, table_path)
            
            logger.info(f"found {len(assets)} assets in {table_path}")
            
        except Exception as e:
            logger.error(f"failed to analyze table {table_path}: {e}")
        
        return assets
    
    def _identify_column_types(self, table) -> Dict[str, str]:
        """
        uses ml models to identify what each column represents
        maps columns to the 17 visibility requirements
        """
        column_mappings = {}
        
        # get sample data for analysis
        sample_query = f"""
        select * from `{table.project}.{table.dataset_id}.{table.table_id}`
        limit 100
        """
        
        try:
            sample_df = self.client.query(sample_query).to_dataframe()
            
            for column in sample_df.columns:
                # get sample values
                sample_values = sample_df[column].dropna().astype(str).tolist()[:10]
                
                if not sample_values:
                    continue
                
                # identify column type using ml
                column_type = self._predict_column_type(column, sample_values)
                
                if column_type and column_type != 'unknown':
                    column_mappings[column_type] = column
                    logger.debug(f"identified column '{column}' as '{column_type}'")
            
        except Exception as e:
            logger.warning(f"failed to sample table for ml analysis: {e}")
            # fall back to schema-based identification
            column_mappings = self._identify_columns_by_name(table.schema)
        
        return column_mappings
    
    def _predict_column_type(self, column_name: str, sample_values: List[str]) -> str:
        """
        uses trained ml models to predict column type
        determines which of the 17 requirements the column represents
        """
        # first try pattern-based identification for common patterns
        column_lower = column_name.lower()
        
        # direct mapping for obvious columns
        direct_mappings = {
            'hostname': ['hostname', 'host_name', 'computer_name', 'device_name', 'server_name'],
            'infrastructure_type': ['infrastructure_type', 'infra_type', 'hosting_type', 'platform_type'],
            'region': ['region', 'global_region', 'geo_region', 'geographic_region'],
            'country': ['country', 'country_code', 'country_name', 'nation'],
            'business_unit': ['business_unit', 'bu', 'business_division', 'org_unit'],
            'datacenter': ['datacenter', 'data_center', 'dc', 'site', 'facility'],
            'cloud_region': ['cloud_region', 'aws_region', 'azure_region', 'gcp_region'],
            'cio': ['cio', 'cio_org', 'it_org', 'technology_org'],
            'apm': ['apm', 'app_performance', 'application_monitoring'],
            'application_class': ['application_class', 'app_class', 'app_type', 'application_type'],
            'system_classification': ['system_class', 'os_type', 'platform', 'system_type'],
            'domain': ['domain', 'ad_domain', 'dns_domain', 'active_directory']
        }
        
        for col_type, keywords in direct_mappings.items():
            for keyword in keywords:
                if keyword in column_lower:
                    return col_type
        
        # check for coverage columns
        if 'edr' in column_lower or 'endpoint_detection' in column_lower:
            return 'edr_coverage'
        if 'tanium' in column_lower:
            return 'tanium_coverage'
        if 'dlp' in column_lower or 'data_loss' in column_lower:
            return 'dlp_coverage'
        if 'splunk' in column_lower or 'logging' in column_lower:
            return 'splunk_coverage'
        if 'crowdstrike' in column_lower or 'falcon' in column_lower:
            return 'crowdstrike_coverage'
        if 'chronicle' in column_lower:
            return 'chronicle_coverage'
        
        # use ml models if available
        if self.models:
            # combine column name and sample values for prediction
            text_features = f"{column_name} {' '.join(sample_values)}"
            
            # try each model
            best_match = None
            best_score = 0.0
            
            for model_name, model in self.models.items():
                try:
                    # models expect specific feature format
                    # this would use the feature extraction from training
                    score = self._get_model_prediction_score(model, text_features)
                    
                    if score > best_score:
                        best_score = score
                        best_match = model_name
                        
                except Exception as e:
                    logger.debug(f"model prediction failed for {model_name}: {e}")
            
            if best_match and best_score > 0.7:
                return best_match
        
        # use semantic similarity as fallback
        return self._semantic_column_matching(column_name, sample_values)
    
    def _semantic_column_matching(self, column_name: str, sample_values: List[str]) -> str:
        """
        uses sentence transformers for semantic understanding of columns
        matches column content to known infrastructure concepts
        """
        try:
            # create embedding for column
            column_text = f"{column_name} {' '.join(sample_values[:5])}"
            column_embedding = self.sentence_model.encode(column_text)
            
            # known concept embeddings
            concepts = {
                'hostname': 'hostname server computer device machine name',
                'infrastructure_type': 'infrastructure cloud onpremise saas platform type',
                'region': 'region geographic area zone location continent',
                'business_unit': 'business unit department division organization group',
                'system_classification': 'system windows linux unix mainframe server database'
            }
            
            best_match = None
            best_similarity = 0.0
            
            for concept, description in concepts.items():
                concept_embedding = self.sentence_model.encode(description)
                
                # calculate cosine similarity
                similarity = np.dot(column_embedding, concept_embedding) / (
                    np.linalg.norm(column_embedding) * np.linalg.norm(concept_embedding)
                )
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = concept
            
            if best_similarity > 0.6:
                return best_match
                
        except Exception as e:
            logger.debug(f"semantic matching failed: {e}")
        
        return 'unknown'
    
    def _is_valid_hostname(self, hostname: str) -> bool:
        """
        validates if a string is a valid hostname
        filters out invalid entries to ensure data quality
        """
        if not hostname or len(hostname) < 2 or len(hostname) > 253:
            return False
        
        # check for invalid characters
        if any(char in hostname for char in ['@', '/', '\\', ' ', '\t', '\n', '|', ';']):
            return False
        
        # check for placeholder values
        invalid_values = ['null', 'none', 'unknown', 'n/a', 'test', 'example', 'localhost']
        if hostname.lower() in invalid_values:
            return False
        
        # basic hostname pattern
        hostname_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        
        return bool(re.match(hostname_pattern, hostname, re.IGNORECASE))
    
    def _update_asset_field(self, asset: AssetRecord, field_type: str, value: Any):
        """
        updates asset record field based on identified column type
        handles data type conversions and validations
        """
        if not value:
            return
        
        # convert value to string for processing
        value_str = str(value).strip()
        
        # update based on field type
        if field_type == 'infrastructure_type':
            asset.infrastructure_type = self._normalize_infrastructure_type(value_str)
        elif field_type == 'region':
            asset.region = self._normalize_region(value_str)
        elif field_type == 'country':
            asset.country = value_str[:100]  # limit length
        elif field_type == 'business_unit':
            asset.business_unit = value_str[:100]
        elif field_type == 'datacenter':
            asset.datacenter = value_str[:100]
        elif field_type == 'cloud_region':
            asset.cloud_region = value_str[:100]
        elif field_type == 'cio':
            asset.cio = value_str[:100]
        elif field_type == 'apm':
            asset.apm = value_str[:100]
        elif field_type == 'application_class':
            asset.application_class = value_str[:100]
        elif field_type == 'system_classification':
            asset.system_classification = self._normalize_system_class(value_str)
        elif field_type == 'domain':
            asset.domain = value_str[:100]
        elif field_type in ['edr_coverage', 'tanium_coverage', 'dlp_coverage', 'splunk_coverage',
                           'chronicle_coverage', 'crowdstrike_coverage']:
            # handle boolean coverage fields
            coverage_value = self._parse_boolean(value_str)
            setattr(asset, field_type, coverage_value)
    
    def _normalize_infrastructure_type(self, value: str) -> str:
        """
        normalizes infrastructure type to standard values
        requirement 2: on_premise, cloud, saas, api
        """
        value_lower = value.lower()
        
        if any(term in value_lower for term in ['cloud', 'aws', 'azure', 'gcp']):
            return 'cloud'
        elif any(term in value_lower for term in ['onprem', 'on-prem', 'physical', 'datacenter']):
            return 'on_premise'
        elif any(term in value_lower for term in ['saas', 'software as a service']):
            return 'saas'
        elif any(term in value_lower for term in ['api', 'endpoint', 'service']):
            return 'api'
        else:
            return value[:50]  # return original if can't normalize
    
    def _normalize_region(self, value: str) -> str:
        """
        normalizes region to standard values
        requirement 3: na, latam, apac, europe
        """
        value_lower = value.lower()
        
        if any(term in value_lower for term in ['na', 'north america', 'us', 'usa', 'canada']):
            return 'na'
        elif any(term in value_lower for term in ['latam', 'latin', 'south america', 'brazil']):
            return 'latam'
        elif any(term in value_lower for term in ['apac', 'asia', 'pacific', 'japan', 'china']):
            return 'apac'
        elif any(term in value_lower for term in ['europe', 'emea', 'eu', 'uk']):
            return 'europe'
        else:
            return value[:50]
    
    def _normalize_system_class(self, value: str) -> str:
        """
        normalizes system classification to standard values
        requirement 12: web server, windows server, linux server, nix, mainframe, database, network appliance
        """
        value_lower = value.lower()
        
        if any(term in value_lower for term in ['web', 'apache', 'nginx', 'iis']):
            return 'web_server'
        elif any(term in value_lower for term in ['windows', 'win', 'microsoft']):
            return 'windows_server'
        elif any(term in value_lower for term in ['linux', 'ubuntu', 'redhat', 'centos']):
            return 'linux_server'
        elif any(term in value_lower for term in ['aix', 'solaris', 'unix', 'nix']):
            return 'nix'
        elif any(term in value_lower for term in ['mainframe', 'zos', 'mvs']):
            return 'mainframe'
        elif any(term in value_lower for term in ['database', 'sql', 'oracle', 'postgres']):
            return 'database'
        elif any(term in value_lower for term in ['network', 'router', 'switch', 'firewall']):
            return 'network_appliance'
        else:
            return value[:50]
    
    def _parse_boolean(self, value: str) -> bool:
        """
        parses boolean values for coverage fields
        handles various representations of true/false
        """
        value_lower = value.lower()
        true_values = ['true', 'yes', '1', 'enabled', 'active', 'installed', 'running']
        return any(term in value_lower for term in true_values)
    
    def _infer_coverage_from_table(self, asset: AssetRecord, table_path: str):
        """
        infers security tool coverage based on table source
        helps identify which tools are monitoring each asset
        """
        table_lower = table_path.lower()
        
        # check for security tool indicators in table name
        if 'edr' in table_lower or 'endpoint_detection' in table_lower:
            asset.edr_coverage = True
        if 'tanium' in table_lower:
            asset.tanium_coverage = True
        if 'dlp' in table_lower:
            asset.dlp_coverage = True
        if 'splunk' in table_lower:
            asset.splunk_coverage = True
        if 'chronicle' in table_lower:
            asset.chronicle_coverage = True
        if 'crowdstrike' in table_lower:
            asset.crowdstrike_coverage = True
    
    def _merge_assets(self, asset1: AssetRecord, asset2: AssetRecord) -> AssetRecord:
        """
        merges data from multiple sources for the same asset
        combines information to build complete visibility picture
        """
        # start with asset1 as base
        merged = asset1
        
        # merge string fields - prefer non-empty values
        string_fields = [
            'infrastructure_type', 'region', 'country', 'business_unit',
            'datacenter', 'cloud_region', 'cio', 'apm', 'application_class',
            'system_classification', 'domain', 'ip_address', 'mac_address',
            'owner', 'criticality', 'environment'
        ]
        
        for field in string_fields:
            value1 = getattr(asset1, field, '')
            value2 = getattr(asset2, field, '')
            if not value1 and value2:
                setattr(merged, field, value2)
        
        # merge boolean fields - true takes precedence
        boolean_fields = [
            'edr_coverage', 'tanium_coverage', 'dlp_coverage', 'splunk_coverage',
            'chronicle_coverage', 'crowdstrike_coverage'
        ]
        
        for field in boolean_fields:
            value1 = getattr(asset1, field, False)
            value2 = getattr(asset2, field, False)
            setattr(merged, field, value1 or value2)
        
        # merge source tables
        merged.source_tables = asset1.source_tables.union(asset2.source_tables)
        
        # update confidence and quality scores
        merged.confidence_score = max(asset1.confidence_score, asset2.confidence_score)
        merged.data_quality_score = self._calculate_data_quality(merged)
        
        return merged
    
    def _calculate_data_quality(self, asset: AssetRecord) -> float:
        """
        calculates data quality score based on completeness
        helps identify assets needing additional data enrichment
        """
        total_fields = 17  # number of required fields
        filled_fields = 0
        
        # check each required field
        if asset.hostname:
            filled_fields += 1
        if asset.infrastructure_type:
            filled_fields += 1
        if asset.region:
            filled_fields += 1
        if asset.country:
            filled_fields += 1
        if asset.business_unit:
            filled_fields += 1
        if asset.datacenter:
            filled_fields += 1
        if asset.cloud_region:
            filled_fields += 1
        if asset.cio:
            filled_fields += 1
        if asset.apm:
            filled_fields += 1
        if asset.application_class:
            filled_fields += 1
        if asset.system_classification:
            filled_fields += 1
        if asset.domain:
            filled_fields += 1
        
        # coverage fields count as filled if explicitly set
        if asset.edr_coverage or hasattr(asset, '_edr_checked'):
            filled_fields += 1
        if asset.tanium_coverage or hasattr(asset, '_tanium_checked'):
            filled_fields += 1
        if asset.dlp_coverage or hasattr(asset, '_dlp_checked'):
            filled_fields += 1
        if asset.splunk_coverage or hasattr(asset, '_splunk_checked'):
            filled_fields += 1
        
        # add source table count to quality
        source_bonus = min(len(asset.source_tables) / 10, 0.2)
        
        quality_score = (filled_fields / total_fields) + source_bonus
        return min(quality_score, 1.0)
    
    def _identify_columns_by_name(self, schema) -> Dict[str, str]:
        """
        fallback method to identify columns by name patterns
        used when ml models are not available or sampling fails
        """
        column_mappings = {}
        
        for field in schema:
            field_name = field.name.lower()
            
            # check for hostname patterns
            if any(term in field_name for term in ['hostname', 'host_name', 'computer', 'device', 'server']):
                if 'hostname' not in column_mappings:
                    column_mappings['hostname'] = field.name
            
            # check for other required fields
            elif 'infrastructure' in field_name or 'infra_type' in field_name:
                column_mappings['infrastructure_type'] = field.name
            elif 'region' in field_name and 'cloud' not in field_name:
                column_mappings['region'] = field.name
            elif 'country' in field_name:
                column_mappings['country'] = field.name
            elif 'business' in field_name or 'bu' == field_name:
                column_mappings['business_unit'] = field.name
            elif 'datacenter' in field_name or 'data_center' in field_name or 'dc' == field_name:
                column_mappings['datacenter'] = field.name
            elif 'cloud_region' in field_name:
                column_mappings['cloud_region'] = field.name
            elif 'cio' in field_name:
                column_mappings['cio'] = field.name
            elif 'apm' in field_name:
                column_mappings['apm'] = field.name
            elif 'application' in field_name and 'class' in field_name:
                column_mappings['application_class'] = field.name
            elif 'system' in field_name and ('class' in field_name or 'type' in field_name):
                column_mappings['system_classification'] = field.name
            elif 'domain' in field_name and 'cloud' not in field_name:
                column_mappings['domain'] = field.name
            elif 'edr' in field_name:
                column_mappings['edr_coverage'] = field.name
            elif 'tanium' in field_name:
                column_mappings['tanium_coverage'] = field.name
            elif 'dlp' in field_name:
                column_mappings['dlp_coverage'] = field.name
            elif 'splunk' in field_name:
                column_mappings['splunk_coverage'] = field.name
        
        return column_mappings

class DuckDBAssetDatabase:
    """
    creates and manages duckdb database for discovered assets
    provides fast analytical queries for visibility reporting
    """
    
    def __init__(self, db_path: str = "asset_visibility.duckdb"):
        """
        initializes duckdb database with schema for all visibility requirements
        creates tables optimized for ao1 measurement queries
        """
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)
        
        # create main assets table with all required columns
        self._create_schema()
        
        logger.info(f"initialized duckdb database: {db_path}")
    
    def _create_schema(self):
        """
        creates database schema matching all 17 visibility requirements
        optimized for fast aggregation and filtering queries
        """
        # drop existing table if exists
        self.conn.execute("drop table if exists assets")
        
        # create assets table with all required columns
        self.conn.execute("""
            create table assets (
                -- requirement 1: unique hostname
                hostname varchar primary key,
                
                -- requirement 2: infrastructure type
                infrastructure_type varchar,
                
                -- requirement 3: region
                region varchar,
                
                -- requirement 4: country
                country varchar,
                
                -- requirement 5: business unit
                business_unit varchar,
                
                -- requirement 6: data center
                datacenter varchar,
                
                -- requirement 7: cloud region
                cloud_region varchar,
                
                -- requirement 8: cio organization
                cio varchar,
                
                -- requirement 9: apm
                apm varchar,
                
                -- requirement 10: application class
                application_class varchar,
                
                -- requirement 11: system classification
                system_classification varchar,
                
                -- requirement 12: edr coverage
                edr_coverage boolean,
                
                -- requirement 13: tanium coverage
                tanium_coverage boolean,
                
                -- requirement 14: dlp coverage
                dlp_coverage boolean,
                
                -- requirement 15: splunk coverage
                splunk_coverage boolean,
                
                -- requirement 16: domain
                domain varchar,
                
                -- additional visibility fields
                chronicle_coverage boolean,
                crowdstrike_coverage boolean,
                ip_address varchar,
                mac_address varchar,
                owner varchar,
                criticality varchar,
                environment varchar,
                
                -- metadata fields
                source_tables varchar[],
                confidence_score double,
                data_quality_score double,
                last_seen timestamp,
                created_at timestamp default current_timestamp
            )
        """)
        
        # create indexes for common query patterns
        self.conn.execute("create index idx_infrastructure on assets(infrastructure_type)")
        self.conn.execute("create index idx_region on assets(region)")
        self.conn.execute("create index idx_business_unit on assets(business_unit)")
        self.conn.execute("create index idx_edr on assets(edr_coverage)")
        self.conn.execute("create index idx_splunk on assets(splunk_coverage)")
        
        logger.info("database schema created successfully")
    
    def insert_assets(self, assets: Dict[str, AssetRecord]):
        """
        inserts discovered assets into database
        handles bulk inserts for performance
        """
        if not assets:
            return
        
        # prepare data for bulk insert
        rows = []
        for hostname, asset in assets.items():
            row = (
                asset.hostname,
                asset.infrastructure_type,
                asset.region,
                asset.country,
                asset.business_unit,
                asset.datacenter,
                asset.cloud_region,
                asset.cio,
                asset.apm,
                asset.application_class,
                asset.system_classification,
                asset.edr_coverage,
                asset.tanium_coverage,
                asset.dlp_coverage,
                asset.splunk_coverage,
                asset.domain,
                asset.chronicle_coverage,
                asset.crowdstrike_coverage,
                asset.ip_address,
                asset.mac_address,
                asset.owner,
                asset.criticality,
                asset.environment,
                list(asset.source_tables),
                asset.confidence_score,
                asset.data_quality_score,
                asset.last_seen
            )
            rows.append(row)
        
        # bulk insert
        self.conn.executemany("""
            insert or replace into assets values (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        """, rows)
        
        logger.info(f"inserted {len(rows)} assets into database")
    
    def get_visibility_metrics(self) -> Dict[str, Any]:
        """
        calculates visibility metrics for ao1 requirements
        provides coverage percentages and gap analysis
        """
        metrics = {}
        
        # total asset count
        total_assets = self.conn.execute("select count(*) from assets").fetchone()[0]
        metrics['total_assets'] = total_assets
        
        # infrastructure type distribution
        infra_dist = self.conn.execute("""
            select infrastructure_type, count(*) as count
            from assets
            group by infrastructure_type
        """).fetchall()
        metrics['infrastructure_distribution'] = {row[0]: row[1] for row in infra_dist}
        
        # regional distribution
        region_dist = self.conn.execute("""
            select region, count(*) as count
            from assets
            group by region
        """).fetchall()
        metrics['regional_distribution'] = {row[0]: row[1] for row in region_dist}
        
        # security tool coverage
        edr_coverage = self.conn.execute("""
            select count(*) from assets where edr_coverage = true
        """).fetchone()[0]
        metrics['edr_coverage_percentage'] = (edr_coverage / total_assets * 100) if total_assets > 0 else 0
        
        tanium_coverage = self.conn.execute("""
            select count(*) from assets where tanium_coverage = true
        """).fetchone()[0]
        metrics['tanium_coverage_percentage'] = (tanium_coverage / total_assets * 100) if total_assets > 0 else 0
        
        dlp_coverage = self.conn.execute("""
            select count(*) from assets where dlp_coverage = true
        """).fetchone()[0]
        metrics['dlp_coverage_percentage'] = (dlp_coverage / total_assets * 100) if total_assets > 0 else 0
        
        splunk_coverage = self.conn.execute("""
            select count(*) from assets where splunk_coverage = true
        """).fetchone()[0]
        metrics['splunk_coverage_percentage'] = (splunk_coverage / total_assets * 100) if total_assets > 0 else 0
        
        # data quality metrics
        high_quality = self.conn.execute("""
            select count(*) from assets where data_quality_score > 0.8
        """).fetchone()[0]
        metrics['high_quality_assets'] = high_quality
        metrics['data_completeness'] = (high_quality / total_assets * 100) if total_assets > 0 else 0
        
        return metrics
    
    def export_to_csv(self, output_path: str):
        """
        exports database to csv for reporting
        useful for sharing visibility data with stakeholders
        """
        df = self.conn.execute("select * from assets").fetchdf()
        df.to_csv(output_path, index=False)
        logger.info(f"exported {len(df)} assets to {output_path}")
    
    def close(self):
        """
        closes database connection
        ensures data is persisted
        """
        self.conn.close()
        logger.info("database connection closed")

async def main():
    """
    main execution function for asset discovery
    orchestrates the complete discovery and database creation process
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("starting intelligent asset discovery system")
    
    # configuration
    project_id = "your-gcp-project"  # replace with actual project
    
    # initialize bigquery reader
    reader = BigQueryIntelligentReader(project_id)
    
    # discover all assets
    logger.info("discovering assets across all bigquery tables...")
    assets = await reader.discover_all_assets()
    
    # create duckdb database
    db = DuckDBAssetDatabase()
    
    # insert discovered assets
    db.insert_assets(assets)
    
    # calculate and display metrics
    metrics = db.get_visibility_metrics()
    
    logger.info("visibility metrics:")
    logger.info(f"  total assets: {metrics['total_assets']}")
    logger.info(f"  edr coverage: {metrics['edr_coverage_percentage']:.1f}%")
    logger.info(f"  tanium coverage: {metrics['tanium_coverage_percentage']:.1f}%")
    logger.info(f"  dlp coverage: {metrics['dlp_coverage_percentage']:.1f}%")
    logger.info(f"  splunk coverage: {metrics['splunk_coverage_percentage']:.1f}%")
    logger.info(f"  data completeness: {metrics['data_completeness']:.1f}%")
    
    # export results
    db.export_to_csv("asset_visibility_report.csv")
    
    # close database
    db.close()
    
    logger.info("asset discovery completed successfully")

if __name__ == "__main__":
    asyncio.run(main())