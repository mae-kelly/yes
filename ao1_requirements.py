AO1_VISIBILITY_REQUIREMENTS = {
    'Network': {
        'URL/FQDN coverage': {
            'synonyms': ['url', 'fqdn', 'domain', 'hostname', 'web_address', 'site', 'uri', 'web_url', 'dns_name', 'domain_name', 'host_name', 'server_name', 'website', 'web_site', 'fully_qualified_domain_name'],
            'partial_matches': ['url', 'domain', 'host', 'fqdn', 'dns', 'web', 'site', 'name', 'server', 'qualified'],
            'description': 'Measure coverage of URL/FQDN data across network logs for threat detection and web traffic analysis',
            'visibility_query': 'What percentage of network events contain URL/domain information for threat intelligence correlation?',
            'business_impact': 'Critical for detecting malicious domains, C2 communications, and web-based threats',
            'threat_context': 'URLs and domains are primary indicators of command & control communications and malicious web activity',
            'priority': 'HIGH',
            'complexity': 'LOW'
        },
        'CMDB Asset Visibility': {
            'synonyms': ['cmdb', 'asset', 'inventory', 'configuration', 'device', 'endpoint', 'machine', 'computer', 'workstation', 'server', 'node', 'equipment', 'hardware', 'configuration_management_database'],
            'partial_matches': ['asset', 'inventory', 'config', 'device', 'endpoint', 'machine', 'computer', 'equipment', 'cmdb', 'mgmt'],
            'description': 'Measure asset visibility through IP/hostname/device correlation with CMDB for comprehensive asset tracking',
            'visibility_query': 'What percentage of network traffic can be correlated to known assets in CMDB for complete visibility?',
            'business_impact': 'Essential for asset management, attack surface visibility, and incident response attribution',
            'threat_context': 'Unknown or unmanaged assets create significant blind spots for threat detection and response',
            'priority': 'HIGH',
            'complexity': 'MEDIUM'
        },
        'Network Zones/spans': {
            'synonyms': ['zone', 'network_zone', 'span', 'network_span', 'segment', 'network_segment', 'vlan', 'subnet', 'network', 'lan', 'wan', 'dmz', 'perimeter', 'security_zone'],
            'partial_matches': ['zone', 'span', 'segment', 'vlan', 'subnet', 'network', 'lan', 'wan', 'dmz', 'perimeter'],
            'description': 'Measure network zone and span visibility coverage for network segmentation monitoring',
            'visibility_query': 'What percentage of traffic is tagged with network zone information for segmentation analysis?',
            'business_impact': 'Critical for network segmentation validation, lateral movement detection, and zero-trust implementation',
            'threat_context': 'Network segmentation visibility enables detection of unauthorized zone traversal and lateral movement',
            'priority': 'HIGH',
            'complexity': 'MEDIUM'
        },
        'IPAM Public IP Coverage': {
            'synonyms': ['ipam', 'public_ip', 'ip_management', 'ip_address_management', 'external_ip', 'internet_ip', 'wan_ip', 'routable_ip', 'public_address'],
            'partial_matches': ['ipam', 'public_ip', 'external_ip', 'internet', 'wan', 'routable', 'ip_mgmt', 'public'],
            'description': 'Measure public IP address management and coverage through IPAM correlation',
            'visibility_query': 'What percentage of public IPs are tracked and managed in IPAM for external exposure monitoring?',
            'business_impact': 'Essential for external attack surface management and public IP governance',
            'threat_context': 'Unmanaged public IPs represent common entry points for external attacks and reconnaissance',
            'priority': 'MEDIUM',
            'complexity': 'MEDIUM'
        },
        'Geolocation': {
            'synonyms': ['geo', 'geolocation', 'geo_location', 'location', 'country', 'region', 'city', 'latitude', 'longitude', 'coordinates', 'geographic', 'locale', 'geoip'],
            'partial_matches': ['geo', 'location', 'country', 'region', 'city', 'lat', 'lon', 'coord', 'geographic'],
            'description': 'Measure geographic location data coverage for threat attribution and anomaly detection',
            'visibility_query': 'What percentage of traffic has geographic location data for threat intelligence and compliance?',
            'business_impact': 'Enables geographic threat analysis, compliance monitoring, and geopolitical risk assessment',
            'threat_context': 'Geolocation anomalies often indicate compromised accounts, VPN usage, or external threat activity',
            'priority': 'MEDIUM',
            'complexity': 'LOW'
        },
        'VPC': {
            'synonyms': ['vpc', 'virtual_private_cloud', 'virtual_network', 'vnet', 'cloud_network', 'private_cloud', 'virtual_lan', 'cloud_vpc'],
            'partial_matches': ['vpc', 'virtual', 'cloud', 'vnet', 'private', 'network'],
            'description': 'Measure VPC and virtual network visibility for cloud network security monitoring',
            'visibility_query': 'What percentage of cloud traffic is VPC-tagged for network security analysis?',
            'business_impact': 'Critical for cloud network security, compliance, and multi-cloud visibility',
            'threat_context': 'VPC visibility is essential for detecting cloud-based lateral movement and network attacks',
            'priority': 'HIGH',
            'complexity': 'LOW'
        },
        'Log Ingest Volume': {
            'synonyms': ['log_volume', 'ingest_volume', 'log_size', 'bytes_ingested', 'events_per_second', 'log_count', 'message_count', 'record_count', 'logging_volume', 'ingestion_rate'],
            'partial_matches': ['volume', 'ingest', 'size', 'bytes', 'count', 'records', 'messages', 'events', 'logging', 'rate'],
            'description': 'Measure log ingestion volume and coverage rates for infrastructure capacity monitoring',
            'visibility_query': 'What is the log ingestion rate and volume coverage percentage for capacity planning?',
            'business_impact': 'Fundamental metric for measuring logging infrastructure capacity and coverage gaps',
            'threat_context': 'Log volume gaps and anomalies indicate potential blind spots or infrastructure issues in security monitoring',
            'priority': 'CRITICAL',
            'complexity': 'LOW'
        }
    },
    'Endpoint': {
        'CMDB Asset Visibility': {
            'synonyms': ['cmdb', 'asset', 'inventory', 'endpoint', 'device', 'computer', 'workstation', 'machine', 'host', 'system', 'endpoint_inventory'],
            'partial_matches': ['asset', 'inventory', 'endpoint', 'device', 'computer', 'machine', 'host', 'cmdb'],
            'description': 'Measure endpoint asset inventory coverage in CMDB for comprehensive endpoint management',
            'visibility_query': 'What percentage of endpoints are tracked in CMDB asset inventory for complete visibility?',
            'business_impact': 'Essential for endpoint management, security coverage assessment, and incident response',
            'threat_context': 'Unmanaged endpoints represent high-risk attack vectors and security blind spots',
            'priority': 'HIGH',
            'complexity': 'MEDIUM'
        },
        'Crowdstrike Agent Coverage': {
            'synonyms': ['crowdstrike', 'cs_agent', 'falcon', 'falcon_sensor', 'edr_agent', 'endpoint_agent', 'security_agent', 'crowdstrike_falcon'],
            'partial_matches': ['crowdstrike', 'falcon', 'cs_agent', 'edr', 'agent', 'sensor'],
            'description': 'Measure Crowdstrike Falcon agent deployment coverage across all endpoints',
            'visibility_query': 'What percentage of endpoints have active Crowdstrike Falcon agents for EDR coverage?',
            'business_impact': 'Critical for endpoint detection and response capabilities and threat hunting',
            'threat_context': 'Endpoints without EDR agents lack behavioral monitoring and advanced threat detection capabilities',
            'priority': 'CRITICAL',
            'complexity': 'LOW'
        },
        'Log Ingest Volume': {
            'synonyms': ['log_volume', 'event_volume', 'endpoint_logs', 'system_logs', 'security_logs', 'audit_logs', 'logging_volume', 'event_count'],
            'partial_matches': ['log', 'event', 'volume', 'audit', 'security', 'system', 'logging', 'endpoint'],
            'description': 'Measure endpoint log ingestion coverage for security monitoring completeness',
            'visibility_query': 'What percentage of endpoints are generating and forwarding log data for security analysis?',
            'business_impact': 'Fundamental for comprehensive endpoint security monitoring and incident detection',
            'threat_context': 'Endpoints without logging create critical security monitoring blind spots',
            'priority': 'HIGH',
            'complexity': 'LOW'
        }
    },
    'Identity_Authentication': {
        'Domain Coverage': {
            'synonyms': ['domain', 'ad_domain', 'authentication_domain', 'login_domain', 'user_domain', 'identity_domain', 'active_directory', 'auth_domain'],
            'partial_matches': ['domain', 'ad', 'auth', 'login', 'identity', 'user', 'directory'],
            'description': 'Measure authentication domain coverage with Internal/External/Controls classification',
            'visibility_query': 'What percentage of authentication events include proper domain classification for risk assessment?',
            'business_impact': 'Critical for identity security, access management, and authentication risk analysis',
            'threat_context': 'Domain classification enables detection of external vs internal authentication threats and anomalies',
            'priority': 'HIGH',
            'complexity': 'MEDIUM'
        }
    },
    'Application': {
        'URL/FQDN coverage': {
            'synonyms': ['url', 'fqdn', 'domain', 'hostname', 'web_address', 'application_url', 'app_url', 'service_url', 'api_endpoint'],
            'partial_matches': ['url', 'domain', 'host', 'fqdn', 'web', 'app', 'service', 'api'],
            'description': 'Measure application URL and domain coverage for web application security monitoring',
            'visibility_query': 'What percentage of application traffic includes URL/domain data for security analysis?',
            'business_impact': 'Essential for web application security monitoring and API security',
            'threat_context': 'Application URLs are key indicators of web-based attacks, API abuse, and malicious activity',
            'priority': 'HIGH',
            'complexity': 'LOW'
        },
        'Agent Coverage': {
            'synonyms': ['agent', 'application_agent', 'app_agent', 'monitoring_agent', 'apm_agent', 'application_monitoring'],
            'partial_matches': ['agent', 'monitor', 'apm', 'app', 'application'],
            'description': 'Measure application monitoring agent coverage for performance and security visibility',
            'visibility_query': 'What percentage of applications have monitoring agents for comprehensive visibility?',
            'business_impact': 'Critical for application performance monitoring, security analysis, and operational intelligence',
            'threat_context': 'Applications without monitoring agents lack visibility into security events and performance anomalies',
            'priority': 'MEDIUM',
            'complexity': 'MEDIUM'
        }
    },
    'Cloud': {
        'VPC coverage': {
            'synonyms': ['vpc', 'virtual_private_cloud', 'cloud_network', 'aws_vpc', 'azure_vnet', 'gcp_vpc', 'cloud_networking'],
            'partial_matches': ['vpc', 'virtual', 'cloud', 'vnet', 'network', 'aws', 'azure', 'gcp'],
            'description': 'Measure cloud VPC visibility and coverage across all cloud environments',
            'visibility_query': 'What percentage of cloud resources are properly VPC-tagged for network security monitoring?',
            'business_impact': 'Essential for multi-cloud security, network visibility, and compliance monitoring',
            'threat_context': 'VPC visibility is critical for detecting cloud-based network attacks and misconfigurations',
            'priority': 'HIGH',
            'complexity': 'MEDIUM'
        }
    }
}