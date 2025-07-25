PATTERN_LIBRARY = {
    'ip_patterns': [
        r'(?:ip|addr|address)(?:_?(?:src|source|dst|dest|destination|client|server|remote|local|public|private))?',
        r'(?:src|source|dst|dest|destination|client|server|remote|local)(?:_?(?:ip|addr|address))',
        r'(?:v4|v6|ipv4|ipv6)(?:_?(?:addr|address))?'
    ],
    'port_patterns': [
        r'(?:port|prt|portnum)(?:_?(?:src|source|dst|dest|destination|local|remote|listen|bind))?',
        r'(?:src|source|dst|dest|destination|local|remote)(?:_?(?:port|prt))'
    ],
    'time_patterns': [
        r'(?:time|timestamp|date|datetime|epoch|utc|gmt|created|modified|updated|start|end|begin|finish|occurred|when)',
        r'(?:create|mod|update|start|end|begin|finish|occur)(?:_?(?:time|date|timestamp))',
        r'(?:year|month|day|hour|minute|second|millisecond|microsecond)(?:s)?'
    ],
    'user_patterns': [
        r'(?:user|usr|account|identity|subject|principal|actor|person|individual)(?:_?(?:name|id|email|domain))?',
        r'(?:login|logon|signin|username|userid|email|upn|dn|cn|sam|guid|uuid)(?:_?(?:name|id))?'
    ],
    'action_patterns': [
        r'(?:action|operation|activity|event|command|request|response|result|outcome|status|verdict)',
        r'(?:allow|deny|block|drop|permit|reject|accept|forward|route|redirect|proxy)',
        r'(?:success|fail|error|ok|pass|deny|grant|revoke|create|delete|modify|update)'
    ],
    'file_patterns': [
        r'(?:file|filename|filepath|path|document|doc|binary|executable|exe|dll|script)',
        r'(?:directory|folder|dir|location|parent|child|root|base|full)(?:_?(?:path|name))',
        r'(?:extension|ext|type|format|mime|content)(?:_?(?:type))?'
    ],
    'process_patterns': [
        r'(?:process|proc|program|application|app|service|daemon|task|job|thread)',
        r'(?:pid|ppid|process_id|parent|child|executable|image|command|cmd)(?:_?(?:line|name|path))?'
    ],
    'network_patterns': [
        r'(?:protocol|proto|transport|network|net|connection|conn|session|flow|stream)',
        r'(?:tcp|udp|icmp|http|https|ftp|ssh|dns|dhcp|smtp|pop|imap|snmp)',
        r'(?:packet|frame|segment|datagram|message|payload|header|body)'
    ],
    'security_patterns': [
        r'(?:security|sec|threat|attack|malware|virus|signature|rule|policy|alert|alarm)',
        r'(?:hash|checksum|digest|signature|certificate|key|token|credential|password)',
        r'(?:encrypt|decrypt|cipher|crypto|ssl|tls|pki|x509|rsa|aes|sha|md5)'
    ],
    'size_patterns': [
        r'(?:size|bytes|length|count|volume|amount|quantity|total|sum|max|min|avg)',
        r'(?:kb|mb|gb|tb|kilobyte|megabyte|gigabyte|terabyte)(?:s)?'
    ],
    'geo_patterns': [
        r'(?:country|region|city|state|province|location|geo|geographic|latitude|longitude|coordinates)',
        r'(?:continent|timezone|locale|language|culture|iso|cc|country_code)'
    ],
    'cloud_patterns': [
        r'(?:cloud|aws|azure|gcp|google|amazon|microsoft)(?:_?(?:service|resource|instance))?',
        r'(?:vpc|vnet|subnet|security_group|nacl|route|gateway)',
        r'(?:container|docker|kubernetes|k8s|pod|namespace|cluster)'
    ]
}