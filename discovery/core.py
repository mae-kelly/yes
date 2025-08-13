# discovery/core.py - ultra-advanced content-based discovery

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
from transformers import AutoTokenizer, AutoModel, pipeline
import requests
import json
import re
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict
from core.types import Asset, TableSchema, Discovery, FieldMapping
from ai.intelligence import EnhancedIntelligenceEngine
import ipaddress
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor
import urllib.parse
import time

logger = logging.getLogger(__name__)

class HyperAdvancedMLContentClassifier(nn.Module):
    def __init__(self, vocab_size=500000, embed_dim=2048, num_classes=157):
        super().__init__()
        
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.positional_encoding = nn.Parameter(torch.randn(1000, embed_dim))
        
        self.transformer_layers = nn.ModuleList([
            nn.TransformerEncoderLayer(
                d_model=embed_dim,
                nhead=32,
                dim_feedforward=8192,
                dropout=0.1,
                activation='gelu',
                batch_first=True
            ) for _ in range(24)
        ])
        
        self.multi_scale_conv = nn.ModuleList([
            nn.Conv1d(embed_dim, embed_dim, kernel_size=k, padding=k//2)
            for k in [3, 5, 7, 11, 15, 21]
        ])
        
        self.attention_fusion = nn.MultiheadAttention(embed_dim * 6, 64, batch_first=True)
        
        self.residual_blocks = nn.ModuleList([
            nn.Sequential(
                nn.LayerNorm(embed_dim * 6),
                nn.Linear(embed_dim * 6, embed_dim * 12),
                nn.GELU(),
                nn.Dropout(0.2),
                nn.Linear(embed_dim * 12, embed_dim * 6),
                nn.Dropout(0.1)
            ) for _ in range(12)
        ])
        
        self.advanced_pooling = nn.ModuleList([
            nn.AdaptiveAvgPool1d(1),
            nn.AdaptiveMaxPool1d(1),
            nn.AdaptiveAvgPool1d(1)
        ])
        
        self.domain_experts = nn.ModuleList([
            nn.Sequential(
                nn.Linear(embed_dim * 6, 4096),
                nn.GELU(),
                nn.Dropout(0.3),
                nn.Linear(4096, 2048),
                nn.GELU(),
                nn.Dropout(0.2),
                nn.Linear(2048, 1024),
                nn.GELU(),
                nn.Linear(1024, num_classes // 4)
            ) for _ in range(4)
        ])
        
        self.meta_classifier = nn.Sequential(
            nn.Linear(num_classes, 4096),
            nn.GELU(),
            nn.Dropout(0.3),
            nn.Linear(4096, 2048),
            nn.GELU(),
            nn.Dropout(0.2),
            nn.Linear(2048, 1024),
            nn.GELU(),
            nn.Linear(1024, num_classes)
        )
        
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
        
        if seq_len <= 1000:
            x = x + self.positional_encoding[:seq_len].unsqueeze(0)
        
        for transformer in self.transformer_layers:
            x = transformer(x, src_key_padding_mask=~attention_mask if attention_mask is not None else None)
        
        x_transposed = x.transpose(1, 2)
        conv_outputs = []
        for conv in self.multi_scale_conv:
            conv_out = F.gelu(conv(x_transposed))
            conv_outputs.append(conv_out.transpose(1, 2))
        
        x_fused = torch.cat(conv_outputs, dim=-1)
        
        x_attended, _ = self.attention_fusion(x_fused, x_fused, x_fused)
        
        for residual_block in self.residual_blocks:
            x_attended = x_attended + residual_block(x_attended)
        
        pooled_outputs = []
        x_pooling = x_attended.transpose(1, 2)
        for pooling in self.advanced_pooling:
            pooled = pooling(x_pooling).squeeze(-1)
            pooled_outputs.append(pooled)
        
        x_pooled = torch.cat(pooled_outputs, dim=-1)
        
        expert_outputs = []
        for expert in self.domain_experts:
            expert_out = expert(x_pooled)
            expert_outputs.append(expert_out)
        
        expert_concat = torch.cat(expert_outputs, dim=-1)
        final_output = self.meta_classifier(expert_concat)
        
        return F.softmax(final_output, dim=-1)

class CybersecurityDatasetBuilder:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained('microsoft/DialoGPT-large')
        self.training_sources = [
            'https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Infrastructure/common-hostnames.txt',
            'https://raw.githubusercontent.com/fuzzdb-project/fuzzdb/master/discovery/predictable-filepaths/filename-dirname-bruteforce/raft-large-words.txt',
            'https://raw.githubusercontent.com/berzerk0/Probable-Wordlists/master/Real-Passwords/Top12Thousand-probable-v2.txt',
            'https://github.com/OWASP/SecLists/raw/master/Discovery/DNS/subdomains-top1million-5000.txt',
            'https://github.com/OWASP/SecLists/raw/master/Fuzzing/fuzz-Bo0oM.txt'
        ]
        
        self.cybersecurity_keywords = [
            'server', 'workstation', 'desktop', 'laptop', 'endpoint', 'device', 'asset',
            'infrastructure', 'network', 'security', 'firewall', 'router', 'switch',
            'windows', 'linux', 'unix', 'macos', 'centos', 'ubuntu', 'redhat',
            'splunk', 'chronicle', 'crowdstrike', 'tanium', 'symantec', 'mcafee',
            'production', 'staging', 'development', 'test', 'qa', 'sandbox',
            'datacenter', 'cloud', 'aws', 'azure', 'gcp', 'kubernetes', 'docker',
            'critical', 'high', 'medium', 'low', 'finance', 'hr', 'legal', 'ops'
        ]
        
        self.training_data = []
        self.label_mappings = {}
    
    async def build_massive_training_dataset(self):
        logger.info("Building massive cybersecurity training dataset from online sources")
        
        training_tasks = [
            self._download_security_wordlists(),
            self._generate_synthetic_hostnames(),
            self._generate_network_identifiers(), 
            self._generate_infrastructure_patterns(),
            self._generate_security_tool_patterns(),
            self._generate_business_context_patterns(),
            self._generate_log_type_patterns(),
            self._generate_coverage_patterns()
        ]
        
        dataset_chunks = await asyncio.gather(*training_tasks)
        
        for chunk in dataset_chunks:
            self.training_data.extend(chunk)
        
        logger.info(f"Generated {len(self.training_data)} training samples from cybersecurity domain")
        return self.training_data
    
    async def _download_security_wordlists(self):
        samples = []
        
        for url in self.training_sources:
            try:
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    lines = response.text.split('\n')[:10000]
                    
                    for line in lines:
                        line = line.strip()
                        if line and len(line) > 2:
                            if self._looks_like_hostname(line):
                                samples.append((line, 'hostname'))
                            elif self._looks_like_domain(line):
                                samples.append((line, 'fqdn'))
            except:
                continue
        
        return samples
    
    async def _generate_synthetic_hostnames(self):
        samples = []
        
        prefixes = ['web', 'app', 'db', 'sql', 'ad', 'dc', 'dns', 'dhcp', 'proxy', 'fw', 'lb', 'file', 'mail', 'print', 'backup', 'monitor', 'log', 'security', 'test', 'dev', 'prod', 'stage']
        environments = ['prod', 'dev', 'test', 'stage', 'qa', 'demo', 'sandbox', 'lab']
        locations = ['us', 'eu', 'ap', 'east', 'west', 'north', 'south', 'central']
        numbers = range(1, 1000)
        
        for prefix in prefixes:
            for env in environments:
                for loc in locations:
                    for num in list(numbers)[:100]:
                        patterns = [
                            f"{prefix}{num:02d}",
                            f"{prefix}-{env}-{num:02d}",
                            f"{prefix}-{loc}-{num:02d}",
                            f"{env}-{prefix}-{num:02d}",
                            f"{loc}-{prefix}-{num:02d}",
                            f"{prefix}{env}{num:02d}",
                            f"{env}{prefix}{num:02d}"
                        ]
                        
                        for pattern in patterns:
                            samples.append((pattern, 'hostname'))
        
        return samples[:50000]
    
    async def _generate_network_identifiers(self):
        samples = []
        
        for a in range(10, 192):
            for b in range(0, 255, 17):
                for c in range(0, 255, 23):
                    for d in range(1, 255, 31):
                        ip = f"{a}.{b}.{c}.{d}"
                        samples.append((ip, 'ip_address'))
                        
                        if len(samples) > 25000:
                            break
                    if len(samples) > 25000:
                        break
                if len(samples) > 25000:
                    break
            if len(samples) > 25000:
                break
        
        mac_prefixes = ['00:50:56', '00:0C:29', '08:00:27', '52:54:00', '00:16:3E']
        for prefix in mac_prefixes:
            for i in range(1000):
                mac = f"{prefix}:{i//256:02X}:{i%256:02X}:{i%16:02X}"
                samples.append((mac, 'mac_address'))
        
        return samples
    
    async def _generate_infrastructure_patterns(self):
        samples = []
        
        infra_types = ['On-Prem', 'Cloud', 'SaaS', 'API', 'Hybrid', 'Multi-Cloud']
        for infra_type in infra_types:
            for i in range(1000):
                samples.append((infra_type, 'infrastructure_type'))
        
        system_types = ['Windows Server', 'Linux Server', 'Unix Server', 'Web Server', 'Database Server', 'Application Server', 'File Server', 'Mail Server', 'DNS Server', 'Proxy Server', 'Firewall', 'Router', 'Switch', 'Load Balancer', 'Network Appliance']
        for sys_type in system_types:
            for i in range(500):
                samples.append((sys_type, 'system_classification'))
        
        regions = ['US-East', 'US-West', 'US-Central', 'EU-West', 'EU-Central', 'Asia-Pacific', 'North-America', 'South-America', 'EMEA', 'APAC']
        for region in regions:
            for i in range(300):
                samples.append((region, 'global_region'))
        
        return samples
    
    async def _generate_security_tool_patterns(self):
        samples = []
        
        edr_tools = ['CrowdStrike', 'SentinelOne', 'Carbon Black', 'Cylance', 'Defender ATP', 'Symantec Endpoint', 'McAfee MVISION', 'Trend Micro']
        for tool in edr_tools:
            for i in range(200):
                samples.append((tool, 'edr_coverage'))
                samples.append(('True', 'edr_coverage'))
                samples.append(('Yes', 'edr_coverage'))
                samples.append(('Installed', 'edr_coverage'))
        
        dlp_tools = ['Symantec DLP', 'Forcepoint DLP', 'Microsoft Purview', 'Digital Guardian', 'GTB Technologies']
        for tool in dlp_tools:
            for i in range(200):
                samples.append((tool, 'dlp_coverage'))
        
        return samples
    
    async def _generate_business_context_patterns(self):
        samples = []
        
        business_units = ['Finance', 'HR', 'IT', 'Operations', 'Sales', 'Marketing', 'Legal', 'Compliance', 'Security', 'Engineering', 'Research', 'Development']
        for bu in business_units:
            for i in range(300):
                samples.append((bu, 'business_unit'))
        
        app_classes = ['Critical', 'High', 'Medium', 'Low', 'Production', 'Non-Production']
        for app_class in app_classes:
            for i in range(400):
                samples.append((app_class, 'application_class'))
        
        return samples
    
    async def _generate_log_type_patterns(self):
        samples = []
        
        network_logs = ['Firewall', 'IDS', 'IPS', 'Proxy', 'DNS', 'DHCP', 'WAF', 'Load Balancer', 'Router', 'Switch', 'VPN']
        for log_type in network_logs:
            for i in range(100):
                samples.append((log_type, 'network_log_types'))
        
        endpoint_logs = ['Windows Events', 'Linux Syslogs', 'macOS Logs', 'EDR Logs', 'Antivirus', 'DLP', 'FIM']
        for log_type in endpoint_logs:
            for i in range(100):
                samples.append((log_type, 'endpoint_log_types'))
        
        return samples
    
    async def _generate_coverage_patterns(self):
        samples = []
        
        coverage_indicators = ['Yes', 'No', 'True', 'False', '1', '0', 'Enabled', 'Disabled', 'Active', 'Inactive', 'Installed', 'Not Installed', 'Covered', 'Not Covered']
        coverage_types = ['splunk_coverage', 'chronicle_coverage', 'edr_coverage', 'dlp_coverage', 'tanium_coverage']
        
        for coverage_type in coverage_types:
            for indicator in coverage_indicators:
                for i in range(50):
                    samples.append((indicator, coverage_type))
        
        return samples
    
    def _looks_like_hostname(self, value):
        if not value or len(value) < 2 or len(value) > 253:
            return False
        return bool(re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$|^[a-zA-Z0-9]+$', value))
    
    def _looks_like_domain(self, value):
        if not value or '.' not in value:
            return False
        return bool(re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*\.[a-zA-Z]{2,}$', value))

class HyperIntelligentContentAnalyzer:
    def __init__(self):
        self.device = torch.device('mps' if torch.backends.mps.is_available() else 'cpu')
        logger.info(f"Initializing hyper-advanced ML on device: {self.device}")
        
        self.model = HyperAdvancedMLContentClassifier().to(self.device)
        self.dataset_builder = CybersecurityDatasetBuilder()
        self.training_complete = False
        self.confidence_threshold = 0.85
        
        if torch.backends.mps.is_available():
            torch.mps.set_per_process_memory_fraction(0.95)
            logger.info("MPS GPU memory fraction set to 95%")
    
    async def initialize_hyperintelligent_training(self):
        logger.info("Initializing hyper-intelligent training with massive cybersecurity datasets")
        
        training_data = await self.dataset_builder.build_massive_training_dataset()
        
        logger.info(f"Training ultra-advanced model on {len(training_data)} cybersecurity samples")
        await self._train_hyperadvanced_model(training_data)
        
        self.training_complete = True
        logger.info("Hyper-intelligent content analysis training complete")
    
    async def _train_hyperadvanced_model(self, training_data):
        class CybersecurityDataset(Dataset):
            def __init__(self, data, tokenizer, max_length=512):
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
        
        dataset = CybersecurityDataset(training_data, self.dataset_builder.tokenizer)
        dataloader = DataLoader(dataset, batch_size=32, shuffle=True, num_workers=8)
        
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=1e-5, weight_decay=0.01)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=100)
        criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
        
        self.model.train()
        
        for epoch in range(50):
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
                
                if batch_count % 100 == 0:
                    logger.info(f"Epoch {epoch}, Batch {batch_count}, Loss: {loss.item():.4f}")
            
            scheduler.step()
            avg_loss = total_loss / batch_count
            logger.info(f"Epoch {epoch} complete, Average Loss: {avg_loss:.4f}")
            
            if epoch % 10 == 0:
                torch.mps.empty_cache() if self.device.type == 'mps' else None
        
        self.model.eval()
        logger.info("Hyper-advanced model training complete")
    
    async def analyze_cell_content_hyperintelligent(self, content: str, context: Dict = None) -> Tuple[str, float, Dict]:
        if not self.training_complete:
            await self.initialize_hyperintelligent_training()
        
        if not content or len(str(content).strip()) == 0:
            return 'unknown', 0.0, {}
        
        content_str = str(content).strip()
        
        with torch.no_grad():
            encoding = self.dataset_builder.tokenizer(
                content_str,
                truncation=True,
                padding='max_length',
                max_length=512,
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
            
            advanced_analysis = await self._perform_advanced_content_analysis(content_str, context)
            
            if confidence > self.confidence_threshold:
                return field_type, confidence, advanced_analysis
            else:
                return 'unknown', confidence, advanced_analysis
    
    async def _perform_advanced_content_analysis(self, content: str, context: Dict = None) -> Dict:
        analysis = {
            'content_length': len(content),
            'content_type': self._analyze_content_type(content),
            'pattern_features': self._extract_pattern_features(content),
            'semantic_features': await self._extract_semantic_features(content),
            'context_relevance': self._calculate_context_relevance(content, context),
            'cybersecurity_relevance': self._calculate_cybersecurity_relevance(content)
        }
        
        return analysis
    
    def _analyze_content_type(self, content: str) -> Dict[str, bool]:
        return {
            'is_numeric': content.isdigit(),
            'is_alphanumeric': content.isalnum(),
            'has_special_chars': bool(re.search(r'[^a-zA-Z0-9]', content)),
            'has_dots': '.' in content,
            'has_dashes': '-' in content,
            'has_underscores': '_' in content,
            'has_spaces': ' ' in content,
            'is_ip_like': bool(re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', content)),
            'is_mac_like': bool(re.match(r'^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$', content)),
            'is_hostname_like': bool(re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$', content)),
            'is_fqdn_like': bool(re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*\.[a-zA-Z]{2,}$', content))
        }
    
    def _extract_pattern_features(self, content: str) -> Dict[str, Any]:
        features = {
            'length': len(content),
            'digit_ratio': sum(c.isdigit() for c in content) / len(content) if content else 0,
            'alpha_ratio': sum(c.isalpha() for c in content) / len(content) if content else 0,
            'special_char_ratio': sum(not c.isalnum() for c in content) / len(content) if content else 0,
            'uppercase_ratio': sum(c.isupper() for c in content) / len(content) if content else 0,
            'word_count': len(content.split()),
            'unique_chars': len(set(content)),
            'repeating_patterns': self._find_repeating_patterns(content)
        }
        
        return features
    
    async def _extract_semantic_features(self, content: str) -> Dict[str, Any]:
        cybersec_keywords = [
            'server', 'workstation', 'desktop', 'laptop', 'endpoint', 'device',
            'production', 'staging', 'development', 'test', 'qa',
            'windows', 'linux', 'unix', 'macos',
            'critical', 'high', 'medium', 'low',
            'finance', 'hr', 'it', 'ops', 'sales', 'marketing',
            'splunk', 'chronicle', 'crowdstrike', 'tanium'
        ]
        
        content_lower = content.lower()
        keyword_matches = [kw for kw in cybersec_keywords if kw in content_lower]
        
        return {
            'cybersec_keywords': keyword_matches,
            'keyword_count': len(keyword_matches),
            'semantic_density': len(keyword_matches) / len(content.split()) if content.split() else 0
        }
    
    def _calculate_context_relevance(self, content: str, context: Dict = None) -> float:
        if not context:
            return 0.5
        
        relevance_score = 0.5
        
        table_name = context.get('table_name', '').lower()
        if any(indicator in table_name for indicator in ['endpoint', 'device', 'asset', 'computer']):
            relevance_score += 0.2
        
        if any(indicator in table_name for indicator in ['security', 'log', 'event']):
            relevance_score += 0.15
        
        return min(1.0, relevance_score)
    
    def _calculate_cybersecurity_relevance(self, content: str) -> float:
        content_lower = content.lower()
        
        cybersec_indicators = [
            'srv', 'web', 'app', 'db', 'sql', 'ad', 'dc', 'dns', 'dhcp',
            'prod', 'dev', 'test', 'stage', 'qa',
            'win', 'linux', 'unix', 'cent', 'ubuntu', 'redhat',
            'critical', 'high', 'medium', 'low',
            'fin', 'hr', 'it', 'ops', 'eng'
        ]
        
        matches = sum(1 for indicator in cybersec_indicators if indicator in content_lower)
        return min(1.0, matches / 5.0)
    
    def _find_repeating_patterns(self, content: str) -> List[str]:
        patterns = []
        
        for length in range(2, min(len(content) // 2 + 1, 10)):
            for start in range(len(content) - length + 1):
                pattern = content[start:start + length]
                if content.count(pattern) > 1:
                    patterns.append(pattern)
        
        return list(set(patterns))

class UltraAdvancedEntityResolver:
    def __init__(self):
        self.content_analyzer = HyperIntelligentContentAnalyzer()
        self.identity_graph = nx.Graph()
        self.entity_clusters = {}
        self.processing_stats = {
            'cells_analyzed': 0,
            'entities_discovered': 0,
            'high_confidence_classifications': 0
        }
    
    async def scan_all_table_content_hyperintelligent(self, client_managers: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Starting hyper-intelligent content-based scanning of ALL table cells")
        
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
                            logger.info(f"Hyper-analyzing table: {table_path}")
                            
                            table_entities, cells_processed = await self._analyze_entire_table_content(
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
                            
                            if total_tables_processed % 10 == 0:
                                logger.info(f"Processed {total_tables_processed} tables, analyzed {total_cells_analyzed:,} cells")
                            
                        except Exception as e:
                            logger.error(f"Failed to process table {table_path}: {e}")
        
        logger.info(f"Hyper-intelligent scanning complete: {len(discovered_entities)} entities from {total_cells_analyzed:,} cells")
        
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
    
    async def _analyze_entire_table_content(self, client, table_path: str) -> Tuple[Dict[str, Any], int]:
        try:
            table = client.get_table(table_path)
            
            if not table.schema or table.num_rows == 0:
                return {}, 0
            
            columns = [field.name for field in table.schema]
            
            content_scan_query = f"""
            SELECT *
            FROM `{table_path}`
            LIMIT 100000
            """
            
            job = client.query(content_scan_query)
            results = list(job.result())
            
            discovered_entities = {}
            cells_processed = 0
            
            logger.info(f"Analyzing {len(results)} rows x {len(columns)} columns = {len(results) * len(columns):,} cells")
            
            entity_evidence = defaultdict(list)
            
            with ThreadPoolExecutor(max_workers=16) as executor:
                analysis_tasks = []
                
                for row_idx, row in enumerate(results):
                    for col_idx, column_name in enumerate(columns):
                        if col_idx < len(row) and row[col_idx] is not None:
                            cell_content = str(row[col_idx]).strip()
                            
                            if cell_content and len(cell_content) > 1:
                                context = {
                                    'table_name': table_path.split('.')[-1],
                                    'column_name': column_name,
                                    'row_index': row_idx,
                                    'column_index': col_idx
                                }
                                
                                task = executor.submit(
                                    asyncio.run,
                                    self.content_analyzer.analyze_cell_content_hyperintelligent(
                                        cell_content, context
                                    )
                                )
                                analysis_tasks.append((cell_content, context, task))
                                cells_processed += 1
                
                logger.info(f"Processing {len(analysis_tasks)} cell analysis tasks")
                
                for cell_content, context, task in analysis_tasks:
                    try:
                        field_type, confidence, analysis = task.result(timeout=10)
                        
                        if confidence > 0.7 and field_type != 'unknown':
                            entity_evidence[cell_content].append({
                                'field_type': field_type,
                                'confidence': confidence,
                                'context': context,
                                'analysis': analysis,
                                'table_source': table_path
                            })
                    except Exception as e:
                        continue
            
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
                            'all_properties': self._extract_all_properties(evidence_list)
                        }
            
            return discovered_entities, cells_processed
            
        except Exception as e:
            logger.error(f"Table content analysis failed for {table_path}: {e}")
            return {}, 0
    
    def _generate_entity_id(self, content: str, field_type: str) -> str:
        normalized_content = content.upper().strip()
        return f"{field_type}_{hashlib.md5(normalized_content.encode()).hexdigest()[:12]}"
    
    def _extract_all_properties(self, evidence_list: List[Dict]) -> Dict[str, Any]:
        all_properties = {}
        
        for evidence in evidence_list:
            context = evidence['context']
            analysis = evidence['analysis']
            
            table_name = context['table_name']
            column_name = context['column_name']
            
            property_mappings = {
                'infrastructure': ['infra', 'infrastructure', 'type', 'platform'],
                'system_class': ['system', 'os', 'operating', 'platform', 'class'],
                'region': ['region', 'location', 'geo', 'datacenter', 'zone'],
                'business_unit': ['business', 'unit', 'department', 'org', 'division'],
                'application': ['application', 'app', 'service', 'software']
            }
            
            for prop_name, keywords in property_mappings.items():
                if any(keyword in column_name.lower() for keyword in keywords):
                    if prop_name not in all_properties:
                        all_properties[prop_name] = []
                    all_properties[prop_name].append({
                        'column': column_name,
                        'table': table_name,
                        'analysis': analysis
                    })
        
        return all_properties
    
    def _merge_entity_data(self, existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
        merged = existing.copy()
        
        merged['evidence'].extend(new['evidence'])
        merged['table_sources'].extend(new['table_sources'])
        merged['table_sources'] = list(set(merged['table_sources']))
        
        for prop_name, prop_data in new['all_properties'].items():
            if prop_name not in merged['all_properties']:
                merged['all_properties'][prop_name] = []
            merged['all_properties'][prop_name].extend(prop_data)
        
        all_confidences = [ev['confidence'] for ev in merged['evidence']]
        merged['confidence'] = max(all_confidences) if all_confidences else 0.0
        
        return merged

class HyperAdvancedDiscoveryEngine:
    def __init__(self, project_id: str, config: Dict[str, Any], cache_manager, intelligence):
        self.project_id = project_id
        self.config = config
        self.cache = cache_manager
        self.intelligence = intelligence
        self.entity_resolver = UltraAdvancedEntityResolver()
        
        self.stats = {
            'hyperintelligent_mode': True,
            'ml_gpu_accelerated': torch.backends.mps.is_available(),
            'total_cells_analyzed': 0,
            'entities_discovered': 0,
            'processing_time': 0.0
        }
    
    async def discover_assets_hyperintelligently(self, client_managers: Dict[str, Any]) -> Discovery:
        logger.info("Starting hyper-intelligent asset discovery with advanced ML content analysis")
        start_time = datetime.now()
        
        discovery = Discovery()
        
        try:
            scan_results = await self.entity_resolver.scan_all_table_content_hyperintelligent(client_managers)
            
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
                'hyperintelligent_discovery': True,
                'ml_gpu_accelerated': self.stats['ml_gpu_accelerated'],
                'total_cells_analyzed': processing_stats['total_cells_analyzed'],
                'total_tables_processed': processing_stats['total_tables_processed'],
                'avg_cells_per_table': processing_stats['avg_cells_per_table'],
                'processing_time_seconds': processing_time,
                'cells_per_second': processing_stats['total_cells_analyzed'] / max(processing_time, 1),
                'advanced_ml_classifications': True,
                'entity_resolution_applied': True
            }
            
            discovery.insights = await self.intelligence.generate_insights(discovery)
            
            logger.info(f"Hyper-intelligent discovery complete: {len(assets)} assets from {processing_stats['total_cells_analyzed']:,} cells")
            
        except Exception as e:
            logger.error(f"Hyper-intelligent discovery failed: {e}")
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
            
            if 'infrastructure' in properties:
                asset.infra_type = self._extract_best_property_value(properties['infrastructure'])
            
            if 'system_class' in properties:
                asset.system_class = self._extract_best_property_value(properties['system_class'])
            
            if 'region' in properties:
                asset.region = self._extract_best_property_value(properties['region'])
            
            if 'business_unit' in properties:
                asset.business_unit = self._extract_best_property_value(properties['business_unit'])
            
            table_sources = entity_data.get('table_sources', [])
            self._set_coverage_flags_from_sources(asset, table_sources)
            
            asset.sources = len(table_sources)
            asset.confidence = entity_data.get('confidence', 0.0)
            asset.intelligence = min(1.0, len(entity_data.get('evidence', [])) / 10.0)
            asset.quality = self._calculate_asset_quality(entity_data)
            
            return asset
            
        except Exception as e:
            logger.error(f"Failed to convert entity {entity_id} to asset: {e}")
            return None
    
    def _extract_best_property_value(self, property_list: List[Dict]) -> str:
        if not property_list:
            return ""
        
        best_prop = max(property_list, key=lambda x: x.get('analysis', {}).get('cybersecurity_relevance', 0))
        return best_prop.get('column', '')
    
    def _set_coverage_flags_from_sources(self, asset: Asset, table_sources: List[str]):
        asset.cmdb = any('endpoint' in source.lower() or 'cmdb' in source.lower() for source in table_sources)
        asset.splunk = any('splunk' in source.lower() for source in table_sources)
        asset.chronicle = any('chronicle' in source.lower() for source in table_sources)
        asset.crowdstrike = any('crowdstrike' in source.lower() or 'endpointagent' in source.lower() for source in table_sources)
        asset.edr = asset.crowdstrike
        asset.tanium = any('tanium' in source.lower() for source in table_sources)
        asset.dlp = any('dlp' in source.lower() for source in table_sources)
    
    def _calculate_asset_quality(self, entity_data: Dict[str, Any]) -> float:
        evidence_count = len(entity_data.get('evidence', []))
        source_count = len(entity_data.get('table_sources', []))
        confidence = entity_data.get('confidence', 0.0)
        property_count = len(entity_data.get('all_properties', {}))
        
        quality = (
            min(1.0, evidence_count / 5.0) * 0.3 +
            min(1.0, source_count / 3.0) * 0.3 +
            confidence * 0.25 +
            min(1.0, property_count / 5.0) * 0.15
        )
        
        return quality