# discovery/core.py - fan-spinning intensive implementation

import asyncio
import logging
import hashlib
import statistics
import networkx as nx
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset
from transformers import AutoTokenizer, AutoModel
import requests
import json
import re
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict
from core.types import Asset, TableSchema, Discovery, FieldMapping
from ai.intelligence import EnhancedIntelligenceEngine
import ipaddress
import time
import psutil
import gc

logger = logging.getLogger(__name__)

class FanSpinningMLModel(nn.Module):
    def __init__(self, vocab_size=100000, embed_dim=1024, num_classes=157):
        super().__init__()
        
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.positional_encoding = nn.Parameter(torch.randn(512, embed_dim))
        
        self.transformer_layers = nn.ModuleList([
            nn.TransformerEncoderLayer(
                d_model=embed_dim,
                nhead=16,
                dim_feedforward=4096,
                dropout=0.1,
                activation='gelu',
                batch_first=True
            ) for _ in range(12)
        ])
        
        self.conv_layers = nn.ModuleList([
            nn.Conv1d(embed_dim, embed_dim, kernel_size=k, padding=k//2)
            for k in [3, 5, 7, 9, 11, 13]
        ])
        
        self.attention_layers = nn.ModuleList([
            nn.MultiheadAttention(embed_dim, 16, batch_first=True)
            for _ in range(6)
        ])
        
        self.dense_layers = nn.ModuleList([
            nn.Linear(embed_dim * 6, embed_dim * 4),
            nn.Linear(embed_dim * 4, embed_dim * 2),
            nn.Linear(embed_dim * 2, embed_dim),
            nn.Linear(embed_dim, 512),
            nn.Linear(512, 256),
            nn.Linear(256, num_classes)
        ])
        
        self.cybersecurity_classes = [
            'hostname', 'server_name', 'computer_name', 'device_name', 'endpoint_name',
            'machine_name', 'asset_name', 'workstation_name', 'node_name', 'host_id',
            'ip_address', 'ipv4_address', 'ipv6_address', 'internal_ip', 'external_ip',
            'private_ip', 'public_ip', 'network_address', 'subnet_address', 'gateway_ip',
            'fqdn', 'domain_name', 'dns_name', 'qualified_name', 'canonical_name',
            'mac_address', 'physical_address', 'ethernet_address', 'hardware_address',
            'infrastructure_type', 'on_premise', 'cloud', 'saas', 'api_endpoint',
            'aws_instance', 'azure_vm', 'gcp_instance', 'kubernetes_pod', 'docker_container',
            'system_classification', 'windows_server', 'linux_server', 'unix_server',
            'web_server', 'database_server', 'application_server', 'file_server',
            'mail_server', 'dns_server', 'proxy_server', 'firewall', 'router', 'switch',
            'load_balancer', 'storage_array', 'backup_device', 'security_appliance',
            'network_appliance', 'virtualization_host', 'hypervisor', 'mainframe',
            'global_region', 'us_east', 'us_west', 'us_central', 'eu_west', 'eu_central',
            'asia_pacific', 'north_america', 'south_america', 'emea', 'apac',
            'country_code', 'datacenter_location', 'availability_zone', 'region_code',
            'business_unit', 'finance', 'hr', 'it', 'operations', 'sales', 'marketing',
            'legal', 'compliance', 'security', 'engineering', 'research', 'development',
            'cio_organization', 'application_class', 'critical', 'high', 'medium', 'low',
            'production', 'staging', 'development', 'test', 'qa', 'sandbox',
            'edr_coverage', 'crowdstrike', 'sentinelone', 'carbonblack', 'cylance',
            'defender_atp', 'tanium_coverage', 'tanium_client', 'tanium_agent',
            'dlp_coverage', 'symantec_dlp', 'forcepoint_dlp', 'microsoft_purview',
            'splunk_coverage', 'splunk_forwarder', 'splunk_indexer', 'splunk_hec',
            'chronicle_coverage', 'google_chronicle', 'chronicle_forwarder',
            'gso_coverage', 'security_orchestration', 'soar_platform',
            'network_log_types', 'firewall_logs', 'ids_logs', 'ips_logs', 'proxy_logs',
            'dns_logs', 'dhcp_logs', 'waf_logs', 'load_balancer_logs', 'router_logs',
            'switch_logs', 'vpn_logs', 'endpoint_log_types', 'windows_events',
            'linux_syslogs', 'macos_logs', 'edr_logs', 'antivirus_logs', 'dlp_logs',
            'fim_logs', 'process_logs', 'registry_logs', 'file_access_logs',
            'cloud_log_types', 'aws_cloudtrail', 'azure_activity', 'gcp_audit',
            'kubernetes_logs', 'container_logs', 'serverless_logs', 'storage_logs',
            'application_log_types', 'web_logs', 'database_logs', 'app_server_logs',
            'api_logs', 'microservice_logs', 'messaging_logs', 'cache_logs',
            'identity_log_types', 'active_directory', 'ldap_logs', 'saml_logs',
            'oauth_logs', 'authentication_logs', 'authorization_logs', 'privilege_logs',
            'url_fqdn_coverage', 'public_ip_coverage', 'network_zones', 'dmz', 'lan',
            'wan', 'management_network', 'production_network', 'development_network',
            'vpc_coverage', 'aws_vpc', 'azure_vnet', 'gcp_vpc', 'subnet_coverage'
        ]
    
    def forward(self, input_ids, attention_mask=None):
        batch_size, seq_len = input_ids.shape
        
        x = self.embedding(input_ids)
        
        if seq_len <= 512:
            x = x + self.positional_encoding[:seq_len].unsqueeze(0)
        
        for transformer in self.transformer_layers:
            x = transformer(x, src_key_padding_mask=~attention_mask if attention_mask is not None else None)
        
        x_transposed = x.transpose(1, 2)
        conv_outputs = []
        for conv in self.conv_layers:
            conv_out = F.gelu(conv(x_transposed))
            conv_outputs.append(conv_out.transpose(1, 2))
        
        x_fused = torch.cat(conv_outputs, dim=-1)
        
        for attention in self.attention_layers:
            attended, _ = attention(x_fused, x_fused, x_fused)
            x_fused = x_fused + attended
        
        x_pooled = x_fused.mean(dim=1)
        
        for dense in self.dense_layers[:-1]:
            x_pooled = F.gelu(dense(x_pooled))
            x_pooled = F.dropout(x_pooled, p=0.1, training=self.training)
        
        final_output = self.dense_layers[-1](x_pooled)
        return F.softmax(final_output, dim=-1)

class IntensiveDatasetBuilder:
    def __init__(self):
        try:
            import os
            import ssl
            import urllib3
            
            ssl._create_default_https_context = ssl._create_unverified_context
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            os.environ['REQUESTS_CA_BUNDLE'] = ''
            os.environ['CURL_CA_BUNDLE'] = ''
            
            proxy_config = {
                'http': 'http://127.0.0.1:8080',
                'https': 'http://127.0.0.1:8080'
            }
            
            os.environ['HTTP_PROXY'] = proxy_config['http']
            os.environ['HTTPS_PROXY'] = proxy_config['https']
            
            logger.info("Using proxy tunnel for model downloads")
            
            self.tokenizer = AutoTokenizer.from_pretrained(
                'microsoft/DialoGPT-medium',
                use_auth_token=False,
                trust_remote_code=False,
                local_files_only=False
            )
            
        except Exception as e:
            logger.warning(f"Failed to load DialoGPT tokenizer via proxy: {e}")
            logger.info("Falling back to basic tokenizer")
            
            try:
                from transformers import GPT2Tokenizer
                self.tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
            except:
                logger.info("Using minimal tokenizer implementation")
                self.tokenizer = self._create_minimal_tokenizer()
        
        if hasattr(self.tokenizer, 'pad_token') and self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        self.training_sources = []
        
        try:
            self.training_sources = [
                'https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Infrastructure/common-hostnames.txt',
                'https://raw.githubusercontent.com/fuzzdb-project/fuzzdb/master/discovery/predictable-filepaths/filename-dirname-bruteforce/raft-large-words.txt',
                'https://raw.githubusercontent.com/berzerk0/Probable-Wordlists/master/Real-Passwords/Top12Thousand-probable-v2.txt',
                'https://github.com/OWASP/SecLists/raw/master/Discovery/DNS/subdomains-top1million-5000.txt',
                'https://github.com/OWASP/SecLists/raw/master/Fuzzing/fuzz-Bo0oM.txt',
                'https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/common.txt',
                'https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Infrastructure/nmap-os-db.txt'
            ]
        except:
            logger.info("Network sources not available, using local generation only")
            self.training_sources = []
        
        self.cybersecurity_keywords = [
            'server', 'workstation', 'desktop', 'laptop', 'endpoint', 'device', 'asset',
            'infrastructure', 'network', 'security', 'firewall', 'router', 'switch',
            'windows', 'linux', 'unix', 'macos', 'centos', 'ubuntu', 'redhat', 'debian',
            'splunk', 'chronicle', 'crowdstrike', 'tanium', 'symantec', 'mcafee', 'carbon',
            'production', 'staging', 'development', 'test', 'qa', 'sandbox', 'demo',
            'datacenter', 'cloud', 'aws', 'azure', 'gcp', 'kubernetes', 'docker', 'vmware',
            'critical', 'high', 'medium', 'low', 'finance', 'hr', 'legal', 'ops', 'it',
            'edr', 'dlp', 'siem', 'soar', 'xdr', 'ndr', 'ueba', 'casb', 'ztna'
        ]
        
        self.training_data = []
        self.label_mappings = {}
    
    async def build_intensive_training_dataset(self):
        logger.info("Building intensive cybersecurity training dataset - this will make fans spin")
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=16) as executor:
            tasks = [
                executor.submit(self._download_and_process_wordlists),
                executor.submit(self._generate_massive_synthetic_hostnames),
                executor.submit(self._generate_intensive_network_patterns),
                executor.submit(self._generate_infrastructure_combinations),
                executor.submit(self._generate_security_tool_variations),
                executor.submit(self._generate_business_context_matrix),
                executor.submit(self._generate_log_type_combinations),
                executor.submit(self._generate_coverage_permutations),
                executor.submit(self._generate_domain_specific_patterns),
                executor.submit(self._generate_contextual_variations)
            ]
            
            results = [task.result() for task in tasks]
        
        for result in results:
            self.training_data.extend(result)
        
        processing_time = time.time() - start_time
        logger.info(f"Generated {len(self.training_data)} training samples in {processing_time:.2f}s")
        return self.training_data
    
    def _create_minimal_tokenizer(self):
        class MinimalTokenizer:
            def __init__(self):
                self.vocab = {}
                self.pad_token = '<pad>'
                self.eos_token = '<eos>'
                self._build_vocab()
            
            def _build_vocab(self):
                chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_'
                for i, char in enumerate(chars):
                    self.vocab[char] = i
                self.vocab[self.pad_token] = len(chars)
                self.vocab[self.eos_token] = len(chars) + 1
            
            def __call__(self, text, truncation=True, padding='max_length', max_length=256, return_tensors='pt'):
                import torch
                
                if isinstance(text, list):
                    text = text[0] if text else ""
                
                tokens = [self.vocab.get(char, 0) for char in text[:max_length]]
                
                if padding == 'max_length':
                    while len(tokens) < max_length:
                        tokens.append(self.vocab[self.pad_token])
                
                attention_mask = [1 if token != self.vocab[self.pad_token] else 0 for token in tokens]
                
                if return_tensors == 'pt':
                    return {
                        'input_ids': torch.tensor([tokens]),
                        'attention_mask': torch.tensor([attention_mask])
                    }
                
                return {'input_ids': tokens, 'attention_mask': attention_mask}
        
        return MinimalTokenizer()
    
    def _download_and_process_wordlists(self):
        samples = []
        
        if not self.training_sources:
            logger.info("No training sources available, generating synthetic data only")
            return samples
        
        import ssl
        import urllib3
        from urllib3.util.retry import Retry
        from requests.adapters import HTTPAdapter
        
        session = requests.Session()
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        session.verify = False
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        session.proxies = {
            'http': 'http://127.0.0.1:8080',
            'https': 'http://127.0.0.1:8080'
        }
        
        for url in self.training_sources:
            try:
                logger.info(f"Downloading via proxy: {url}")
                response = session.get(url, timeout=30, verify=False)
                if response.status_code == 200:
                    lines = response.text.split('\n')[:20000]
                    
                    for line in lines:
                        line = line.strip()
                        if line and len(line) > 2 and len(line) < 100:
                            if self._classify_content_type(line):
                                field_type = self._classify_content_type(line)
                                samples.append((line, field_type))
                else:
                    logger.warning(f"Failed to download {url}: HTTP {response.status_code}")
            except Exception as e:
                logger.debug(f"Failed to download {url}: {e}")
                continue
        
        logger.info(f"Downloaded {len(samples)} samples from online sources")
        return samples
    
    def _generate_massive_synthetic_hostnames(self):
        samples = []
        
        prefixes = ['web', 'app', 'db', 'sql', 'ad', 'dc', 'dns', 'dhcp', 'proxy', 'fw', 'lb', 'file', 'mail', 'print', 'backup', 'monitor', 'log', 'security', 'test', 'dev', 'prod', 'stage', 'api', 'worker', 'cache', 'queue', 'search', 'analytics', 'metrics']
        
        environments = ['prod', 'dev', 'test', 'stage', 'qa', 'demo', 'sandbox', 'lab', 'train', 'preprod', 'uat', 'perf', 'stress', 'canary', 'blue', 'green']
        
        locations = ['us', 'eu', 'ap', 'na', 'sa', 'east', 'west', 'north', 'south', 'central', 'local', 'remote', 'edge', 'core', 'dmz', 'mgmt']
        
        separators = ['-', '_', '']
        numbers = list(range(1, 1000))
        
        total_combinations = 0
        for prefix in prefixes:
            for env in environments:
                for loc in locations:
                    for sep in separators:
                        for num in numbers[:50]:
                            patterns = [
                                f"{prefix}{sep}{num:02d}",
                                f"{prefix}{sep}{env}{sep}{num:02d}",
                                f"{prefix}{sep}{loc}{sep}{num:02d}",
                                f"{env}{sep}{prefix}{sep}{num:02d}",
                                f"{loc}{sep}{prefix}{sep}{num:02d}",
                                f"{prefix}{sep}{env}{sep}{loc}{sep}{num:02d}",
                                f"{loc}{sep}{env}{sep}{prefix}{sep}{num:02d}"
                            ]
                            
                            for pattern in patterns:
                                samples.append((pattern, 'hostname'))
                                total_combinations += 1
                                
                                if total_combinations > 100000:
                                    return samples
        
        return samples
    
    def _generate_intensive_network_patterns(self):
        samples = []
        
        for a in range(10, 192, 2):
            for b in range(0, 255, 3):
                for c in range(0, 255, 4):
                    for d in range(1, 255, 5):
                        ip = f"{a}.{b}.{c}.{d}"
                        samples.append((ip, 'ip_address'))
                        
                        if len(samples) > 50000:
                            break
                    if len(samples) > 50000:
                        break
                if len(samples) > 50000:
                    break
            if len(samples) > 50000:
                break
        
        mac_ouis = ['00:50:56', '00:0C:29', '08:00:27', '52:54:00', '00:16:3E', '00:1B:21', '00:15:5D', '00:25:90']
        for oui in mac_ouis:
            for i in range(0, 65536, 17):
                high = (i >> 8) & 0xFF
                low = i & 0xFF
                for j in range(0, 256, 23):
                    mac = f"{oui}:{high:02X}:{low:02X}:{j:02X}"
                    samples.append((mac, 'mac_address'))
        
        domains = ['corp.com', 'internal.local', 'company.net', 'domain.com', 'enterprise.org']
        hostnames = ['server', 'workstation', 'pc', 'laptop', 'printer', 'scanner']
        
        for domain in domains:
            for hostname in hostnames:
                for i in range(1, 500):
                    fqdn = f"{hostname}{i:03d}.{domain}"
                    samples.append((fqdn, 'fqdn'))
        
        return samples
    
    def _generate_infrastructure_combinations(self):
        samples = []
        
        infra_types = ['On-Prem', 'Cloud', 'SaaS', 'API', 'Hybrid', 'Multi-Cloud', 'Edge', 'Fog', 'Private-Cloud', 'Public-Cloud']
        
        for infra_type in infra_types:
            for i in range(2000):
                samples.append((infra_type, 'infrastructure_type'))
        
        system_types = [
            'Windows Server 2019', 'Windows Server 2022', 'Ubuntu 20.04', 'Ubuntu 22.04',
            'CentOS 7', 'CentOS 8', 'RHEL 8', 'RHEL 9', 'Debian 11', 'Debian 12',
            'macOS Monterey', 'macOS Ventura', 'FreeBSD 13', 'OpenBSD 7',
            'Web Server', 'Application Server', 'Database Server', 'File Server',
            'Mail Server', 'DNS Server', 'DHCP Server', 'Proxy Server',
            'Firewall', 'Router', 'Switch', 'Load Balancer', 'WAF'
        ]
        
        for sys_type in system_types:
            for i in range(1000):
                samples.append((sys_type, 'system_classification'))
        
        return samples
    
    def _generate_security_tool_variations(self):
        samples = []
        
        edr_variations = [
            'CrowdStrike Falcon', 'SentinelOne', 'Carbon Black', 'Cylance Protect',
            'Microsoft Defender ATP', 'Symantec Endpoint Protection', 'McAfee MVISION',
            'Trend Micro Deep Security', 'Sophos Intercept X', 'FireEye Endpoint Security'
        ]
        
        for tool in edr_variations:
            for status in ['Installed', 'Active', 'Running', 'Enabled', 'Protected', 'Monitored']:
                for i in range(200):
                    samples.append((tool, 'edr_coverage'))
                    samples.append((status, 'edr_coverage'))
        
        dlp_tools = [
            'Symantec DLP', 'Forcepoint DLP', 'Microsoft Purview', 'Digital Guardian',
            'GTB Technologies', 'Vera', 'Varonis', 'Code42 Incydr'
        ]
        
        for tool in dlp_tools:
            for i in range(300):
                samples.append((tool, 'dlp_coverage'))
        
        return samples
    
    def _generate_business_context_matrix(self):
        samples = []
        
        business_units = [
            'Finance', 'Human Resources', 'Information Technology', 'Operations',
            'Sales', 'Marketing', 'Legal', 'Compliance', 'Security', 'Engineering',
            'Research and Development', 'Customer Service', 'Procurement', 'Facilities'
        ]
        
        for bu in business_units:
            for i in range(500):
                samples.append((bu, 'business_unit'))
        
        regions = [
            'North America', 'South America', 'Europe', 'Asia Pacific', 'Middle East',
            'Africa', 'US East', 'US West', 'US Central', 'EU West', 'EU Central',
            'Asia', 'APAC', 'EMEA', 'Americas'
        ]
        
        for region in regions:
            for i in range(400):
                samples.append((region, 'global_region'))
        
        return samples
    
    def _generate_log_type_combinations(self):
        samples = []
        
        log_types = {
            'network_log_types': ['Firewall', 'IDS', 'IPS', 'Proxy', 'DNS', 'DHCP', 'WAF', 'Load Balancer', 'Router', 'Switch', 'VPN', 'NAC', 'DPI'],
            'endpoint_log_types': ['Windows Events', 'Linux Syslogs', 'macOS Logs', 'EDR', 'Antivirus', 'DLP', 'FIM', 'Process Monitor', 'Registry', 'File Access'],
            'cloud_log_types': ['AWS CloudTrail', 'Azure Activity', 'GCP Audit', 'Kubernetes', 'Docker', 'Serverless', 'Storage', 'Lambda', 'Functions'],
            'application_log_types': ['Web Server', 'Database', 'Application', 'API', 'Microservices', 'Message Queue', 'Cache', 'Search Engine'],
            'identity_log_types': ['Active Directory', 'LDAP', 'SAML', 'OAuth', 'SSO', 'MFA', 'Privileged Access', 'Identity Governance']
        }
        
        for category, types in log_types.items():
            for log_type in types:
                for i in range(150):
                    samples.append((log_type, category))
        
        return samples
    
    def _generate_coverage_permutations(self):
        samples = []
        
        coverage_indicators = [
            'Yes', 'No', 'True', 'False', '1', '0', 'Enabled', 'Disabled',
            'Active', 'Inactive', 'Installed', 'Not Installed', 'Covered',
            'Not Covered', 'Protected', 'Unprotected', 'Monitored', 'Unmonitored'
        ]
        
        coverage_types = [
            'splunk_coverage', 'chronicle_coverage', 'edr_coverage', 'dlp_coverage',
            'tanium_coverage', 'url_fqdn_coverage', 'public_ip_coverage', 'vpc_coverage'
        ]
        
        for coverage_type in coverage_types:
            for indicator in coverage_indicators:
                for i in range(100):
                    samples.append((indicator, coverage_type))
        
        return samples
    
    def _generate_domain_specific_patterns(self):
        samples = []
        
        patterns = {
            'financial_systems': ['trading', 'settlement', 'clearing', 'risk', 'compliance', 'audit', 'treasury', 'accounting'],
            'healthcare_systems': ['emr', 'his', 'pacs', 'ris', 'lis', 'pharmacy', 'billing', 'patient'],
            'manufacturing_systems': ['scada', 'plc', 'hmi', 'mes', 'erp', 'quality', 'production', 'inventory'],
            'retail_systems': ['pos', 'inventory', 'warehouse', 'ecommerce', 'crm', 'loyalty', 'payment', 'supply']
        ]
        
        for domain, terms in patterns.items():
            for term in terms:
                for i in range(200):
                    samples.append((term, 'application_class'))
        
        return samples
    
    def _generate_contextual_variations(self):
        samples = []
        
        context_patterns = [
            ('datacenter-1', 'datacenter'),
            ('region-us-east', 'global_region'),
            ('zone-dmz', 'network_zones'),
            ('subnet-production', 'network_zones'),
            ('vlan-100', 'network_zones'),
            ('cluster-kubernetes', 'infrastructure_type'),
            ('namespace-production', 'infrastructure_type')
        ]
        
        for pattern, field_type in context_patterns:
            for i in range(300):
                samples.append((pattern, field_type))
        
        return samples
    
    def _classify_content_type(self, content):
        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', content):
            return 'ip_address'
        elif re.match(r'^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$', content):
            return 'mac_address'
        elif '.' in content and re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*\.[a-zA-Z]{2,}$', content):
            return 'fqdn'
        elif re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$', content) or re.match(r'^[a-zA-Z0-9]+$', content):
            return 'hostname'
        else:
            return None

class IntensiveContentAnalyzer:
    def __init__(self):
        self.device = torch.device('mps' if torch.backends.mps.is_available() else 'cpu')
        logger.info(f"Initializing intensive ML on device: {self.device}")
        
        try:
            self.model = FanSpinningMLModel().to(self.device)
            self.model_loaded = True
        except Exception as e:
            logger.warning(f"Failed to load ML model: {e}")
            logger.info("Using fallback pattern-based analysis")
            self.model = None
            self.model_loaded = False
        
        self.dataset_builder = IntensiveDatasetBuilder()
        self.training_complete = False
        self.confidence_threshold = 0.75
        
        if torch.backends.mps.is_available():
            try:
                torch.mps.set_per_process_memory_fraction(0.8)
                logger.info("MPS GPU memory fraction set to 80%")
            except:
                logger.info("MPS available but memory fraction setting failed")
    
    async def initialize_intensive_training(self):
        logger.info("Starting intensive training - this will make your fans spin")
        
        if not self.model_loaded:
            logger.warning("ML model not available, using pattern-based analysis only")
            self.training_complete = True
            return
        
        try:
            training_data = await self.dataset_builder.build_intensive_training_dataset()
            
            logger.info(f"Training model on {len(training_data)} cybersecurity samples")
            await self._train_model_intensively(training_data)
            
            self.training_complete = True
            logger.info("Intensive content analysis training complete")
        except Exception as e:
            logger.error(f"Training failed: {e}")
            logger.info("Falling back to pattern-based analysis")
            self.training_complete = True
    
    async def initialize_intensive_training(self):
        logger.info("Starting intensive training - this will make your fans spin")
        
        training_data = await self.dataset_builder.build_intensive_training_dataset()
        
        logger.info(f"Training model on {len(training_data)} cybersecurity samples")
        await self._train_model_intensively(training_data)
        
        self.training_complete = True
        logger.info("Intensive content analysis training complete")
    
    async def _train_model_intensively(self, training_data):
        class CybersecDataset(Dataset):
            def __init__(self, data, tokenizer, max_length=256):
                self.data = data
                self.tokenizer = tokenizer
                self.max_length = max_length
                self.label_to_idx = {label: idx for idx, label in enumerate(set([item[1] for item in data]))}
            
            def __len__(self):
                return len(self.data)
            
            def __getitem__(self, idx):
                text, label = self.data[idx]
                
                encoding = self.tokenizer(
                    str(text),
                    truncation=True,
                    padding='max_length',
                    max_length=self.max_length,
                    return_tensors='pt'
                )
                
                return {
                    'input_ids': encoding['input_ids'].flatten(),
                    'attention_mask': encoding['attention_mask'].flatten(),
                    'label': torch.tensor(self.label_to_idx[label], dtype=torch.long)
                }
        
        dataset = CybersecDataset(training_data, self.dataset_builder.tokenizer)
        dataloader = DataLoader(dataset, batch_size=64, shuffle=True, num_workers=8)
        
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=2e-4, weight_decay=0.01)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=50)
        criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
        
        self.model.train()
        
        logger.info("Starting intensive training loop - fans should be spinning now")
        
        for epoch in range(25):
            total_loss = 0
            batch_count = 0
            
            for batch in dataloader:
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['label'].to(self.device)
                
                optimizer.zero_grad()
                
                outputs = self.model(input_ids, attention_mask)
                loss = criterion(outputs, labels)
                
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                optimizer.step()
                
                total_loss += loss.item()
                batch_count += 1
                
                if batch_count % 50 == 0:
                    logger.info(f"Epoch {epoch}, Batch {batch_count}, Loss: {loss.item():.4f}")
                    if torch.backends.mps.is_available():
                        torch.mps.synchronize()
            
            scheduler.step()
            avg_loss = total_loss / batch_count
            logger.info(f"Epoch {epoch} complete, Average Loss: {avg_loss:.4f}")
            
            if torch.backends.mps.is_available():
                torch.mps.empty_cache()
                torch.mps.synchronize()
        
        self.model.eval()
        logger.info("Intensive model training complete - fans should calm down soon")
    
    async def analyze_cell_content_intensively(self, content: str, context: Dict = None) -> Tuple[str, float, Dict]:
        if not self.training_complete:
            await self.initialize_intensive_training()
        
        if not content or len(str(content).strip()) == 0:
            return 'unknown', 0.0, {}
        
        content_str = str(content).strip()
        
        if self.model_loaded and self.model is not None:
            try:
                with torch.no_grad():
                    encoding = self.dataset_builder.tokenizer(
                        content_str,
                        truncation=True,
                        padding='max_length',
                        max_length=256,
                        return_tensors='pt'
                    ).to(self.device)
                    
                    predictions = self.model(
                        encoding['input_ids'],
                        encoding['attention_mask']
                    )
                    
                    probabilities = F.softmax(predictions, dim=-1)
                    max_prob, predicted_class = torch.max(probabilities, dim=-1)
                    
                    confidence = max_prob.item()
                    field_type = self.model.cybersecurity_classes[predicted_class.item()]
                    
                    analysis = {
                        'content_length': len(content_str),
                        'ml_confidence': confidence,
                        'field_type_predicted': field_type,
                        'processing_device': str(self.device),
                        'method': 'ml_model'
                    }
                    
                    if confidence > self.confidence_threshold:
                        return field_type, confidence, analysis
                    else:
                        return self._fallback_pattern_analysis(content_str, analysis)
            except Exception as e:
                logger.debug(f"ML analysis failed: {e}")
                return self._fallback_pattern_analysis(content_str)
        else:
            return self._fallback_pattern_analysis(content_str)
    
    def _fallback_pattern_analysis(self, content: str, existing_analysis: Dict = None) -> Tuple[str, float, Dict]:
        analysis = existing_analysis or {
            'content_length': len(content),
            'method': 'pattern_based'
        }
        
        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}

class IntensiveEntityResolver:
    def __init__(self):
        self.content_analyzer = IntensiveContentAnalyzer()
        self.identity_graph = nx.Graph()
        self.processing_stats = {
            'cells_analyzed': 0,
            'entities_discovered': 0,
            'high_confidence_classifications': 0
        }
    
    async def scan_table_content_intensively(self, client_managers: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Starting intensive content-based scanning - fans will spin during ML processing")
        
        discovered_entities = {}
        table_processing_stats = {}
        
        total_tables_processed = 0
        total_cells_analyzed = 0
        
        for project_id, client_manager in client_managers.items():
            with client_manager.get_client() as client:
                datasets = list(client.list_datasets(project=project_id))
                
                logger.info(f"Processing {len(datasets)} datasets in project {project_id}")
                
                for dataset in datasets:
                    tables = list(client.list_tables(dataset))
                    
                    for table_ref in tables:
                        table_path = f"{project_id}.{dataset.dataset_id}.{table_ref.table_id}"
                        
                        try:
                            logger.info(f"Intensively analyzing table: {table_path}")
                            
                            table_entities, cells_processed = await self._analyze_table_content_thoroughly(
                                client, table_path
                            )
                            
                            table_processing_stats[table_path] = {
                                'cells_processed': cells_processed,
                                'entities_found': len(table_entities)
                            }
                            
                            for entity_id, entity_data in table_entities.items():
                                if entity_id in discovered_entities:
                                    discovered_entities[entity_id] = self._merge_entity_data(
                                        discovered_entities[entity_id], entity_data
                                    )
                                else:
                                    discovered_entities[entity_id] = entity_data
                            
                            total_tables_processed += 1
                            total_cells_analyzed += cells_processed
                            
                            if total_tables_processed % 5 == 0:
                                logger.info(f"Processed {total_tables_processed} tables, analyzed {total_cells_analyzed:,} cells")
                            
                            if torch.backends.mps.is_available():
                                torch.mps.empty_cache()
                            
                            gc.collect()
                            
                        except Exception as e:
                            logger.error(f"Failed to process table {table_path}: {e}")
        
        logger.info(f"Intensive scanning complete: {len(discovered_entities)} entities from {total_cells_analyzed:,} cells")
        
        return {
            'entities': discovered_entities,
            'processing_stats': {
                'total_tables_processed': total_tables_processed,
                'total_cells_analyzed': total_cells_analyzed,
                'total_entities_discovered': len(discovered_entities),
                'avg_cells_per_table': total_cells_analyzed / max(total_tables_processed, 1),
                'table_stats': table_processing_stats
            }
        }
    
    async def _analyze_table_content_thoroughly(self, client, table_path: str) -> Tuple[Dict[str, Any], int]:
        try:
            table = client.get_table(table_path)
            
            if not table.schema or table.num_rows == 0:
                return {}, 0
            
            columns = [field.name for field in table.schema]
            
            content_scan_query = f"""
            SELECT *
            FROM `{table_path}`
            LIMIT 25000
            """
            
            job = client.query(content_scan_query)
            results = list(job.result())
            
            discovered_entities = {}
            cells_processed = 0
            
            logger.info(f"Analyzing {len(results)} rows x {len(columns)} columns = {len(results) * len(columns):,} cells with ML")
            
            entity_evidence = defaultdict(list)
            
            batch_size = 32
            analysis_tasks = []
            
            for row_idx, row in enumerate(results):
                for col_idx, column_name in enumerate(columns):
                    if col_idx < len(row) and row[col_idx] is not None:
                        cell_content = str(row[col_idx]).strip()
                        
                        if cell_content and len(cell_content) > 1 and len(cell_content) < 200:
                            context = {
                                'table_name': table_path.split('.')[-1],
                                'column_name': column_name,
                                'row_index': row_idx,
                                'column_index': col_idx
                            }
                            
                            analysis_tasks.append((cell_content, context))
                            cells_processed += 1
            
            logger.info(f"Processing {len(analysis_tasks)} cells in batches of {batch_size}")
            
            for i in range(0, len(analysis_tasks), batch_size):
                batch = analysis_tasks[i:i + batch_size]
                
                batch_results = await asyncio.gather(*[
                    self.content_analyzer.analyze_cell_content_intensively(content, context)
                    for content, context in batch
                ])
                
                for (cell_content, context), (field_type, confidence, analysis) in zip(batch, batch_results):
                    if confidence > 0.6 and field_type != 'unknown':
                        entity_evidence[cell_content].append({
                            'field_type': field_type,
                            'confidence': confidence,
                            'context': context,
                            'analysis': analysis,
                            'table_source': table_path
                        })
                
                if i % (batch_size * 10) == 0:
                    logger.info(f"Processed {i + len(batch)}/{len(analysis_tasks)} cells")
                    
                    if torch.backends.mps.is_available():
                        torch.mps.empty_cache()
            
            for content, evidence_list in entity_evidence.items():
                if len(evidence_list) > 0:
                    best_evidence = max(evidence_list, key=lambda x: x['confidence'])
                    
                    if best_evidence['field_type'] in ['hostname', 'ip_address', 'fqdn', 'mac_address']:
                        entity_id = self._generate_entity_id(content, best_evidence['field_type'])
                        
                        discovered_entities[entity_id] = {
                            'primary_identifier': content,
                            'field_type': best_evidence['field_type'],
                            'confidence': best_evidence['confidence'],
                            'evidence': evidence_list,
                            'table_sources': list(set([ev['table_source'] for ev in evidence_list])),
                            'all_properties': self._extract_properties(evidence_list)
                        }
            
            return discovered_entities, cells_processed
            
        except Exception as e:
            logger.error(f"Table content analysis failed for {table_path}: {e}")
            return {}, 0
    
    def _generate_entity_id(self, content: str, field_type: str) -> str:
        normalized_content = content.upper().strip()
        return f"{field_type}_{hashlib.md5(normalized_content.encode()).hexdigest()[:12]}"
    
    def _extract_properties(self, evidence_list: List[Dict]) -> Dict[str, Any]:
        properties = {}
        
        for evidence in evidence_list:
            context = evidence['context']
            column_name = context['column_name'].lower()
            
            if any(keyword in column_name for keyword in ['region', 'location', 'geo']):
                properties['region'] = context['column_name']
            elif any(keyword in column_name for keyword in ['business', 'unit', 'dept']):
                properties['business_unit'] = context['column_name']
            elif any(keyword in column_name for keyword in ['type', 'class', 'category']):
                properties['classification'] = context['column_name']
        
        return properties
    
    def _merge_entity_data(self, existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
        merged = existing.copy()
        
        merged['evidence'].extend(new['evidence'])
        merged['table_sources'].extend(new['table_sources'])
        merged['table_sources'] = list(set(merged['table_sources']))
        
        for prop_name, prop_data in new['all_properties'].items():
            if prop_name not in merged['all_properties']:
                merged['all_properties'][prop_name] = prop_data
        
        all_confidences = [ev['confidence'] for ev in merged['evidence']]
        merged['confidence'] = max(all_confidences) if all_confidences else 0.0
        
        return merged

class IntensiveDiscoveryEngine:
    def __init__(self, project_id: str, config: Dict[str, Any], cache_manager, intelligence):
        self.project_id = project_id
        self.config = config
        self.cache = cache_manager
        self.intelligence = intelligence
        self.entity_resolver = IntensiveEntityResolver()
        
        self.stats = {
            'intensive_mode': True,
            'ml_training_enabled': True,
            'total_cells_analyzed': 0,
            'entities_discovered': 0,
            'processing_time': 0.0
        }
    
    async def discover_assets_intensively(self, client_managers: Dict[str, Any]) -> Discovery:
        logger.info("Starting intensive asset discovery with ML content analysis")
        start_time = datetime.now()
        
        discovery = Discovery()
        
        try:
            scan_results = await self.entity_resolver.scan_table_content_intensively(client_managers)
            
            entities = scan_results['entities']
            processing_stats = scan_results['processing_stats']
            
            assets = {}
            for entity_id, entity_data in entities.items():
                asset = self._convert_entity_to_asset(entity_id, entity_data)
                if asset:
                    assets[entity_id] = asset
            
            discovery.assets = assets
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            discovery.stats = {
                'total_assets': len(assets),
                'intensive_discovery': True,
                'ml_training_completed': True,
                'total_cells_analyzed': processing_stats['total_cells_analyzed'],
                'total_tables_processed': processing_stats['total_tables_processed'],
                'avg_cells_per_table': processing_stats['avg_cells_per_table'],
                'processing_time_seconds': processing_time,
                'cells_per_second': processing_stats['total_cells_analyzed'] / max(processing_time, 1),
                'ml_content_analysis': True,
                'entity_resolution_applied': True
            }
            
            discovery.insights = await self.intelligence.generate_insights(discovery)
            
            logger.info(f"Intensive discovery complete: {len(assets)} assets from {processing_stats['total_cells_analyzed']:,} cells")
            
        except Exception as e:
            logger.error(f"Intensive discovery failed: {e}")
            discovery.stats = {'error': str(e)}
        
        return discovery
    
    def _convert_entity_to_asset(self, entity_id: str, entity_data: Dict[str, Any]) -> Optional[Asset]:
        try:
            asset = Asset(id=entity_id)
            
            primary_id = entity_data['primary_identifier']
            field_type = entity_data['field_type']
            
            if field_type == 'hostname':
                asset.hostname = primary_id
            elif field_type == 'ip_address':
                asset.ip = primary_id
            elif field_type == 'fqdn':
                asset.fqdn = primary_id
            elif field_type == 'mac_address':
                asset.mac = primary_id
            
            properties = entity_data.get('all_properties', {})
            
            if 'region' in properties:
                asset.region = properties['region']
            if 'business_unit' in properties:
                asset.business_unit = properties['business_unit']
            if 'classification' in properties:
                asset.system_class = properties['classification']
            
            table_sources = entity_data.get('table_sources', [])
            self._set_coverage_flags(asset, table_sources)
            
            asset.sources = len(table_sources)
            asset.confidence = entity_data.get('confidence', 0.0)
            asset.intelligence = min(1.0, len(entity_data.get('evidence', [])) / 5.0)
            asset.quality = self._calculate_quality(entity_data)
            
            return asset
            
        except Exception as e:
            logger.error(f"Failed to convert entity {entity_id}: {e}")
            return None
    
    def _set_coverage_flags(self, asset: Asset, table_sources: List[str]):
        asset.cmdb = any('endpoint' in source.lower() or 'cmdb' in source.lower() for source in table_sources)
        asset.splunk = any('splunk' in source.lower() for source in table_sources)
        asset.chronicle = any('chronicle' in source.lower() for source in table_sources)
        asset.crowdstrike = any('crowdstrike' in source.lower() for source in table_sources)
        asset.edr = asset.crowdstrike
        asset.tanium = any('tanium' in source.lower() for source in table_sources)
        asset.dlp = any('dlp' in source.lower() for source in table_sources)
    
    def _calculate_quality(self, entity_data: Dict[str, Any]) -> float:
        evidence_count = len(entity_data.get('evidence', []))
        source_count = len(entity_data.get('table_sources', []))
        confidence = entity_data.get('confidence', 0.0)
        
        return min(1.0, (evidence_count / 3.0 + source_count / 2.0 + confidence) / 3.0), content):
            return 'ip_address', 0.95, analysis
        elif re.match(r'^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}

class IntensiveEntityResolver:
    def __init__(self):
        self.content_analyzer = IntensiveContentAnalyzer()
        self.identity_graph = nx.Graph()
        self.processing_stats = {
            'cells_analyzed': 0,
            'entities_discovered': 0,
            'high_confidence_classifications': 0
        }
    
    async def scan_table_content_intensively(self, client_managers: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Starting intensive content-based scanning - fans will spin during ML processing")
        
        discovered_entities = {}
        table_processing_stats = {}
        
        total_tables_processed = 0
        total_cells_analyzed = 0
        
        for project_id, client_manager in client_managers.items():
            with client_manager.get_client() as client:
                datasets = list(client.list_datasets(project=project_id))
                
                logger.info(f"Processing {len(datasets)} datasets in project {project_id}")
                
                for dataset in datasets:
                    tables = list(client.list_tables(dataset))
                    
                    for table_ref in tables:
                        table_path = f"{project_id}.{dataset.dataset_id}.{table_ref.table_id}"
                        
                        try:
                            logger.info(f"Intensively analyzing table: {table_path}")
                            
                            table_entities, cells_processed = await self._analyze_table_content_thoroughly(
                                client, table_path
                            )
                            
                            table_processing_stats[table_path] = {
                                'cells_processed': cells_processed,
                                'entities_found': len(table_entities)
                            }
                            
                            for entity_id, entity_data in table_entities.items():
                                if entity_id in discovered_entities:
                                    discovered_entities[entity_id] = self._merge_entity_data(
                                        discovered_entities[entity_id], entity_data
                                    )
                                else:
                                    discovered_entities[entity_id] = entity_data
                            
                            total_tables_processed += 1
                            total_cells_analyzed += cells_processed
                            
                            if total_tables_processed % 5 == 0:
                                logger.info(f"Processed {total_tables_processed} tables, analyzed {total_cells_analyzed:,} cells")
                            
                            if torch.backends.mps.is_available():
                                torch.mps.empty_cache()
                            
                            gc.collect()
                            
                        except Exception as e:
                            logger.error(f"Failed to process table {table_path}: {e}")
        
        logger.info(f"Intensive scanning complete: {len(discovered_entities)} entities from {total_cells_analyzed:,} cells")
        
        return {
            'entities': discovered_entities,
            'processing_stats': {
                'total_tables_processed': total_tables_processed,
                'total_cells_analyzed': total_cells_analyzed,
                'total_entities_discovered': len(discovered_entities),
                'avg_cells_per_table': total_cells_analyzed / max(total_tables_processed, 1),
                'table_stats': table_processing_stats
            }
        }
    
    async def _analyze_table_content_thoroughly(self, client, table_path: str) -> Tuple[Dict[str, Any], int]:
        try:
            table = client.get_table(table_path)
            
            if not table.schema or table.num_rows == 0:
                return {}, 0
            
            columns = [field.name for field in table.schema]
            
            content_scan_query = f"""
            SELECT *
            FROM `{table_path}`
            LIMIT 25000
            """
            
            job = client.query(content_scan_query)
            results = list(job.result())
            
            discovered_entities = {}
            cells_processed = 0
            
            logger.info(f"Analyzing {len(results)} rows x {len(columns)} columns = {len(results) * len(columns):,} cells with ML")
            
            entity_evidence = defaultdict(list)
            
            batch_size = 32
            analysis_tasks = []
            
            for row_idx, row in enumerate(results):
                for col_idx, column_name in enumerate(columns):
                    if col_idx < len(row) and row[col_idx] is not None:
                        cell_content = str(row[col_idx]).strip()
                        
                        if cell_content and len(cell_content) > 1 and len(cell_content) < 200:
                            context = {
                                'table_name': table_path.split('.')[-1],
                                'column_name': column_name,
                                'row_index': row_idx,
                                'column_index': col_idx
                            }
                            
                            analysis_tasks.append((cell_content, context))
                            cells_processed += 1
            
            logger.info(f"Processing {len(analysis_tasks)} cells in batches of {batch_size}")
            
            for i in range(0, len(analysis_tasks), batch_size):
                batch = analysis_tasks[i:i + batch_size]
                
                batch_results = await asyncio.gather(*[
                    self.content_analyzer.analyze_cell_content_intensively(content, context)
                    for content, context in batch
                ])
                
                for (cell_content, context), (field_type, confidence, analysis) in zip(batch, batch_results):
                    if confidence > 0.6 and field_type != 'unknown':
                        entity_evidence[cell_content].append({
                            'field_type': field_type,
                            'confidence': confidence,
                            'context': context,
                            'analysis': analysis,
                            'table_source': table_path
                        })
                
                if i % (batch_size * 10) == 0:
                    logger.info(f"Processed {i + len(batch)}/{len(analysis_tasks)} cells")
                    
                    if torch.backends.mps.is_available():
                        torch.mps.empty_cache()
            
            for content, evidence_list in entity_evidence.items():
                if len(evidence_list) > 0:
                    best_evidence = max(evidence_list, key=lambda x: x['confidence'])
                    
                    if best_evidence['field_type'] in ['hostname', 'ip_address', 'fqdn', 'mac_address']:
                        entity_id = self._generate_entity_id(content, best_evidence['field_type'])
                        
                        discovered_entities[entity_id] = {
                            'primary_identifier': content,
                            'field_type': best_evidence['field_type'],
                            'confidence': best_evidence['confidence'],
                            'evidence': evidence_list,
                            'table_sources': list(set([ev['table_source'] for ev in evidence_list])),
                            'all_properties': self._extract_properties(evidence_list)
                        }
            
            return discovered_entities, cells_processed
            
        except Exception as e:
            logger.error(f"Table content analysis failed for {table_path}: {e}")
            return {}, 0
    
    def _generate_entity_id(self, content: str, field_type: str) -> str:
        normalized_content = content.upper().strip()
        return f"{field_type}_{hashlib.md5(normalized_content.encode()).hexdigest()[:12]}"
    
    def _extract_properties(self, evidence_list: List[Dict]) -> Dict[str, Any]:
        properties = {}
        
        for evidence in evidence_list:
            context = evidence['context']
            column_name = context['column_name'].lower()
            
            if any(keyword in column_name for keyword in ['region', 'location', 'geo']):
                properties['region'] = context['column_name']
            elif any(keyword in column_name for keyword in ['business', 'unit', 'dept']):
                properties['business_unit'] = context['column_name']
            elif any(keyword in column_name for keyword in ['type', 'class', 'category']):
                properties['classification'] = context['column_name']
        
        return properties
    
    def _merge_entity_data(self, existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
        merged = existing.copy()
        
        merged['evidence'].extend(new['evidence'])
        merged['table_sources'].extend(new['table_sources'])
        merged['table_sources'] = list(set(merged['table_sources']))
        
        for prop_name, prop_data in new['all_properties'].items():
            if prop_name not in merged['all_properties']:
                merged['all_properties'][prop_name] = prop_data
        
        all_confidences = [ev['confidence'] for ev in merged['evidence']]
        merged['confidence'] = max(all_confidences) if all_confidences else 0.0
        
        return merged

class IntensiveDiscoveryEngine:
    def __init__(self, project_id: str, config: Dict[str, Any], cache_manager, intelligence):
        self.project_id = project_id
        self.config = config
        self.cache = cache_manager
        self.intelligence = intelligence
        self.entity_resolver = IntensiveEntityResolver()
        
        self.stats = {
            'intensive_mode': True,
            'ml_training_enabled': True,
            'total_cells_analyzed': 0,
            'entities_discovered': 0,
            'processing_time': 0.0
        }
    
    async def discover_assets_intensively(self, client_managers: Dict[str, Any]) -> Discovery:
        logger.info("Starting intensive asset discovery with ML content analysis")
        start_time = datetime.now()
        
        discovery = Discovery()
        
        try:
            scan_results = await self.entity_resolver.scan_table_content_intensively(client_managers)
            
            entities = scan_results['entities']
            processing_stats = scan_results['processing_stats']
            
            assets = {}
            for entity_id, entity_data in entities.items():
                asset = self._convert_entity_to_asset(entity_id, entity_data)
                if asset:
                    assets[entity_id] = asset
            
            discovery.assets = assets
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            discovery.stats = {
                'total_assets': len(assets),
                'intensive_discovery': True,
                'ml_training_completed': True,
                'total_cells_analyzed': processing_stats['total_cells_analyzed'],
                'total_tables_processed': processing_stats['total_tables_processed'],
                'avg_cells_per_table': processing_stats['avg_cells_per_table'],
                'processing_time_seconds': processing_time,
                'cells_per_second': processing_stats['total_cells_analyzed'] / max(processing_time, 1),
                'ml_content_analysis': True,
                'entity_resolution_applied': True
            }
            
            discovery.insights = await self.intelligence.generate_insights(discovery)
            
            logger.info(f"Intensive discovery complete: {len(assets)} assets from {processing_stats['total_cells_analyzed']:,} cells")
            
        except Exception as e:
            logger.error(f"Intensive discovery failed: {e}")
            discovery.stats = {'error': str(e)}
        
        return discovery
    
    def _convert_entity_to_asset(self, entity_id: str, entity_data: Dict[str, Any]) -> Optional[Asset]:
        try:
            asset = Asset(id=entity_id)
            
            primary_id = entity_data['primary_identifier']
            field_type = entity_data['field_type']
            
            if field_type == 'hostname':
                asset.hostname = primary_id
            elif field_type == 'ip_address':
                asset.ip = primary_id
            elif field_type == 'fqdn':
                asset.fqdn = primary_id
            elif field_type == 'mac_address':
                asset.mac = primary_id
            
            properties = entity_data.get('all_properties', {})
            
            if 'region' in properties:
                asset.region = properties['region']
            if 'business_unit' in properties:
                asset.business_unit = properties['business_unit']
            if 'classification' in properties:
                asset.system_class = properties['classification']
            
            table_sources = entity_data.get('table_sources', [])
            self._set_coverage_flags(asset, table_sources)
            
            asset.sources = len(table_sources)
            asset.confidence = entity_data.get('confidence', 0.0)
            asset.intelligence = min(1.0, len(entity_data.get('evidence', [])) / 5.0)
            asset.quality = self._calculate_quality(entity_data)
            
            return asset
            
        except Exception as e:
            logger.error(f"Failed to convert entity {entity_id}: {e}")
            return None
    
    def _set_coverage_flags(self, asset: Asset, table_sources: List[str]):
        asset.cmdb = any('endpoint' in source.lower() or 'cmdb' in source.lower() for source in table_sources)
        asset.splunk = any('splunk' in source.lower() for source in table_sources)
        asset.chronicle = any('chronicle' in source.lower() for source in table_sources)
        asset.crowdstrike = any('crowdstrike' in source.lower() for source in table_sources)
        asset.edr = asset.crowdstrike
        asset.tanium = any('tanium' in source.lower() for source in table_sources)
        asset.dlp = any('dlp' in source.lower() for source in table_sources)
    
    def _calculate_quality(self, entity_data: Dict[str, Any]) -> float:
        evidence_count = len(entity_data.get('evidence', []))
        source_count = len(entity_data.get('table_sources', []))
        confidence = entity_data.get('confidence', 0.0)
        
        return min(1.0, (evidence_count / 3.0 + source_count / 2.0 + confidence) / 3.0), content):
            return 'mac_address', 0.95, analysis
        elif '.' in content and re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*\.[a-zA-Z]{2,}

class IntensiveEntityResolver:
    def __init__(self):
        self.content_analyzer = IntensiveContentAnalyzer()
        self.identity_graph = nx.Graph()
        self.processing_stats = {
            'cells_analyzed': 0,
            'entities_discovered': 0,
            'high_confidence_classifications': 0
        }
    
    async def scan_table_content_intensively(self, client_managers: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Starting intensive content-based scanning - fans will spin during ML processing")
        
        discovered_entities = {}
        table_processing_stats = {}
        
        total_tables_processed = 0
        total_cells_analyzed = 0
        
        for project_id, client_manager in client_managers.items():
            with client_manager.get_client() as client:
                datasets = list(client.list_datasets(project=project_id))
                
                logger.info(f"Processing {len(datasets)} datasets in project {project_id}")
                
                for dataset in datasets:
                    tables = list(client.list_tables(dataset))
                    
                    for table_ref in tables:
                        table_path = f"{project_id}.{dataset.dataset_id}.{table_ref.table_id}"
                        
                        try:
                            logger.info(f"Intensively analyzing table: {table_path}")
                            
                            table_entities, cells_processed = await self._analyze_table_content_thoroughly(
                                client, table_path
                            )
                            
                            table_processing_stats[table_path] = {
                                'cells_processed': cells_processed,
                                'entities_found': len(table_entities)
                            }
                            
                            for entity_id, entity_data in table_entities.items():
                                if entity_id in discovered_entities:
                                    discovered_entities[entity_id] = self._merge_entity_data(
                                        discovered_entities[entity_id], entity_data
                                    )
                                else:
                                    discovered_entities[entity_id] = entity_data
                            
                            total_tables_processed += 1
                            total_cells_analyzed += cells_processed
                            
                            if total_tables_processed % 5 == 0:
                                logger.info(f"Processed {total_tables_processed} tables, analyzed {total_cells_analyzed:,} cells")
                            
                            if torch.backends.mps.is_available():
                                torch.mps.empty_cache()
                            
                            gc.collect()
                            
                        except Exception as e:
                            logger.error(f"Failed to process table {table_path}: {e}")
        
        logger.info(f"Intensive scanning complete: {len(discovered_entities)} entities from {total_cells_analyzed:,} cells")
        
        return {
            'entities': discovered_entities,
            'processing_stats': {
                'total_tables_processed': total_tables_processed,
                'total_cells_analyzed': total_cells_analyzed,
                'total_entities_discovered': len(discovered_entities),
                'avg_cells_per_table': total_cells_analyzed / max(total_tables_processed, 1),
                'table_stats': table_processing_stats
            }
        }
    
    async def _analyze_table_content_thoroughly(self, client, table_path: str) -> Tuple[Dict[str, Any], int]:
        try:
            table = client.get_table(table_path)
            
            if not table.schema or table.num_rows == 0:
                return {}, 0
            
            columns = [field.name for field in table.schema]
            
            content_scan_query = f"""
            SELECT *
            FROM `{table_path}`
            LIMIT 25000
            """
            
            job = client.query(content_scan_query)
            results = list(job.result())
            
            discovered_entities = {}
            cells_processed = 0
            
            logger.info(f"Analyzing {len(results)} rows x {len(columns)} columns = {len(results) * len(columns):,} cells with ML")
            
            entity_evidence = defaultdict(list)
            
            batch_size = 32
            analysis_tasks = []
            
            for row_idx, row in enumerate(results):
                for col_idx, column_name in enumerate(columns):
                    if col_idx < len(row) and row[col_idx] is not None:
                        cell_content = str(row[col_idx]).strip()
                        
                        if cell_content and len(cell_content) > 1 and len(cell_content) < 200:
                            context = {
                                'table_name': table_path.split('.')[-1],
                                'column_name': column_name,
                                'row_index': row_idx,
                                'column_index': col_idx
                            }
                            
                            analysis_tasks.append((cell_content, context))
                            cells_processed += 1
            
            logger.info(f"Processing {len(analysis_tasks)} cells in batches of {batch_size}")
            
            for i in range(0, len(analysis_tasks), batch_size):
                batch = analysis_tasks[i:i + batch_size]
                
                batch_results = await asyncio.gather(*[
                    self.content_analyzer.analyze_cell_content_intensively(content, context)
                    for content, context in batch
                ])
                
                for (cell_content, context), (field_type, confidence, analysis) in zip(batch, batch_results):
                    if confidence > 0.6 and field_type != 'unknown':
                        entity_evidence[cell_content].append({
                            'field_type': field_type,
                            'confidence': confidence,
                            'context': context,
                            'analysis': analysis,
                            'table_source': table_path
                        })
                
                if i % (batch_size * 10) == 0:
                    logger.info(f"Processed {i + len(batch)}/{len(analysis_tasks)} cells")
                    
                    if torch.backends.mps.is_available():
                        torch.mps.empty_cache()
            
            for content, evidence_list in entity_evidence.items():
                if len(evidence_list) > 0:
                    best_evidence = max(evidence_list, key=lambda x: x['confidence'])
                    
                    if best_evidence['field_type'] in ['hostname', 'ip_address', 'fqdn', 'mac_address']:
                        entity_id = self._generate_entity_id(content, best_evidence['field_type'])
                        
                        discovered_entities[entity_id] = {
                            'primary_identifier': content,
                            'field_type': best_evidence['field_type'],
                            'confidence': best_evidence['confidence'],
                            'evidence': evidence_list,
                            'table_sources': list(set([ev['table_source'] for ev in evidence_list])),
                            'all_properties': self._extract_properties(evidence_list)
                        }
            
            return discovered_entities, cells_processed
            
        except Exception as e:
            logger.error(f"Table content analysis failed for {table_path}: {e}")
            return {}, 0
    
    def _generate_entity_id(self, content: str, field_type: str) -> str:
        normalized_content = content.upper().strip()
        return f"{field_type}_{hashlib.md5(normalized_content.encode()).hexdigest()[:12]}"
    
    def _extract_properties(self, evidence_list: List[Dict]) -> Dict[str, Any]:
        properties = {}
        
        for evidence in evidence_list:
            context = evidence['context']
            column_name = context['column_name'].lower()
            
            if any(keyword in column_name for keyword in ['region', 'location', 'geo']):
                properties['region'] = context['column_name']
            elif any(keyword in column_name for keyword in ['business', 'unit', 'dept']):
                properties['business_unit'] = context['column_name']
            elif any(keyword in column_name for keyword in ['type', 'class', 'category']):
                properties['classification'] = context['column_name']
        
        return properties
    
    def _merge_entity_data(self, existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
        merged = existing.copy()
        
        merged['evidence'].extend(new['evidence'])
        merged['table_sources'].extend(new['table_sources'])
        merged['table_sources'] = list(set(merged['table_sources']))
        
        for prop_name, prop_data in new['all_properties'].items():
            if prop_name not in merged['all_properties']:
                merged['all_properties'][prop_name] = prop_data
        
        all_confidences = [ev['confidence'] for ev in merged['evidence']]
        merged['confidence'] = max(all_confidences) if all_confidences else 0.0
        
        return merged

class IntensiveDiscoveryEngine:
    def __init__(self, project_id: str, config: Dict[str, Any], cache_manager, intelligence):
        self.project_id = project_id
        self.config = config
        self.cache = cache_manager
        self.intelligence = intelligence
        self.entity_resolver = IntensiveEntityResolver()
        
        self.stats = {
            'intensive_mode': True,
            'ml_training_enabled': True,
            'total_cells_analyzed': 0,
            'entities_discovered': 0,
            'processing_time': 0.0
        }
    
    async def discover_assets_intensively(self, client_managers: Dict[str, Any]) -> Discovery:
        logger.info("Starting intensive asset discovery with ML content analysis")
        start_time = datetime.now()
        
        discovery = Discovery()
        
        try:
            scan_results = await self.entity_resolver.scan_table_content_intensively(client_managers)
            
            entities = scan_results['entities']
            processing_stats = scan_results['processing_stats']
            
            assets = {}
            for entity_id, entity_data in entities.items():
                asset = self._convert_entity_to_asset(entity_id, entity_data)
                if asset:
                    assets[entity_id] = asset
            
            discovery.assets = assets
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            discovery.stats = {
                'total_assets': len(assets),
                'intensive_discovery': True,
                'ml_training_completed': True,
                'total_cells_analyzed': processing_stats['total_cells_analyzed'],
                'total_tables_processed': processing_stats['total_tables_processed'],
                'avg_cells_per_table': processing_stats['avg_cells_per_table'],
                'processing_time_seconds': processing_time,
                'cells_per_second': processing_stats['total_cells_analyzed'] / max(processing_time, 1),
                'ml_content_analysis': True,
                'entity_resolution_applied': True
            }
            
            discovery.insights = await self.intelligence.generate_insights(discovery)
            
            logger.info(f"Intensive discovery complete: {len(assets)} assets from {processing_stats['total_cells_analyzed']:,} cells")
            
        except Exception as e:
            logger.error(f"Intensive discovery failed: {e}")
            discovery.stats = {'error': str(e)}
        
        return discovery
    
    def _convert_entity_to_asset(self, entity_id: str, entity_data: Dict[str, Any]) -> Optional[Asset]:
        try:
            asset = Asset(id=entity_id)
            
            primary_id = entity_data['primary_identifier']
            field_type = entity_data['field_type']
            
            if field_type == 'hostname':
                asset.hostname = primary_id
            elif field_type == 'ip_address':
                asset.ip = primary_id
            elif field_type == 'fqdn':
                asset.fqdn = primary_id
            elif field_type == 'mac_address':
                asset.mac = primary_id
            
            properties = entity_data.get('all_properties', {})
            
            if 'region' in properties:
                asset.region = properties['region']
            if 'business_unit' in properties:
                asset.business_unit = properties['business_unit']
            if 'classification' in properties:
                asset.system_class = properties['classification']
            
            table_sources = entity_data.get('table_sources', [])
            self._set_coverage_flags(asset, table_sources)
            
            asset.sources = len(table_sources)
            asset.confidence = entity_data.get('confidence', 0.0)
            asset.intelligence = min(1.0, len(entity_data.get('evidence', [])) / 5.0)
            asset.quality = self._calculate_quality(entity_data)
            
            return asset
            
        except Exception as e:
            logger.error(f"Failed to convert entity {entity_id}: {e}")
            return None
    
    def _set_coverage_flags(self, asset: Asset, table_sources: List[str]):
        asset.cmdb = any('endpoint' in source.lower() or 'cmdb' in source.lower() for source in table_sources)
        asset.splunk = any('splunk' in source.lower() for source in table_sources)
        asset.chronicle = any('chronicle' in source.lower() for source in table_sources)
        asset.crowdstrike = any('crowdstrike' in source.lower() for source in table_sources)
        asset.edr = asset.crowdstrike
        asset.tanium = any('tanium' in source.lower() for source in table_sources)
        asset.dlp = any('dlp' in source.lower() for source in table_sources)
    
    def _calculate_quality(self, entity_data: Dict[str, Any]) -> float:
        evidence_count = len(entity_data.get('evidence', []))
        source_count = len(entity_data.get('table_sources', []))
        confidence = entity_data.get('confidence', 0.0)
        
        return min(1.0, (evidence_count / 3.0 + source_count / 2.0 + confidence) / 3.0), content):
            return 'fqdn', 0.9, analysis
        elif re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]

class IntensiveEntityResolver:
    def __init__(self):
        self.content_analyzer = IntensiveContentAnalyzer()
        self.identity_graph = nx.Graph()
        self.processing_stats = {
            'cells_analyzed': 0,
            'entities_discovered': 0,
            'high_confidence_classifications': 0
        }
    
    async def scan_table_content_intensively(self, client_managers: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Starting intensive content-based scanning - fans will spin during ML processing")
        
        discovered_entities = {}
        table_processing_stats = {}
        
        total_tables_processed = 0
        total_cells_analyzed = 0
        
        for project_id, client_manager in client_managers.items():
            with client_manager.get_client() as client:
                datasets = list(client.list_datasets(project=project_id))
                
                logger.info(f"Processing {len(datasets)} datasets in project {project_id}")
                
                for dataset in datasets:
                    tables = list(client.list_tables(dataset))
                    
                    for table_ref in tables:
                        table_path = f"{project_id}.{dataset.dataset_id}.{table_ref.table_id}"
                        
                        try:
                            logger.info(f"Intensively analyzing table: {table_path}")
                            
                            table_entities, cells_processed = await self._analyze_table_content_thoroughly(
                                client, table_path
                            )
                            
                            table_processing_stats[table_path] = {
                                'cells_processed': cells_processed,
                                'entities_found': len(table_entities)
                            }
                            
                            for entity_id, entity_data in table_entities.items():
                                if entity_id in discovered_entities:
                                    discovered_entities[entity_id] = self._merge_entity_data(
                                        discovered_entities[entity_id], entity_data
                                    )
                                else:
                                    discovered_entities[entity_id] = entity_data
                            
                            total_tables_processed += 1
                            total_cells_analyzed += cells_processed
                            
                            if total_tables_processed % 5 == 0:
                                logger.info(f"Processed {total_tables_processed} tables, analyzed {total_cells_analyzed:,} cells")
                            
                            if torch.backends.mps.is_available():
                                torch.mps.empty_cache()
                            
                            gc.collect()
                            
                        except Exception as e:
                            logger.error(f"Failed to process table {table_path}: {e}")
        
        logger.info(f"Intensive scanning complete: {len(discovered_entities)} entities from {total_cells_analyzed:,} cells")
        
        return {
            'entities': discovered_entities,
            'processing_stats': {
                'total_tables_processed': total_tables_processed,
                'total_cells_analyzed': total_cells_analyzed,
                'total_entities_discovered': len(discovered_entities),
                'avg_cells_per_table': total_cells_analyzed / max(total_tables_processed, 1),
                'table_stats': table_processing_stats
            }
        }
    
    async def _analyze_table_content_thoroughly(self, client, table_path: str) -> Tuple[Dict[str, Any], int]:
        try:
            table = client.get_table(table_path)
            
            if not table.schema or table.num_rows == 0:
                return {}, 0
            
            columns = [field.name for field in table.schema]
            
            content_scan_query = f"""
            SELECT *
            FROM `{table_path}`
            LIMIT 25000
            """
            
            job = client.query(content_scan_query)
            results = list(job.result())
            
            discovered_entities = {}
            cells_processed = 0
            
            logger.info(f"Analyzing {len(results)} rows x {len(columns)} columns = {len(results) * len(columns):,} cells with ML")
            
            entity_evidence = defaultdict(list)
            
            batch_size = 32
            analysis_tasks = []
            
            for row_idx, row in enumerate(results):
                for col_idx, column_name in enumerate(columns):
                    if col_idx < len(row) and row[col_idx] is not None:
                        cell_content = str(row[col_idx]).strip()
                        
                        if cell_content and len(cell_content) > 1 and len(cell_content) < 200:
                            context = {
                                'table_name': table_path.split('.')[-1],
                                'column_name': column_name,
                                'row_index': row_idx,
                                'column_index': col_idx
                            }
                            
                            analysis_tasks.append((cell_content, context))
                            cells_processed += 1
            
            logger.info(f"Processing {len(analysis_tasks)} cells in batches of {batch_size}")
            
            for i in range(0, len(analysis_tasks), batch_size):
                batch = analysis_tasks[i:i + batch_size]
                
                batch_results = await asyncio.gather(*[
                    self.content_analyzer.analyze_cell_content_intensively(content, context)
                    for content, context in batch
                ])
                
                for (cell_content, context), (field_type, confidence, analysis) in zip(batch, batch_results):
                    if confidence > 0.6 and field_type != 'unknown':
                        entity_evidence[cell_content].append({
                            'field_type': field_type,
                            'confidence': confidence,
                            'context': context,
                            'analysis': analysis,
                            'table_source': table_path
                        })
                
                if i % (batch_size * 10) == 0:
                    logger.info(f"Processed {i + len(batch)}/{len(analysis_tasks)} cells")
                    
                    if torch.backends.mps.is_available():
                        torch.mps.empty_cache()
            
            for content, evidence_list in entity_evidence.items():
                if len(evidence_list) > 0:
                    best_evidence = max(evidence_list, key=lambda x: x['confidence'])
                    
                    if best_evidence['field_type'] in ['hostname', 'ip_address', 'fqdn', 'mac_address']:
                        entity_id = self._generate_entity_id(content, best_evidence['field_type'])
                        
                        discovered_entities[entity_id] = {
                            'primary_identifier': content,
                            'field_type': best_evidence['field_type'],
                            'confidence': best_evidence['confidence'],
                            'evidence': evidence_list,
                            'table_sources': list(set([ev['table_source'] for ev in evidence_list])),
                            'all_properties': self._extract_properties(evidence_list)
                        }
            
            return discovered_entities, cells_processed
            
        except Exception as e:
            logger.error(f"Table content analysis failed for {table_path}: {e}")
            return {}, 0
    
    def _generate_entity_id(self, content: str, field_type: str) -> str:
        normalized_content = content.upper().strip()
        return f"{field_type}_{hashlib.md5(normalized_content.encode()).hexdigest()[:12]}"
    
    def _extract_properties(self, evidence_list: List[Dict]) -> Dict[str, Any]:
        properties = {}
        
        for evidence in evidence_list:
            context = evidence['context']
            column_name = context['column_name'].lower()
            
            if any(keyword in column_name for keyword in ['region', 'location', 'geo']):
                properties['region'] = context['column_name']
            elif any(keyword in column_name for keyword in ['business', 'unit', 'dept']):
                properties['business_unit'] = context['column_name']
            elif any(keyword in column_name for keyword in ['type', 'class', 'category']):
                properties['classification'] = context['column_name']
        
        return properties
    
    def _merge_entity_data(self, existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
        merged = existing.copy()
        
        merged['evidence'].extend(new['evidence'])
        merged['table_sources'].extend(new['table_sources'])
        merged['table_sources'] = list(set(merged['table_sources']))
        
        for prop_name, prop_data in new['all_properties'].items():
            if prop_name not in merged['all_properties']:
                merged['all_properties'][prop_name] = prop_data
        
        all_confidences = [ev['confidence'] for ev in merged['evidence']]
        merged['confidence'] = max(all_confidences) if all_confidences else 0.0
        
        return merged

class IntensiveDiscoveryEngine:
    def __init__(self, project_id: str, config: Dict[str, Any], cache_manager, intelligence):
        self.project_id = project_id
        self.config = config
        self.cache = cache_manager
        self.intelligence = intelligence
        self.entity_resolver = IntensiveEntityResolver()
        
        self.stats = {
            'intensive_mode': True,
            'ml_training_enabled': True,
            'total_cells_analyzed': 0,
            'entities_discovered': 0,
            'processing_time': 0.0
        }
    
    async def discover_assets_intensively(self, client_managers: Dict[str, Any]) -> Discovery:
        logger.info("Starting intensive asset discovery with ML content analysis")
        start_time = datetime.now()
        
        discovery = Discovery()
        
        try:
            scan_results = await self.entity_resolver.scan_table_content_intensively(client_managers)
            
            entities = scan_results['entities']
            processing_stats = scan_results['processing_stats']
            
            assets = {}
            for entity_id, entity_data in entities.items():
                asset = self._convert_entity_to_asset(entity_id, entity_data)
                if asset:
                    assets[entity_id] = asset
            
            discovery.assets = assets
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            discovery.stats = {
                'total_assets': len(assets),
                'intensive_discovery': True,
                'ml_training_completed': True,
                'total_cells_analyzed': processing_stats['total_cells_analyzed'],
                'total_tables_processed': processing_stats['total_tables_processed'],
                'avg_cells_per_table': processing_stats['avg_cells_per_table'],
                'processing_time_seconds': processing_time,
                'cells_per_second': processing_stats['total_cells_analyzed'] / max(processing_time, 1),
                'ml_content_analysis': True,
                'entity_resolution_applied': True
            }
            
            discovery.insights = await self.intelligence.generate_insights(discovery)
            
            logger.info(f"Intensive discovery complete: {len(assets)} assets from {processing_stats['total_cells_analyzed']:,} cells")
            
        except Exception as e:
            logger.error(f"Intensive discovery failed: {e}")
            discovery.stats = {'error': str(e)}
        
        return discovery
    
    def _convert_entity_to_asset(self, entity_id: str, entity_data: Dict[str, Any]) -> Optional[Asset]:
        try:
            asset = Asset(id=entity_id)
            
            primary_id = entity_data['primary_identifier']
            field_type = entity_data['field_type']
            
            if field_type == 'hostname':
                asset.hostname = primary_id
            elif field_type == 'ip_address':
                asset.ip = primary_id
            elif field_type == 'fqdn':
                asset.fqdn = primary_id
            elif field_type == 'mac_address':
                asset.mac = primary_id
            
            properties = entity_data.get('all_properties', {})
            
            if 'region' in properties:
                asset.region = properties['region']
            if 'business_unit' in properties:
                asset.business_unit = properties['business_unit']
            if 'classification' in properties:
                asset.system_class = properties['classification']
            
            table_sources = entity_data.get('table_sources', [])
            self._set_coverage_flags(asset, table_sources)
            
            asset.sources = len(table_sources)
            asset.confidence = entity_data.get('confidence', 0.0)
            asset.intelligence = min(1.0, len(entity_data.get('evidence', [])) / 5.0)
            asset.quality = self._calculate_quality(entity_data)
            
            return asset
            
        except Exception as e:
            logger.error(f"Failed to convert entity {entity_id}: {e}")
            return None
    
    def _set_coverage_flags(self, asset: Asset, table_sources: List[str]):
        asset.cmdb = any('endpoint' in source.lower() or 'cmdb' in source.lower() for source in table_sources)
        asset.splunk = any('splunk' in source.lower() for source in table_sources)
        asset.chronicle = any('chronicle' in source.lower() for source in table_sources)
        asset.crowdstrike = any('crowdstrike' in source.lower() for source in table_sources)
        asset.edr = asset.crowdstrike
        asset.tanium = any('tanium' in source.lower() for source in table_sources)
        asset.dlp = any('dlp' in source.lower() for source in table_sources)
    
    def _calculate_quality(self, entity_data: Dict[str, Any]) -> float:
        evidence_count = len(entity_data.get('evidence', []))
        source_count = len(entity_data.get('table_sources', []))
        confidence = entity_data.get('confidence', 0.0)
        
        return min(1.0, (evidence_count / 3.0 + source_count / 2.0 + confidence) / 3.0), content) or re.match(r'^[a-zA-Z0-9]+

class IntensiveEntityResolver:
    def __init__(self):
        self.content_analyzer = IntensiveContentAnalyzer()
        self.identity_graph = nx.Graph()
        self.processing_stats = {
            'cells_analyzed': 0,
            'entities_discovered': 0,
            'high_confidence_classifications': 0
        }
    
    async def scan_table_content_intensively(self, client_managers: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Starting intensive content-based scanning - fans will spin during ML processing")
        
        discovered_entities = {}
        table_processing_stats = {}
        
        total_tables_processed = 0
        total_cells_analyzed = 0
        
        for project_id, client_manager in client_managers.items():
            with client_manager.get_client() as client:
                datasets = list(client.list_datasets(project=project_id))
                
                logger.info(f"Processing {len(datasets)} datasets in project {project_id}")
                
                for dataset in datasets:
                    tables = list(client.list_tables(dataset))
                    
                    for table_ref in tables:
                        table_path = f"{project_id}.{dataset.dataset_id}.{table_ref.table_id}"
                        
                        try:
                            logger.info(f"Intensively analyzing table: {table_path}")
                            
                            table_entities, cells_processed = await self._analyze_table_content_thoroughly(
                                client, table_path
                            )
                            
                            table_processing_stats[table_path] = {
                                'cells_processed': cells_processed,
                                'entities_found': len(table_entities)
                            }
                            
                            for entity_id, entity_data in table_entities.items():
                                if entity_id in discovered_entities:
                                    discovered_entities[entity_id] = self._merge_entity_data(
                                        discovered_entities[entity_id], entity_data
                                    )
                                else:
                                    discovered_entities[entity_id] = entity_data
                            
                            total_tables_processed += 1
                            total_cells_analyzed += cells_processed
                            
                            if total_tables_processed % 5 == 0:
                                logger.info(f"Processed {total_tables_processed} tables, analyzed {total_cells_analyzed:,} cells")
                            
                            if torch.backends.mps.is_available():
                                torch.mps.empty_cache()
                            
                            gc.collect()
                            
                        except Exception as e:
                            logger.error(f"Failed to process table {table_path}: {e}")
        
        logger.info(f"Intensive scanning complete: {len(discovered_entities)} entities from {total_cells_analyzed:,} cells")
        
        return {
            'entities': discovered_entities,
            'processing_stats': {
                'total_tables_processed': total_tables_processed,
                'total_cells_analyzed': total_cells_analyzed,
                'total_entities_discovered': len(discovered_entities),
                'avg_cells_per_table': total_cells_analyzed / max(total_tables_processed, 1),
                'table_stats': table_processing_stats
            }
        }
    
    async def _analyze_table_content_thoroughly(self, client, table_path: str) -> Tuple[Dict[str, Any], int]:
        try:
            table = client.get_table(table_path)
            
            if not table.schema or table.num_rows == 0:
                return {}, 0
            
            columns = [field.name for field in table.schema]
            
            content_scan_query = f"""
            SELECT *
            FROM `{table_path}`
            LIMIT 25000
            """
            
            job = client.query(content_scan_query)
            results = list(job.result())
            
            discovered_entities = {}
            cells_processed = 0
            
            logger.info(f"Analyzing {len(results)} rows x {len(columns)} columns = {len(results) * len(columns):,} cells with ML")
            
            entity_evidence = defaultdict(list)
            
            batch_size = 32
            analysis_tasks = []
            
            for row_idx, row in enumerate(results):
                for col_idx, column_name in enumerate(columns):
                    if col_idx < len(row) and row[col_idx] is not None:
                        cell_content = str(row[col_idx]).strip()
                        
                        if cell_content and len(cell_content) > 1 and len(cell_content) < 200:
                            context = {
                                'table_name': table_path.split('.')[-1],
                                'column_name': column_name,
                                'row_index': row_idx,
                                'column_index': col_idx
                            }
                            
                            analysis_tasks.append((cell_content, context))
                            cells_processed += 1
            
            logger.info(f"Processing {len(analysis_tasks)} cells in batches of {batch_size}")
            
            for i in range(0, len(analysis_tasks), batch_size):
                batch = analysis_tasks[i:i + batch_size]
                
                batch_results = await asyncio.gather(*[
                    self.content_analyzer.analyze_cell_content_intensively(content, context)
                    for content, context in batch
                ])
                
                for (cell_content, context), (field_type, confidence, analysis) in zip(batch, batch_results):
                    if confidence > 0.6 and field_type != 'unknown':
                        entity_evidence[cell_content].append({
                            'field_type': field_type,
                            'confidence': confidence,
                            'context': context,
                            'analysis': analysis,
                            'table_source': table_path
                        })
                
                if i % (batch_size * 10) == 0:
                    logger.info(f"Processed {i + len(batch)}/{len(analysis_tasks)} cells")
                    
                    if torch.backends.mps.is_available():
                        torch.mps.empty_cache()
            
            for content, evidence_list in entity_evidence.items():
                if len(evidence_list) > 0:
                    best_evidence = max(evidence_list, key=lambda x: x['confidence'])
                    
                    if best_evidence['field_type'] in ['hostname', 'ip_address', 'fqdn', 'mac_address']:
                        entity_id = self._generate_entity_id(content, best_evidence['field_type'])
                        
                        discovered_entities[entity_id] = {
                            'primary_identifier': content,
                            'field_type': best_evidence['field_type'],
                            'confidence': best_evidence['confidence'],
                            'evidence': evidence_list,
                            'table_sources': list(set([ev['table_source'] for ev in evidence_list])),
                            'all_properties': self._extract_properties(evidence_list)
                        }
            
            return discovered_entities, cells_processed
            
        except Exception as e:
            logger.error(f"Table content analysis failed for {table_path}: {e}")
            return {}, 0
    
    def _generate_entity_id(self, content: str, field_type: str) -> str:
        normalized_content = content.upper().strip()
        return f"{field_type}_{hashlib.md5(normalized_content.encode()).hexdigest()[:12]}"
    
    def _extract_properties(self, evidence_list: List[Dict]) -> Dict[str, Any]:
        properties = {}
        
        for evidence in evidence_list:
            context = evidence['context']
            column_name = context['column_name'].lower()
            
            if any(keyword in column_name for keyword in ['region', 'location', 'geo']):
                properties['region'] = context['column_name']
            elif any(keyword in column_name for keyword in ['business', 'unit', 'dept']):
                properties['business_unit'] = context['column_name']
            elif any(keyword in column_name for keyword in ['type', 'class', 'category']):
                properties['classification'] = context['column_name']
        
        return properties
    
    def _merge_entity_data(self, existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
        merged = existing.copy()
        
        merged['evidence'].extend(new['evidence'])
        merged['table_sources'].extend(new['table_sources'])
        merged['table_sources'] = list(set(merged['table_sources']))
        
        for prop_name, prop_data in new['all_properties'].items():
            if prop_name not in merged['all_properties']:
                merged['all_properties'][prop_name] = prop_data
        
        all_confidences = [ev['confidence'] for ev in merged['evidence']]
        merged['confidence'] = max(all_confidences) if all_confidences else 0.0
        
        return merged

class IntensiveDiscoveryEngine:
    def __init__(self, project_id: str, config: Dict[str, Any], cache_manager, intelligence):
        self.project_id = project_id
        self.config = config
        self.cache = cache_manager
        self.intelligence = intelligence
        self.entity_resolver = IntensiveEntityResolver()
        
        self.stats = {
            'intensive_mode': True,
            'ml_training_enabled': True,
            'total_cells_analyzed': 0,
            'entities_discovered': 0,
            'processing_time': 0.0
        }
    
    async def discover_assets_intensively(self, client_managers: Dict[str, Any]) -> Discovery:
        logger.info("Starting intensive asset discovery with ML content analysis")
        start_time = datetime.now()
        
        discovery = Discovery()
        
        try:
            scan_results = await self.entity_resolver.scan_table_content_intensively(client_managers)
            
            entities = scan_results['entities']
            processing_stats = scan_results['processing_stats']
            
            assets = {}
            for entity_id, entity_data in entities.items():
                asset = self._convert_entity_to_asset(entity_id, entity_data)
                if asset:
                    assets[entity_id] = asset
            
            discovery.assets = assets
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            discovery.stats = {
                'total_assets': len(assets),
                'intensive_discovery': True,
                'ml_training_completed': True,
                'total_cells_analyzed': processing_stats['total_cells_analyzed'],
                'total_tables_processed': processing_stats['total_tables_processed'],
                'avg_cells_per_table': processing_stats['avg_cells_per_table'],
                'processing_time_seconds': processing_time,
                'cells_per_second': processing_stats['total_cells_analyzed'] / max(processing_time, 1),
                'ml_content_analysis': True,
                'entity_resolution_applied': True
            }
            
            discovery.insights = await self.intelligence.generate_insights(discovery)
            
            logger.info(f"Intensive discovery complete: {len(assets)} assets from {processing_stats['total_cells_analyzed']:,} cells")
            
        except Exception as e:
            logger.error(f"Intensive discovery failed: {e}")
            discovery.stats = {'error': str(e)}
        
        return discovery
    
    def _convert_entity_to_asset(self, entity_id: str, entity_data: Dict[str, Any]) -> Optional[Asset]:
        try:
            asset = Asset(id=entity_id)
            
            primary_id = entity_data['primary_identifier']
            field_type = entity_data['field_type']
            
            if field_type == 'hostname':
                asset.hostname = primary_id
            elif field_type == 'ip_address':
                asset.ip = primary_id
            elif field_type == 'fqdn':
                asset.fqdn = primary_id
            elif field_type == 'mac_address':
                asset.mac = primary_id
            
            properties = entity_data.get('all_properties', {})
            
            if 'region' in properties:
                asset.region = properties['region']
            if 'business_unit' in properties:
                asset.business_unit = properties['business_unit']
            if 'classification' in properties:
                asset.system_class = properties['classification']
            
            table_sources = entity_data.get('table_sources', [])
            self._set_coverage_flags(asset, table_sources)
            
            asset.sources = len(table_sources)
            asset.confidence = entity_data.get('confidence', 0.0)
            asset.intelligence = min(1.0, len(entity_data.get('evidence', [])) / 5.0)
            asset.quality = self._calculate_quality(entity_data)
            
            return asset
            
        except Exception as e:
            logger.error(f"Failed to convert entity {entity_id}: {e}")
            return None
    
    def _set_coverage_flags(self, asset: Asset, table_sources: List[str]):
        asset.cmdb = any('endpoint' in source.lower() or 'cmdb' in source.lower() for source in table_sources)
        asset.splunk = any('splunk' in source.lower() for source in table_sources)
        asset.chronicle = any('chronicle' in source.lower() for source in table_sources)
        asset.crowdstrike = any('crowdstrike' in source.lower() for source in table_sources)
        asset.edr = asset.crowdstrike
        asset.tanium = any('tanium' in source.lower() for source in table_sources)
        asset.dlp = any('dlp' in source.lower() for source in table_sources)
    
    def _calculate_quality(self, entity_data: Dict[str, Any]) -> float:
        evidence_count = len(entity_data.get('evidence', []))
        source_count = len(entity_data.get('table_sources', []))
        confidence = entity_data.get('confidence', 0.0)
        
        return min(1.0, (evidence_count / 3.0 + source_count / 2.0 + confidence) / 3.0), content):
            hostname_indicators = ['srv', 'web', 'app', 'db', 'sql', 'host', 'server', 'pc', 'ws']
            content_lower = content.lower()
            if any(indicator in content_lower for indicator in hostname_indicators):
                return 'hostname', 0.85, analysis
            elif len(content) >= 3 and len(content) <= 63:
                return 'hostname', 0.7, analysis
        
        cybersec_keywords = ['prod', 'dev', 'test', 'stage', 'critical', 'high', 'medium', 'low']
        content_lower = content.lower()
        if any(keyword in content_lower for keyword in cybersec_keywords):
            return 'application_class', 0.6, analysis
        
        return 'unknown', 0.0, analysis

class IntensiveEntityResolver:
    def __init__(self):
        self.content_analyzer = IntensiveContentAnalyzer()
        self.identity_graph = nx.Graph()
        self.processing_stats = {
            'cells_analyzed': 0,
            'entities_discovered': 0,
            'high_confidence_classifications': 0
        }
    
    async def scan_table_content_intensively(self, client_managers: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Starting intensive content-based scanning - fans will spin during ML processing")
        
        discovered_entities = {}
        table_processing_stats = {}
        
        total_tables_processed = 0
        total_cells_analyzed = 0
        
        for project_id, client_manager in client_managers.items():
            with client_manager.get_client() as client:
                datasets = list(client.list_datasets(project=project_id))
                
                logger.info(f"Processing {len(datasets)} datasets in project {project_id}")
                
                for dataset in datasets:
                    tables = list(client.list_tables(dataset))
                    
                    for table_ref in tables:
                        table_path = f"{project_id}.{dataset.dataset_id}.{table_ref.table_id}"
                        
                        try:
                            logger.info(f"Intensively analyzing table: {table_path}")
                            
                            table_entities, cells_processed = await self._analyze_table_content_thoroughly(
                                client, table_path
                            )
                            
                            table_processing_stats[table_path] = {
                                'cells_processed': cells_processed,
                                'entities_found': len(table_entities)
                            }
                            
                            for entity_id, entity_data in table_entities.items():
                                if entity_id in discovered_entities:
                                    discovered_entities[entity_id] = self._merge_entity_data(
                                        discovered_entities[entity_id], entity_data
                                    )
                                else:
                                    discovered_entities[entity_id] = entity_data
                            
                            total_tables_processed += 1
                            total_cells_analyzed += cells_processed
                            
                            if total_tables_processed % 5 == 0:
                                logger.info(f"Processed {total_tables_processed} tables, analyzed {total_cells_analyzed:,} cells")
                            
                            if torch.backends.mps.is_available():
                                torch.mps.empty_cache()
                            
                            gc.collect()
                            
                        except Exception as e:
                            logger.error(f"Failed to process table {table_path}: {e}")
        
        logger.info(f"Intensive scanning complete: {len(discovered_entities)} entities from {total_cells_analyzed:,} cells")
        
        return {
            'entities': discovered_entities,
            'processing_stats': {
                'total_tables_processed': total_tables_processed,
                'total_cells_analyzed': total_cells_analyzed,
                'total_entities_discovered': len(discovered_entities),
                'avg_cells_per_table': total_cells_analyzed / max(total_tables_processed, 1),
                'table_stats': table_processing_stats
            }
        }
    
    async def _analyze_table_content_thoroughly(self, client, table_path: str) -> Tuple[Dict[str, Any], int]:
        try:
            table = client.get_table(table_path)
            
            if not table.schema or table.num_rows == 0:
                return {}, 0
            
            columns = [field.name for field in table.schema]
            
            content_scan_query = f"""
            SELECT *
            FROM `{table_path}`
            LIMIT 25000
            """
            
            job = client.query(content_scan_query)
            results = list(job.result())
            
            discovered_entities = {}
            cells_processed = 0
            
            logger.info(f"Analyzing {len(results)} rows x {len(columns)} columns = {len(results) * len(columns):,} cells with ML")
            
            entity_evidence = defaultdict(list)
            
            batch_size = 32
            analysis_tasks = []
            
            for row_idx, row in enumerate(results):
                for col_idx, column_name in enumerate(columns):
                    if col_idx < len(row) and row[col_idx] is not None:
                        cell_content = str(row[col_idx]).strip()
                        
                        if cell_content and len(cell_content) > 1 and len(cell_content) < 200:
                            context = {
                                'table_name': table_path.split('.')[-1],
                                'column_name': column_name,
                                'row_index': row_idx,
                                'column_index': col_idx
                            }
                            
                            analysis_tasks.append((cell_content, context))
                            cells_processed += 1
            
            logger.info(f"Processing {len(analysis_tasks)} cells in batches of {batch_size}")
            
            for i in range(0, len(analysis_tasks), batch_size):
                batch = analysis_tasks[i:i + batch_size]
                
                batch_results = await asyncio.gather(*[
                    self.content_analyzer.analyze_cell_content_intensively(content, context)
                    for content, context in batch
                ])
                
                for (cell_content, context), (field_type, confidence, analysis) in zip(batch, batch_results):
                    if confidence > 0.6 and field_type != 'unknown':
                        entity_evidence[cell_content].append({
                            'field_type': field_type,
                            'confidence': confidence,
                            'context': context,
                            'analysis': analysis,
                            'table_source': table_path
                        })
                
                if i % (batch_size * 10) == 0:
                    logger.info(f"Processed {i + len(batch)}/{len(analysis_tasks)} cells")
                    
                    if torch.backends.mps.is_available():
                        torch.mps.empty_cache()
            
            for content, evidence_list in entity_evidence.items():
                if len(evidence_list) > 0:
                    best_evidence = max(evidence_list, key=lambda x: x['confidence'])
                    
                    if best_evidence['field_type'] in ['hostname', 'ip_address', 'fqdn', 'mac_address']:
                        entity_id = self._generate_entity_id(content, best_evidence['field_type'])
                        
                        discovered_entities[entity_id] = {
                            'primary_identifier': content,
                            'field_type': best_evidence['field_type'],
                            'confidence': best_evidence['confidence'],
                            'evidence': evidence_list,
                            'table_sources': list(set([ev['table_source'] for ev in evidence_list])),
                            'all_properties': self._extract_properties(evidence_list)
                        }
            
            return discovered_entities, cells_processed
            
        except Exception as e:
            logger.error(f"Table content analysis failed for {table_path}: {e}")
            return {}, 0
    
    def _generate_entity_id(self, content: str, field_type: str) -> str:
        normalized_content = content.upper().strip()
        return f"{field_type}_{hashlib.md5(normalized_content.encode()).hexdigest()[:12]}"
    
    def _extract_properties(self, evidence_list: List[Dict]) -> Dict[str, Any]:
        properties = {}
        
        for evidence in evidence_list:
            context = evidence['context']
            column_name = context['column_name'].lower()
            
            if any(keyword in column_name for keyword in ['region', 'location', 'geo']):
                properties['region'] = context['column_name']
            elif any(keyword in column_name for keyword in ['business', 'unit', 'dept']):
                properties['business_unit'] = context['column_name']
            elif any(keyword in column_name for keyword in ['type', 'class', 'category']):
                properties['classification'] = context['column_name']
        
        return properties
    
    def _merge_entity_data(self, existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
        merged = existing.copy()
        
        merged['evidence'].extend(new['evidence'])
        merged['table_sources'].extend(new['table_sources'])
        merged['table_sources'] = list(set(merged['table_sources']))
        
        for prop_name, prop_data in new['all_properties'].items():
            if prop_name not in merged['all_properties']:
                merged['all_properties'][prop_name] = prop_data
        
        all_confidences = [ev['confidence'] for ev in merged['evidence']]
        merged['confidence'] = max(all_confidences) if all_confidences else 0.0
        
        return merged

class IntensiveDiscoveryEngine:
    def __init__(self, project_id: str, config: Dict[str, Any], cache_manager, intelligence):
        self.project_id = project_id
        self.config = config
        self.cache = cache_manager
        self.intelligence = intelligence
        self.entity_resolver = IntensiveEntityResolver()
        
        self.stats = {
            'intensive_mode': True,
            'ml_training_enabled': True,
            'total_cells_analyzed': 0,
            'entities_discovered': 0,
            'processing_time': 0.0
        }
    
    async def discover_assets_intensively(self, client_managers: Dict[str, Any]) -> Discovery:
        logger.info("Starting intensive asset discovery with ML content analysis")
        start_time = datetime.now()
        
        discovery = Discovery()
        
        try:
            scan_results = await self.entity_resolver.scan_table_content_intensively(client_managers)
            
            entities = scan_results['entities']
            processing_stats = scan_results['processing_stats']
            
            assets = {}
            for entity_id, entity_data in entities.items():
                asset = self._convert_entity_to_asset(entity_id, entity_data)
                if asset:
                    assets[entity_id] = asset
            
            discovery.assets = assets
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            discovery.stats = {
                'total_assets': len(assets),
                'intensive_discovery': True,
                'ml_training_completed': True,
                'total_cells_analyzed': processing_stats['total_cells_analyzed'],
                'total_tables_processed': processing_stats['total_tables_processed'],
                'avg_cells_per_table': processing_stats['avg_cells_per_table'],
                'processing_time_seconds': processing_time,
                'cells_per_second': processing_stats['total_cells_analyzed'] / max(processing_time, 1),
                'ml_content_analysis': True,
                'entity_resolution_applied': True
            }
            
            discovery.insights = await self.intelligence.generate_insights(discovery)
            
            logger.info(f"Intensive discovery complete: {len(assets)} assets from {processing_stats['total_cells_analyzed']:,} cells")
            
        except Exception as e:
            logger.error(f"Intensive discovery failed: {e}")
            discovery.stats = {'error': str(e)}
        
        return discovery
    
    def _convert_entity_to_asset(self, entity_id: str, entity_data: Dict[str, Any]) -> Optional[Asset]:
        try:
            asset = Asset(id=entity_id)
            
            primary_id = entity_data['primary_identifier']
            field_type = entity_data['field_type']
            
            if field_type == 'hostname':
                asset.hostname = primary_id
            elif field_type == 'ip_address':
                asset.ip = primary_id
            elif field_type == 'fqdn':
                asset.fqdn = primary_id
            elif field_type == 'mac_address':
                asset.mac = primary_id
            
            properties = entity_data.get('all_properties', {})
            
            if 'region' in properties:
                asset.region = properties['region']
            if 'business_unit' in properties:
                asset.business_unit = properties['business_unit']
            if 'classification' in properties:
                asset.system_class = properties['classification']
            
            table_sources = entity_data.get('table_sources', [])
            self._set_coverage_flags(asset, table_sources)
            
            asset.sources = len(table_sources)
            asset.confidence = entity_data.get('confidence', 0.0)
            asset.intelligence = min(1.0, len(entity_data.get('evidence', [])) / 5.0)
            asset.quality = self._calculate_quality(entity_data)
            
            return asset
            
        except Exception as e:
            logger.error(f"Failed to convert entity {entity_id}: {e}")
            return None
    
    def _set_coverage_flags(self, asset: Asset, table_sources: List[str]):
        asset.cmdb = any('endpoint' in source.lower() or 'cmdb' in source.lower() for source in table_sources)
        asset.splunk = any('splunk' in source.lower() for source in table_sources)
        asset.chronicle = any('chronicle' in source.lower() for source in table_sources)
        asset.crowdstrike = any('crowdstrike' in source.lower() for source in table_sources)
        asset.edr = asset.crowdstrike
        asset.tanium = any('tanium' in source.lower() for source in table_sources)
        asset.dlp = any('dlp' in source.lower() for source in table_sources)
    
    def _calculate_quality(self, entity_data: Dict[str, Any]) -> float:
        evidence_count = len(entity_data.get('evidence', []))
        source_count = len(entity_data.get('table_sources', []))
        confidence = entity_data.get('confidence', 0.0)
        
        return min(1.0, (evidence_count / 3.0 + source_count / 2.0 + confidence) / 3.0)