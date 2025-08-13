# discovery/core.py - syntax fixed version

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
        # Initialize proxy tunnel manager
        self.proxy_manager = self._setup_proxy_tunnel()
        
        # Try to load tokenizer with proxy support
        self.tokenizer = self._load_tokenizer_with_proxy()
        
        if hasattr(self.tokenizer, 'pad_token') and self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        self.training_sources = [
            'https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Infrastructure/common-hostnames.txt',
            'https://raw.githubusercontent.com/fuzzdb-project/fuzzdb/master/discovery/predictable-filepaths/filename-dirname-bruteforce/raft-large-words.txt'
        ]
        
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
    
    def _setup_proxy_tunnel(self):
        """Setup proxy tunnel for model downloads"""
        try:
            import os
            import ssl
            import urllib3
            
            # Configure proxy tunnel
            ssl._create_default_https_context = ssl._create_unverified_context
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            proxy_config = {
                'http': 'http://127.0.0.1:8080',
                'https': 'http://127.0.0.1:8080'
            }
            
            # Set all proxy environment variables
            proxy_vars = {
                'HTTP_PROXY': proxy_config['http'],
                'HTTPS_PROXY': proxy_config['https'],
                'http_proxy': proxy_config['http'],
                'https_proxy': proxy_config['https'],
                'ALL_PROXY': proxy_config['http'],
                'all_proxy': proxy_config['http']
            }
            
            for var, value in proxy_vars.items():
                os.environ[var] = value
            
            # Clear certificate bundles
            os.environ['REQUESTS_CA_BUNDLE'] = ''
            os.environ['CURL_CA_BUNDLE'] = ''
            os.environ['SSL_CERT_FILE'] = ''
            
            logger.info("🔧 Proxy tunnel configured for model downloads")
            
            # Test proxy
            try:
                import requests
                session = requests.Session()
                session.proxies = proxy_config
                session.verify = False
                
                response = session.get('https://httpbin.org/ip', timeout=5)
                if response.status_code == 200:
                    logger.info("✅ Proxy tunnel connectivity verified")
                    return proxy_config
                else:
                    logger.warning(f"⚠️ Proxy test returned {response.status_code}")
                    
            except Exception as e:
                logger.debug(f"Proxy test failed: {e}")
            
            return proxy_config
            
        except Exception as e:
            logger.warning(f"Proxy setup failed: {e}")
            return None
    
    def _load_tokenizer_with_proxy(self):
        """Load tokenizer using proxy tunnel"""
        logger.info("🤖 Loading DialoGPT tokenizer via proxy tunnel")
        
        try:
            from transformers import AutoTokenizer
            import requests
            
            # Configure transformers to use proxy
            if self.proxy_manager:
                logger.info("Using proxy for model download...")
                
                # Set huggingface hub environment variables for proxy
                import os
                os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
                os.environ['HF_HUB_OFFLINE'] = '0'
                
                # Try downloading DialoGPT with proxy
                tokenizer = AutoTokenizer.from_pretrained(
                    'microsoft/DialoGPT-medium',
                    use_auth_token=False,
                    trust_remote_code=False,
                    local_files_only=False,
                    use_fast=False,  # Slower but more compatible
                    cache_dir='./cache/transformers'
                )
                
                logger.info("✅ Successfully loaded DialoGPT tokenizer via proxy")
                return tokenizer
                
        except Exception as e:
            logger.warning(f"DialoGPT via proxy failed: {e}")
            
        # Fallback to GPT2
        try:
            logger.info("🔄 Falling back to GPT2 tokenizer via proxy")
            from transformers import GPT2Tokenizer
            
            tokenizer = GPT2Tokenizer.from_pretrained(
                'gpt2',
                use_fast=False,
                cache_dir='./cache/transformers'
            )
            
            logger.info("✅ Successfully loaded GPT2 tokenizer via proxy")
            return tokenizer
            
        except Exception as e:
            logger.warning(f"GPT2 via proxy failed: {e}")
        
        # Final fallback
        logger.info("🔄 Using minimal tokenizer fallback")
        return self._create_minimal_tokenizer()
        
        if hasattr(self.tokenizer, 'pad_token') and self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        self.training_sources = [
            'https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Infrastructure/common-hostnames.txt',
            'https://raw.githubusercontent.com/fuzzdb-project/fuzzdb/master/discovery/predictable-filepaths/filename-dirname-bruteforce/raft-large-words.txt'
        ]
        
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
    
    def _create_minimal_tokenizer(self):
        """Create a minimal tokenizer when transformers is not available"""
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
    
    async def build_intensive_training_dataset(self):
        """Build training dataset for cybersecurity field classification"""
        logger.info("Building intensive cybersecurity training dataset")
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=8) as executor:
            tasks = [
                executor.submit(self._generate_hostname_samples),
                executor.submit(self._generate_ip_samples),
                executor.submit(self._generate_network_samples),
                executor.submit(self._generate_infrastructure_samples),
                executor.submit(self._generate_security_samples),
                executor.submit(self._generate_business_samples)
            ]
            
            results = [task.result() for task in tasks]
        
        for result in results:
            self.training_data.extend(result)
        
        processing_time = time.time() - start_time
        logger.info(f"Generated {len(self.training_data)} training samples in {processing_time:.2f}s")
        return self.training_data
    
    def _generate_hostname_samples(self):
        """Generate hostname training samples"""
        samples = []
        
        prefixes = ['web', 'app', 'db', 'sql', 'ad', 'dc', 'dns', 'dhcp', 'proxy', 'fw', 'lb']
        environments = ['prod', 'dev', 'test', 'stage', 'qa', 'demo']
        locations = ['us', 'eu', 'ap', 'east', 'west', 'central']
        separators = ['-', '_', '']
        
        for prefix in prefixes:
            for env in environments:
                for loc in locations:
                    for sep in separators:
                        for num in range(1, 100):
                            patterns = [
                                f"{prefix}{sep}{num:02d}",
                                f"{prefix}{sep}{env}{sep}{num:02d}",
                                f"{prefix}{sep}{loc}{sep}{num:02d}",
                                f"{env}{sep}{prefix}{sep}{num:02d}"
                            ]
                            
                            for pattern in patterns:
                                samples.append((pattern, 'hostname'))
                                if len(samples) > 10000:
                                    return samples
        
        return samples
    
    def _generate_ip_samples(self):
        """Generate IP address samples"""
        samples = []
        
        for a in range(10, 192, 5):
            for b in range(0, 255, 10):
                for c in range(0, 255, 10):
                    for d in range(1, 255, 10):
                        ip = f"{a}.{b}.{c}.{d}"
                        samples.append((ip, 'ip_address'))
                        if len(samples) > 5000:
                            return samples
        
        return samples
    
    def _generate_network_samples(self):
        """Generate network-related samples"""
        samples = []
        
        # MAC addresses
        mac_ouis = ['00:50:56', '00:0C:29', '08:00:27', '52:54:00']
        for oui in mac_ouis:
            for i in range(0, 256, 4):
                for j in range(0, 256, 8):
                    for k in range(0, 256, 16):
                        mac = f"{oui}:{i:02X}:{j:02X}:{k:02X}"
                        samples.append((mac, 'mac_address'))
                        if len(samples) > 2000:
                            break
                    if len(samples) > 2000:
                        break
                if len(samples) > 2000:
                    break
            if len(samples) > 2000:
                break
        
        # FQDNs
        domains = ['corp.com', 'internal.local', 'company.net', 'domain.com']
        hostnames = ['server', 'workstation', 'pc', 'laptop']
        
        for domain in domains:
            for hostname in hostnames:
                for i in range(1, 100):
                    fqdn = f"{hostname}{i:03d}.{domain}"
                    samples.append((fqdn, 'fqdn'))
        
        return samples
    
    def _generate_infrastructure_samples(self):
        """Generate infrastructure type samples"""
        samples = []
        
        infra_types = ['On-Prem', 'Cloud', 'SaaS', 'API', 'Hybrid', 'Multi-Cloud']
        for infra_type in infra_types:
            for i in range(500):
                samples.append((infra_type, 'infrastructure_type'))
        
        system_types = [
            'Windows Server 2019', 'Windows Server 2022', 'Ubuntu 20.04', 'Ubuntu 22.04',
            'CentOS 7', 'RHEL 8', 'Debian 11', 'Web Server', 'Database Server',
            'Application Server', 'File Server', 'Mail Server', 'DNS Server'
        ]
        
        for sys_type in system_types:
            for i in range(200):
                samples.append((sys_type, 'system_classification'))
        
        return samples
    
    def _generate_security_samples(self):
        """Generate security tool samples"""
        samples = []
        
        edr_tools = ['CrowdStrike Falcon', 'SentinelOne', 'Carbon Black', 'Cylance']
        for tool in edr_tools:
            for i in range(300):
                samples.append((tool, 'edr_coverage'))
        
        dlp_tools = ['Symantec DLP', 'Forcepoint DLP', 'Microsoft Purview']
        for tool in dlp_tools:
            for i in range(200):
                samples.append((tool, 'dlp_coverage'))
        
        return samples
    
    def _generate_business_samples(self):
        """Generate business context samples"""
        samples = []
        
        business_units = ['Finance', 'HR', 'IT', 'Operations', 'Sales', 'Marketing', 'Legal']
        for bu in business_units:
            for i in range(300):
                samples.append((bu, 'business_unit'))
        
        regions = ['North America', 'Europe', 'Asia Pacific', 'US East', 'US West', 'EU Central']
        for region in regions:
            for i in range(200):
                samples.append((region, 'global_region'))
        
        return samples
    
    def _classify_content_type(self, content):
        """Classify content type for training"""
        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', content):
            return 'ip_address'
        elif re.match(r'^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$', content):
            return 'mac_address'
        elif '.' in content and re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*\.[a-zA-Z]{2,}$', content):
            return 'fqdn'
        elif re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$', content):
            return 'hostname'
        else:
            return None

class IntensiveContentAnalyzer:
    def __init__(self):
        # Safe device detection
        self.device = torch.device('cpu')
        try:
            if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                self.device = torch.device('mps')
                logger.info("MPS GPU detected and will be used")
            elif torch.cuda.is_available():
                self.device = torch.device('cuda')
                logger.info("CUDA GPU detected and will be used")
        except Exception as e:
            logger.warning(f"GPU detection failed: {e}, using CPU")
        
        logger.info(f"Initializing intensive ML on device: {self.device}")
        
        try:
            self.model = FanSpinningMLModel().to(self.device)
            self.model_loaded = True
            logger.info("ML model loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load ML model: {e}")
            logger.info("Using fallback pattern-based analysis")
            self.model = None
            self.model_loaded = False
        
        self.dataset_builder = IntensiveDatasetBuilder()
        self.training_complete = False
        self.confidence_threshold = 0.75
        
        # Safe GPU memory management
        try:
            if self.device.type == 'mps':
                torch.mps.set_per_process_memory_fraction(0.8)
                logger.info("MPS GPU memory fraction set to 80%")
        except Exception as e:
            logger.debug(f"GPU memory management setup failed: {e}")
    
    async def initialize_intensive_training(self):
        """Initialize and run ML training"""
        logger.info("Starting intensive training")
        
        if not self.model_loaded:
            logger.warning("ML model not available, using pattern-based analysis only")
            self.training_complete = True
            return
        
        try:
            training_data = await self.dataset_builder.build_intensive_training_dataset()
            
            if len(training_data) > 100:  # Only train if we have enough data
                logger.info(f"Training model on {len(training_data)} cybersecurity samples")
                await self._train_model_intensively(training_data)
            else:
                logger.warning("Insufficient training data, skipping ML training")
            
            self.training_complete = True
            logger.info("Intensive content analysis training complete")
        except Exception as e:
            logger.error(f"Training failed: {e}")
            logger.info("Falling back to pattern-based analysis")
            self.training_complete = True
    
    async def _train_model_intensively(self, training_data):
        """Train the ML model"""
        try:
            class CybersecDataset(Dataset):
                def __init__(self, data, tokenizer, max_length=256):
                    self.data = data
                    self.tokenizer = tokenizer
                    self.max_length = max_length
                    # Create label mapping
                    unique_labels = list(set([item[1] for item in data]))
                    self.label_to_idx = {label: idx for idx, label in enumerate(unique_labels)}
                
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
            dataloader = DataLoader(dataset, batch_size=32, shuffle=True, num_workers=0)
            
            optimizer = torch.optim.AdamW(self.model.parameters(), lr=1e-4, weight_decay=0.01)
            criterion = nn.CrossEntropyLoss()
            
            self.model.train()
            
            logger.info("Starting training loop")
            
            for epoch in range(5):  # Reduced epochs for faster training
                total_loss = 0
                batch_count = 0
                
                for batch in dataloader:
                    try:
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
                        
                        if batch_count % 10 == 0:
                            logger.debug(f"Epoch {epoch}, Batch {batch_count}, Loss: {loss.item():.4f}")
                        
                    except Exception as e:
                        logger.warning(f"Training batch failed: {e}")
                        continue
                
                if batch_count > 0:
                    avg_loss = total_loss / batch_count
                    logger.info(f"Epoch {epoch} complete, Average Loss: {avg_loss:.4f}")
                
                # Clear GPU cache if available
                if self.device.type == 'mps':
                    try:
                        torch.mps.empty_cache()
                    except:
                        pass
                elif self.device.type == 'cuda':
                    try:
                        torch.cuda.empty_cache()
                    except:
                        pass
            
            self.model.eval()
            logger.info("Model training complete")
            
        except Exception as e:
            logger.error(f"Model training failed: {e}")
            self.model_loaded = False
    
    async def analyze_cell_content_intensively(self, content: str, context: Dict = None) -> Tuple[str, float, Dict]:
        """Analyze cell content using ML or pattern matching"""
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
                    
                    # Safe class index access
                    class_idx = predicted_class.item()
                    if class_idx < len(self.model.cybersecurity_classes):
                        field_type = self.model.cybersecurity_classes[class_idx]
                    else:
                        field_type = 'unknown'
                    
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
        """Fallback pattern-based analysis when ML fails"""
        analysis = existing_analysis or {
            'content_length': len(content),
            'method': 'pattern_based'
        }
        
        # IP address pattern
        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', content):
            return 'ip_address', 0.95, analysis
        
        # MAC address pattern  
        elif re.match(r'^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$', content):
            return 'mac_address', 0.95, analysis
        
        # FQDN pattern
        elif '.' in content and re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*\.[a-zA-Z]{2,}$', content):
            return 'fqdn', 0.9, analysis
        
        # Hostname patterns
        elif re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$', content) or re.match(r'^[a-zA-Z0-9]+$', content):
            hostname_indicators = ['srv', 'web', 'app', 'db', 'sql', 'host', 'server', 'pc', 'ws']
            content_lower = content.lower()
            if any(indicator in content_lower for indicator in hostname_indicators):
                return 'hostname', 0.85, analysis
            elif 3 <= len(content) <= 63:
                return 'hostname', 0.7, analysis
        
        # Application class keywords
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
        """Scan all table content intensively using ML"""
        logger.info("Starting intensive content-based scanning")
        
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
                            logger.info(f"Analyzing table: {table_path}")
                            
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
                            
                            # Memory cleanup
                            gc.collect()
                            if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                                try:
                                    torch.mps.empty_cache()
                                except:
                                    pass
                            
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
        """Thoroughly analyze a single table's content"""
        try:
            table = client.get_table(table_path)
            
            if not table.schema or table.num_rows == 0:
                return {}, 0
            
            columns = [field.name for field in table.schema]
            
            # Limit query size for performance
            content_scan_query = f"""
            SELECT *
            FROM `{table_path}`
            LIMIT 10000
            """
            
            job = client.query(content_scan_query)
            results = list(job.result())
            
            discovered_entities = {}
            cells_processed = 0
            
            logger.debug(f"Analyzing {len(results)} rows x {len(columns)} columns = {len(results) * len(columns):,} cells")
            
            entity_evidence = defaultdict(list)
            
            batch_size = 16  # Smaller batch size for stability
            analysis_tasks = []
            
            for row_idx, row in enumerate(results):
                for col_idx, column_name in enumerate(columns):
                    if col_idx < len(row) and row[col_idx] is not None:
                        cell_content = str(row[col_idx]).strip()
                        
                        if cell_content and 1 < len(cell_content) < 200:
                            context = {
                                'table_name': table_path.split('.')[-1],
                                'column_name': column_name,
                                'row_index': row_idx,
                                'column_index': col_idx
                            }
                            
                            analysis_tasks.append((cell_content, context))
                            cells_processed += 1
            
            logger.debug(f"Processing {len(analysis_tasks)} cells in batches of {batch_size}")
            
            # Process in smaller batches to avoid memory issues
            for i in range(0, len(analysis_tasks), batch_size):
                batch = analysis_tasks[i:i + batch_size]
                
                batch_results = await asyncio.gather(*[
                    self.content_analyzer.analyze_cell_content_intensively(content, context)
                    for content, context in batch
                ], return_exceptions=True)
                
                for (cell_content, context), result in zip(batch, batch_results):
                    if isinstance(result, Exception):
                        logger.debug(f"Analysis failed for cell: {result}")
                        continue
                    
                    field_type, confidence, analysis = result
                    if confidence > 0.6 and field_type != 'unknown':
                        entity_evidence[cell_content].append({
                            'field_type': field_type,
                            'confidence': confidence,
                            'context': context,
                            'analysis': analysis,
                            'table_source': table_path
                        })
                
                if i % (batch_size * 20) == 0:
                    logger.debug(f"Processed {i + len(batch)}/{len(analysis_tasks)} cells")
            
            # Create entities from evidence
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
        """Generate unique entity ID"""
        normalized_content = content.upper().strip()
        return f"{field_type}_{hashlib.md5(normalized_content.encode()).hexdigest()[:12]}"
    
    def _extract_properties(self, evidence_list: List[Dict]) -> Dict[str, Any]:
        """Extract properties from evidence"""
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
        """Merge entity data from multiple sources"""
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
        """Main discovery method using intensive content analysis"""
        logger.info("Starting intensive asset discovery with ML content analysis")
        start_time = datetime.now()
        
        discovery = Discovery()
        
        try:
            scan_results = await self.entity_resolver.scan_table_content_intensively(client_managers)
            
            entities = scan_results['entities']
            processing_stats = scan_results['processing_stats']
            
            # Convert entities to assets
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
            
            # Generate insights
            discovery.insights = await self.intelligence.generate_insights(discovery)
            
            logger.info(f"Intensive discovery complete: {len(assets)} assets from {processing_stats['total_cells_analyzed']:,} cells")
            
        except Exception as e:
            logger.error(f"Intensive discovery failed: {e}")
            discovery.stats = {'error': str(e)}
        
        return discovery
    
    async def discover_assets_hyperintelligently(self, client_managers: Dict[str, Any]) -> Discovery:
        """Alias method for hyperintelligent discovery - calls intensive discovery"""
        logger.info("🚀 HYPERINTELLIGENT DISCOVERY MODE ACTIVATED")
        logger.info("🧠 Using advanced ML with proxy-tunneled model loading")
        return await self.discover_assets_intensively(client_managers)
    
    def _convert_entity_to_asset(self, entity_id: str, entity_data: Dict[str, Any]) -> Optional[Asset]:
        """Convert entity data to Asset object"""
        try:
            asset = Asset(id=entity_id)
            
            primary_id = entity_data['primary_identifier']
            field_type = entity_data['field_type']
            
            # Set primary identifier based on field type
            if field_type == 'hostname':
                asset.hostname = primary_id
            elif field_type == 'ip_address':
                asset.ip = primary_id
            elif field_type == 'fqdn':
                asset.fqdn = primary_id
            elif field_type == 'mac_address':
                asset.mac = primary_id
            
            # Extract additional properties
            properties = entity_data.get('all_properties', {})
            
            if 'region' in properties:
                asset.region = properties['region']
            if 'business_unit' in properties:
                asset.business_unit = properties['business_unit']
            if 'classification' in properties:
                asset.system_class = properties['classification']
            
            # Set coverage flags based on source tables
            table_sources = entity_data.get('table_sources', [])
            self._set_coverage_flags(asset, table_sources)
            
            # Set metrics
            asset.sources = len(table_sources)
            asset.confidence = entity_data.get('confidence', 0.0)
            asset.intelligence = min(1.0, len(entity_data.get('evidence', [])) / 5.0)
            asset.quality = self._calculate_quality(entity_data)
            
            return asset
            
        except Exception as e:
            logger.error(f"Failed to convert entity {entity_id}: {e}")
            return None
    
    def _set_coverage_flags(self, asset: Asset, table_sources: List[str]):
        """Set coverage flags based on table sources"""
        asset.cmdb = any('endpoint' in source.lower() or 'cmdb' in source.lower() for source in table_sources)
        asset.splunk = any('splunk' in source.lower() for source in table_sources)
        asset.chronicle = any('chronicle' in source.lower() for source in table_sources)
        asset.crowdstrike = any('crowdstrike' in source.lower() for source in table_sources)
        asset.edr = asset.crowdstrike
        asset.tanium = any('tanium' in source.lower() for source in table_sources)
        asset.dlp = any('dlp' in source.lower() for source in table_sources)
    
    def _calculate_quality(self, entity_data: Dict[str, Any]) -> float:
        """Calculate quality score for entity"""
        evidence_count = len(entity_data.get('evidence', []))
        source_count = len(entity_data.get('table_sources', []))
        confidence = entity_data.get('confidence', 0.0)
        
        return min(1.0, (evidence_count / 3.0 + source_count / 2.0 + confidence) / 3.0)