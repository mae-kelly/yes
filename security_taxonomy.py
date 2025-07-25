SECURITY_TAXONOMY = {
    'network': {
        'layer2_datalink': ['mac', 'ethernet', 'switch', 'vlan', 'trunk', 'spanning_tree', 'arp', 'frame', 'bridge'],
        'layer3_network': ['ip', 'routing', 'subnet', 'gateway', 'router', 'ospf', 'bgp', 'rip', 'packet', 'icmp'],
        'layer4_transport': ['tcp', 'udp', 'port', 'socket', 'connection', 'session', 'flow', 'segment'],
        'layer7_application': ['http', 'https', 'ftp', 'smtp', 'dns', 'dhcp', 'snmp', 'ssh', 'telnet', 'api'],
        'topology': ['source', 'destination', 'origin', 'target', 'from', 'to', 'via', 'through', 'path', 'route'],
        'metrics': ['bandwidth', 'throughput', 'latency', 'jitter', 'packet_loss', 'utilization', 'capacity'],
        'protocols': ['icmp', 'igmp', 'gre', 'ipsec', 'vpn', 'mpls', 'vxlan', 'geneve', 'nvgre'],
        'wireless': ['wifi', 'wlan', '802.11', 'ssid', 'bssid', 'wpa', 'wep', 'radius', 'bluetooth'],
        'monitoring': ['snmp', 'netflow', 'sflow', 'ipfix', 'packet_capture', 'mirroring', 'span']
    },
    'security': {
        'threats': ['malware', 'virus', 'trojan', 'worm', 'ransomware', 'spyware', 'adware', 'rootkit', 'botnet', 'apt'],
        'attacks': ['dos', 'ddos', 'mitm', 'phishing', 'spoofing', 'hijacking', 'injection', 'overflow', 'poisoning'],
        'vulnerabilities': ['cve', 'exploit', 'zero_day', 'buffer_overflow', 'sql_injection', 'xss', 'csrf', 'lfi', 'rfi'],
        'controls': ['firewall', 'ids', 'ips', 'waf', 'proxy', 'antivirus', 'edr', 'dlp', 'sandbox', 'honeypot'],
        'cryptography': ['encryption', 'decryption', 'hash', 'digest', 'signature', 'certificate', 'pki', 'ssl', 'tls'],
        'analysis': ['forensics', 'incident', 'investigation', 'attribution', 'indicators', 'ioc', 'ttp', 'mitre'],
        'intelligence': ['threat_intel', 'feeds', 'reputation', 'blacklist', 'whitelist', 'indicators', 'yara', 'sigma'],
        'frameworks': ['nist', 'iso27001', 'cis', 'owasp', 'sans', 'mitre_attack', 'kill_chain'],
        'governance': ['policy', 'compliance', 'audit', 'risk', 'assessment', 'framework', 'standard', 'regulation']
    },
    'identity': {
        'authentication': ['login', 'logon', 'signin', 'sso', 'mfa', '2fa', 'biometric', 'token', 'password', 'pin'],
        'authorization': ['permission', 'privilege', 'access', 'role', 'group', 'policy', 'acl', 'rbac', 'abac'],
        'provisioning': ['create', 'modify', 'delete', 'disable', 'enable', 'suspend', 'unlock', 'reset', 'lifecycle'],
        'federation': ['saml', 'oauth', 'oidc', 'jwt', 'kerberos', 'ldap', 'ad', 'radius', 'tacacs'],
        'lifecycle': ['joiner', 'mover', 'leaver', 'onboard', 'offboard', 'transfer', 'promote', 'terminate'],
        'attributes': ['username', 'email', 'domain', 'group', 'role', 'department', 'title', 'manager'],
        'directory': ['active_directory', 'ldap', 'azure_ad', 'okta', 'ping', 'forgerock', 'sailpoint'],
        'privileged': ['pam', 'privileged_access', 'admin', 'root', 'sudo', 'elevation', 'just_in_time']
    },
    'data': {
        'classification': ['public', 'internal', 'confidential', 'restricted', 'secret', 'top_secret', 'pii', 'phi'],
        'handling': ['create', 'read', 'update', 'delete', 'copy', 'move', 'share', 'print', 'download', 'export'],
        'protection': ['encryption', 'masking', 'tokenization', 'anonymization', 'pseudonymization', 'redaction'],
        'formats': ['json', 'xml', 'csv', 'pdf', 'doc', 'xls', 'txt', 'binary', 'compressed', 'archive'],
        'storage': ['database', 'file', 'object', 'block', 'cloud', 'on_premise', 'hybrid', 'backup', 'archive'],
        'governance': ['retention', 'disposal', 'archival', 'compliance', 'audit', 'lineage', 'catalog', 'quality'],
        'privacy': ['gdpr', 'ccpa', 'hipaa', 'pci_dss', 'sox', 'ferpa', 'consent', 'right_to_be_forgotten'],
        'lifecycle': ['creation', 'storage', 'usage', 'sharing', 'archival', 'destruction', 'retention']
    },
    'operations': {
        'monitoring': ['log', 'event', 'alert', 'alarm', 'notification', 'dashboard', 'metric', 'kpi', 'sla'],
        'analysis': ['correlation', 'aggregation', 'enrichment', 'normalization', 'parsing', 'filtering'],
        'response': ['incident', 'investigation', 'containment', 'eradication', 'recovery', 'lessons_learned'],
        'automation': ['orchestration', 'playbook', 'workflow', 'script', 'api', 'webhook', 'trigger', 'soar'],
        'maintenance': ['patch', 'update', 'upgrade', 'configuration', 'deployment', 'rollback', 'backup'],
        'compliance': ['audit', 'assessment', 'scan', 'validation', 'certification', 'attestation', 'evidence'],
        'performance': ['capacity', 'utilization', 'throughput', 'response_time', 'availability', 'reliability'],
        'integration': ['api', 'webhook', 'etl', 'connector', 'adapter', 'middleware', 'message_queue']
    },
    'infrastructure': {
        'compute': ['server', 'vm', 'container', 'pod', 'node', 'cluster', 'hypervisor', 'docker', 'kubernetes'],
        'storage': ['disk', 'volume', 'partition', 'filesystem', 'raid', 'san', 'nas', 'object_store'],
        'network': ['switch', 'router', 'firewall', 'load_balancer', 'proxy', 'gateway', 'bridge', 'hub'],
        'cloud': ['aws', 'azure', 'gcp', 'hybrid', 'multi_cloud', 'saas', 'paas', 'iaas', 'serverless'],
        'platforms': ['windows', 'linux', 'unix', 'macos', 'android', 'ios', 'embedded', 'iot'],
        'services': ['web', 'database', 'application', 'middleware', 'message_queue', 'cache', 'cdn'],
        'orchestration': ['kubernetes', 'docker_swarm', 'nomad', 'mesos', 'openshift', 'rancher'],
        'automation': ['ansible', 'puppet', 'chef', 'terraform', 'cloudformation', 'arm', 'pulumi']
    },
    'application': {
        'architecture': ['monolith', 'microservices', 'soa', 'event_driven', 'serverless', 'mesh', 'layered'],
        'development': ['devops', 'cicd', 'agile', 'waterfall', 'scrum', 'kanban', 'lean', 'safe'],
        'security': ['sast', 'dast', 'iast', 'rasp', 'dependency_scanning', 'container_scanning'],
        'testing': ['unit', 'integration', 'system', 'acceptance', 'performance', 'security', 'chaos'],
        'deployment': ['blue_green', 'canary', 'rolling', 'ab_testing', 'feature_flags', 'dark_launch'],
        'monitoring': ['apm', 'logs', 'metrics', 'traces', 'synthetic', 'rum', 'uptime', 'sla']
    }
}