BASE_ABBREVIATIONS = {
    'auth': 'authentication', 'authz': 'authorization', 'authn': 'authentication',
    'sso': 'single_sign_on', 'mfa': 'multi_factor_authentication', '2fa': 'two_factor_authentication',
    'saml': 'security_assertion_markup_language', 'oauth': 'open_authorization',
    'oidc': 'openid_connect', 'jwt': 'json_web_token', 'ldap': 'lightweight_directory_access_protocol',
    'ad': 'active_directory', 'pam': 'privileged_access_management',
    'fw': 'firewall', 'gw': 'gateway', 'lb': 'load_balancer', 'nat': 'network_address_translation',
    'dns': 'domain_name_system', 'dhcp': 'dynamic_host_configuration_protocol',
    'tcp': 'transmission_control_protocol', 'udp': 'user_datagram_protocol',
    'icmp': 'internet_control_message_protocol', 'http': 'hypertext_transfer_protocol',
    'https': 'http_secure', 'ftp': 'file_transfer_protocol', 'ssh': 'secure_shell',
    'ssl': 'secure_sockets_layer', 'tls': 'transport_layer_security',
    'vpn': 'virtual_private_network', 'wan': 'wide_area_network', 'lan': 'local_area_network',
    'vlan': 'virtual_local_area_network', 'vpc': 'virtual_private_cloud',
    'ids': 'intrusion_detection_system', 'ips': 'intrusion_prevention_system',
    'waf': 'web_application_firewall', 'edr': 'endpoint_detection_response',
    'siem': 'security_information_event_management', 'soar': 'security_orchestration_automated_response',
    'dlp': 'data_loss_prevention', 'av': 'antivirus', 'apm': 'application_performance_monitoring',
    'noc': 'network_operations_center', 'soc': 'security_operations_center',
    'db': 'database', 'dbms': 'database_management_system', 'sql': 'structured_query_language',
    'etl': 'extract_transform_load', 'oltp': 'online_transaction_processing',
    'olap': 'online_analytical_processing', 'crud': 'create_read_update_delete',
    'aws': 'amazon_web_services', 'gcp': 'google_cloud_platform', 'k8s': 'kubernetes',
    'vm': 'virtual_machine', 'os': 'operating_system', 'api': 'application_programming_interface',
    'sdk': 'software_development_kit', 'cli': 'command_line_interface',
    'gui': 'graphical_user_interface', 'ui': 'user_interface', 'ux': 'user_experience',
    'cicd': 'continuous_integration_continuous_deployment', 'devops': 'development_operations',
    'iac': 'infrastructure_as_code', 'sast': 'static_application_security_testing',
    'dast': 'dynamic_application_security_testing', 'iast': 'interactive_application_security_testing',
    'pci': 'payment_card_industry', 'sox': 'sarbanes_oxley', 'gdpr': 'general_data_protection_regulation',
    'hipaa': 'health_insurance_portability_accountability_act', 'nist': 'national_institute_standards_technology',
    'iso': 'international_organization_standardization', 'cis': 'center_internet_security',
    'json': 'javascript_object_notation', 'xml': 'extensible_markup_language',
    'yaml': 'yaml_aint_markup_language', 'csv': 'comma_separated_values',
    'html': 'hypertext_markup_language', 'css': 'cascading_style_sheets',
    'rest': 'representational_state_transfer', 'soap': 'simple_object_access_protocol',
    'src': 'source', 'dst': 'destination', 'dest': 'destination', 'orig': 'origin',
    'usr': 'user', 'usr_id': 'user_id', 'uid': 'user_id', 'gid': 'group_id',
    'pwd': 'password', 'passwd': 'password', 'cred': 'credential', 'cert': 'certificate',
    'conn': 'connection', 'sess': 'session', 'req': 'request', 'resp': 'response',
    'msg': 'message', 'sig': 'signature', 'proc': 'process', 'svc': 'service',
    'sys': 'system', 'net': 'network', 'addr': 'address', 'proto': 'protocol',
    'url': 'uniform_resource_locator', 'uri': 'uniform_resource_identifier',
    'fqdn': 'fully_qualified_domain_name', 'ip': 'internet_protocol',
    'mac': 'media_access_control', 'uuid': 'universally_unique_identifier',
    'guid': 'globally_unique_identifier', 'md5': 'message_digest_5',
    'sha': 'secure_hash_algorithm', 'aes': 'advanced_encryption_standard',
    'rsa': 'rivest_shamir_adleman', 'pki': 'public_key_infrastructure',
    'cmdb': 'configuration_management_database', 'ipam': 'ip_address_management'
}

ABBREVIATION_ENGINE = {}
for abbrev, full in BASE_ABBREVIATIONS.items():
    ABBREVIATION_ENGINE[abbrev] = full
    ABBREVIATION_ENGINE[abbrev.upper()] = full
    ABBREVIATION_ENGINE[abbrev.capitalize()] = full
    
    if '_' in full:
        parts = full.split('_')
        if len(parts) == 2:
            ABBREVIATION_ENGINE[abbrev + '_' + parts[1]] = full
            ABBREVIATION_ENGINE[parts[0] + '_' + abbrev] = full