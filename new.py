import json
import pandas as pd
from collections import defaultdict
from typing import Dict, List, Set, Tuple
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComprehensiveKeyMapper:
    def __init__(self, results_file: str):
        self.results_file = results_file
        self.data = None
        self.load_results()
        
        self.security_requirements = {
            'Network': {
                'Firewall Traffic': [
                    'firewall', 'fw', 'filter', 'traffic', 'packet', 'flow', 'connection', 'session',
                    'iptables', 'pf', 'ufw', 'pfctl', 'netfilter', 'pix', 'asa', 'fwsm', 'checkpoint', 'fw1',
                    'fortigate', 'fortinet', 'fortianalyzer', 'fortimanager', 'palo_alto', 'paloalto', 'panorama',
                    'juniper', 'srx', 'netscreen', 'cisco_asa', 'cisco_pix', 'sonicwall', 'watchguard', 'firebox',
                    'barracuda', 'sophos', 'astaro', 'cyberoam', 'smoothwall', 'endian', 'untangle', 'clearos',
                    'pfense', 'opnsense', 'ipfire', 'zeroshell', 'vyos', 'vyatta', 'mikrotik', 'routeros',
                    'allow', 'deny', 'drop', 'reject', 'block', 'permit', 'accept', 'forward', 'route',
                    'nat', 'pat', 'xlate', 'translation', 'masquerade', 'snat', 'dnat', 'port_forward',
                    'acl', 'access_list', 'rule', 'policy', 'security_policy', 'zone', 'interface',
                    'ingress', 'egress', 'inbound', 'outbound', 'north_south', 'east_west'
                ],
                'IDS/IPS': [
                    'ids', 'ips', 'intrusion', 'detection', 'prevention', 'signature', 'alert', 'event',
                    'anomaly', 'threat', 'attack', 'exploit', 'malware', 'virus', 'trojan', 'worm',
                    'snort', 'suricata', 'zeek', 'bro', 'emerging_threats', 'et_pro', 'vrt', 'talos',
                    'sourcefire', 'firesight', 'cisco_ips', 'cisco_ids', 'checkpoint_ips', 'smart_defense',
                    'juniper_ips', 'juniper_ids', 'fortinet_ips', 'fortigate_ips', 'palo_alto_threat',
                    'wildfire', 'mcafee_ips', 'mcafee_ids', 'tippingpoint', 'hp_tippingpoint', 'trend_micro',
                    'deep_security', 'nessus', 'rapid7', 'nexpose', 'qualys', 'tenable', 'greenbone',
                    'ossim', 'ossec', 'samhain', 'aide', 'prelude', 'suricata_eve', 'fast_log',
                    'behavioral', 'heuristic', 'machine_learning', 'ai_detection', 'statistical', 'baseline',
                    'correlation', 'rule_based', 'signature_based', 'anomaly_based', 'reputation_based',
                    'nids', 'hids', 'nips', 'hips', 'network_intrusion', 'host_intrusion', 'endpoint_detection'
                ],
                'NDR': [
                    'ndr', 'network_detection', 'network_detection_response', 'network_monitoring', 'netmon',
                    'traffic_analysis', 'flow_analysis', 'packet_analysis', 'deep_packet_inspection', 'dpi',
                    'behavioral_analysis', 'anomaly_detection', 'lateral_movement', 'east_west', 'north_south',
                    'darktrace', 'vectra', 'extrahop', 'corelight', 'plixer', 'scrutinizer', 'flowmon',
                    'kentik', 'gigamon', 'ixia', 'netscout', 'arbor', 'radware', 'a10_networks',
                    'netflow', 'sflow', 'ipfix', 'jflow', 'cflowd', 'nfcapd', 'softflowd', 'fprobe',
                    'metadata', 'session_data', 'connection_tracking', 'state_tracking', 'flow_record',
                    'network_forensics', 'pcap', 'packet_capture', 'full_packet', 'session_reconstruction'
                ],
                'Proxy': [
                    'proxy', 'gateway', 'web_gateway', 'secure_web_gateway', 'swg', 'web_security',
                    'web_filter', 'content_filter', 'url_filter', 'category_filter', 'reputation_filter',
                    'squid', 'squidguard', 'dansguardian', 'e2guardian', 'bluecoat', 'proxysg', 'packetshaper',
                    'zscaler', 'zpa', 'zia', 'forcepoint', 'websense', 'triton', 'mcafee_proxy', 'web_gateway',
                    'symantec_proxy', 'broadcom_proxy', 'cisco_wsa', 'ironport', 'smoothwall', 'untangle',
                    'forward_proxy', 'reverse_proxy', 'transparent_proxy', 'explicit_proxy', 'intercepting_proxy',
                    'http_proxy', 'https_proxy', 'socks_proxy', 'connect_proxy', 'ssl_proxy', 'tls_proxy'
                ],
                'DNS': [
                    'dns', 'domain', 'hostname', 'fqdn', 'subdomain', 'tld', 'nameserver', 'resolver',
                    'bind', 'named', 'bind9', 'isc_bind', 'unbound', 'powerdns', 'pdns', 'knot', 'knot_dns',
                    'nsd', 'authoritative', 'recursive', 'dnsmasq', 'systemd_resolved', 'windows_dns',
                    'active_directory_dns', 'ad_dns', 'infoblox', 'bluecat', 'efficient_ip',
                    'dnssec', 'dns_over_https', 'doh', 'dns_over_tls', 'dot', 'dns_crypt', 'quad9',
                    'dns_poisoning', 'dns_spoofing', 'dns_hijacking', 'dns_tunneling', 'dns_exfiltration',
                    'dga', 'domain_generation', 'malicious_domain', 'typosquatting', 'homograph', 'punycode'
                ],
                'WAF': [
                    'waf', 'web_application_firewall', 'application_firewall', 'web_protection', 'app_protection',
                    'f5_asm', 'f5_awaf', 'f5_bigip', 'imperva', 'incapsula', 'cloudflare', 'cloudflare_waf',
                    'akamai', 'kona', 'prolexic', 'aws_waf', 'azure_waf', 'azure_front_door', 'gcp_armor',
                    'barracuda_waf', 'fortinet_waf', 'fortigate_waf', 'checkpoint_waf', 'radware', 'alteon',
                    'modsecurity', 'apache_modsecurity', 'nginx_modsecurity', 'sucuri', 'wordfence',
                    'owasp', 'sql_injection', 'sqli', 'cross_site_scripting', 'xss', 'csrf', 'xxe',
                    'ssrf', 'lfi', 'rfi', 'path_traversal', 'command_injection', 'code_injection'
                ]
            },
            'Endpoint': {
                'OS logs (WinEVT, Linux syslog)': [
                    'winevent', 'winevt', 'eventlog', 'event_log', 'windows_event', 'win_event', 'evtx', 'evt',
                    'security_log', 'system_log', 'application_log', 'setup_log', 'forwarded_events', 'wef', 'wec',
                    'sysmon', 'process_monitor', 'procmon', 'audit_policy', 'advanced_audit', 'sacl', 'dacl',
                    'syslog', 'rsyslog', 'syslog_ng', 'journald', 'systemd_journal', 'kern_log', 'daemon_log',
                    'auth_log', 'secure_log', 'messages', 'var_log', 'system_journal', 'user_journal',
                    'auditd', 'ausearch', 'aureport', 'pam_log', 'sudo_log', 'su_log', 'cron_log'
                ],
                'EDR': [
                    'edr', 'endpoint_detection', 'endpoint_detection_response', 'endpoint_protection', 'endpoint_security',
                    'crowdstrike', 'falcon', 'falcon_sensor', 'carbon_black', 'cb_response', 'cb_protection',
                    'sentinelone', 's1_agent', 'sentinel_agent', 'cylance', 'cylance_protect', 'blackberry_cylance',
                    'defender_atp', 'microsoft_defender', 'windows_defender_atp', 'mdatp', 'mde', 'cortex_xdr',
                    'palo_alto_traps', 'traps_agent', 'symantec_endpoint', 'sep', 'mcafee_endpoint', 'trellix',
                    'behavioral_analysis', 'machine_learning_detection', 'threat_hunting', 'incident_response',
                    'process_tracking', 'file_analysis', 'network_analysis', 'memory_analysis', 'registry_analysis'
                ],
                'DLP': [
                    'dlp', 'data_loss_prevention', 'data_leak_prevention', 'information_protection', 'data_protection',
                    'symantec_dlp', 'broadcom_dlp', 'forcepoint_dlp', 'websense_dlp', 'mcafee_dlp', 'trellix_dlp',
                    'microsoft_purview', 'information_protection', 'azure_information_protection', 'aip',
                    'pii', 'personally_identifiable', 'phi', 'protected_health', 'pci', 'payment_card', 'ssn',
                    'data_classification', 'content_classification', 'sensitive_data', 'confidential_data'
                ],
                'FIM': [
                    'fim', 'file_integrity', 'file_integrity_monitoring', 'integrity_monitoring', 'file_monitoring',
                    'tripwire', 'tripwire_enterprise', 'aide', 'samhain', 'ossec', 'ossec_hids', 'wazuh',
                    'osquery', 'facebook_osquery', 'auditbeat', 'elastic_auditbeat', 'filebeat', 'winlogbeat',
                    'system_files', 'configuration_files', 'registry', 'windows_registry', 'boot_sector',
                    'file_hash', 'checksum', 'md5', 'sha1', 'sha256', 'modification_time', 'permissions'
                ]
            },
            'Cloud': {
                'Cloud Event': [
                    'cloudtrail', 'aws_cloudtrail', 'cloudwatch', 'aws_cloudwatch', 'vpc_flow_logs', 'aws_config',
                    'guardduty', 'aws_guardduty', 'macie', 'aws_macie', 'inspector', 'aws_inspector',
                    'activity_log', 'azure_activity_log', 'azure_monitor', 'log_analytics', 'azure_sentinel',
                    'cloud_logging', 'stackdriver', 'cloud_audit_logs', 'admin_activity', 'data_access',
                    'cloud_security', 'cloud_audit', 'cloud_compliance', 'infrastructure_logs', 'platform_logs'
                ],
                'Cloud Load Balancer': [
                    'elb', 'elastic_load_balancer', 'alb', 'application_load_balancer', 'nlb', 'network_load_balancer',
                    'azure_load_balancer', 'application_gateway', 'front_door', 'traffic_manager',
                    'cloud_load_balancing', 'http_load_balancer', 'https_load_balancer', 'tcp_load_balancer',
                    'load_balancing', 'traffic_distribution', 'session_affinity', 'sticky_session'
                ]
            },
            'Application': {
                'Web Logs (HTTP Access)': [
                    'apache', 'httpd', 'apache_access', 'apache_error', 'nginx', 'nginx_access', 'nginx_error',
                    'iis', 'internet_information_services', 'iis_log', 'w3c_log', 'ncsa_log', 'tomcat', 'catalina',
                    'access_log', 'error_log', 'combined_log', 'common_log', 'referer_log', 'agent_log',
                    'http_request', 'http_response', 'http_method', 'status_code', 'response_code', 'user_agent',
                    'django', 'flask', 'fastapi', 'rails', 'express', 'spring', 'laravel', 'asp.net', 'php'
                ],
                'API Gateway': [
                    'api_gateway', 'aws_api_gateway', 'azure_api_management', 'gcp_api_gateway', 'apigee',
                    'kong', 'kong_gateway', 'ambassador', 'istio', 'envoy_proxy', 'traefik', 'zuul',
                    'rate_limiting', 'throttling', 'api_key', 'oauth', 'jwt', 'bearer_token', 'api_versioning'
                ]
            },
            'Identity_Authentication': {
                'Authentication attempts': [
                    'auth', 'login', 'authentication', 'signin', 'logon', 'kerberos', 'ldap', 'saml', 'oauth',
                    'active_directory', 'ad_audit', 'identity_provider', 'sso', 'single_sign_on', 'mfa',
                    'multi_factor', 'two_factor', '2fa', 'okta', 'ping_identity', 'azure_ad', 'google_identity'
                ],
                'Privilege escalation': [
                    'privilege', 'escalation', 'sudo', 'runas', 'su_log', 'elevation', 'admin_access', 'root_access',
                    'administrator', 'elevated', 'impersonation', 'token_manipulation', 'uac', 'user_account_control'
                ],
                'Identity creation/modification/destroy': [
                    'user_creation', 'user_modification', 'user_deletion', 'account_creation', 'account_modification',
                    'identity_management', 'provisioning', 'deprovisioning', 'user_lifecycle', 'joiner_mover_leaver',
                    'role_assignment', 'group_membership', 'permission_change', 'access_change', 'entitlement'
                ]
            }
        }
        
        self.data_fields = {
            'IP (source, target)': ['source_ip', 'target_ip', 'src_ip', 'dst_ip', 'ip_address', 'client_ip', 'server_ip'],
            'Protocol': ['protocol', 'ip_protocol', 'transport_protocol'],
            'Detection Signature': ['signature', 'detection_signature', 'rule_signature', 'rule_id', 'signature_id'],
            'Port': ['port', 'source_port', 'dest_port', 'src_port', 'dst_port', 'service_port'],
            'Record/FQDN': ['fqdn', 'domain', 'record', 'dns_name', 'hostname'],
            'HTTP Headers': ['http_headers', 'headers', 'http_header', 'request_headers', 'response_headers'],
            'system name': ['system_name', 'hostname', 'host_name', 'computer_name', 'machine_name'],
            'filename': ['filename', 'file_name', 'file_path', 'path', 'full_path']
        }
        
        self.visibility_factors = {
            'URL/FQDN coverage': ['url', 'fqdn', 'domain_coverage', 'web_coverage', 'site_coverage'],
            'CMDB Asset Visibility': ['cmdb', 'asset_visibility', 'configuration_management', 'asset_inventory'],
            'Network Zones/spans': ['network_zone', 'network_span', 'zone', 'network_segment', 'vlan', 'subnet'],
            'IPAM Public IP Coverage': ['ipam', 'public_ip', 'ip_management', 'ip_address_management'],
            'Geolocation': ['geolocation', 'geo_location', 'country', 'region', 'city', 'coordinates'],
            'VPC': ['vpc', 'virtual_private_cloud', 'virtual_network', 'vnet'],
            'Crowdstrike Agent Coverage': ['crowdstrike', 'cs_agent', 'falcon', 'falcon_sensor'],
            '%log ingest volume': ['log_volume', 'ingest_volume', 'log_size', 'bytes_ingested', 'events_per_second']
        }

    def load_results(self):
        import os
        
        current_dir = os.getcwd()
        file_path = os.path.abspath(self.results_file)
        file_exists = os.path.exists(self.results_file)
        
        print(f"Current directory: {current_dir}")
        print(f"Looking for file: {self.results_file}")
        print(f"Full path: {file_path}")
        print(f"File exists: {file_exists}")
        
        files_in_dir = [f for f in os.listdir('.') if f.endswith('.json')]
        print(f"JSON files in current directory: {files_in_dir}")
        
        try:
            with open(self.results_file, 'r') as f:
                self.data = json.load(f)
            logger.info(f"Successfully loaded results from {self.results_file}")
        except FileNotFoundError as e:
            logger.error(f"File not found: {self.results_file}")
            logger.error(f"Available JSON files: {files_in_dir}")
            raise
        except Exception as e:
            logger.error(f"Error loading results: {e}")
            raise

    def extract_all_keys(self) -> Dict[str, List[Dict]]:
        all_keys = {
            'dataset_names': [],
            'table_names': [],
            'column_names': []
        }
        
        if not self.data or 'datasets' not in self.data:
            logger.warning("No datasets found in data structure")
            return all_keys
        
        for dataset_id in self.data['datasets'].keys():
            all_keys['dataset_names'].append({
                'name': dataset_id,
                'dataset_id': dataset_id,
                'type': 'dataset'
            })
        
        for dataset_id, dataset_info in self.data['datasets'].items():
            if isinstance(dataset_info, dict) and 'tables' in dataset_info:
                for table_id, table_info in dataset_info['tables'].items():
                    all_keys['table_names'].append({
                        'name': table_id,
                        'dataset_id': dataset_id,
                        'table_id': table_id,
                        'type': 'table'
                    })
                    
                    if isinstance(table_info, dict) and 'columns' in table_info:
                        columns = table_info['columns']
                        if isinstance(columns, list):
                            for column in columns:
                                if isinstance(column, dict) and 'name' in column:
                                    all_keys['column_names'].append({
                                        'name': column['name'],
                                        'dataset_id': dataset_id,
                                        'table_id': table_id,
                                        'column_type': column.get('type', 'unknown'),
                                        'column_mode': column.get('mode', 'unknown'),
                                        'type': 'column'
                                    })
        
        return all_keys

    def find_matches(self, key_name: str, requirement_terms: List[str]) -> bool:
        key_lower = key_name.lower()
        
        for term in requirement_terms:
            term_lower = term.lower()
            if term_lower == key_lower or term_lower in key_lower:
                return True
        return False

    def map_keys_to_requirements(self) -> Dict[str, Any]:
        all_keys = self.extract_all_keys()
        
        results = {
            'matches': {
                'log_types': {},
                'data_fields': {},
                'visibility_factors': {}
            },
            'unmapped': {
                'dataset_names': [],
                'table_names': [],
                'column_names': []
            },
            'summary': {
                'total_keys': {},
                'mapped_keys': {},
                'unmapped_keys': {},
                'mapping_rate': {}
            }
        }
        
        all_mapped_keys = {
            'dataset_names': set(),
            'table_names': set(), 
            'column_names': set()
        }
        
        for role, requirements in self.security_requirements.items():
            results['matches']['log_types'][role] = {}
            
            for log_type, terms in requirements.items():
                results['matches']['log_types'][role][log_type] = {
                    'dataset_names': [],
                    'table_names': [],
                    'column_names': []
                }
                
                for key_type in ['dataset_names', 'table_names', 'column_names']:
                    for key_info in all_keys[key_type]:
                        if self.find_matches(key_info['name'], terms):
                            results['matches']['log_types'][role][log_type][key_type].append(key_info)
                            all_mapped_keys[key_type].add(key_info['name'])
        
        for field_name, terms in self.data_fields.items():
            results['matches']['data_fields'][field_name] = {
                'dataset_names': [],
                'table_names': [],
                'column_names': []
            }
            
            for key_type in ['dataset_names', 'table_names', 'column_names']:
                for key_info in all_keys[key_type]:
                    if self.find_matches(key_info['name'], terms):
                        results['matches']['data_fields'][field_name][key_type].append(key_info)
                        all_mapped_keys[key_type].add(key_info['name'])
        
        for factor_name, terms in self.visibility_factors.items():
            results['matches']['visibility_factors'][factor_name] = {
                'dataset_names': [],
                'table_names': [],
                'column_names': []
            }
            
            for key_type in ['dataset_names', 'table_names', 'column_names']:
                for key_info in all_keys[key_type]:
                    if self.find_matches(key_info['name'], terms):
                        results['matches']['visibility_factors'][factor_name][key_type].append(key_info)
                        all_mapped_keys[key_type].add(key_info['name'])
        
        for key_type in ['dataset_names', 'table_names', 'column_names']:
            for key_info in all_keys[key_type]:
                if key_info['name'] not in all_mapped_keys[key_type]:
                    results['unmapped'][key_type].append(key_info)
        
        for key_type in ['dataset_names', 'table_names', 'column_names']:
            total = len(all_keys[key_type])
            unmapped = len(results['unmapped'][key_type])
            mapped = total - unmapped
            
            results['summary']['total_keys'][key_type] = total
            results['summary']['mapped_keys'][key_type] = mapped
            results['summary']['unmapped_keys'][key_type] = unmapped
            results['summary']['mapping_rate'][key_type] = (mapped / total * 100) if total > 0 else 0
        
        return results

    def generate_report(self) -> str:
        mapping_results = self.map_keys_to_requirements()
        
        report = []
        report.append("=" * 80)
        report.append("CYBERSECURITY LOG VISIBILITY - COMPREHENSIVE KEY MAPPING REPORT")
        report.append("=" * 80)
        report.append("")
        
        report.append("EXECUTIVE SUMMARY:")
        report.append("-" * 40)
        total_all = sum(mapping_results['summary']['total_keys'].values())
        mapped_all = sum(mapping_results['summary']['mapped_keys'].values())
        overall_rate = (mapped_all / total_all * 100) if total_all > 0 else 0
        
        report.append(f"Overall Mapping Rate: {mapped_all}/{total_all} ({overall_rate:.1f}%)")
        report.append("")
        
        for key_type in ['dataset_names', 'table_names', 'column_names']:
            total = mapping_results['summary']['total_keys'][key_type]
            mapped = mapping_results['summary']['mapped_keys'][key_type]
            rate = mapping_results['summary']['mapping_rate'][key_type]
            report.append(f"{key_type.replace('_', ' ').title()}: {mapped}/{total} ({rate:.1f}%)")
        
        report.append("")
        
        report.append("SECURITY ROLE COVERAGE:")
        report.append("-" * 40)
        
        for role, requirements in mapping_results['matches']['log_types'].items():
            report.append(f"\n{role.upper()}:")
            
            for log_type, matches in requirements.items():
                total_matches = sum(len(matches[kt]) for kt in ['dataset_names', 'table_names', 'column_names'])
                
                if total_matches > 0:
                    report.append(f"  ✓ {log_type}: {total_matches} matches")
                    
                    for key_type in ['dataset_names', 'table_names', 'column_names']:
                        if matches[key_type]:
                            sample_names = [m['name'] for m in matches[key_type][:3]]
                            if len(matches[key_type]) > 3:
                                sample_names.append(f"...and {len(matches[key_type])-3} more")
                            report.append(f"    {key_type}: {', '.join(sample_names)}")
                else:
                    report.append(f"  ✗ {log_type}: No matches found")
        
        report.append("")
        report.append("")
        report.append("DATA FIELDS COVERAGE:")
        report.append("-" * 40)
        
        for field_name, matches in mapping_results['matches']['data_fields'].items():
            total_matches = sum(len(matches[kt]) for kt in ['dataset_names', 'table_names', 'column_names'])
            
            if total_matches > 0:
                report.append(f"✓ {field_name}: {total_matches} matches")
                for key_type in ['dataset_names', 'table_names', 'column_names']:
                    if matches[key_type]:
                        sample_names = [m['name'] for m in matches[key_type][:3]]
                        if len(matches[key_type]) > 3:
                            sample_names.append(f"...and {len(matches[key_type])-3} more")
                        report.append(f"  {key_type}: {', '.join(sample_names)}")
            else:
                report.append(f"✗ {field_name}: No matches found")
        
        report.append("")
        report.append("")
        report.append("VISIBILITY FACTORS COVERAGE:")
        report.append("-" * 40)
        
        for factor_name, matches in mapping_results['matches']['visibility_factors'].items():
            total_matches = sum(len(matches[kt]) for kt in ['dataset_names', 'table_names', 'column_names'])
            
            if total_matches > 0:
                report.append(f"✓ {factor_name}: {total_matches} matches")
                for key_type in ['dataset_names', 'table_names', 'column_names']:
                    if matches[key_type]:
                        sample_names = [m['name'] for m in matches[key_type][:3]]
                        if len(matches[key_type]) > 3:
                            sample_names.append(f"...and {len(matches[key_type])-3} more")
                        report.append(f"  {key_type}: {', '.join(sample_names)}")
            else:
                report.append(f"✗ {factor_name}: No matches found")
        
        report.append("")
        report.append("")
        report.append("GAP ANALYSIS - UNMAPPED KEYS:")
        report.append("-" * 40)
        
        for key_type in ['dataset_names', 'table_names', 'column_names']:
            unmapped = mapping_results['unmapped'][key_type]
            if unmapped:
                report.append("")
                report.append(f"Unmapped {key_type}:")
                for key_info in unmapped[:10]:
                    location = f"{key_info.get('dataset_id', '')}"
                    if key_info.get('table_id'):
                        location += f".{key_info['table_id']}"
                    report.append(f"  - {key_info['name']} ({location})")
                
                if len(unmapped) > 10:
                    report.append(f"  ... and {len(unmapped)-10} more unmapped {key_type}")
        
        return "\n".join(report)

    def save_detailed_results(self, output_file: str):
        mapping_results = self.map_keys_to_requirements()
        
        with open(output_file, 'w') as f:
            json.dump(mapping_results, f, indent=2, default=str)
        
        logger.info(f"Detailed results saved to {output_file}")

if __name__ == "__main__":
    analyzer = ComprehensiveKeyMapper("new.json")
    
    report = analyzer.generate_report()
    print(report)
    
    analyzer.save_detailed_results("security_mapping_results.json")