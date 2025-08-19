import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from transformers import AutoModel, AutoTokenizer
import hashlib
import re

class QuantumNeuralNetwork(nn.Module):
    def __init__(self, input_dim=768, hidden_dims=[512, 256, 128], num_classes=17):
        super().__init__()
        self.encoder = nn.ModuleList()
        dims = [input_dim] + hidden_dims
        for i in range(len(dims)-1):
            self.encoder.append(nn.Linear(dims[i], dims[i+1]))
            self.encoder.append(nn.LayerNorm(dims[i+1]))
            self.encoder.append(nn.Dropout(0.1))
        
        self.attention = nn.MultiheadAttention(hidden_dims[-1], num_heads=8, batch_first=True)
        self.classifier = nn.Linear(hidden_dims[-1], num_classes)
        self.confidence = nn.Linear(hidden_dims[-1], 1)
        
    def forward(self, x):
        for layer in self.encoder:
            if isinstance(layer, nn.Linear):
                x = F.gelu(layer(x))
            else:
                x = layer(x)
        
        if len(x.shape) == 2:
            x = x.unsqueeze(1)
        
        attn_output, _ = self.attention(x, x, x)
        x = x + attn_output
        
        logits = self.classifier(x.squeeze(1))
        conf = torch.sigmoid(self.confidence(x.squeeze(1)))
        
        return logits, conf

class HyperIntelligence:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
        self.transformer = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2").to(self.device)
        self.neural_net = QuantumNeuralNetwork().to(self.device)
        
        self.field_mappings = {
            'hostname': ['hostname', 'host_name', 'computer_name', 'device_name', 'machine_name', 'system_name', 'server_name', 'endpoint_name', 'asset_name'],
            'infrastructure_type': ['infrastructure_type', 'infra_type', 'platform_type', 'hosting_type', 'deployment_type', 'cloud', 'onprem', 'on_premise', 'saas', 'api'],
            'region': ['region', 'global_region', 'geo_region', 'geographic_region', 'location_region', 'area', 'territory'],
            'country': ['country', 'nation', 'country_code', 'country_name', 'geo_country'],
            'business_unit': ['business_unit', 'bu', 'department', 'division', 'org_unit', 'organization', 'business_division'],
            'datacenter': ['datacenter', 'data_center', 'dc', 'site', 'facility', 'location', 'data_centre'],
            'cloud_region': ['cloud_region', 'aws_region', 'azure_region', 'gcp_region', 'cloud_zone', 'availability_zone'],
            'cio': ['cio', 'cio_org', 'it_org', 'technology_org', 'it_organization', 'tech_org'],
            'apm': ['apm', 'application_monitoring', 'app_performance', 'performance_monitoring'],
            'application_class': ['application_class', 'app_class', 'app_type', 'application_type', 'app_category'],
            'system_classification': ['system_class', 'os_type', 'platform', 'operating_system', 'system_type', 'server_type'],
            'domain': ['domain', 'dns_domain', 'ad_domain', 'active_directory', 'dns', 'fqdn'],
            'ip_address': ['ip_address', 'ip', 'ipv4', 'ipv6', 'ip_addr', 'network_address'],
            'mac_address': ['mac_address', 'mac', 'physical_address', 'ethernet_address', 'hardware_address']
        }
        
        self.log_type_patterns = {
            'network': {
                'patterns': ['firewall', 'ids', 'ips', 'ndr', 'proxy', 'dns', 'waf', 'traffic'],
                'fields': ['source_ip', 'dest_ip', 'protocol', 'port', 'detection_signature', 'dns_record', 'http_headers'],
                'visibility': ['url_fqdn_coverage', 'cmdb_visibility', 'network_zones', 'ipam_public_ip', 'geolocation', 'vpc']
            },
            'endpoint': {
                'patterns': ['os_logs', 'edr', 'dlp', 'fim', 'winEvt', 'linux_syslog'],
                'fields': ['system_name', 'ip', 'filename'],
                'visibility': ['cmdb_visibility', 'crowdstrike_coverage', 'log_ingest_volume']
            },
            'cloud': {
                'patterns': ['cloud_event', 'cloud_load_balancer', 'cloud_config', 'theom', 'wiz', 'cloud_security'],
                'fields': [],
                'visibility': ['vpc', 'ipam_public_ip', 'url_fqdn_coverage', 'crowdstrike_coverage']
            },
            'application': {
                'patterns': ['web_logs', 'api_gateway', 'http_access'],
                'fields': ['authentication_attempts', 'privilege_escalation', 'identity_create_modify_destroy'],
                'visibility': ['url_fqdn_coverage', 'control_coverage', 'domain', 'internal', 'external', 'controls']
            },
            'identity': {
                'patterns': ['authentication', 'privilege', 'identity', 'access'],
                'fields': ['authentication_attempts', 'privilege_escalation', 'identity_operations'],
                'visibility': ['domain', 'internal', 'external', 'controls']
            }
        }
        
        self.system_classifications = {
            'web_server': ['web', 'apache', 'nginx', 'iis', 'tomcat', 'http'],
            'windows_server': ['windows', 'win', 'microsoft', 'server2019', 'server2016'],
            'linux_server': ['linux', 'ubuntu', 'centos', 'rhel', 'debian', 'suse'],
            'nix': ['aix', 'solaris', 'unix', 'hpux', 'bsd'],
            'mainframe': ['mainframe', 'zos', 'mvs', 'as400'],
            'database': ['database', 'sql', 'oracle', 'postgres', 'mysql', 'mongodb', 'db'],
            'network_appliance': ['firewall', 'router', 'switch', 'proxy', 'loadbalancer', 'fw', 'ndr']
        }
        
        self.infrastructure_types = {
            'on_premise': ['onprem', 'on-prem', 'datacenter', 'physical', 'bare_metal', 'local'],
            'cloud': ['aws', 'azure', 'gcp', 'cloud', 'ec2', 'vm', 'virtual'],
            'saas': ['saas', 'software_as_service', 'hosted', 'managed_service'],
            'api': ['api', 'endpoint', 'service', 'gateway', 'rest', 'soap']
        }
        
        self.regional_mappings = {
            'na': ['north_america', 'usa', 'united_states', 'canada', 'mexico', 'us-east', 'us-west'],
            'latam': ['latin_america', 'south_america', 'brazil', 'argentina', 'chile', 'colombia'],
            'europe': ['europe', 'eu', 'uk', 'germany', 'france', 'spain', 'italy', 'emea'],
            'apac': ['asia', 'pacific', 'japan', 'china', 'india', 'australia', 'singapore']
        }
    
    def encode_text(self, text: str) -> torch.Tensor:
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = self.transformer(**inputs)
            embeddings = outputs.last_hidden_state.mean(dim=1)
        return embeddings
    
    def classify_column(self, column_name: str, sample_values: List[str]) -> Tuple[str, float, Dict[str, Any]]:
        text = f"{column_name} {' '.join(sample_values[:10])}"
        embeddings = self.encode_text(text)
        
        with torch.no_grad():
            logits, confidence = self.neural_net(embeddings)
            probs = F.softmax(logits, dim=-1)
            max_prob, pred_idx = torch.max(probs, dim=-1)
        
        field_types = list(self.field_mappings.keys()) + ['unknown']
        predicted_type = field_types[pred_idx.item()] if pred_idx.item() < len(field_types) else 'unknown'
        
        pattern_score = self._calculate_pattern_score(column_name, sample_values, predicted_type)
        semantic_score = self._calculate_semantic_score(text, predicted_type)
        
        final_confidence = (max_prob.item() * 0.5 + pattern_score * 0.3 + semantic_score * 0.2)
        
        metadata = {
            'ml_confidence': max_prob.item(),
            'pattern_score': pattern_score,
            'semantic_score': semantic_score,
            'neural_confidence': confidence.item(),
            'method': 'quantum_neural_classification'
        }
        
        return predicted_type, final_confidence, metadata
    
    def _calculate_pattern_score(self, column_name: str, samples: List[str], field_type: str) -> float:
        if field_type not in self.field_mappings:
            return 0.0
        
        patterns = self.field_mappings[field_type]
        column_lower = column_name.lower()
        
        name_score = max([1.0 if p in column_lower else 0.0 for p in patterns], default=0.0)
        
        if field_type == 'hostname':
            hostname_pattern = r'^[a-zA-Z][a-zA-Z0-9\-]{1,62}[a-zA-Z0-9]$'
            valid_samples = sum(1 for s in samples if re.match(hostname_pattern, s))
            content_score = valid_samples / len(samples) if samples else 0.0
        elif field_type == 'ip_address':
            ip_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
            valid_samples = sum(1 for s in samples if re.match(ip_pattern, s))
            content_score = valid_samples / len(samples) if samples else 0.0
        elif field_type == 'mac_address':
            mac_pattern = r'^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$'
            valid_samples = sum(1 for s in samples if re.match(mac_pattern, s))
            content_score = valid_samples / len(samples) if samples else 0.0
        else:
            content_score = 0.5
        
        return (name_score * 0.6 + content_score * 0.4)
    
    def _calculate_semantic_score(self, text: str, field_type: str) -> float:
        if field_type == 'infrastructure_type':
            for infra_type, keywords in self.infrastructure_types.items():
                if any(kw in text.lower() for kw in keywords):
                    return 0.9
        elif field_type == 'system_classification':
            for sys_class, keywords in self.system_classifications.items():
                if any(kw in text.lower() for kw in keywords):
                    return 0.9
        elif field_type == 'region':
            for region, keywords in self.regional_mappings.items():
                if any(kw in text.lower() for kw in keywords):
                    return 0.9
        return 0.5
    
    def identify_log_type(self, table_name: str, columns: List[str]) -> Dict[str, Any]:
        table_lower = table_name.lower()
        columns_lower = [c.lower() for c in columns]
        all_text = f"{table_lower} {' '.join(columns_lower)}"
        
        scores = {}
        for log_role, config in self.log_type_patterns.items():
            pattern_score = sum(1 for p in config['patterns'] if p in all_text) / len(config['patterns'])
            field_score = sum(1 for f in config['fields'] if any(f in c for c in columns_lower)) / max(len(config['fields']), 1)
            scores[log_role] = (pattern_score * 0.6 + field_score * 0.4)
        
        best_role = max(scores, key=scores.get)
        confidence = scores[best_role]
        
        return {
            'role': best_role,
            'confidence': confidence,
            'log_types': self.log_type_patterns[best_role]['patterns'],
            'visibility_factors': self.log_type_patterns[best_role]['visibility'],
            'scores': scores
        }
    
    def classify_infrastructure(self, text: str) -> str:
        text_lower = text.lower()
        for infra_type, keywords in self.infrastructure_types.items():
            if any(kw in text_lower for kw in keywords):
                return infra_type
        return 'on_premise'
    
    def classify_system(self, text: str) -> str:
        text_lower = text.lower()
        for sys_class, keywords in self.system_classifications.items():
            if any(kw in text_lower for kw in keywords):
                return sys_class
        return 'unknown'
    
    def map_region(self, text: str) -> str:
        text_lower = text.lower()
        for region, keywords in self.regional_mappings.items():
            if any(kw in text_lower for kw in keywords):
                return region
        return 'unknown'
    
    def calculate_anomaly_score(self, values: List[Any]) -> float:
        if not values:
            return 0.0
        
        str_values = [str(v) for v in values]
        unique_ratio = len(set(str_values)) / len(str_values)
        
        lengths = [len(v) for v in str_values]
        if lengths:
            mean_len = np.mean(lengths)
            std_len = np.std(lengths)
            cv = std_len / mean_len if mean_len > 0 else 0
        else:
            cv = 0
        
        anomaly_score = (1 - unique_ratio) * 0.5 + min(cv, 1.0) * 0.5
        return anomaly_score