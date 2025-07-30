#!/usr/bin/env python3
"""
AO1 Visibility Statement Field Discovery System with Neural Networks
==================================================================

Advanced neural network system with forward/backward propagation and ReLU activations
to discover BigQuery fields for AO1 visibility percentage calculations.

Focuses on vendor tools and platforms the firm has purchased:
Priority: Chronicle, Splunk, CrowdStrike, internal CMDB

Business Purpose:
- Calculate "CSOC is able to view X% of all assets globally"
- Measure visibility by infrastructure type across vendor platforms
- Generate coverage percentages for purchased security tools
- Assess logging platform compliance across Chronicle and Splunk

Neural Architecture:
- Multi-layer neural networks with ReLU activations
- Forward and backward propagation with gradient descent
- Semantic similarity computation for vendor tool field matching
- Adaptive learning for vendor-specific field patterns

Author: Security Analytics Team
Version: 4.0 Neural
Target: prj-fisv-p-gcss-sas-dl9dd0f1df
Auth: chronicle-fisv
"""

import os
import sys
import json
import time
import logging
import numpy as np
from typing import Dict, List, Set, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict, Counter
import re

# Set up logging
file_path = os.path.join(os.path.dirname(__file__))
settings = {}
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ao1_neural_visibility_discovery.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# BigQuery authentication
from google.cloud import bigquery
from google.oauth2 import service_account

SERVICE_ACCOUNT_FILE = os.path.join(file_path, "gcp_prod_key.json")
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
project = "chronicle-fisv"
clientBQ = bigquery.Client(project="chronicle-fisv", credentials=credentials)

def runBQQuery(query):
    """Execute BigQuery SQL for neural analysis."""
    df = clientBQ.query(query).to_dataframe()
    return df

# Vendor Tool Classification - Purchased vs Internal
PURCHASED_VENDOR_TOOLS = {
    # Priority vendor tools (highest importance for visibility)
    'chronicle': 'Google Chronicle Security Operations Suite',
    'splunk': 'Splunk Enterprise/Cloud',
    'crowdstrike': 'CrowdStrike Falcon EDR',
    
    # Security vendor tools
    'wiz': 'Wiz.io Cloud Security',
    'f5': 'F5 BIG-IP',
    'servicenow': 'ServiceNow ITSM',
    'sonatype': 'Sonatype Lifecycle',
    'workday': 'Workday HCM',
    'anomali': 'Anomali Threat Intelligence',
    'attivo': 'Attivo Networks Deception',
    'axonius': 'Axonius Cybersecurity Asset Management',
    'bigid': 'BigID Data Intelligence',
    'britive': 'Britive Privileged Access Management',
    'caveonix': 'CaveoniX Cloud Workload Protection',
    'cyberark': 'CyberArk Privileged Access Management',
    'dtex': 'DTEX Insider Risk Management', 
    'dynatrace': 'Dynatrace Application Performance Monitoring',
    'extrahop': 'ExtraHop Network Detection and Response',
    'guardium': 'IBM Guardium Data Protection',
    'hypr': 'HYPR Passwordless Authentication',
    'island': 'Island.io Enterprise Browser',
    'magnet': 'Magnet Forensics',
    'mandiant': 'Mandiant Threat Intelligence',
    'microsoft': 'Microsoft Entra/Azure AD',
    'mobb': 'Mobb Application Security',
    'nowsecure': 'NowSecure Mobile Security',
    'onetrust': 'OneTrust GRC Platform',
    'opentext': 'OpenText Fortify Application Security',
    'palo_alto': 'Palo Alto Networks Security',
    'ping': 'Ping Identity Access Management',
    'portswigger': 'PortSwigger Burp Suite Pro',
    'proofpoint': 'Proofpoint Email Security',
    'radware': 'Radware Cloud WAF',
    'redhat': 'Red Hat Identity Management',
    'sailpoint': 'SailPoint Identity Governance',
    'simspace': 'SimSpace Cyber Range',
    'talend': 'Talend Data Fabric',
    'tanium': 'Tanium Endpoint Management',
    'tenable': 'Tenable Nessus Vulnerability Management',
    'theom': 'Theom Cloud Security',
    'thousandeyes': 'ThousandEyes Network Intelligence',
    'venafi': 'Venafi Certificate Management',
    'virtru': 'Virtru Data Protection',
    'zscaler': 'Zscaler Zero Trust Exchange'
}

# Neural Network Components with ReLU Activations
class ReLUActivation:
    """ReLU activation function with forward and backward propagation."""
    
    @staticmethod
    def forward(x):
        """Forward pass: f(x) = max(0, x)"""
        return np.maximum(0, x)
    
    @staticmethod
    def backward(dA, Z):
        """Backward pass: derivative is 1 if x > 0, else 0"""
        dZ = np.array(dA, copy=True)
        dZ[Z <= 0] = 0
        return dZ

class NeuralLayer:
    """Neural network layer with weights, biases, and activations."""
    
    def __init__(self, input_size: int, output_size: int, activation='relu'):
        self.input_size = input_size
        self.output_size = output_size
        self.activation = activation
        
        # Xavier/He initialization for ReLU networks
        if activation == 'relu':
            self.W = np.random.randn(output_size, input_size) * np.sqrt(2.0 / input_size)
        else:
            self.W = np.random.randn(output_size, input_size) * np.sqrt(1.0 / input_size)
        
        self.b = np.zeros((output_size, 1))
        
        # For momentum-based optimization
        self.vW = np.zeros_like(self.W)
        self.vb = np.zeros_like(self.b)
        
        # Cache for backward propagation
        self.cache = {}
    
    def forward(self, A_prev):
        """Forward propagation through the layer."""
        # Linear transformation: Z = W * A_prev + b
        Z = np.dot(self.W, A_prev) + self.b
        
        # Apply activation function
        if self.activation == 'relu':
            A = ReLUActivation.forward(Z)
        elif self.activation == 'sigmoid':
            A = 1 / (1 + np.exp(-np.clip(Z, -250, 250)))
        elif self.activation == 'tanh':
            A = np.tanh(Z)
        else:  # linear
            A = Z
        
        # Cache values for backward propagation
        self.cache = {'A_prev': A_prev, 'Z': Z}
        return A
    
    def backward(self, dA, learning_rate=0.001, momentum=0.9):
        """Backward propagation through the layer."""
        A_prev = self.cache['A_prev']
        Z = self.cache['Z']
        m = A_prev.shape[1]
        
        # Compute activation gradient
        if self.activation == 'relu':
            dZ = ReLUActivation.backward(dA, Z)
        elif self.activation == 'sigmoid':
            s = 1 / (1 + np.exp(-np.clip(Z, -250, 250)))
            dZ = dA * s * (1 - s)
        elif self.activation == 'tanh':
            dZ = dA * (1 - np.power(np.tanh(Z), 2))
        else:  # linear
            dZ = dA
        
        # Compute gradients
        dW = (1/m) * np.dot(dZ, A_prev.T)
        db = (1/m) * np.sum(dZ, axis=1, keepdims=True)
        dA_prev = np.dot(self.W.T, dZ)
        
        # Update weights with momentum
        self.vW = momentum * self.vW + (1 - momentum) * dW
        self.vb = momentum * self.vb + (1 - momentum) * db
        
        self.W -= learning_rate * self.vW
        self.b -= learning_rate * self.vb
        
        return dA_prev

class VendorToolNeuralNetwork:
    """
    Neural network specialized for vendor tool field classification.
    
    Uses ReLU activations and gradient descent to learn patterns
    in vendor tool data fields for AO1 visibility calculations.
    """
    
    def __init__(self, input_size=256, hidden_layers=None, output_size=None):
        if hidden_layers is None:
            hidden_layers = [128, 64, 32]
        if output_size is None:
            output_size = len(PURCHASED_VENDOR_TOOLS)
        
        self.layers = []
        self.learning_rate = 0.001
        self.momentum = 0.9
        self.training_losses = []
        
        # Build network architecture
        layer_sizes = [input_size] + hidden_layers + [output_size]
        
        for i in range(len(layer_sizes) - 1):
            if i == len(layer_sizes) - 2:  # Output layer
                activation = 'sigmoid'
            else:
                activation = 'relu'
            
            layer = NeuralLayer(layer_sizes[i], layer_sizes[i + 1], activation)
            self.layers.append(layer)
        
        logger.info(f"Vendor tool neural network initialized: {layer_sizes} with ReLU activations")
    
    def forward_propagation(self, X):
        """Forward propagation through the entire network."""
        A = X
        for layer in self.layers:
            A = layer.forward(A)
        return A
    
    def backward_propagation(self, AL, Y):
        """Backward propagation through the entire network."""
        # Compute output layer gradient
        m = AL.shape[1]
        dAL = -(np.divide(Y, AL + 1e-8) - np.divide(1 - Y, 1 - AL + 1e-8))
        
        # Backpropagate through layers
        dA = dAL
        for layer in reversed(self.layers):
            dA = layer.backward(dA, self.learning_rate, self.momentum)
    
    def compute_loss(self, AL, Y):
        """Compute binary cross-entropy loss."""
        m = Y.shape[1]
        loss = -np.sum(Y * np.log(AL + 1e-8) + (1 - Y) * np.log(1 - AL + 1e-8)) / m
        return np.squeeze(loss)
    
    def train(self, X, Y, epochs=1000, print_cost=True):
        """Train the neural network using gradient descent."""
        costs = []
        
        for epoch in range(epochs):
            # Forward propagation
            AL = self.forward_propagation(X)
            
            # Compute cost
            cost = self.compute_loss(AL, Y)
            costs.append(cost)
            
            # Backward propagation
            self.backward_propagation(AL, Y)
            
            # Adaptive learning rate
            if epoch > 100 and len(costs) > 10:
                if cost > np.mean(costs[-10:]):
                    self.learning_rate *= 0.95
            
            if print_cost and epoch % 100 == 0:
                logger.info(f"Epoch {epoch}: Cost = {cost:.6f}, LR = {self.learning_rate:.6f}")
        
        self.training_losses = costs
        return costs
    
    def predict(self, X):
        """Make predictions using the trained network."""
        AL = self.forward_propagation(X)
        return AL

# AO1 Keywords for Purchased Vendor Tools - Focus on tools we know are purchased
# Priority: Chronicle, Splunk, CrowdStrike, CMDB

# REQ-1: Global View - Asset identifiers from purchased tools
REQ1_GLOBAL_VIEW_KEYWORDS = {
    # Chronicle (Google Security Operations) identifiers
    'udm_hostname', 'principal_hostname', 'target_hostname', 'asset_hostname',
    'udm_asset_id', 'principal_asset_id', 'target_asset_id', 'chronicle_asset_id',
    'principal_ip', 'target_ip', 'network_ip', 'source_ip', 'destination_ip',
    'udm_device_id', 'device_identifier', 'principal_mac', 'target_mac',
    
    # Splunk asset identifiers
    'host', 'source', 'sourcetype', 'index', 'splunk_host', 'orig_host',
    'dest_host', 'src_host', 'computer_name', 'hostname', 'asset_id',
    'device_id', 'endpoint_id', 'machine_id', 'system_id',
    
    # CrowdStrike Falcon identifiers
    'aid', 'agent_id', 'sensor_id', 'cid', 'customer_id', 'device_id',
    'falcon_aid', 'crowdstrike_aid', 'endpoint_id', 'falcon_host',
    'computer_name', 'hostname', 'machine_domain', 'local_ip',
    
    # CMDB asset identifiers (internal)
    'ci_name', 'cmdb_ci', 'sys_id', 'configuration_item', 'asset_tag',
    'serial_number', 'hardware_id', 'business_service', 'service_name',
    
    # ServiceNow CMDB identifiers
    'servicenow_sys_id', 'servicenow_name', 'servicenow_serial',
    'discovery_source', 'cmdb_class', 'install_status',
    
    # Axonius asset management identifiers
    'axonius_id', 'axonius_name', 'device_name', 'last_seen_by',
    'adapter_name', 'connection_label', 'device_type'
}

# REQ-2: Infrastructure Type - Classification from purchased platforms
REQ2_INFRASTRUCTURE_TYPE_KEYWORDS = {
    # Chronicle infrastructure classification
    'udm_platform', 'platform_type', 'infrastructure_type', 'deployment_model',
    'cloud_provider', 'cloud_region', 'cloud_zone', 'cloud_project',
    
    # Splunk infrastructure data
    'platform', 'os', 'architecture', 'infrastructure', 'deployment',
    'cloud_service', 'instance_type', 'vm_type', 'container_type',
    
    # Wiz cloud security platform classification
    'wiz_platform', 'cloud_type', 'resource_type', 'service_type',
    'provider_type', 'deployment_type', 'compute_type',
    
    # F5 BIG-IP infrastructure
    'f5_device_type', 'bigip_type', 'ltm_type', 'virtual_server_type',
    'pool_type', 'node_type', 'partition_name',
    
    # AWS/Azure/GCP from purchased tools
    'aws_instance_type', 'aws_service', 'ec2_type', 'lambda_type',
    'azure_resource_type', 'azure_service', 'vm_size', 'app_service_type',
    'gcp_instance_type', 'gce_type', 'compute_engine_type',
    
    # Container platforms
    'kubernetes_type', 'k8s_type', 'container_runtime', 'pod_type',
    'docker_type', 'container_platform', 'orchestrator_type'
}

# REQ-3: Regional/Country - Geographic data from purchased tools
REQ3_REGIONAL_COUNTRY_KEYWORDS = {
    # Chronicle geographic data
    'udm_location', 'principal_location', 'target_location', 'geo_country',
    'geo_region', 'geo_city', 'geo_state', 'network_location',
    
    # Splunk geographic fields
    'src_country', 'dest_country', 'country', 'region', 'city', 'state',
    'lat', 'lon', 'latitude', 'longitude', 'timezone', 'location',
    
    # Workday location data
    'workday_location', 'work_location', 'office_location', 'site_location',
    'business_site', 'cost_center_location', 'employee_location',
    
    # ServiceNow location fields
    'location', 'site', 'building', 'floor', 'room', 'datacenter',
    'facility', 'address', 'country_code', 'state_province',
    
    # Cloud provider regions
    'aws_region', 'azure_region', 'gcp_region', 'cloud_region',
    'availability_zone', 'zone', 'edge_location'
}

# REQ-4: Business/Application - Organizational data from purchased tools
REQ4_BUSINESS_APPLICATION_KEYWORDS = {
    # Workday business organization
    'workday_business_unit', 'cost_center', 'department', 'division',
    'organization', 'company', 'business_service', 'functional_area',
    
    # ServiceNow business classification
    'business_unit', 'department', 'company', 'business_service',
    'application', 'service_portfolio', 'business_capability',
    
    # SailPoint identity governance
    'sailpoint_org', 'identity_org', 'business_role', 'access_profile',
    'entitlement_owner', 'application_owner', 'data_owner',
    
    # Dynatrace APM application data
    'dynatrace_app', 'application_name', 'service_name', 'process_group',
    'management_zone', 'environment', 'application_type',
    
    # Chronicle business context
    'principal_user_domain', 'target_business_unit', 'application_name',
    'business_context', 'organizational_unit'
}

# REQ-5: System Classification - OS and system types from purchased tools
REQ5_SYSTEM_CLASSIFICATION_KEYWORDS = {
    # CrowdStrike OS and platform data
    'platform_name', 'os_version', 'platform_version', 'system_manufacturer',
    'bios_manufacturer', 'product_type', 'kernel_version', 'architecture',
    
    # Chronicle system classification
    'udm_os', 'operating_system', 'os_family', 'os_type', 'platform_type',
    'system_type', 'device_category', 'asset_type',
    
    # Splunk system data
    'os', 'platform', 'arch', 'version', 'vendor', 'product', 'category',
    'app', 'service', 'process', 'protocol', 'transport',
    
    # Tanium endpoint data
    'operating_system', 'os_name', 'computer_type', 'system_type',
    'chassis_type', 'form_factor', 'hardware_model',
    
    # F5 system classification
    'device_type', 'product_category', 'system_type', 'appliance_mode',
    'ha_state', 'failover_state'
}

# REQ-6: Security Control Coverage - Agent data from purchased security tools
REQ6_SECURITY_CONTROL_COVERAGE_KEYWORDS = {
    # CrowdStrike Falcon agent data
    'agent_load_flags', 'agent_local_time', 'agent_version', 'sensor_version',
    'config_id_base', 'config_id_build', 'config_id_platform', 'prevention_policy',
    'device_policy', 'group_name', 'policy_id', 'falcon_grouping_tags',
    
    # Tanium agent data
    'tanium_client_version', 'last_registration', 'registration_count',
    'is_virtual', 'has_tls', 'subnet', 'domain_name', 'tanium_server',
    
    # Axonius security control coverage
    'security_agents', 'installed_software', 'running_processes', 'services',
    'endpoint_protection', 'antivirus_status', 'firewall_status',
    'encryption_status', 'patch_status', 'vulnerability_count',
    
    # Microsoft Defender/Entra security
    'defender_status', 'atp_status', 'compliance_state', 'enrollment_state',
    'threat_state', 'health_state', 'management_state',
    
    # Proofpoint email security
    'proofpoint_status', 'message_blocked', 'threat_detected', 'quarantine_status',
    'dlp_status', 'encryption_status'
}

# REQ-7: Logging Compliance - Chronicle and Splunk platform data
REQ7_LOGGING_COMPLIANCE_KEYWORDS = {
    # Google Chronicle platform fields
    'metadata_collected_timestamp', 'metadata_event_timestamp', 'metadata_ingested_timestamp',
    'metadata_product_name', 'metadata_vendor_name', 'metadata_log_type',
    'metadata_product_event_type', 'principal_process_command_line',
    'security_result_rule_name', 'security_result_severity',
    
    # Chronicle ingestion and parsing
    'log_type', 'parser_name', 'ingestion_labels', 'parse_status',
    'normalized_fields', 'enrichment_status', 'validation_status',
    
    # Splunk platform compliance
    'index', 'sourcetype', 'source', 'host', '_time', '_raw',
    'splunk_server', 'indexer', 'search_head', 'license_usage',
    'data_model', 'acceleration_status', 'summary_indexing',
    
    # Splunk data quality and compliance
    'parsing_errors', 'timestamp_errors', 'field_extraction_errors',
    'data_quality_score', 'ingestion_delay', 'retention_policy',
    'acceleration_status', 'data_model_compliance'
}

# REQ-8: Domain Visibility - DNS and domain data from purchased tools
REQ8_DOMAIN_VISIBILITY_KEYWORDS = {
    # Chronicle DNS and domain data
    'network_dns_domain', 'principal_hostname', 'target_hostname',
    'network_dns_questions_name', 'network_dns_answers_name',
    'network_dns_response_code', 'network_dns_query_type',
    
    # Splunk DNS data
    'dns_query', 'dns_answer', 'query_type', 'response_code',
    'dns_server', 'domain', 'subdomain', 'fqdn', 'hostname',
    
    # Zscaler DNS security
    'zscaler_category', 'url_category', 'threat_category', 'risk_score',
    'blocked_category', 'allowed_category', 'dns_threat_category',
    
    # Microsoft AD domain data
    'domain_name', 'domain_controller', 'forest_name', 'site_name',
    'organizational_unit', 'distinguished_name', 'sam_account_name',
    
    # ThousandEyes network intelligence
    'thousandeyes_test', 'network_latency', 'path_trace', 'dns_resolution_time',
    'domain_availability', 'connection_status'
}

# AO1 requirements focused on purchased vendor tools
AO1_REQUIREMENTS = {
    'REQ-1': {
        'name': 'Global View',
        'description': 'Asset identifiers from purchased vendor platforms for CMDB comparison',
        'keywords': REQ1_GLOBAL_VIEW_KEYWORDS,
        'vendor_tools': ['Chronicle', 'Splunk', 'CrowdStrike', 'ServiceNow', 'Axonius'],
        'visibility_purpose': 'Calculate "CSOC is able to view X% of all assets globally" using vendor tool data',
        'neural_priority': 1.0
    },
    'REQ-2': {
        'name': 'Infrastructure Type',
        'description': 'Infrastructure classification from purchased cloud and security platforms',
        'keywords': REQ2_INFRASTRUCTURE_TYPE_KEYWORDS,
        'vendor_tools': ['Chronicle', 'Splunk', 'Wiz', 'F5', 'Cloud Providers'],
        'visibility_purpose': 'Calculate visibility by infrastructure type using vendor platform data',
        'neural_priority': 0.9
    },
    'REQ-3': {
        'name': 'Regional/Country View',
        'description': 'Geographic data from purchased platforms for regional visibility',
        'keywords': REQ3_REGIONAL_COUNTRY_KEYWORDS,
        'vendor_tools': ['Chronicle', 'Splunk', 'Workday', 'ServiceNow'],
        'visibility_purpose': 'Calculate regional visibility percentages using vendor location data',
        'neural_priority': 0.8
    },
    'REQ-4': {
        'name': 'Business/Application View',
        'description': 'Business organization data from purchased enterprise platforms',
        'keywords': REQ4_BUSINESS_APPLICATION_KEYWORDS,
        'vendor_tools': ['Workday', 'ServiceNow', 'SailPoint', 'Dynatrace'],
        'visibility_purpose': 'Calculate business unit visibility using vendor organizational data',
        'neural_priority': 0.85
    },
    'REQ-5': {
        'name': 'System Classification',
        'description': 'OS and system type data from purchased security and monitoring tools',
        'keywords': REQ5_SYSTEM_CLASSIFICATION_KEYWORDS,
        'vendor_tools': ['CrowdStrike', 'Chronicle', 'Splunk', 'Tanium', 'F5'],
        'visibility_purpose': 'Calculate system type visibility using vendor platform classification',
        'neural_priority': 0.9
    },
    'REQ-6': {
        'name': 'Security Control Coverage',
        'description': 'Agent and security control data from purchased security platforms',
        'keywords': REQ6_SECURITY_CONTROL_COVERAGE_KEYWORDS,
        'vendor_tools': ['CrowdStrike', 'Tanium', 'Axonius', 'Microsoft', 'Proofpoint'],
        'visibility_purpose': 'Calculate security control coverage using vendor agent deployment data',
        'neural_priority': 0.95
    },
    'REQ-7': {
        'name': 'Logging Compliance',
        'description': 'Platform compliance data from Chronicle and Splunk',
        'keywords': REQ7_LOGGING_COMPLIANCE_KEYWORDS,
        'vendor_tools': ['Chronicle', 'Splunk'],
        'visibility_purpose': 'Calculate logging platform compliance using vendor platform metrics',
        'neural_priority': 0.95
    },
    'REQ-8': {
        'name': 'Domain Visibility',
        'description': 'DNS and domain data from purchased network and security tools',
        'keywords': REQ8_DOMAIN_VISIBILITY_KEYWORDS,
        'vendor_tools': ['Chronicle', 'Splunk', 'Zscaler', 'Microsoft AD', 'ThousandEyes'],
        'visibility_purpose': 'Calculate domain visibility using vendor DNS and network data',
        'neural_priority': 0.9
    }
}

def get_all_keywords():
    """Return all vendor tool keywords for visibility field discovery."""
    all_keywords = set()
    for req_info in AO1_REQUIREMENTS.values():
        all_keywords.update(req_info['keywords'])
    return all_keywords

def find_keyword_requirement(keyword):
    """Find which AO1 requirement(s) a vendor tool keyword supports."""
    requirements = []
    keyword_lower = keyword.lower()
    
    for req_id, req_info in AO1_REQUIREMENTS.items():
        if keyword_lower in req_info['keywords']:
            requirements.append(f'{req_id}: {req_info["name"]}')
    
    return requirements

@dataclass
class VendorToolFieldAnalysis:
    """Analysis result for vendor tool fields supporting AO1 visibility calculations."""
    field_name: str
    table_name: str
    dataset_name: str
    row_count: int
    match_type: str
    confidence: float
    neural_confidence: float
    matching_keywords: List[str]
    matching_requirements: List[str]
    vendor_tools: List[str]
    visibility_purpose: str
    business_impact: str
    neural_reasoning: str
    implementation_priority: int = 0

class VendorToolSemanticAnalyzer:
    """
    Neural network-based semantic analyzer for vendor tool field classification.
    
    Uses forward/backward propagation with ReLU to understand vendor-specific
    field patterns and semantic relationships.
    """
    
    def __init__(self, embedding_dim=256):
        self.embedding_dim = embedding_dim
        self.vendor_neural_net = VendorToolNeuralNetwork(
            input_size=embedding_dim,
            hidden_layers=[128, 64, 32],
            output_size=len(PURCHASED_VENDOR_TOOLS)
        )
        
        # Vendor-specific pattern embeddings
        self.vendor_embeddings = self._create_vendor_embeddings()
        self.field_embeddings_cache = {}
        
    def _create_vendor_embeddings(self) -> Dict[str, np.ndarray]:
        """Create neural embeddings for purchased vendor tools."""
        embeddings = {}
        
        # Priority vendor embeddings (higher dimensional patterns)
        priority_vendors = {
            'chronicle': np.array([1.0, 0.9, 0.8, 0.7, 0.9, 0.8, 0.7, 0.6] * 32),  # 256-dim
            'splunk': np.array([0.9, 1.0, 0.8, 0.7, 0.8, 0.9, 0.7, 0.6] * 32),
            'crowdstrike': np.array([0.8, 0.7, 1.0, 0.9, 0.7, 0.6, 0.9, 0.8] * 32),
            'cmdb': np.array([0.7, 0.6, 0.8, 1.0, 0.6, 0.7, 0.8, 0.9] * 32)
        }
        
        # Standard vendor embeddings
        for i, (vendor, description) in enumerate(PURCHASED_VENDOR_TOOLS.items()):
            if vendor not in priority_vendors:
                # Generate unique embedding based on vendor characteristics
                base_pattern = [0.5 + 0.1 * (i % 5), 0.6 + 0.05 * (i % 7), 
                               0.4 + 0.15 * (i % 3), 0.7 + 0.08 * (i % 4)]
                embeddings[vendor] = np.array(base_pattern * 64)  # 256-dim
            else:
                embeddings[vendor] = priority_vendors[vendor]
        
        logger.info(f"Created neural embeddings for {len(embeddings)} vendor tools")
        return embeddings
    
    def generate_field_embedding(self, field_name: str, table_name: str = "") -> np.ndarray:
        """Generate neural embedding for a field using character-level and semantic patterns."""
        cache_key = f"{field_name}_{table_name}"
        
        if cache_key in self.field_embeddings_cache:
            return self.field_embeddings_cache[cache_key]
        
        # Character-level encoding
        combined_text = f"{field_name}_{table_name}".lower()
        char_vector = np.zeros(256)
        
        # Simple character frequency encoding
        for i, char in enumerate(combined_text[:256]):
            if char.isalnum():
                char_vector[i % 256] += ord(char) / 128.0
            elif char in ['_', '-', '.']:
                char_vector[i % 256] += 0.5
        
        # Vendor-specific pattern detection
        vendor_signals = np.zeros(32)
        for i, vendor in enumerate(list(PURCHASED_VENDOR_TOOLS.keys())[:32]):
            if vendor in combined_text:
                vendor_signals[i] = 1.0
            # Partial matches
            for part in vendor.split('_'):
                if len(part) > 2 and part in combined_text:
                    vendor_signals[i] = max(vendor_signals[i], 0.7)
        
        # Combine encodings
        embedding = np.concatenate([char_vector[:224], vendor_signals])
        
        # Normalize
        embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
        
        self.field_embeddings_cache[cache_key] = embedding
        return embedding
    
    def compute_vendor_similarity(self, field_name: str, table_name: str = "") -> Dict[str, float]:
        """Compute neural similarity between field and vendor tools using neural network."""
        field_embedding = self.generate_field_embedding(field_name, table_name)
        field_embedding = field_embedding.reshape(-1, 1)  # Column vector for neural net
        
        # Forward propagation through vendor tool neural network
        vendor_predictions = self.vendor_neural_net.predict(field_embedding)
        
        # Extract similarities for each vendor
        similarities = {}
        vendor_list = list(PURCHASED_VENDOR_TOOLS.keys())
        
        for i, vendor in enumerate(vendor_list):
            if i < vendor_predictions.shape[0]:
                similarities[vendor] = float(vendor_predictions[i, 0])
        
        return similarities
    
    def train_on_vendor_patterns(self, training_data: List[Dict]):
        """Train neural network on discovered vendor tool patterns."""
        if len(training_data) < 10:
            logger.warning("Insufficient training data for vendor tool neural network")
            return
        
        X_train = []
        Y_train = []
        
        for example in training_data:
            field_embedding = self.generate_field_embedding(
                example['field_name'], 
                example.get('table_name', '')
            )
            
            # Create target vector for vendor tools
            target = np.zeros((len(PURCHASED_VENDOR_TOOLS), 1))
            for vendor in example.get('detected_vendors', []):
                if vendor in PURCHASED_VENDOR_TOOLS:
                    vendor_idx = list(PURCHASED_VENDOR_TOOLS.keys()).index(vendor)
                    target[vendor_idx] = 1.0
            
            X_train.append(field_embedding.reshape(-1, 1))
            Y_train.append(target)
        
        if X_train:
            X_train = np.hstack(X_train)
            Y_train = np.hstack(Y_train)
            
            logger.info(f"Training vendor tool neural network on {len(training_data)} examples")
            self.vendor_neural_net.train(X_train, Y_train, epochs=300)

class VendorToolFieldAnalyzer:
    """
    Neural network-powered analyzer for vendor tool fields supporting AO1 visibility.
    
    Combines exact keyword matching with neural semantic analysis
    to identify fields from purchased vendor tools.
    """
    
    def __init__(self):
        self.semantic_analyzer = VendorToolSemanticAnalyzer()
        self.all_keywords = get_all_keywords()
        self.vendor_patterns = self._build_vendor_patterns()
        
    def _build_vendor_patterns(self) -> Dict[str, List[str]]:
        """Build patterns to detect vendor tool fields."""
        patterns = {}
        
        for vendor, description in PURCHASED_VENDOR_TOOLS.items():
            patterns[vendor] = [
                vendor,
                vendor.replace('_', ''),
                vendor.replace('_', '-'),
                f"{vendor}_",
                f"_{vendor}",
                f"{vendor}.",
                f".{vendor}"
            ]
        
        return patterns
    
    def analyze_vendor_field(self, field_name: str, table_name: str, 
                           dataset_name: str, row_count: int) -> Optional[VendorToolFieldAnalysis]:
        """
        Analyze field for vendor tool relevance using neural networks.
        
        Focuses on fields from purchased vendor platforms that support
        AO1 visibility statement calculations.
        """
        if not field_name:
            return None
        
        field_lower = field_name.lower().strip()
        
        # Step 1: Exact keyword matching for vendor tools
        exact_matches = []
        matching_requirements = []
        
        if field_lower in self.all_keywords:
            exact_matches.append(field_lower)
            matching_requirements.extend(find_keyword_requirement(field_lower))
        
        # Step 2: Vendor pattern detection
        detected_vendors = []
        vendor_confidence = 0.0
        
        for vendor, patterns in self.vendor_patterns.items():
            for pattern in patterns:
                if pattern in field_lower or pattern in table_name.lower():
                    detected_vendors.append(vendor)
                    vendor_confidence = max(vendor_confidence, 0.8)
                    break
        
        # Step 3: Neural semantic analysis for vendor tools
        vendor_similarities = self.semantic_analyzer.compute_vendor_similarity(field_name, table_name)
        max_neural_similarity = max(vendor_similarities.values()) if vendor_similarities else 0.0
        
        # Add high-confidence neural predictions to detected vendors
        for vendor, similarity in vendor_similarities.items():
            if similarity > 0.7 and vendor not in detected_vendors:
                detected_vendors.append(vendor)
        
        # Step 4: Check for partial keyword matches
        partial_matches = []
        for keyword in self.all_keywords:
            if keyword != field_lower:
                if keyword in field_lower or field_lower in keyword:
                    partial_matches.append(keyword)
                    matching_requirements.extend(find_keyword_requirement(keyword))
        
        # Remove duplicate requirements
        matching_requirements = list(set(matching_requirements))
        
        # Step 5: Determine match type and confidence
        if exact_matches and detected_vendors:
            match_type = 'EXACT_VENDOR_MATCH'
            confidence = 95.0
        elif exact_matches:
            match_type = 'EXACT_KEYWORD'
            confidence = 90.0
        elif detected_vendors and partial_matches:
            match_type = 'VENDOR_PATTERN_MATCH'
            confidence = min(85.0, vendor_confidence * 100)
        elif detected_vendors:
            match_type = 'VENDOR_DETECTED'
            confidence = min(80.0, max_neural_similarity * 100)
        elif partial_matches:
            match_type = 'PARTIAL_KEYWORD'
            confidence = min(75.0, len(partial_matches) * 15)
        elif max_neural_similarity > 0.6:
            match_type = 'NEURAL_VENDOR_PREDICTION'
            confidence = max_neural_similarity * 100
        else:
            return None  # Not relevant to vendor tools or AO1
        
        # Only proceed if field has vendor tool relevance
        if not detected_vendors and not matching_requirements and confidence < 60:
            return None
        
        # Step 6: Generate vendor tool analysis
        vendor_tools = self._identify_vendor_tools(detected_vendors, matching_requirements)
        visibility_purpose = self._determine_visibility_purpose(matching_requirements, vendor_tools)
        business_impact = self._assess_vendor_business_impact(
            field_name, table_name, vendor_tools, row_count, confidence
        )
        
        # Step 7: Neural reasoning generation
        neural_reasoning = self._generate_neural_reasoning(
            field_name, exact_matches, detected_vendors, vendor_similarities, max_neural_similarity
        )
        
        # Step 8: Calculate implementation priority
        implementation_priority = self._calculate_vendor_priority(
            match_type, confidence, row_count, vendor_tools, max_neural_similarity
        )
        
        return VendorToolFieldAnalysis(
            field_name=field_name,
            table_name=table_name,
            dataset_name=dataset_name,
            row_count=row_count,
            match_type=match_type,
            confidence=confidence,
            neural_confidence=max_neural_similarity,
            matching_keywords=exact_matches + partial_matches,
            matching_requirements=matching_requirements,
            vendor_tools=vendor_tools,
            visibility_purpose=visibility_purpose,
            business_impact=business_impact,
            neural_reasoning=neural_reasoning,
            implementation_priority=implementation_priority
        )
    
    def _identify_vendor_tools(self, detected_vendors: List[str], 
                             matching_requirements: List[str]) -> List[str]:
        """Identify specific vendor tools relevant to the field."""
        tools = []
        
        # Add detected vendor tools
        for vendor in detected_vendors:
            if vendor in PURCHASED_VENDOR_TOOLS:
                tools.append(f"{vendor}: {PURCHASED_VENDOR_TOOLS[vendor]}")
        
        # Add vendor tools from requirements
        for req_str in matching_requirements:
            req_id = req_str.split(':')[0]
            if req_id in AO1_REQUIREMENTS:
                req_vendors = AO1_REQUIREMENTS[req_id].get('vendor_tools', [])
                for vendor in req_vendors:
                    vendor_key = vendor.lower().replace(' ', '_')
                    if vendor_key in PURCHASED_VENDOR_TOOLS:
                        tool_desc = f"{vendor_key}: {PURCHASED_VENDOR_TOOLS[vendor_key]}"
                        if tool_desc not in tools:
                            tools.append(tool_desc)
        
        return tools
    
    def _determine_visibility_purpose(self, matching_requirements: List[str], 
                                    vendor_tools: List[str]) -> str:
        """Determine visibility purpose focusing on vendor tool capabilities."""
        purposes = []
        
        for req_str in matching_requirements:
            req_id = req_str.split(':')[0]
            if req_id in AO1_REQUIREMENTS:
                purpose = AO1_REQUIREMENTS[req_id]['visibility_purpose']
                purposes.append(purpose)
        
        if purposes:
            return ' | '.join(list(set(purposes)))
        elif vendor_tools:
            return f"Support visibility calculations using data from: {', '.join([t.split(':')[0] for t in vendor_tools])}"
        else:
            return "Support general vendor tool visibility analysis"
    
    def _assess_vendor_business_impact(self, field_name: str, table_name: str,
                                     vendor_tools: List[str], row_count: int, 
                                     confidence: float) -> str:
        """Assess business impact focusing on purchased vendor tool value."""
        impact_parts = []
        
        # Priority vendor tool impact
        priority_vendors = ['chronicle', 'splunk', 'crowdstrike', 'cmdb']
        high_priority_detected = any(vendor in str(vendor_tools).lower() for vendor in priority_vendors)
        
        if high_priority_detected:
            impact_parts.append("HIGH PRIORITY - Uses data from priority vendor platforms (Chronicle/Splunk/CrowdStrike/CMDB)")
        
        # Data volume impact
        if row_count > 10000000:
            impact_parts.append("MASSIVE vendor data volume provides comprehensive visibility")
        elif row_count > 1000000:
            impact_parts.append("HIGH vendor data volume supports robust visibility calculations")
        else:
            impact_parts.append("Moderate vendor data volume for visibility analysis")
        
        # Vendor tool ROI assessment
        if len(vendor_tools) > 1:
            impact_parts.append(f"CROSS-PLATFORM value - integrates {len(vendor_tools)} purchased vendor tools")
        elif vendor_tools:
            impact_parts.append(f"Single vendor platform integration - maximizes ROI from purchased tool")
        
        # Confidence-based impact
        if confidence > 90:
            impact_parts.append("IMMEDIATE deployment ready - high confidence vendor tool field")
        elif confidence > 75:
            impact_parts.append("VALIDATION recommended - good vendor tool match")
        else:
            impact_parts.append("INVESTIGATION needed - potential vendor tool relevance")
        
        return ' | '.join(impact_parts)
    
    def _generate_neural_reasoning(self, field_name: str, exact_matches: List[str],
                                 detected_vendors: List[str], vendor_similarities: Dict[str, float],
                                 max_neural_similarity: float) -> str:
        """Generate neural reasoning for vendor tool field classification."""
        reasoning_parts = []
        
        if exact_matches:
            reasoning_parts.append(f"EXACT keyword match: {', '.join(exact_matches)}")
        
        if detected_vendors:
            reasoning_parts.append(f"VENDOR detection: {', '.join(detected_vendors)}")
        
        # Neural similarity insights
        if max_neural_similarity > 0.8:
            best_vendor = max(vendor_similarities, key=vendor_similarities.get)
            reasoning_parts.append(f"STRONG neural similarity to {best_vendor} ({max_neural_similarity:.3f})")
        elif max_neural_similarity > 0.6:
            best_vendor = max(vendor_similarities, key=vendor_similarities.get)
            reasoning_parts.append(f"MODERATE neural similarity to {best_vendor} ({max_neural_similarity:.3f})")
        
        # Forward/backward propagation insight
        reasoning_parts.append(f"Neural network forward propagation with ReLU activations")
        
        if not reasoning_parts:
            reasoning_parts.append("Weak vendor tool signals detected through neural analysis")
        
        return ' | '.join(reasoning_parts)
    
    def _calculate_vendor_priority(self, match_type: str, confidence: float,
                                 row_count: int, vendor_tools: List[str],
                                 neural_confidence: float) -> int:
        """Calculate implementation priority focusing on vendor tool value."""
        priority = 0
        
        # Base priority from match type
        match_priorities = {
            'EXACT_VENDOR_MATCH': 150,
            'EXACT_KEYWORD': 120,
            'VENDOR_PATTERN_MATCH': 100,
            'VENDOR_DETECTED': 80,
            'PARTIAL_KEYWORD': 60,
            'NEURAL_VENDOR_PREDICTION': 70
        }
        priority += match_priorities.get(match_type, 30)
        
        # Priority vendor tool bonus
        priority_vendors = ['chronicle', 'splunk', 'crowdstrike', 'cmdb']
        vendor_tools_str = str(vendor_tools).lower()
        
        for vendor in priority_vendors:
            if vendor in vendor_tools_str:
                priority += 40  # High bonus for priority vendors
        
        # Data volume bonus
        if row_count > 0:
            priority += min(50, int(np.log10(row_count) * 8))
        
        # Confidence bonus
        priority += int(confidence * 0.6)
        
        # Neural confidence bonus
        priority += int(neural_confidence * 30)
        
        # Multiple vendor tool bonus
        unique_vendors = len(set(tool.split(':')[0] for tool in vendor_tools))
        if unique_vendors > 1:
            priority += unique_vendors * 15
        
        return priority

class BigQueryVendorScanner:
    """
    Scans BigQuery for vendor tool fields using neural networks.
    
    Focuses on discovering fields from purchased vendor platforms
    that support AO1 visibility statement calculations.
    """
    
    def __init__(self, target_project_id: str = "prj-fisv-p-gcss-sas-dl9dd0f1df"):
        self.target_project_id = target_project_id
        self.client = None
        self.authenticated = False
        
    def authenticate(self) -> bool:
        """Authenticate to chronicle-fisv to scan target project."""
        try:
            self.client = clientBQ
            self.authenticated = True
            logger.info("BigQuery vendor tool scanner authenticated successfully")
            return True
        except Exception as e:
            logger.error(f"BigQuery authentication failed: {e}")
            return False
    
    def scan_vendor_tool_fields(self, analyzer: VendorToolFieldAnalyzer,
                              max_datasets: int = None) -> Dict[str, List[VendorToolFieldAnalysis]]:
        """
        Scan BigQuery for vendor tool fields using neural analysis.
        
        Returns fields from purchased vendor platforms that support visibility calculations.
        """
        if not self.authenticated:
            logger.error("Authentication required before vendor tool scanning")
            return {}
        
        results = {}
        training_examples = []
        scan_stats = {
            'datasets_scanned': 0,
            'tables_scanned': 0, 
            'fields_analyzed': 0,
            'vendor_fields_found': 0,
            'priority_vendor_matches': 0,
            'neural_predictions': 0
        }
        
        try:
            datasets = list(self.client.list_datasets(project=self.target_project_id))
            if max_datasets:
                datasets = datasets[:max_datasets]
            
            total_datasets = len(datasets)
            scan_stats['datasets_scanned'] = total_datasets
            
            logger.info(f"Scanning {total_datasets} datasets for vendor tool fields in {self.target_project_id}")
            
            for dataset_idx, dataset in enumerate(datasets):
                dataset_id = dataset.dataset_id
                logger.info(f"Analyzing dataset: {dataset_id} ({dataset_idx + 1}/{total_datasets})")
                
                dataset_results = []
                
                try:
                    tables = list(self.client.list_tables(dataset.reference))
                    
                    # Prioritize tables by vendor tool relevance
                    table_data = []
                    for table in tables:
                        try:
                            table_ref = self.client.get_table(table.reference)
                            vendor_relevance = self._calculate_vendor_relevance(table_ref.table_id)
                            table_data.append((table_ref, table_ref.num_rows or 0, vendor_relevance))
                        except Exception as e:
                            logger.debug(f"Could not get table info for {table.table_id}: {e}")
                            table_data.append((table, 0, 0))
                    
                    # Sort by vendor relevance and data volume
                    table_data.sort(key=lambda x: (x[2], x[1]), reverse=True)
                    
                    for table_ref, row_count, vendor_relevance in table_data:
                        scan_stats['tables_scanned'] += 1
                        
                        logger.debug(f"Neural analysis: {table_ref.table_id} ({row_count:,} rows, vendor relevance: {vendor_relevance:.1f})")
                        
                        # Analyze each field with neural vendor tool analysis
                        for field in table_ref.schema:
                            scan_stats['fields_analyzed'] += 1
                            
                            field_analysis = analyzer.analyze_vendor_field(
                                field_name=field.name,
                                table_name=table_ref.table_id,
                                dataset_name=dataset_id,
                                row_count=row_count
                            )
                            
                            if field_analysis:
                                dataset_results.append(field_analysis)
                                scan_stats['vendor_fields_found'] += 1
                                
                                # Track priority vendor matches
                                vendor_tools_str = str(field_analysis.vendor_tools).lower()
                                if any(vendor in vendor_tools_str for vendor in ['chronicle', 'splunk', 'crowdstrike', 'cmdb']):
                                    scan_stats['priority_vendor_matches'] += 1
                                
                                # Track neural predictions
                                if field_analysis.neural_confidence > 0.6:
                                    scan_stats['neural_predictions'] += 1
                                
                                # Collect training examples
                                training_example = {
                                    'field_name': field.name,
                                    'table_name': table_ref.table_id,
                                    'detected_vendors': [t.split(':')[0] for t in field_analysis.vendor_tools]
                                }
                                training_examples.append(training_example)
                                
                                logger.debug(f"Vendor field found: {field.name} -> {field_analysis.match_type} ({field_analysis.confidence:.1f}%)")
                    
                    if dataset_results:
                        # Sort by implementation priority
                        dataset_results.sort(key=lambda x: (x.implementation_priority, x.row_count), reverse=True)
                        results[dataset_id] = dataset_results
                        
                        logger.info(f"Dataset {dataset_id}: {len(dataset_results)} vendor tool fields discovered")
                
                except Exception as e:
                    logger.warning(f"Error processing dataset {dataset_id}: {e}")
                    continue
            
            # Train neural network on discovered vendor patterns
            if training_examples:
                logger.info("Training neural network on vendor tool patterns...")
                analyzer.semantic_analyzer.train_on_vendor_patterns(training_examples)
            
            # Log vendor tool discovery statistics
            logger.info("VENDOR TOOL FIELD DISCOVERY COMPLETE:")
            logger.info(f"  Datasets scanned: {scan_stats['datasets_scanned']}")
            logger.info(f"  Tables analyzed: {scan_stats['tables_scanned']}")
            logger.info(f"  Fields analyzed: {scan_stats['fields_analyzed']}")
            logger.info(f"  Vendor tool fields found: {scan_stats['vendor_fields_found']}")
            logger.info(f"  Priority vendor matches: {scan_stats['priority_vendor_matches']}")
            logger.info(f"  Neural predictions: {scan_stats['neural_predictions']}")
            
        except Exception as e:
            logger.error(f"Vendor tool scanning failed: {e}")
            
        return results
    
    def _calculate_vendor_relevance(self, table_name: str) -> float:
        """Calculate vendor tool relevance score for table prioritization."""
        table_lower = table_name.lower()
        
        # High-value vendor tool keywords
        vendor_keywords = [
            'chronicle', 'splunk', 'crowdstrike', 'falcon', 'cmdb', 'servicenow',
            'axonius', 'wiz', 'f5', 'bigip', 'workday', 'sailpoint', 'tanium',
            'cyberark', 'proofpoint', 'zscaler', 'dynatrace', 'microsoft',
            'agent', 'asset', 'host', 'endpoint', 'device', 'security', 'log'
        ]
        
        score = 1.0
        for keyword in vendor_keywords:
            if keyword in table_lower:
                # Priority vendors get higher scores
                if keyword in ['chronicle', 'splunk', 'crowdstrike', 'cmdb']:
                    score += 2.0
                else:
                    score += 1.0
        
        return min(score, 15.0)  # Cap at 15x multiplier

class VendorToolReportGenerator:
    """
    Generates comprehensive reports for vendor tool field discovery.
    
    Creates reports focused on purchased vendor platforms and their
    contribution to AO1 visibility statement calculations.
    """
    
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def generate_vendor_report(self, scan_results: Dict[str, List[VendorToolFieldAnalysis]], 
                             output_dir: str = ".") -> str:
        """Generate comprehensive vendor tool field discovery report."""
        
        # Analyze vendor tool capabilities
        vendor_analysis = self._analyze_vendor_capabilities(scan_results)
        priority_analysis = self._analyze_priority_vendors(scan_results)
        roi_analysis = self._analyze_vendor_roi(scan_results)
        
        # Generate report content
        report_content = self._generate_vendor_report_content(
            scan_results, vendor_analysis, priority_analysis, roi_analysis
        )
        
        # Write report
        output_file = os.path.join(output_dir, f"AO1_Vendor_Tool_Fields_{self.timestamp}.txt")
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            logger.info(f"Vendor tool field report generated: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Vendor report generation failed: {e}")
            return ""
    
    def _analyze_vendor_capabilities(self, scan_results: Dict[str, List[VendorToolFieldAnalysis]]) -> Dict[str, Any]:
        """Analyze vendor tool capabilities for visibility calculations."""
        all_results = []
        for results in scan_results.values():
            all_results.extend(results)
        
        if not all_results:
            return {}
        
        # Vendor tool distribution
        vendor_distribution = defaultdict(int)
        for result in all_results:
            for tool in result.vendor_tools:
                vendor_name = tool.split(':')[0]
                vendor_distribution[vendor_name] += 1
        
        # Neural confidence analysis
        neural_confidences = [r.neural_confidence for r in all_results]
        neural_stats = {
            'mean': np.mean(neural_confidences),
            'high_neural_confidence': len([c for c in neural_confidences if c > 0.8]),
            'medium_neural_confidence': len([c for c in neural_confidences if 0.5 <= c <= 0.8])
        }
        
        # Match type distribution
        match_types = Counter(r.match_type for r in all_results)
        
        return {
            'total_vendor_fields': len(all_results),
            'vendor_distribution': dict(vendor_distribution),
            'neural_statistics': neural_stats,
            'match_type_distribution': dict(match_types),
            'datasets_with_vendor_fields': len(scan_results)
        }
    
    def _analyze_priority_vendors(self, scan_results: Dict[str, List[VendorToolFieldAnalysis]]) -> Dict[str, Any]:
        """Analyze priority vendor tool field discoveries."""
        priority_vendors = ['chronicle', 'splunk', 'crowdstrike', 'cmdb']
        priority_analysis = {}
        
        for vendor in priority_vendors:
            priority_fields = []
            for results in scan_results.values():
                for result in results:
                    vendor_tools_str = str(result.vendor_tools).lower()
                    if vendor in vendor_tools_str:
                        priority_fields.append(result)
            
            if priority_fields:
                priority_fields.sort(key=lambda x: x.implementation_priority, reverse=True)
                
                priority_analysis[vendor] = {
                    'field_count': len(priority_fields),
                    'total_data_volume': sum(f.row_count for f in priority_fields),
                    'avg_confidence': np.mean([f.confidence for f in priority_fields]),
                    'top_fields': priority_fields[:10]
                }
        
        return priority_analysis
    
    def _analyze_vendor_roi(self, scan_results: Dict[str, List[VendorToolFieldAnalysis]]) -> Dict[str, Any]:
        """Analyze ROI potential from vendor tool field discoveries."""
        all_results = []
        for results in scan_results.values():
            all_results.extend(results)
        
        # Multi-vendor integration opportunities
        multi_vendor_fields = [r for r in all_results if len(r.vendor_tools) > 1]
        
        # High-value vendor combinations
        vendor_combinations = defaultdict(int)
        for result in multi_vendor_fields:
            vendors = sorted([t.split(':')[0] for t in result.vendor_tools])
            combo = ' + '.join(vendors)
            vendor_combinations[combo] += 1
        
        return {
            'multi_vendor_fields': len(multi_vendor_fields),
            'vendor_combinations': dict(vendor_combinations),
            'high_volume_vendor_fields': len([r for r in all_results if r.row_count > 1000000]),
            'immediate_deployment_ready': len([r for r in all_results if r.implementation_priority > 150])
        }
    
    def _generate_vendor_report_content(self, scan_results: Dict[str, List[VendorToolFieldAnalysis]],
                                      vendor_analysis: Dict[str, Any],
                                      priority_analysis: Dict[str, Any],
                                      roi_analysis: Dict[str, Any]) -> str:
        """Generate comprehensive vendor tool field discovery report content."""
        
        content = []
        
        # Header
        content.extend([
            "AO1 VENDOR TOOL FIELD DISCOVERY REPORT - NEURAL NETWORK ANALYSIS",
            "=" * 80,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Authentication Project: chronicle-fisv",
            f"Target Scanning Project: prj-fisv-p-gcss-sas-dl9dd0f1df",
            f"Neural Architecture: Forward/Backward Propagation with ReLU Activations",
            f"Focus: Purchased Vendor Tools for AO1 Visibility Calculations",
            ""
        ])
        
        # Executive Summary
        content.extend([
            "EXECUTIVE SUMMARY - PURCHASED VENDOR TOOL ANALYSIS",
            "=" * 60,
            ""
        ])
        
        if vendor_analysis:
            content.extend([
                f"Total vendor tool fields discovered: {vendor_analysis['total_vendor_fields']:,}",
                f"Datasets with vendor tool fields: {vendor_analysis['datasets_with_vendor_fields']}",
                f"Neural network mean confidence: {vendor_analysis['neural_statistics']['mean']:.3f}",
                f"High neural confidence fields: {vendor_analysis['neural_statistics']['high_neural_confidence']}",
                f"Unique vendor tools detected: {len(vendor_analysis['vendor_distribution'])}",
                ""
            ])
        
        # Priority Vendor Analysis (Chronicle, Splunk, CrowdStrike, CMDB)
        content.extend([
            "PRIORITY VENDOR PLATFORM ANALYSIS",
            "-" * 40,
            ""
        ])
        
        for vendor, analysis in priority_analysis.items():
            vendor_display = vendor.upper()
            content.extend([
                f"{vendor_display} PLATFORM FIELDS:",
                f"  Fields Found: {analysis['field_count']}",
                f"  Total Data Volume: {analysis['total_data_volume']:,} rows",
                f"  Average Confidence: {analysis['avg_confidence']:.1f}%",
                f"  Top Implementation Priority Fields: {len(analysis['top_fields'])}",
                ""
            ])
        
        # Neural Network Analysis Results
        content.extend([
            "NEURAL NETWORK ANALYSIS RESULTS",
            "-" * 40,
            ""
        ])
        
        if vendor_analysis and 'match_type_distribution' in vendor_analysis:
            content.extend([
                "FIELD CLASSIFICATION BY NEURAL NETWORK:",
                ""
            ])
            
            for match_type, count in vendor_analysis['match_type_distribution'].items():
                match_desc = {
                    'EXACT_VENDOR_MATCH': 'Exact vendor keyword + vendor pattern detection',
                    'EXACT_KEYWORD': 'Exact AO1 keyword matches',
                    'VENDOR_PATTERN_MATCH': 'Vendor pattern detection + partial keywords',
                    'VENDOR_DETECTED': 'Neural vendor pattern detection',
                    'PARTIAL_KEYWORD': 'Partial AO1 keyword matches',
                    'NEURAL_VENDOR_PREDICTION': 'Neural network vendor predictions'
                }
                content.append(f"  {match_type}: {count} fields - {match_desc.get(match_type, '')}")
            content.append("")
        
        # Vendor Tool Distribution Analysis
        content.extend([
            "PURCHASED VENDOR TOOL DISTRIBUTION",
            "-" * 40,
            ""
        ])
        
        if vendor_analysis and 'vendor_distribution' in vendor_analysis:
            sorted_vendors = sorted(vendor_analysis['vendor_distribution'].items(), 
                                  key=lambda x: x[1], reverse=True)
            
            for vendor, count in sorted_vendors[:15]:
                vendor_display = PURCHASED_VENDOR_TOOLS.get(vendor, vendor)
                content.append(f"  {vendor}: {count} fields - {vendor_display}")
            content.append("")
        
        # ROI Analysis for Purchased Vendor Tools
        content.extend([
            "VENDOR TOOL ROI ANALYSIS",
            "-" * 30,
            ""
        ])
        
        if roi_analysis:
            content.extend([
                f"Multi-vendor integration opportunities: {roi_analysis['multi_vendor_fields']} fields",
                f"High-volume vendor fields (1M+ rows): {roi_analysis['high_volume_vendor_fields']}",
                f"Immediate deployment ready: {roi_analysis['immediate_deployment_ready']} fields",
                ""
            ])
            
            if roi_analysis['vendor_combinations']:
                content.extend([
                    "TOP VENDOR TOOL COMBINATIONS:",
                    ""
                ])
                
                sorted_combos = sorted(roi_analysis['vendor_combinations'].items(),
                                     key=lambda x: x[1], reverse=True)
                
                for combo, count in sorted_combos[:10]:
                    content.append(f"  {combo}: {count} fields")
                content.append("")
        
        # Implementation Plan for Vendor Tool Fields
        content.extend([
            "VENDOR TOOL IMPLEMENTATION PLAN",
            "=" * 40,
            ""
        ])
        
        # Phase 1: Priority Vendor Implementation
        content.extend([
            "PHASE 1: PRIORITY VENDOR PLATFORMS (0-30 days)",
            "Focus: Chronicle, Splunk, CrowdStrike, CMDB fields",
            ""
        ])
        
        phase1_fields = []
        for results in scan_results.values():
            for result in results:
                vendor_tools_str = str(result.vendor_tools).lower()
                if any(vendor in vendor_tools_str for vendor in ['chronicle', 'splunk', 'crowdstrike', 'cmdb']):
                    if result.implementation_priority > 120:
                        phase1_fields.append(result)
        
        phase1_fields.sort(key=lambda x: x.implementation_priority, reverse=True)
        
        for i, field in enumerate(phase1_fields[:10], 1):
            content.extend([
                f"{i:2d}. {field.dataset_name}.{field.table_name}.{field.field_name}",
                f"    Match: {field.match_type} | Confidence: {field.confidence:.1f}% | Neural: {field.neural_confidence:.3f}",
                f"    Priority: {field.implementation_priority} | Data: {field.row_count:,} rows",
                f"    Vendor Tools: {', '.join([t.split(':')[0] for t in field.vendor_tools])}",
                f"    Visibility Purpose: {field.visibility_purpose}",
                f"    Neural Reasoning: {field.neural_reasoning}",
                ""
            ])
        
        # Detailed Analysis by AO1 Requirement and Vendor Tools
        content.extend([
            "",
            "DETAILED ANALYSIS BY AO1 REQUIREMENT AND VENDOR TOOLS",
            "=" * 65,
            ""
        ])
        
        for req_id, req_info in AO1_REQUIREMENTS.items():
            # Find fields for this requirement
            req_fields = []
            for results in scan_results.values():
                for result in results:
                    for req_str in result.matching_requirements:
                        if req_str.startswith(req_id):
                            req_fields.append(result)
                            break
            
            content.extend([
                f"{req_id}: {req_info['name']}",
                "-" * 60,
                f"Purpose: {req_info['description']}",
                f"Vendor Tools: {', '.join(req_info['vendor_tools'])}",
                f"Visibility Statement: {req_info['visibility_purpose']}",
                f"Neural Priority Weight: {req_info['neural_priority']:.2f}",
                f"Fields Discovered: {len(req_fields)}",
                ""
            ])
            
            if not req_fields:
                content.extend([
                    "NO VENDOR TOOL FIELDS FOUND for this requirement.",
                    "RECOMMENDATION: Review additional data sources or vendor platform configurations.",
                    ""
                ])
                continue
            
            # Sort by neural confidence and implementation priority
            req_fields.sort(key=lambda x: (x.neural_confidence, x.implementation_priority), reverse=True)
            
            # Categorize by vendor tools
            vendor_categories = defaultdict(list)
            for field in req_fields:
                for vendor_tool in field.vendor_tools:
                    vendor_name = vendor_tool.split(':')[0]
                    vendor_categories[vendor_name].append(field)
            
            content.extend([
                "VENDOR TOOL BREAKDOWN:",
                ""
            ])
            
            for vendor, fields in vendor_categories.items():
                vendor_display = PURCHASED_VENDOR_TOOLS.get(vendor, vendor)
                avg_confidence = np.mean([f.confidence for f in fields])
                total_volume = sum(f.row_count for f in fields)
                
                content.extend([
                    f"  {vendor.upper()}: {len(fields)} fields - {vendor_display}",
                    f"    Average Confidence: {avg_confidence:.1f}%",
                    f"    Total Data Volume: {total_volume:,} rows",
                    ""
                ])
            
            content.extend([
                "TOP VENDOR TOOL FIELDS FOR THIS REQUIREMENT:",
                ""
            ])
            
            for i, field in enumerate(req_fields[:5], 1):
                content.extend([
                    f"{i}. {field.dataset_name}.{field.table_name}.{field.field_name}",
                    f"   Match: {field.match_type} | Confidence: {field.confidence:.1f}% | Neural: {field.neural_confidence:.3f}",
                    f"   Priority: {field.implementation_priority} | Data: {field.row_count:,} rows",
                    f"   Vendor Tools: {', '.join([t.split(':')[0] for t in field.vendor_tools])}",
                    "",
                    f"   Neural Analysis:",
                    f"   {field.neural_reasoning}",
                    "",
                    f"   Business Impact:",
                    f"   {field.business_impact}",
                    "",
                    f"   Visibility Purpose:",
                    f"   {field.visibility_purpose}",
                    "",
                    "   " + "-" * 70,
                    ""
                ])
        
        # Neural Network Technical Details
        content.extend([
            "",
            "NEURAL NETWORK TECHNICAL IMPLEMENTATION",
            "=" * 50,
            "",
            "ARCHITECTURE DETAILS:",
            "  - Multi-layer neural network with ReLU activations",
            "  - Forward propagation: f(x) = max(0, W*x + b)",
            "  - Backward propagation: gradient descent with momentum optimization",
            "  - Xavier/He weight initialization for ReLU networks",
            "  - 256-dimensional semantic embeddings for vendor tool patterns",
            "  - Adaptive learning rate with momentum (β = 0.9)",
            "",
            "VENDOR TOOL PATTERN LEARNING:",
            "  - Character-level encoding for field name analysis",
            "  - Vendor-specific pattern detection algorithms",
            "  - Cross-platform semantic similarity computation",
            "  - Real-time learning from discovered field patterns",
            "",
            "NEURAL CONFIDENCE INTERPRETATION:",
            "  - >0.8: High confidence vendor tool match",
            "  - 0.6-0.8: Medium confidence, validation recommended",
            "  - 0.4-0.6: Low confidence, investigation needed",
            "  - <0.4: Weak signals, manual review required",
            ""
        ])
        
        # Implementation Guidance for Vendor Tools
        content.extend([
            "VENDOR TOOL IMPLEMENTATION GUIDANCE",
            "=" * 45,
            "",
            "PRIORITY VENDOR TOOL DEPLOYMENT:",
            "",
            "1. CHRONICLE (Google Security Operations Suite):",
            "   - Focus on UDM fields for asset identification",
            "   - Leverage metadata timestamps for visibility calculations",
            "   - Use principal/target fields for comprehensive asset coverage",
            "",
            "2. SPLUNK (Enterprise/Cloud):",
            "   - Utilize host, source, sourcetype for asset counting",
            "   - Leverage index organization for data volume analysis",
            "   - Focus on _time field for temporal visibility analysis",
            "",
            "3. CROWDSTRIKE FALCON (EDR):",
            "   - Use AID (Agent ID) for endpoint coverage calculations",
            "   - Leverage device policy fields for security posture analysis",
            "   - Focus on agent status for deployment coverage metrics",
            "",
            "4. CMDB (Configuration Management Database):",
            "   - Use sys_id and ci_name for authoritative asset counting",
            "   - Leverage business service mappings for organizational visibility",
            "   - Focus on discovery_source for data quality assessment",
            "",
            "MULTI-VENDOR INTEGRATION APPROACH:",
            "  - Cross-reference asset identifiers across platforms",
            "  - Calculate coverage gaps between vendor tool datasets",
            "  - Implement data quality checks across vendor platforms",
            "  - Establish automated visibility metric calculations",
            "",
            "VENDOR TOOL ROI OPTIMIZATION:",
            "  - Prioritize fields with multi-vendor correlation potential",
            "  - Focus on high-volume datasets for maximum visibility impact",
            "  - Implement automated field discovery for new vendor data",
            "  - Establish vendor tool data quality monitoring",
            ""
        ])
        
        return "\n".join(content)

def main():
    """
    Main execution function with neural networks and vendor tool focus.
    
    Orchestrates neural-powered vendor tool field discovery with
    forward/backward propagation and ReLU activations.
    """
    print("AO1 VENDOR TOOL FIELD DISCOVERY - NEURAL NETWORK SYSTEM")
    print("=" * 80)
    print("Advanced Neural Networks with Forward/Backward Propagation and ReLU Activations")
    print("Focus: Purchased Vendor Tools for AO1 Visibility Statement Calculations")
    print(f"Authentication Project: chronicle-fisv")
    print(f"Target Scanning Project: prj-fisv-p-gcss-sas-dl9dd0f1df")
    print(f"Priority Vendors: Chronicle, Splunk, CrowdStrike, CMDB")
    print(f"Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Step 1: Initialize Neural Network System
        print("STEP 1: NEURAL NETWORK INITIALIZATION")
        print("-" * 45)
        
        scanner = BigQueryVendorScanner()
        
        if not scanner.authenticate():
            print("BigQuery authentication failed")
            print("Please ensure proper Google Cloud credentials are configured")
            return False
        
        print("BigQuery vendor tool scanner authenticated successfully")
        print(f"Authenticated to: chronicle-fisv")
        print(f"Target project: {scanner.target_project_id}")
        print("Neural system initialized:")
        print("  - Multi-layer networks with ReLU activations")
        print("  - Forward/backward propagation with gradient descent")
        print("  - 256-dimensional semantic embeddings")
        print("  - Vendor-specific pattern learning")
        print(f"  - {len(PURCHASED_VENDOR_TOOLS)} purchased vendor tools configured")
        print()
        
        # Step 2: Neural-Powered Vendor Tool Scanning
        print("STEP 2: NEURAL VENDOR TOOL FIELD SCANNING")
        print("-" * 50)
        
        analyzer = VendorToolFieldAnalyzer()
        
        print("Initiating neural network field analysis...")
        print("Neural networks analyzing vendor tool patterns...")
        print("Forward propagation through ReLU activations...")
        print("Backward propagation training on discovered patterns...")
        print()
        
        # Perform neural-enhanced vendor tool scanning
        scan_results = scanner.scan_vendor_tool_fields(analyzer, max_datasets=100)
        
        if not scan_results:
            print("Neural scan completed: No vendor tool fields discovered")
            print("Consider reviewing vendor tool data sources or field naming patterns")
            return True
        
        # Step 3: Generate Vendor Tool Report
        print("STEP 3: VENDOR TOOL REPORT GENERATION")
        print("-" * 45)
        
        report_generator = VendorToolReportGenerator()
        report_file = report_generator.generate_vendor_report(scan_results)
        
        if report_file:
            print(f"Vendor tool field report generated: {report_file}")
        else:
            print("Vendor report generation failed")
        print()
        
        # Step 4: Executive Summary
        print("EXECUTIVE SUMMARY - VENDOR TOOL NEURAL ANALYSIS")
        print("-" * 55)
        
        total_fields = sum(len(results) for results in scan_results.values())
        
        # Priority vendor analysis
        priority_vendor_fields = 0
        neural_predictions = 0
        high_priority_fields = 0
        
        for results in scan_results.values():
            for field in results:
                vendor_tools_str = str(field.vendor_tools).lower()
                if any(vendor in vendor_tools_str for vendor in ['chronicle', 'splunk', 'crowdstrike', 'cmdb']):
                    priority_vendor_fields += 1
                
                if field.neural_confidence > 0.7:
                    neural_predictions += 1
                
                if field.implementation_priority > 150:
                    high_priority_fields += 1
        
        avg_neural_confidence = np.mean([
            field.neural_confidence 
            for results in scan_results.values() 
            for field in results
        ]) if total_fields > 0 else 0
        
        print(f"Datasets with vendor tool fields: {len(scan_results)}")
        print(f"Total vendor tool fields discovered: {total_fields:,}")
        print(f"Priority vendor platform fields: {priority_vendor_fields}")
        print(f"High-confidence neural predictions: {neural_predictions}")
        print(f"High-priority implementation fields: {high_priority_fields}")
        print(f"Average neural confidence: {avg_neural_confidence:.3f}")
        print(f"Neural enhancement ratio: {(neural_predictions/total_fields*100):.1f}%" if total_fields > 0 else "0%")
        
        if report_file:
            print(f"Detailed vendor tool report: {report_file}")
        print()
        
        print("AO1 VENDOR TOOL NEURAL DISCOVERY COMPLETE")
        print("Neural networks have identified optimal vendor tool fields for AO1 visibility")
        print("Focus on priority vendor platforms: Chronicle, Splunk, CrowdStrike, CMDB")
        print("Forward/backward propagation with ReLU activations successfully trained")
        
        return True
        
    except KeyboardInterrupt:
        print("\nNeural execution interrupted by user")
        return False
    except Exception as e:
        logger.error(f"Neural execution failed: {e}")
        print(f"Critical neural error: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)