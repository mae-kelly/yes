import subprocess
import socket
import json
import re
import logging
import ipaddress
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC

logger = logging.getLogger(__name__)

class NetworkScannerIntegration:
    def __init__(self):
        self.discovered_assets = []
        self.device_classifier = None
        
        logger.info("Network Scanner Integration initialized with SNMP, WMI, SSH, API discovery")
    
    def basic_scan(self, network_range: str) -> List[Dict]:
        logger.info(f"Starting basic network scan of {network_range}")
        
        assets = []
        
        assets.extend(self._simulate_nmap_scan(network_range))
        
        assets.extend(self._simulate_snmp_scan(network_range))
        
        assets.extend(self._simulate_wmi_scan(network_range))
        
        assets.extend(self._simulate_ssh_scan(network_range))
        
        correlated = self._multi_protocol_correlation(assets)
        
        logger.info(f"  Basic scan discovered {len(correlated)} unique assets")
        
        return correlated
    
    def _simulate_nmap_scan(self, network: str) -> List[Dict]:
        logger.info("  Running NMAP scan simulation...")
        
        simulated_results = []
        
        try:
            net = ipaddress.ip_network(network, strict=False)
            
            sample_hosts = list(net.hosts())[:100]
            
            for ip in sample_hosts[:20]:
                simulated_results.append({
                    'ip': str(ip),
                    'hostname': f"host-{ip.packed[-1]}.example.com",
                    'source': 'nmap',
                    'ports': [22, 80, 443],
                    'os': 'Linux' if ip.packed[-1] % 2 == 0 else 'Windows'
                })
            
            logger.info(f"    NMAP discovered {len(simulated_results)} hosts")
            
        except Exception as e:
            logger.error(f"    NMAP scan error: {e}")
        
        return simulated_results
    
    def _simulate_snmp_scan(self, network: str) -> List[Dict]:
        logger.info("  Running SNMP scan simulation...")
        
        results = []
        
        try:
            net = ipaddress.ip_network(network, strict=False)
            
            for ip in list(net.hosts())[:10]:
                results.append({
                    'ip': str(ip),
                    'source': 'snmp',
                    'sysName': f"switch-{ip.packed[-1]}",
                    'sysDescr': 'Cisco IOS Software',
                    'protocol': 'SNMPv2c'
                })
            
            logger.info(f"    SNMP discovered {len(results)} network devices")
            
        except Exception as e:
            logger.error(f"    SNMP scan error: {e}")
        
        return results
    
    def _simulate_wmi_scan(self, network: str) -> List[Dict]:
        logger.info("  Running WMI Windows scan simulation...")
        
        results = []
        
        try:
            for i in range(5):
                results.append({
                    'hostname': f"win-srv-{i:02d}.domain.local",
                    'source': 'wmi',
                    'os': 'Windows Server 2019',
                    'domain': 'DOMAIN',
                    'ram': '16GB',
                    'cpu': '8 cores'
                })
            
            logger.info(f"    WMI discovered {len(results)} Windows systems")
            
        except Exception as e:
            logger.error(f"    WMI scan error: {e}")
        
        return results
    
    def _simulate_ssh_scan(self, network: str) -> List[Dict]:
        logger.info("  Running SSH Unix/Linux scan simulation...")
        
        results = []
        
        try:
            for i in range(8):
                results.append({
                    'hostname': f"linux-{i:02d}.example.com",
                    'source': 'ssh',
                    'banner': f"SSH-2.0-OpenSSH_8.{i}",
                    'port': 22,
                    'os': 'Ubuntu' if i % 2 == 0 else 'CentOS'
                })
            
            logger.info(f"    SSH discovered {len(results)} Unix/Linux systems")
            
        except Exception as e:
            logger.error(f"    SSH scan error: {e}")
        
        return results
    
    def _multi_protocol_correlation(self, assets: List[Dict]) -> List[Dict]:
        logger.info("  Correlating multi-protocol scan results...")
        
        correlated = {}
        
        for asset in assets:
            key = None
            
            if 'ip' in asset:
                key = asset['ip']
            elif 'hostname' in asset:
                key = asset['hostname']
            
            if key:
                if key not in correlated:
                    correlated[key] = asset
                else:
                    correlated[key].update(asset)
        
        temporal_aligned = []
        for key, data in correlated.items():
            data['correlation_confidence'] = len(data.get('source', '').split(','))
            temporal_aligned.append(data)
        
        logger.info(f"    Correlated {len(assets)} results into {len(temporal_aligned)} unique assets")
        
        return temporal_aligned
    
    def cloud_api_discovery(self) -> List[Dict]:
        logger.info("Running cloud API discovery for AWS, Azure, GCP")
        
        discovered = []
        
        discovered.extend(self._aws_discovery())
        discovered.extend(self._azure_discovery())
        discovered.extend(self._gcp_discovery())
        
        return discovered
    
    def _aws_discovery(self) -> List[Dict]:
        logger.info("  AWS API discovery simulation...")
        
        assets = []
        
        for i in range(10):
            assets.append({
                'hostname': f"ec2-{i:03d}.amazonaws.com",
                'source': 'aws_api',
                'instance_id': f"i-{i:016x}",
                'instance_type': 't3.medium',
                'state': 'running',
                'vpc_id': f"vpc-{i:08x}",
                'cloud_provider': 'AWS'
            })
        
        logger.info(f"    AWS discovered {len(assets)} EC2 instances")
        
        return assets
    
    def _azure_discovery(self) -> List[Dict]:
        logger.info("  Azure API discovery simulation...")
        
        assets = []
        
        for i in range(8):
            assets.append({
                'hostname': f"vm-{i:03d}.azure.com",
                'source': 'azure_api',
                'vm_id': f"/subscriptions/xxx/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm{i}",
                'size': 'Standard_B2s',
                'os': 'Windows' if i % 2 == 0 else 'Linux',
                'cloud_provider': 'Azure'
            })
        
        logger.info(f"    Azure discovered {len(assets)} VMs")
        
        return assets
    
    def _gcp_discovery(self) -> List[Dict]:
        logger.info("  GCP API discovery simulation...")
        
        assets = []
        
        for i in range(6):
            assets.append({
                'hostname': f"instance-{i}.c.project.internal",
                'source': 'gcp_api',
                'instance_name': f"instance-{i}",
                'machine_type': 'n1-standard-1',
                'zone': f"us-central1-{'abc'[i%3]}",
                'cloud_provider': 'GCP'
            })
        
        logger.info(f"    GCP discovered {len(assets)} compute instances")
        
        return assets
    
    def train_device_classifier(self, scan_data: List[Dict]):
        logger.info("Training ML classifiers for device type identification")
        
        if not scan_data:
            return
        
        features = []
        labels = []
        
        for asset in scan_data:
            feature_vec = [
                1 if 'ssh' in asset.get('source', '') else 0,
                1 if 'snmp' in asset.get('source', '') else 0,
                1 if 'wmi' in asset.get('source', '') else 0,
                1 if 'Windows' in asset.get('os', '') else 0,
                1 if 'Linux' in asset.get('os', '') else 0,
                len(asset.get('ports', [])),
                1 if asset.get('cloud_provider') else 0
            ]
            
            features.append(feature_vec)
            
            if 'switch' in asset.get('hostname', '').lower():
                labels.append('network_device')
            elif 'Windows' in asset.get('os', ''):
                labels.append('windows_server')
            elif 'Linux' in asset.get('os', '') or 'Ubuntu' in asset.get('os', ''):
                labels.append('linux_server')
            elif asset.get('cloud_provider'):
                labels.append('cloud_instance')
            else:
                labels.append('unknown')
        
        if len(set(labels)) > 1:
            logger.info("  Training Random Forest classifier...")
            rf_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
            rf_classifier.fit(features, labels)
            
            logger.info("  Training Support Vector Machine classifier...")
            svm_classifier = SVC(kernel='rbf', gamma='scale')
            svm_classifier.fit(features, labels)
            
            rf_score = rf_classifier.score(features, labels)
            svm_score = svm_classifier.score(features, labels)
            
            logger.info(f"    Random Forest accuracy: {rf_score:.2%}")
            logger.info(f"    SVM accuracy: {svm_score:.2%}")
            
            self.device_classifier = rf_classifier
    
    def fuzzy_match_assets(self, scan_assets: List[Dict], cmdb_assets: List[Dict]) -> List[Dict]:
        logger.info("Performing fuzzy matching between scan and CMDB data")
        
        matches = []
        
        for scan_asset in scan_assets:
            best_match = None
            best_score = 0
            
            scan_hostname = scan_asset.get('hostname', '').lower()
            scan_ip = scan_asset.get('ip', '')
            scan_mac = scan_asset.get('mac', '').lower()
            
            for cmdb_asset in cmdb_assets:
                score = 0
                
                cmdb_hostname = cmdb_asset.get('hostname', '').lower()
                cmdb_ip = cmdb_asset.get('ip', '')
                cmdb_mac = cmdb_asset.get('mac', '').lower()
                
                if scan_hostname and cmdb_hostname:
                    if scan_hostname == cmdb_hostname:
                        score += 3
                    elif scan_hostname in cmdb_hostname or cmdb_hostname in scan_hostname:
                        score += 1
                
                if scan_ip and cmdb_ip and scan_ip == cmdb_ip:
                    score += 2
                
                if scan_mac and cmdb_mac and scan_mac == cmdb_mac:
                    score += 3
                
                if score > best_score:
                    best_score = score
                    best_match = cmdb_asset
            
            if best_score > 0:
                matches.append({
                    'scan_asset': scan_asset,
                    'cmdb_asset': best_match,
                    'match_score': best_score
                })
        
        logger.info(f"  Found {len(matches)} matches between scan and CMDB")
        
        return matches