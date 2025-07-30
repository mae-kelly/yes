"""
AO1 Keywords: Complete Classification System for Security & IT Asset Management
EXACT MATCHES ONLY - No loose associations

Requirements Coverage:
REQ-1: Global View - Asset identifiers for counting unique logging assets vs CMDB
REQ-2: Infrastructure Type - Exact deployment model classification  
REQ-3: Regional/Country View - Geographic location classification
REQ-4: Business/Application View - Organizational classification
REQ-5: System Classification - Server function and OS type classification
REQ-6: Security Control Coverage - Agent presence for coverage measurement
REQ-7: Logging Compliance - GSO (Chronicle) and Splunk platform compliance
REQ-8: Domain Visibility - Asset visibility by hostname and domain
"""

# REQ-1: GLOBAL VIEW - Asset identifiers for counting unique logging assets vs CMDB
REQ1_GLOBAL_VIEW_KEYWORDS = {
    # Hostname identifiers
    'hostname', 'host_name', 'computer_name', 'machine_name', 'device_name', 'system_name', 
    'server_name', 'node_name', 'endpoint_name', 'asset_name', 'workstation_name', 'client_name', 'pc_name',
    
    # Asset IDs
    'asset_id', 'sys_id', 'device_id', 'machine_id', 'computer_id', 'endpoint_id', 'node_id', 
    'host_id', 'system_id', 'unique_id', 'ci_name', 'cmdb_ci',
    
    # Hardware identifiers
    'serial_number', 'serial_no', 'sn', 'uuid', 'guid', 'hardware_id', 'hw_id',
    
    # Network identifiers
    'fqdn', 'fully_qualified_domain_name', 'dns_name', 'canonical_name', 'cname',
    'ip_address', 'ip_addr', 'ipv4', 'ipv6', 'inet_addr', 'network_address', 'host_address',
    'mac_address', 'physical_address', 'ethernet_address',
    
    # Security agent identifiers
    'aid', 'agent_id', 'sensor_id', 'cid', 'detection_id', 'incident_id', 'falcon_host_link',
    
    # Logging identifiers
    'host', 'source', 'log_source', 'data_source', 'event_source',
    
    # Status tracking
    'operational_status', 'discovery_source', 'last_seen', 'first_seen',
    'collected_timestamp', 'event_timestamp', 'ingested_timestamp'
}

# REQ-2: INFRASTRUCTURE TYPE - Exact deployment model classification
REQ2_INFRASTRUCTURE_TYPE_KEYWORDS = {
    # On-Premises EXACT indicators
    'on_premises', 'on_prem', 'onpremises', 'onprem', 'datacenter', 'data_center', 
    'physical_server', 'bare_metal', 'facility', 'rack', 'cabinet', 'server_room',
    
    # Cloud EXACT indicators  
    'cloud', 'public_cloud', 'private_cloud', 'hybrid_cloud', 'multi_cloud',
    
    # AWS
    'aws', 'amazon_web_services', 'ec2', 's3', 'lambda', 'rds', 'vpc', 'ecs', 'eks',
    
    # Azure
    'azure', 'microsoft_azure', 'azure_vm', 'azure_sql', 'azure_storage', 'azure_ad', 'entra', 'entra_id',
    
    # Google Cloud
    'gcp', 'google_cloud', 'google_cloud_platform', 'gce', 'compute_engine', 'gcs', 
    'cloud_storage', 'bigquery', 'cloud_functions', 'gke',
    
    # Virtualization and containers
    'virtual_machine', 'vm', 'instance', 'cloud_instance', 'container', 'docker', 
    'kubernetes', 'k8s', 'pod', 'namespace', 'cluster',
    'serverless', 'function', 'faas', 'lambda_function',
    
    # SaaS EXACT indicators
    'saas', 'software_as_a_service', 'office365', 'o365', 'microsoft_365', 'm365', 
    'teams', 'outlook', 'exchange', 'sharepoint', 'onedrive',
    'salesforce', 'workday', 'servicenow', 'okta', 'zoom', 'slack', 'google_workspace', 'gsuite',
    'application_type', 'hosted_application', 'cloud_software',
    
    # API EXACT indicators
    'api', 'rest_api', 'soap_api', 'graphql', 'api_gateway', 'microservice', 'webhook', 
    'integration', 'service_mesh',
    
    # F5 BIG-IP specific
    'f5', 'bigip', 'big_ip', 'ltm', 'asm', 'afm', 'gtm', 'virtual_server', 'pool', 
    'pool_member', 'node', 'irule'
}

# REQ-3: REGIONAL/COUNTRY VIEW - Geographic location classification
REQ3_REGIONAL_COUNTRY_KEYWORDS = {
    # Global regions EXACT
    'global_region', 'region', 'geo_region', 'geographic_region', 'world_region',
    'americas', 'north_america', 'south_america', 'emea', 'europe_middle_east_africa', 
    'europe', 'middle_east', 'africa', 'asia_pacific', 'apac', 'asia', 'pacific', 'oceania',
    
    # Countries EXACT
    'country', 'country_code', 'iso_country', 'iso_code',
    'united_states', 'usa', 'us', 'canada', 'ca', 'united_kingdom', 'uk', 'britain', 
    'great_britain', 'gb', 'germany', 'de', 'france', 'fr', 'japan', 'jp', 'china', 'cn', 
    'india', 'in', 'australia', 'au', 'brazil', 'br', 'mexico', 'mx', 'russia', 'ru', 
    'italy', 'it', 'spain', 'es', 'netherlands', 'nl',
    
    # Data centers EXACT
    'data_center', 'datacenter', 'dc', 'facility', 'site', 'location', 'building', 
    'campus', 'office', 'branch', 'headquarters', 'hq',
    
    # Cloud regions EXACT
    'cloud_region', 'aws_region', 'awsregion', 'azure_region', 'gcp_region', 
    'availability_zone', 'az', 'zone', 'edge_location', 'pop',
    'us_east_1', 'us_west_1', 'us_west_2', 'eu_west_1', 'eu_central_1', 
    'ap_southeast_1', 'ap_northeast_1',
    
    # Address components EXACT
    'address', 'street_address', 'city', 'state', 'province', 'postal_code', 'zip_code', 'zip',
    'latitude', 'longitude', 'coordinates', 'gps_coordinates',
    
    # IP geolocation EXACT
    'sourceipaddress', 'source_ip_address', 'client_ip', 'remote_ip', 'external_ip', 'public_ip',
    
    # Timezone EXACT
    'timezone', 'time_zone', 'tz', 'utc_offset', 'gmt_offset'
}

# REQ-4: BUSINESS/APPLICATION VIEW - Organizational classification
REQ4_BUSINESS_APPLICATION_KEYWORDS = {
    # Business Unit EXACT
    'business_unit', 'bu', 'org_unit', 'organizational_unit', 'ou', 'division', 'department', 
    'dept', 'organization', 'org', 'company', 'corporation', 'enterprise', 'subsidiary', 'entity',
    'cost_center', 'profit_center', 'budget_center', 'business_service', 'support_group',
    
    # CIO Organization EXACT (IT leadership only)
    'cio', 'chief_information_officer', 'it_organization', 'information_technology', 
    'technology_organization', 'information_systems', 'it_department', 'technology_department',
    'engineering', 'software_engineering', 'infrastructure', 'it_infrastructure', 'operations', 
    'it_operations', 'security', 'information_security', 'cybersecurity', 'it_security',
    'architecture', 'enterprise_architecture', 'solution_architecture', 'technical_architecture',
    
    # APM (Application Performance Management) EXACT
    'apm', 'application_performance_management', 'application', 'app', 'service', 'platform', 
    'workload', 'solution', 'product', 'system',
    'application_name', 'app_name', 'service_name', 'platform_name', 'solution_name', 
    'product_name', 'system_name',
    
    # Application Class EXACT
    'application_class', 'app_class', 'application_type', 'app_type', 'application_category', 
    'service_class', 'service_type',
    'tier', 'application_tier', 'web_tier', 'app_tier', 'data_tier', 'presentation_tier', 
    'business_tier', 'database_tier',
    'layer', 'application_layer', 'component', 'application_component', 'module', 'application_module',
    
    # Business functions EXACT
    'finance', 'accounting', 'human_resources', 'hr', 'sales', 'marketing', 'operations', 
    'business_operations', 'manufacturing', 'production', 'legal', 'compliance', 'risk_management', 
    'audit', 'internal_audit', 'procurement', 'supply_chain', 'logistics', 'customer_service', 'support'
}

# REQ-5: SYSTEM CLASSIFICATION - Server function and OS type classification
REQ5_SYSTEM_CLASSIFICATION_KEYWORDS = {
    # Web Server EXACT
    'web_server', 'http_server', 'https_server', 'apache', 'nginx', 'iis', 'internet_information_services', 
    'tomcat', 'jetty', 'lighttpd', 'caddy', 'haproxy', 'web_application_server', 'application_server', 
    'webapp', 'web_service',
    
    # Windows Server EXACT
    'windows_server', 'windows', 'microsoft_windows', 'win_server', 'windows_2019', 'windows_2022', 
    'windows_2016', 'windows_2012', 'windows_2008', 'domain_controller', 'dc', 'active_directory', 
    'ad', 'exchange_server', 'exchange', 'sql_server_windows', 'iis_server', 'windows_datacenter', 
    'windows_standard', 'windows_enterprise', 'server_core', 'nano_server',
    
    # Linux Server EXACT
    'linux_server', 'linux', 'gnu_linux', 'redhat', 'red_hat', 'rhel', 'red_hat_enterprise_linux', 
    'centos', 'ubuntu', 'debian', 'suse', 'opensuse', 'sles', 'amazon_linux', 'oracle_linux', 
    'rocky_linux', 'alma_linux', 'fedora', 'mint', 'arch_linux', 'gentoo', 'slackware', 'alpine',
    
    # *Nix (AIX, Solaris, etc) EXACT
    'unix', 'aix', 'ibm_aix', 'solaris', 'oracle_solaris', 'sun_solaris', 'sunos', 'hp_ux', 
    'hpux', 'freebsd', 'openbsd', 'netbsd', 'dragonfly_bsd', 'digital_unix', 'tru64', 'osf1', 
    'irix', 'sgi_irix', 'qnx', 'unicos', 'cray_unicos',
    
    # Mainframe EXACT (Splunk only)
    'mainframe', 'zos', 'z_os', 'mvs', 'vse', 'tpf', 'cics', 'ims', 'db2_mainframe', 'cobol', 
    'jcl', 'rexx', 'pli', 'assembler', 'sysplex', 'lpar', 'zvm', 'vtam', 'racf', 'top_secret', 'acf2',
    
    # Database EXACT
    'database_server', 'database', 'db_server', 'sql_server', 'microsoft_sql_server', 'mssql', 
    'oracle_database', 'oracle_db', 'mysql', 'mariadb', 'postgresql', 'postgres', 'mongodb', 
    'cassandra', 'redis', 'elasticsearch', 'influxdb', 'couchdb', 'dynamodb', 'cosmos_db',
    'db2', 'sybase', 'informix', 'teradata', 'vertica', 'snowflake', 'bigquery_db',
    
    # Network Appliance EXACT (FW, NDR, switch, router, etc)
    'network_appliance', 'firewall', 'fw', 'router', 'switch', 'load_balancer', 'lb', 
    'proxy_server', 'proxy_appliance', 'ndr', 'network_detection_response', 'ids', 
    'intrusion_detection_system', 'ips', 'intrusion_prevention_system', 'utm', 
    'unified_threat_management', 'ngfw', 'next_generation_firewall', 'waf', 'web_application_firewall',
    'wireless_controller', 'access_point', 'ap', 'network_switch', 'core_switch', 
    'distribution_switch', 'access_switch', 'border_router', 'core_router', 'edge_router', 
    'gateway', 'network_gateway', 'vpn_gateway', 'nat_gateway'
}

# REQ-6: SECURITY CONTROL COVERAGE - Agent presence for coverage measurement
REQ6_SECURITY_CONTROL_COVERAGE_KEYWORDS = {
    # EDR EXACT (Axonius or console stats)
    'edr', 'endpoint_detection_response', 'endpoint_detection_and_response', 'crowdstrike', 'falcon', 
    'crowdstrike_falcon', 'aid', 'agent_id', 'sensor_id', 'cid', 'customer_id', 'detection_id', 
    'incident_id', 'falcon_host_link', 'agent_version', 'sensor_version', 'prevention_policy', 
    'device_policy', 'endpoint_security', 'behavioral_detection', 'threat_hunting', 
    'real_time_response', 'rtr', 'overwatch', 'falcon_insight', 'falcon_prevent', 'falcon_discover',
    
    # Tanium EXACT (Axonius or console stats)
    'tanium', 'tanium_client', 'tanium_agent', 'computer_id', 'endpoint_id', 'tanium_server', 
    'sensor_name', 'sensor_hash', 'package_name', 'action_name', 'question', 'tanium_question', 
    'saved_question', 'scheduled_action', 'comply', 'detect', 'respond', 'threat_response', 
    'patch_deployment', 'software_deployment', 'endpoint_management', 'vulnerability_scanning', 
    'compliance_monitoring', 'asset_discovery', 'patch_management', 'configuration_management',
    
    # DLP Agent EXACT (Axonius or console stats)
    'dlp', 'data_loss_prevention', 'dlp_agent', 'endpoint_dlp', 'network_dlp', 'content_inspection', 
    'data_classification', 'policy_violation', 'sensitive_data', 'data_exfiltration', 'content_analysis', 
    'pattern_matching', 'fingerprinting', 'exact_data_match', 'edm', 'document_fingerprint', 
    'data_protection', 'information_protection',
    
    # Axonius coverage stats EXACT
    'axonius', 'device_type', 'data_source', 'adapter', 'connection', 'last_seen', 'first_seen', 
    'installed_software', 'security_software', 'running_processes', 'network_interfaces', 'open_ports', 
    'services', 'vulnerabilities', 'patches', 'compliance_status', 'risk_score', 'agent_coverage', 
    'endpoint_protection', 'security_control_coverage',
    
    # Console stats indicators EXACT
    'console_stats', 'agent_status', 'deployment_status', 'management_console', 'security_console', 
    'endpoint_console', 'agent_health', 'connectivity_status', 'last_checkin', 'heartbeat', 
    'communication_status', 'online_status'
}

# REQ-7: LOGGING COMPLIANCE - GSO (Chronicle) and Splunk platform compliance
REQ7_LOGGING_COMPLIANCE_KEYWORDS = {
    # Chronicle (GSO) EXACT
    'chronicle', 'google_chronicle', 'google_security_operations', 'gso', 'security_operations_suite',
    'udm', 'unified_data_model', 'detection_engine', 'yara_l', 'yaral', 'chronicle_detection',
    'ingestion_time', 'collection_timestamp', 'event_timestamp', 'parsed_timestamp', 'normalized_timestamp',
    'metadata.collected_timestamp', 'metadata.event_timestamp', 'metadata.ingested_timestamp',
    'security_result', 'detection_result', 'rule_detection', 'chronicle_rule', 'detection_rule',
    'log_type', 'parser', 'chronicle_parser', 'data_ingestion', 'log_ingestion', 'ingestion_api',
    
    # Splunk EXACT
    'splunk', 'splunk_enterprise', 'splunk_cloud', 'sourcetype', 'index', 'source', 'host', '_time',
    'splunk_server', 'indexer', 'search_head', 'forwarder', 'universal_forwarder', 'heavy_forwarder',
    'deployment_server', 'license_master', 'cluster_master', 'search_head_cluster',
    'splunk_app', 'splunk_addon', 'technology_addon', 'ta', 'splunk_es', 'enterprise_security',
    'splunk_itsi', 'it_service_intelligence', 'splunk_phantom', 'phantom', 'soar',
    
    # Logging compliance measurement EXACT
    'log_completeness', 'data_completeness', 'ingestion_latency', 'parsing_success', 'parse_rate',
    'field_extraction', 'data_normalization', 'normalization_success', 'enrichment_success',
    'data_retention', 'retention_policy', 'log_retention', 'storage_policy', 'archival_policy',
    'visibility_statement', 'coverage_statement', 'logging_platform', 'platform_compliance',
    'compliance_percentage', 'coverage_percentage', 'ingestion_rate', 'throughput', 'data_volume'
}

# REQ-8: DOMAIN VISIBILITY - Asset visibility by hostname and domain
REQ8_DOMAIN_VISIBILITY_KEYWORDS = {
    # Hostname EXACT
    'hostname', 'host_name', 'computer_name', 'machine_name', 'device_name', 'server_name', 
    'node_name', 'system_name', 'endpoint_name', 'asset_name', 'workstation_name', 'client_name', 'pc_name',
    
    # Domain EXACT
    'domain', 'domain_name', 'fqdn', 'fully_qualified_domain_name', 'dns_name', 'canonical_name', 
    'cname', 'subdomain', 'parent_domain', 'root_domain', 'apex_domain', 'top_level_domain', 'tld', 
    'second_level_domain', 'sld',
    
    # DNS records EXACT
    'a_record', 'aaaa_record', 'cname_record', 'mx_record', 'ns_record', 'ptr_record', 'soa_record', 
    'srv_record', 'txt_record', 'dns_query', 'dns_response', 'dns_request', 'dns_reply', 'query_name', 
    'qname', 'query_type', 'qtype', 'response_code', 'rcode', 'dns_lookup', 'name_resolution', 
    'domain_resolution', 'reverse_dns', 'forward_dns', 'dns_resolution',
    
    # Domain classification EXACT
    'internal_domain', 'external_domain', 'corporate_domain', 'company_domain', 'business_domain',
    'public_domain', 'private_domain', 'internet_domain', 'intranet_domain', 'local_domain',
    'registered_domain', 'authoritative_domain', 'delegated_domain',
    
    # DNS servers and infrastructure EXACT
    'dns_server', 'nameserver', 'name_server', 'authoritative_server', 'recursive_server', 'dns_resolver',
    'root_server', 'tld_server', 'forwarder', 'dns_forwarder', 'caching_server', 'dns_cache',
    
    # Domain resolution status EXACT
    'nxdomain', 'servfail', 'refused', 'noerror', 'dns_timeout', 'dns_failure', 'resolution_failure',
    'domain_reachability', 'connectivity_test', 'domain_status', 'dns_status',
    
    # Domain membership and authentication EXACT
    'domain_controller', 'dc', 'active_directory', 'ad', 'domain_membership', 'domain_joined',
    'workgroup', 'kerberos_realm', 'ldap_domain', 'distinguished_name', 'dn', 'organizational_unit', 'ou',
    'forest', 'domain_tree', 'trust_relationship', 'domain_trust', 'forest_trust',
    
    # Domain security EXACT
    'domain_reputation', 'malicious_domain', 'suspicious_domain', 'blacklisted_domain', 'whitelisted_domain',
    'blocked_domain', 'allowed_domain', 'threat_intelligence', 'domain_intelligence', 'ioc_domain',
    'dga', 'domain_generation_algorithm', 'typosquatting', 'homograph_attack', 'punycode',
    
    # Domain registration EXACT
    'domain_registrar', 'registrar', 'whois_data', 'domain_age', 'creation_date', 'expiration_date',
    'registration_date', 'domain_owner', 'registrant', 'admin_contact', 'technical_contact'
}

# Export all keyword sets for easy import
__all__ = [
    'REQ1_GLOBAL_VIEW_KEYWORDS',
    'REQ2_INFRASTRUCTURE_TYPE_KEYWORDS', 
    'REQ3_REGIONAL_COUNTRY_KEYWORDS',
    'REQ4_BUSINESS_APPLICATION_KEYWORDS',
    'REQ5_SYSTEM_CLASSIFICATION_KEYWORDS',
    'REQ6_SECURITY_CONTROL_COVERAGE_KEYWORDS',
    'REQ7_LOGGING_COMPLIANCE_KEYWORDS',
    'REQ8_DOMAIN_VISIBILITY_KEYWORDS'
]

# Utility functions for keyword validation and lookup
def get_all_keywords():
    """Return all keywords from all requirements as a single set."""
    all_keywords = set()
    for keyword_set in [
        REQ1_GLOBAL_VIEW_KEYWORDS,
        REQ2_INFRASTRUCTURE_TYPE_KEYWORDS,
        REQ3_REGIONAL_COUNTRY_KEYWORDS,
        REQ4_BUSINESS_APPLICATION_KEYWORDS,
        REQ5_SYSTEM_CLASSIFICATION_KEYWORDS,
        REQ6_SECURITY_CONTROL_COVERAGE_KEYWORDS,
        REQ7_LOGGING_COMPLIANCE_KEYWORDS,
        REQ8_DOMAIN_VISIBILITY_KEYWORDS
    ]:
        all_keywords.update(keyword_set)
    return all_keywords

def find_keyword_requirement(keyword):
    """Find which requirement(s) contain a specific keyword."""
    requirements = []
    keyword_lower = keyword.lower()
    
    if keyword_lower in REQ1_GLOBAL_VIEW_KEYWORDS:
        requirements.append('REQ-1: Global View')
    if keyword_lower in REQ2_INFRASTRUCTURE_TYPE_KEYWORDS:
        requirements.append('REQ-2: Infrastructure Type')
    if keyword_lower in REQ3_REGIONAL_COUNTRY_KEYWORDS:
        requirements.append('REQ-3: Regional/Country View')
    if keyword_lower in REQ4_BUSINESS_APPLICATION_KEYWORDS:
        requirements.append('REQ-4: Business/Application View')
    if keyword_lower in REQ5_SYSTEM_CLASSIFICATION_KEYWORDS:
        requirements.append('REQ-5: System Classification')
    if keyword_lower in REQ6_SECURITY_CONTROL_COVERAGE_KEYWORDS:
        requirements.append('REQ-6: Security Control Coverage')
    if keyword_lower in REQ7_LOGGING_COMPLIANCE_KEYWORDS:
        requirements.append('REQ-7: Logging Compliance')
    if keyword_lower in REQ8_DOMAIN_VISIBILITY_KEYWORDS:
        requirements.append('REQ-8: Domain Visibility')
    
    return requirements

def get_requirement_keywords(req_number):
    """Get keywords for a specific requirement number (1-8)."""
    req_map = {
        1: REQ1_GLOBAL_VIEW_KEYWORDS,
        2: REQ2_INFRASTRUCTURE_TYPE_KEYWORDS,
        3: REQ3_REGIONAL_COUNTRY_KEYWORDS,
        4: REQ4_BUSINESS_APPLICATION_KEYWORDS,
        5: REQ5_SYSTEM_CLASSIFICATION_KEYWORDS,
        6: REQ6_SECURITY_CONTROL_COVERAGE_KEYWORDS,
        7: REQ7_LOGGING_COMPLIANCE_KEYWORDS,
        8: REQ8_DOMAIN_VISIBILITY_KEYWORDS
    }
    return req_map.get(req_number, set())

def validate_keyword(keyword, requirement=None):
    """Validate if a keyword exists in the system, optionally for a specific requirement."""
    keyword_lower = keyword.lower()
    
    if requirement is None:
        return keyword_lower in get_all_keywords()
    else:
        req_keywords = get_requirement_keywords(requirement)
        return keyword_lower in req_keywords