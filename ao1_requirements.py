"""
AO1 Log Visibility Measurement - Keywords Dictionary for Metrics Calculation

This dictionary explains WHY each keyword matters for AO1 visibility metrics calculation.
Each keyword is mapped to specific measurements and explains HOW finding it in BigQuery 
helps calculate the visibility percentages CSOC needs for the AO1 project.

CORRECT AO1 REQUIREMENTS:
REQ-1: Global View - x% of all assets globally (CMDB count vs logging assets count)
REQ-2: Infrastructure Type - % visibility by host/log type across infrastructure types (On-Prem, Cloud, SaaS, API)
REQ-3: Regional and Country View - % visibility by location (Global Region, Country, Data Center, Cloud region)
REQ-4: BU and Application View - % visibility by business context (Business Unit, CIO, APM, Application Class)
REQ-5: System Classification - % by server function (Web Server, Windows Server, Linux Server, *Nix, Mainframe, Database, Network Appliance)
REQ-6: Security Control Coverage - Agent-based visibility % (EDR, Tanium, DLP coverage via Axonius or console stats)
REQ-7: Logging Compliance in GSO and Splunk - Ensure visibility statements based on logging platform
REQ-8: Domain Visibility - Asset visibility by hostname and domain

Author: [Your Name]
Date: [Date]
Version: 10.0 - Correct Requirements Mapping
"""

# KEYWORDS ORGANIZED BY CORRECT AO1 REQUIREMENTS
AO1_REQUIREMENTS_KEYWORDS = {

    # ==================== REQ-1: GLOBAL VIEW KEYWORDS ====================
    # PURPOSE: Count unique assets generating logs vs total assets in CMDB for "x% of all assets globally"
    # VENDORS: ServiceNow CMDB, Axonius, Chronicle, Splunk, ALL log sources
    
    'req1_global_view_identifiers': {
        'requirement': 'REQ-1: Global View - x% of all assets globally',
        'vendors': ['servicenow', 'axonius', 'chronicle', 'splunk', 'all_log_sources'],
        'calculation': 'COUNT DISTINCT logging assets / COUNT total CMDB assets * 100 = Global Visibility %',
        'keywords': {
            # Primary asset identifiers for global counting
            'hostname': 'REQ-1 GLOBAL - Primary asset identifier. COUNT DISTINCT hostnames across all log sources vs total CMDB hostnames for global visibility %.',
            'computer_name': 'REQ-1 GLOBAL - Windows asset identifier. Count unique Windows systems generating logs vs CMDB Windows inventory.',
            'asset_id': 'REQ-1 GLOBAL - ServiceNow asset ID. Direct CMDB asset correlation for precise global asset counting.',
            'sys_id': 'REQ-1 GLOBAL - ServiceNow system ID. Unique CMDB identifier for global asset inventory correlation.',
            'device_id': 'REQ-1 GLOBAL - Axonius device ID. Unique device identifier for cybersecurity asset management counting.',
            'machine_id': 'REQ-1 GLOBAL - Generic machine identifier. Universal asset ID for global asset deduplication.',
            'serial_number': 'REQ-1 GLOBAL - Hardware serial number. Physical asset identifier for global hardware inventory correlation.',
            'uuid': 'REQ-1 GLOBAL - Universally unique identifier. VM/cloud instance identifier for global virtual asset counting.',
            'fqdn': 'REQ-1 GLOBAL - Fully qualified domain name. Complete hostname for global DNS-based asset identification.',
            'ip_address': 'REQ-1 GLOBAL - Network identifier. IP-based asset identification when hostname unavailable for global counting.',
            'mac_address': 'REQ-1 GLOBAL - Hardware network identifier. Physical network asset identification for global inventory.',
            
            # CMDB-specific global identifiers (ServiceNow)
            'cmdb_ci': 'REQ-1 GLOBAL - ServiceNow configuration item. CMDB asset record for global inventory baseline counting.',
            'ci_name': 'REQ-1 GLOBAL - ServiceNow CI name. CMDB asset name for global asset correlation and counting.',
            'operational_status': 'REQ-1 GLOBAL - ServiceNow operational status. Active CMDB assets for global active asset counting.',
            'discovery_source': 'REQ-1 GLOBAL - ServiceNow discovery source. Asset discovery method for global asset discovery tracking.',
            
            # Axonius global asset identifiers
            'unique_id': 'REQ-1 GLOBAL - Axonius unique identifier. Cybersecurity asset management unique ID for global counting.',
            'last_seen': 'REQ-1 GLOBAL - Axonius last seen timestamp. Active asset indicator for global active asset counting.',
            'data_source': 'REQ-1 GLOBAL - Axonius data source. Asset data source for global asset source diversity counting.',
            
            # Chronicle/Splunk global log source identifiers
            'host': 'REQ-1 GLOBAL - Chronicle/Splunk host field. Log source system for global logging asset counting.',
            'source': 'REQ-1 GLOBAL - Splunk source field. Log file source for global log source counting.',
            'metadata.collected_timestamp': 'REQ-1 GLOBAL - Chronicle collection timestamp. Log collection indicator for global log timing.',
            'aid': 'REQ-1 GLOBAL - CrowdStrike Agent ID. EDR asset identifier for global endpoint security asset counting.'
        }
    },

    # ==================== REQ-2: INFRASTRUCTURE TYPE KEYWORDS ====================
    # PURPOSE: Classify assets by infrastructure type (On-Prem, Cloud, SaaS, API) for type-based visibility %
    # VENDORS: AWS, F5 BIG-IP, Wiz.io, Office365, API platforms
    
    'req2_infrastructure_type_classifiers': {
        'requirement': 'REQ-2: Infrastructure Type - % visibility by host/log type across infrastructure types',
        'vendors': ['aws', 'f5_bigip', 'wiz', 'office365', 'api_platforms'],
        'calculation': 'GROUP BY infrastructure type, COUNT assets per type for type-specific visibility %',
        'keywords': {
            # On-Premises infrastructure indicators
            'on_premises': 'REQ-2 ON-PREM - On-premises deployment indicator. Classify assets as On-Prem infrastructure type for visibility %.',
            'datacenter': 'REQ-2 ON-PREM - Physical data center indicator. On-premises facility classification for infrastructure type counting.',
            'physical_server': 'REQ-2 ON-PREM - Physical server indicator. Bare metal infrastructure classification for On-Prem type visibility.',
            'f5_bigip': 'REQ-2 ON-PREM - F5 BIG-IP indicator. On-premises network infrastructure for On-Prem classification.',
            'ltm': 'REQ-2 ON-PREM - F5 Local Traffic Manager. On-premises load balancer for On-Prem infrastructure counting.',
            'facility': 'REQ-2 ON-PREM - Physical facility indicator. On-premises location classification for infrastructure type.',
            'rack': 'REQ-2 ON-PREM - Server rack location. Physical infrastructure indicator for On-Prem classification.',
            
            # Cloud infrastructure indicators  
            'cloud': 'REQ-2 CLOUD - Cloud deployment indicator. Classify assets as Cloud infrastructure type for visibility %.',
            'aws': 'REQ-2 CLOUD - Amazon Web Services indicator. AWS cloud platform classification for Cloud type visibility.',
            'azure': 'REQ-2 CLOUD - Microsoft Azure indicator. Azure cloud platform classification for Cloud infrastructure counting.',
            'gcp': 'REQ-2 CLOUD - Google Cloud Platform indicator. GCP cloud classification for Cloud type visibility.',
            'ec2': 'REQ-2 CLOUD - AWS EC2 instance indicator. Cloud compute classification for Cloud infrastructure counting.',
            'virtual_machine': 'REQ-2 CLOUD - Virtual machine indicator. Cloud VM classification for Cloud type visibility.',
            'container': 'REQ-2 CLOUD - Container deployment indicator. Cloud container classification for Cloud infrastructure counting.',
            'serverless': 'REQ-2 CLOUD - Serverless deployment indicator. Cloud function classification for Cloud type visibility.',
            'cloud_provider': 'REQ-2 CLOUD - Wiz cloud provider field. Cloud platform classification for Cloud infrastructure counting.',
            'subscription_id': 'REQ-2 CLOUD - Cloud subscription identifier. Cloud account classification for Cloud type visibility.',
            
            # SaaS application indicators
            'saas': 'REQ-2 SAAS - Software-as-a-Service indicator. Classify applications as SaaS infrastructure type for visibility %.',
            'office365': 'REQ-2 SAAS - Microsoft Office 365 indicator. SaaS platform classification for SaaS type visibility.',
            'workday': 'REQ-2 SAAS - Workday platform indicator. SaaS application classification for SaaS infrastructure counting.',
            'salesforce': 'REQ-2 SAAS - Salesforce platform indicator. SaaS CRM classification for SaaS type visibility.',
            'servicenow': 'REQ-2 SAAS - ServiceNow platform indicator. SaaS ITSM classification for SaaS infrastructure counting.',
            'application_type': 'REQ-2 SAAS - Application type field from CMDB. SaaS classification for SaaS type visibility.',
            'software_as_a_service': 'REQ-2 SAAS - SaaS deployment model. Direct SaaS classification for SaaS infrastructure counting.',
            
            # API infrastructure indicators
            'api': 'REQ-2 API - API infrastructure indicator. Classify systems as API infrastructure type for visibility %.',
            'api_gateway': 'REQ-2 API - API Gateway indicator. API management platform classification for API type visibility.',
            'rest_api': 'REQ-2 API - REST API indicator. RESTful service classification for API infrastructure counting.',
            'graphql': 'REQ-2 API - GraphQL API indicator. GraphQL service classification for API type visibility.',
            'microservice': 'REQ-2 API - Microservice indicator. Service architecture classification for API infrastructure counting.',
            'webhook': 'REQ-2 API - Webhook indicator. Event-driven API classification for API type visibility.',
            'integration': 'REQ-2 API - Integration platform indicator. API integration classification for API infrastructure counting.'
        }
    },

    # ==================== REQ-3: REGIONAL AND COUNTRY VIEW KEYWORDS ====================
    # PURPOSE: Map assets to geographic locations for regional visibility %
    # VENDORS: ServiceNow CMDB, AWS regions, Chronicle/Splunk, all systems with location data
    
    'req3_regional_country_classifiers': {
        'requirement': 'REQ-3: Regional and Country View - % visibility by location',
        'vendors': ['servicenow', 'aws', 'chronicle', 'splunk', 'all_location_sources'],
        'calculation': 'GROUP BY geographic location, COUNT assets per region/country for location-based visibility %',
        'keywords': {
            # Global Region classification
            'global_region': 'REQ-3 REGION - Global region classifier. Top-level geographic grouping for regional visibility % calculation.',
            'region': 'REQ-3 REGION - Regional location field. Geographic region classification for regional asset counting.',
            'americas': 'REQ-3 REGION - Americas region indicator. Major geographic region for Americas visibility measurement.',
            'emea': 'REQ-3 REGION - EMEA region indicator. Europe/Middle East/Africa region for EMEA visibility counting.',
            'asia_pacific': 'REQ-3 REGION - APAC region indicator. Asia Pacific region for APAC visibility measurement.',
            'awsregion': 'REQ-3 REGION - AWS region field. Cloud geographic region for cloud regional visibility counting.',
            
            # Country classification
            'country': 'REQ-3 COUNTRY - Country location field. National-level geographic classification for country visibility %.',
            'country_code': 'REQ-3 COUNTRY - ISO country code. Standardized country identifier for country-level asset counting.',
            'united_states': 'REQ-3 COUNTRY - United States indicator. US country classification for US visibility measurement.',
            'canada': 'REQ-3 COUNTRY - Canada indicator. Canadian country classification for Canada visibility counting.',
            'united_kingdom': 'REQ-3 COUNTRY - UK indicator. UK country classification for UK visibility measurement.',
            'germany': 'REQ-3 COUNTRY - Germany indicator. German country classification for Germany visibility counting.',
            'sourceipaddress': 'REQ-3 COUNTRY - Source IP for geolocation. IP-based geographic classification for country visibility.',
            
            # Data Center classification
            'data_center': 'REQ-3 DATACENTER - Data center location field. Physical facility classification for data center visibility %.',
            'datacenter': 'REQ-3 DATACENTER - Data center identifier. Facility location for data center visibility counting.',
            'facility': 'REQ-3 DATACENTER - Physical facility field. Building location for facility-based visibility measurement.',
            'site': 'REQ-3 DATACENTER - Site location field. Physical site classification for site visibility counting.',
            'location': 'REQ-3 DATACENTER - ServiceNow location field. Asset location for location-based visibility measurement.',
            'building': 'REQ-3 DATACENTER - Building location field. Physical building for building-level visibility counting.',
            
            # Cloud Region classification
            'cloud_region': 'REQ-3 CLOUDREGION - Cloud provider region field. Cloud geographic region for cloud regional visibility %.',
            'availability_zone': 'REQ-3 CLOUDREGION - Cloud availability zone. Sub-regional cloud classification for zone visibility counting.',
            'edge_location': 'REQ-3 CLOUDREGION - CDN edge location. Content delivery geographic point for edge visibility measurement.',
            'aws_region': 'REQ-3 CLOUDREGION - AWS region identifier. Amazon cloud region for AWS regional visibility counting.'
        }
    },

    # ==================== REQ-4: BU AND APPLICATION VIEW KEYWORDS ====================
    # PURPOSE: Map assets to business context for organizational visibility %
    # VENDORS: ServiceNow, Workday, application-specific logs, business context in all tools
    
    'req4_business_application_classifiers': {
        'requirement': 'REQ-4: BU and Application View - Business Unit, CIO, APM, Application Class',
        'vendors': ['servicenow', 'workday', 'application_logs', 'business_context_all_tools'],
        'calculation': 'GROUP BY business unit/application, COUNT assets per BU/app for organizational visibility %',
        'keywords': {
            # Business Unit classification
            'business_unit': 'REQ-4 BU - Business unit field. Primary organizational classification for BU-level visibility % calculation.',
            'bu': 'REQ-4 BU - Business unit abbreviation. Organizational unit identifier for business unit visibility counting.',
            'division': 'REQ-4 BU - Business division field. Major organizational unit for divisional visibility measurement.',
            'department': 'REQ-4 BU - Department field. Departmental classification for department-level visibility counting.',
            'cost_center': 'REQ-4 BU - Cost center field. Financial organizational unit for cost center visibility measurement.',
            'business_service': 'REQ-4 BU - ServiceNow business service. Service-to-BU mapping for business service visibility counting.',
            'support_group': 'REQ-4 BU - ServiceNow support group. Asset ownership for organizational visibility measurement.',
            
            # CIO organization classification
            'cio': 'REQ-4 CIO - CIO organization field. IT leadership classification for CIO organization visibility % calculation.',
            'it_organization': 'REQ-4 CIO - IT organization unit. Technology organization for IT organizational visibility counting.',
            'technology': 'REQ-4 CIO - Technology organization field. IT department classification for technology visibility measurement.',
            'information_systems': 'REQ-4 CIO - Information systems unit. IT systems organization for IS visibility counting.',
            'engineering': 'REQ-4 CIO - Engineering organization field. Technical development unit for engineering visibility measurement.',
            'infrastructure': 'REQ-4 CIO - Infrastructure organization. IT infrastructure unit for infrastructure visibility counting.',
            'security': 'REQ-4 CIO - Security organization field. Cybersecurity unit for security organization visibility measurement.',
            
            # APM (Application Performance Management) classification
            'apm': 'REQ-4 APM - Application Performance Management field. APM classification for APM visibility % calculation.',
            'application': 'REQ-4 APM - Application identifier. Primary application classification for application visibility counting.',
            'app_name': 'REQ-4 APM - Application name field. Application identifier for application visibility measurement.',
            'service': 'REQ-4 APM - Service identifier. Service-level classification for service visibility counting.',
            'platform': 'REQ-4 APM - Platform identifier. Platform classification for platform visibility measurement.',
            'workload': 'REQ-4 APM - Workload identifier. Application workload for workload visibility counting.',
            'solution': 'REQ-4 APM - Solution identifier. Solution-level classification for solution visibility measurement.',
            
            # Application Class classification
            'application_class': 'REQ-4 APPCLASS - Application class field. Application category classification for app class visibility % calculation.',
            'app_class': 'REQ-4 APPCLASS - Application class abbreviation. App category for application class visibility counting.',
            'application_type': 'REQ-4 APPCLASS - Application type field. App type classification for type-based visibility measurement.',
            'service_class': 'REQ-4 APPCLASS - Service class field. Service category for service class visibility counting.',
            'tier': 'REQ-4 APPCLASS - Application tier field. App tier (web/app/data) for tier-based visibility measurement.',
            'component': 'REQ-4 APPCLASS - Application component field. App component for component visibility counting.'
        }
    },

    # ==================== REQ-5: SYSTEM CLASSIFICATION KEYWORDS ====================
    # PURPOSE: Classify assets by server function/OS type for system-type visibility %
    # VENDORS: All OS/platform indicators across all tools, ServiceNow CMDB, Axonius
    
    'req5_system_classification': {
        'requirement': 'REQ-5: System Classification - Web Server, Windows Server, Linux Server, *Nix, Mainframe, Database, Network Appliance',
        'vendors': ['all_os_platforms', 'servicenow', 'axonius'],
        'calculation': 'GROUP BY system type/function, COUNT assets per system classification for system-specific visibility %',
        'keywords': {
            # Web Server classification
            'web_server': 'REQ-5 WEBSERVER - Web server function classification. Web infrastructure for Web Server visibility % calculation.',
            'http_server': 'REQ-5 WEBSERVER - HTTP server function. Web service classification for web server visibility counting.',
            'apache': 'REQ-5 WEBSERVER - Apache web server indicator. Apache web server for Apache visibility measurement.',
            'nginx': 'REQ-5 WEBSERVER - Nginx web server indicator. Nginx web server for Nginx visibility counting.',
            'iis': 'REQ-5 WEBSERVER - IIS web server indicator. Microsoft IIS for Windows web server visibility measurement.',
            'tomcat': 'REQ-5 WEBSERVER - Tomcat application server. Java web server for Tomcat visibility counting.',
            'web_application': 'REQ-5 WEBSERVER - Web application indicator. Web app classification for web application visibility measurement.',
            
            # Windows Server classification
            'windows_server': 'REQ-5 WINDOWS - Windows server classification. Windows infrastructure for Windows Server visibility % calculation.',
            'windows': 'REQ-5 WINDOWS - Windows OS indicator. Microsoft Windows for Windows system visibility counting.',
            'microsoft_windows': 'REQ-5 WINDOWS - Microsoft Windows OS. Full Windows identifier for Windows visibility measurement.',
            'domain_controller': 'REQ-5 WINDOWS - Windows domain controller. AD server for Windows infrastructure visibility counting.',
            'active_directory': 'REQ-5 WINDOWS - Active Directory service. Windows directory service for AD visibility measurement.',
            'exchange': 'REQ-5 WINDOWS - Exchange mail server. Microsoft mail server for Windows mail visibility counting.',
            'windows_2019': 'REQ-5 WINDOWS - Windows Server 2019. Specific Windows version for Windows 2019 visibility measurement.',
            'windows_2022': 'REQ-5 WINDOWS - Windows Server 2022. Latest Windows server for Windows 2022 visibility counting.',
            
            # Linux Server classification
            'linux_server': 'REQ-5 LINUX - Linux server classification. Linux infrastructure for Linux Server visibility % calculation.',
            'linux': 'REQ-5 LINUX - Linux OS indicator. Linux operating system for Linux system visibility counting.',
            'redhat': 'REQ-5 LINUX - Red Hat Linux indicator. RHEL distribution for Red Hat visibility measurement.',
            'rhel': 'REQ-5 LINUX - Red Hat Enterprise Linux. Enterprise Linux for RHEL visibility counting.',
            'centos': 'REQ-5 LINUX - CentOS Linux indicator. CentOS distribution for CentOS visibility measurement.',
            'ubuntu': 'REQ-5 LINUX - Ubuntu Linux indicator. Ubuntu distribution for Ubuntu visibility counting.',
            'debian': 'REQ-5 LINUX - Debian Linux indicator. Debian distribution for Debian visibility measurement.',
            'suse': 'REQ-5 LINUX - SUSE Linux indicator. SUSE distribution for SUSE visibility counting.',
            
            # *Nix (AIX, Solaris, etc) classification
            'unix': 'REQ-5 NIX - Unix system classification. Unix OS for *Nix (AIX, Solaris, etc) visibility % calculation.',
            'aix': 'REQ-5 NIX - IBM AIX Unix indicator. AIX system for AIX visibility counting.',
            'solaris': 'REQ-5 NIX - Oracle Solaris Unix. Solaris system for Solaris visibility measurement.',
            'hp_ux': 'REQ-5 NIX - HP-UX Unix indicator. HP Unix for HP-UX visibility counting.',
            'freebsd': 'REQ-5 NIX - FreeBSD Unix indicator. BSD variant for FreeBSD visibility measurement.',
            'sunos': 'REQ-5 NIX - SunOS Unix indicator. Legacy Sun Unix for SunOS visibility counting.',
            'digital_unix': 'REQ-5 NIX - Digital Unix indicator. Legacy Unix for Digital Unix visibility measurement.',
            
            # Mainframe classification (Splunk only - no Chronicle migration)
            'mainframe': 'REQ-5 MAINFRAME - Mainframe system classification. Mainframe infrastructure for Mainframe visibility % (Splunk only).',
            'zos': 'REQ-5 MAINFRAME - z/OS mainframe OS. IBM mainframe for z/OS visibility counting (Splunk only).',
            'mvs': 'REQ-5 MAINFRAME - MVS mainframe OS. Legacy mainframe for MVS visibility measurement (Splunk only).',
            'cics': 'REQ-5 MAINFRAME - CICS transaction system. Mainframe transaction processing for CICS visibility counting (Splunk only).',
            'ims': 'REQ-5 MAINFRAME - IMS database system. Mainframe database for IMS visibility measurement (Splunk only).',
            'cobol': 'REQ-5 MAINFRAME - COBOL application indicator. Mainframe programming for COBOL visibility counting (Splunk only).',
            
            # Database classification
            'database': 'REQ-5 DATABASE - Database server classification. Database infrastructure for Database visibility % calculation.',
            'database_server': 'REQ-5 DATABASE - Database server function. Database server role for database visibility counting.',
            'sql_server': 'REQ-5 DATABASE - Microsoft SQL Server. Microsoft database for SQL Server visibility measurement.',
            'oracle_database': 'REQ-5 DATABASE - Oracle Database indicator. Oracle database for Oracle visibility counting.',
            'mysql': 'REQ-5 DATABASE - MySQL database indicator. MySQL database for MySQL visibility measurement.',
            'postgresql': 'REQ-5 DATABASE - PostgreSQL database. PostgreSQL for PostgreSQL visibility counting.',
            'mongodb': 'REQ-5 DATABASE - MongoDB database indicator. NoSQL database for MongoDB visibility measurement.',
            'db_engine': 'REQ-5 DATABASE - Database engine type. Database technology for database engine visibility counting.',
            
            # Network Appliance classification (FW, NDR, switch, router, etc)
            'network_appliance': 'REQ-5 NETAPPL - Network appliance classification. Network infrastructure for Network Appliance visibility % calculation.',
            'firewall': 'REQ-5 NETAPPL - Firewall appliance indicator. Security appliance for firewall visibility counting.',
            'router': 'REQ-5 NETAPPL - Network router indicator. Routing appliance for router visibility measurement.',
            'switch': 'REQ-5 NETAPPL - Network switch indicator. Switching appliance for switch visibility counting.',
            'load_balancer': 'REQ-5 NETAPPL - Load balancer appliance. Load balancing for load balancer visibility measurement.',
            'proxy': 'REQ-5 NETAPPL - Proxy appliance indicator. Proxy infrastructure for proxy visibility counting.',
            'ndr': 'REQ-5 NETAPPL - Network Detection & Response. NDR appliance for NDR visibility measurement.',
            'extrahop': 'REQ-5 NETAPPL - ExtraHop NDR platform. NDR system for ExtraHop visibility counting.',
            'f5_bigip': 'REQ-5 NETAPPL - F5 BIG-IP appliance. Network appliance for F5 visibility measurement.',
            'palo_alto': 'REQ-5 NETAPPL - Palo Alto firewall. Security appliance for Palo Alto visibility counting.'
        }
    },

    # ==================== REQ-6: SECURITY CONTROL COVERAGE KEYWORDS ====================
    # PURPOSE: Identify security agent presence for agent-based coverage % (via Axonius or console stats)
    # VENDORS: CrowdStrike Falcon, Tanium, Axonius, DLP tools
    
    'req6_security_control_coverage': {
        'requirement': 'REQ-6: Security Control Coverage - EDR, Tanium, DLP Agent (agent-based via Axonius or console stats)',
        'vendors': ['crowdstrike', 'tanium', 'axonius', 'dlp_tools'],
        'calculation': 'COUNT assets with security agents / COUNT total CMDB assets for agent coverage %',
        'keywords': {
            # EDR coverage (Axonius or console stats)
            'edr': 'REQ-6 EDR - EDR agent coverage indicator. Endpoint Detection Response for EDR coverage % via Axonius or console stats.',
            'crowdstrike': 'REQ-6 EDR - CrowdStrike Falcon EDR. Primary EDR platform for EDR agent coverage measurement via Axonius.',
            'falcon': 'REQ-6 EDR - CrowdStrike Falcon agent. EDR agent presence for Falcon coverage counting via console stats.',
            'aid': 'REQ-6 EDR - CrowdStrike Agent ID. Unique EDR agent identifier for precise EDR coverage calculation via Axonius.',
            'sensor_id': 'REQ-6 EDR - EDR sensor identifier. EDR agent sensor for endpoint security coverage via console stats.',
            'agent_version': 'REQ-6 EDR - EDR agent version. Agent deployment status for EDR coverage measurement via Axonius.',
            'endpoint_detection': 'REQ-6 EDR - Endpoint detection capability. EDR functionality for endpoint security coverage via console stats.',
            'detection_id': 'REQ-6 EDR - EDR detection event. EDR activity indicator for active EDR coverage via Axonius.',
            
            # Tanium coverage (Axonius or console stats)  
            'tanium': 'REQ-6 TANIUM - Tanium agent coverage indicator. Endpoint management platform for Tanium coverage % via Axonius or console stats.',
            'tanium_client': 'REQ-6 TANIUM - Tanium client agent. Endpoint agent presence for Tanium coverage counting via console stats.',
            'computer_id': 'REQ-6 TANIUM - Tanium computer ID. Unique endpoint identifier for Tanium coverage calculation via Axonius.',
            'sensor': 'REQ-6 TANIUM - Tanium sensor. Endpoint monitoring capability for Tanium sensor coverage via console stats.',
            'endpoint_management': 'REQ-6 TANIUM - Endpoint management capability. Tanium functionality for endpoint management coverage via Axonius.',
            'patch_management': 'REQ-6 TANIUM - Patch management capability. Tanium patching for patch management coverage via console stats.',
            'compliance_monitoring': 'REQ-6 TANIUM - Compliance monitoring capability. Tanium compliance for compliance coverage via Axonius.',
            
            # DLP Agent coverage (Axonius or console stats)
            'dlp': 'REQ-6 DLP - DLP agent coverage indicator. Data Loss Prevention for DLP Agent coverage % via Axonius or console stats.',
            'dlp_agent': 'REQ-6 DLP - DLP agent identifier. Data protection agent for DLP agent coverage counting via console stats.',
            'data_loss_prevention': 'REQ-6 DLP - Data Loss Prevention system. DLP platform for data protection coverage via Axonius.',
            'endpoint_dlp': 'REQ-6 DLP - Endpoint DLP agent. Endpoint data protection for endpoint DLP coverage via console stats.',
            'content_inspection': 'REQ-6 DLP - Content inspection capability. DLP analysis for data inspection coverage via Axonius.',
            'policy_violation': 'REQ-6 DLP - DLP policy violation. DLP enforcement activity for DLP coverage measurement via console stats.',
            
            # Axonius coverage statistics
            'axonius': 'REQ-6 AXONIUS - Axonius asset platform. Cybersecurity asset management for agent coverage statistics aggregation.',
            'installed_software': 'REQ-6 AXONIUS - Axonius installed software. Software inventory for security agent presence detection via Axonius.',
            'security_software': 'REQ-6 AXONIUS - Axonius security software. Security agent inventory for security control coverage via Axonius.',
            'agent_coverage': 'REQ-6 AXONIUS - Axonius agent coverage. Security agent coverage statistics for coverage % calculation via Axonius.',
            'endpoint_protection': 'REQ-6 AXONIUS - Axonius endpoint protection. Endpoint security coverage for security control measurement via Axonius.',
            
            # Console stats indicators
            'console_stats': 'REQ-6 CONSOLE - Security console statistics. Agent management console for coverage statistics collection.',
            'agent_status': 'REQ-6 CONSOLE - Agent status indicator. Security agent status for coverage measurement via console stats.',
            'deployment_status': 'REQ-6 CONSOLE - Agent deployment status. Agent installation status for deployment coverage via console stats.',
            'management_console': 'REQ-6 CONSOLE - Agent management console. Security platform console for agent coverage statistics.'
        }
    },

    # ==================== REQ-7: LOGGING COMPLIANCE GSO AND SPLUNK KEYWORDS ====================
    # PURPOSE: Ensure visibility statements based on logging platform compliance
    # VENDORS: Chronicle (GSO), Splunk
    
    'req7_logging_compliance': {
        'requirement': 'REQ-7: Logging Compliance in GSO and Splunk - Ensure visibility statements based on logging platform',
        'vendors': ['chronicle_gso', 'splunk'],
        'calculation': 'MEASURE logging compliance and visibility statement accuracy per platform',
        'keywords': {
            # Chronicle (GSO) compliance indicators
            'chronicle': 'REQ-7 GSO - Google Chronicle SIEM platform. Primary SIEM for GSO logging compliance measurement.',
            'gso': 'REQ-7 GSO - Google Security Operations. Chronicle platform for GSO visibility compliance tracking.',
            'google_chronicle': 'REQ-7 GSO - Google Chronicle platform. Security operations platform for Chronicle compliance measurement.',
            'udm': 'REQ-7 GSO - Chronicle Unified Data Model. Normalized data model for GSO data standardization compliance.',
            'detection_engine': 'REQ-7 GSO - Chronicle detection engine. Security detection platform for GSO detection compliance.',
            'yara_l': 'REQ-7 GSO - Chronicle YARA-L rules. Detection rule language for GSO rule compliance measurement.',
            'ingestion_time': 'REQ-7 GSO - Chronicle ingestion timestamp. Log ingestion timing for GSO ingestion compliance.',
            'metadata.collected_timestamp': 'REQ-7 GSO - Chronicle collection metadata. Log collection tracking for GSO collection compliance.',
            'metadata.event_timestamp': 'REQ-7 GSO - Chronicle event metadata. Event timing for GSO event compliance measurement.',
            'security_result': 'REQ-7 GSO - Chronicle security result. Security findings for GSO security compliance tracking.',
            
            # Splunk compliance indicators
            'splunk': 'REQ-7 SPLUNK - Splunk SIEM platform. Secondary SIEM for Splunk logging compliance measurement.',
            'sourcetype': 'REQ-7 SPLUNK - Splunk sourcetype field. Log source classification for Splunk source compliance tracking.',
            'index': 'REQ-7 SPLUNK - Splunk index field. Data organization for Splunk index compliance measurement.',
            '_time': 'REQ-7 SPLUNK - Splunk timestamp field. Event timing for Splunk temporal compliance tracking.',
            'host': 'REQ-7 SPLUNK - Splunk host field. Source system identification for Splunk host compliance measurement.',
            'source': 'REQ-7 SPLUNK - Splunk source field. Log file source for Splunk source compliance tracking.',
            'splunk_server': 'REQ-7 SPLUNK - Splunk infrastructure. Platform deployment for Splunk infrastructure compliance.',
            'indexer': 'REQ-7 SPLUNK - Splunk indexer. Data processing component for Splunk processing compliance measurement.',
            'forwarder': 'REQ-7 SPLUNK - Splunk forwarder. Log collection agent for Splunk collection compliance tracking.',
            'search_head': 'REQ-7 SPLUNK - Splunk search head. Query processing for Splunk query compliance measurement.',
            
            # Logging compliance measurement indicators
            'log_ingestion': 'REQ-7 COMPLIANCE - Log ingestion measurement. Data ingestion rate for logging compliance tracking.',
            'data_retention': 'REQ-7 COMPLIANCE - Data retention compliance. Log retention policy for compliance measurement.',
            'log_completeness': 'REQ-7 COMPLIANCE - Log completeness indicator. Data completeness for logging compliance tracking.',
            'ingestion_latency': 'REQ-7 COMPLIANCE - Ingestion latency measurement. Log processing delay for compliance measurement.',
            'parsing_success': 'REQ-7 COMPLIANCE - Log parsing success rate. Data parsing compliance for logging compliance tracking.',
            'field_extraction': 'REQ-7 COMPLIANCE - Field extraction success. Data extraction compliance for compliance measurement.',
            'normalization': 'REQ-7 COMPLIANCE - Data normalization compliance. Data standardization for logging compliance tracking.',
            'enrichment': 'REQ-7 COMPLIANCE - Data enrichment compliance. Data enhancement for compliance measurement.',
            
            # Platform-specific compliance
            'visibility_statement': 'REQ-7 STATEMENT - Visibility statement accuracy. Platform-based visibility claims for statement compliance.',
            'logging_platform': 'REQ-7 PLATFORM - Logging platform identifier. Platform classification for platform-specific compliance.',
            'compliance_percentage': 'REQ-7 PERCENTAGE - Compliance percentage measurement. Platform compliance rate for compliance tracking.',
            'coverage_statement': 'REQ-7 COVERAGE - Coverage statement accuracy. Platform coverage claims for coverage compliance measurement.'
        }
    },

    # ==================== REQ-8: DOMAIN VISIBILITY KEYWORDS ====================
    # PURPOSE: Asset visibility by hostname and domain for domain-based coverage %
    # VENDORS: DNS systems, all hostname fields, ServiceNow CMDB, domain controllers
    
    'req8_domain_visibility': {
        'requirement': 'REQ-8: Domain Visibility - Asset visibility by hostname and domain',
        'vendors': ['dns_systems', 'all_hostname_sources', 'servicenow', 'domain_controllers'],
        'calculation': 'COUNT DISTINCT domains and hostnames in logs vs DNS/CMDB records for domain coverage %',
        'keywords': {
            # Hostname visibility patterns
            'hostname': 'REQ-8 HOSTNAME - Primary hostname field. Host name identification for hostname visibility measurement.',
            'host_name': 'REQ-8 HOSTNAME - Host name field. System hostname for host-based visibility counting.',
            'computer_name': 'REQ-8 HOSTNAME - Computer name field. Windows computer name for Windows hostname visibility.',
            'machine_name': 'REQ-8 HOSTNAME - Machine name field. Generic machine identifier for machine hostname visibility.',
            'server_name': 'REQ-8 HOSTNAME - Server name field. Server hostname for server hostname visibility measurement.',
            'device_name': 'REQ-8 HOSTNAME - Device name field. Network device name for device hostname visibility.',
            'node_name': 'REQ-8 HOSTNAME - Node name field. Cluster node name for node hostname visibility counting.',
            'system_name': 'REQ-8 HOSTNAME - System name field. System identifier for system hostname visibility measurement.',
            'asset_name': 'REQ-8 HOSTNAME - Asset name field. CMDB asset name for asset hostname visibility counting.',
            
            # Domain visibility patterns
            'domain': 'REQ-8 DOMAIN - Domain name field. Primary domain identification for domain visibility measurement.',
            'domain_name': 'REQ-8 DOMAIN - Domain name field. Full domain identifier for domain visibility counting.',
            'fqdn': 'REQ-8 DOMAIN - Fully qualified domain name. Complete hostname+domain for FQDN visibility measurement.',
            'dns_name': 'REQ-8 DOMAIN - DNS registered name. Authoritative DNS name for DNS visibility counting.',
            'canonical_name': 'REQ-8 DOMAIN - DNS canonical name. CNAME record for DNS alias visibility measurement.',
            'subdomain': 'REQ-8 DOMAIN - Subdomain identifier. Subdomain classification for subdomain visibility counting.',
            'parent_domain': 'REQ-8 DOMAIN - Parent domain name. Higher-level domain for domain hierarchy visibility.',
            'root_domain': 'REQ-8 DOMAIN - Root domain name. Base domain for primary domain visibility measurement.',
            
            # DNS record visibility
            'a_record': 'REQ-8 DNS - DNS A record. IPv4 DNS record for DNS A record visibility measurement.',
            'aaaa_record': 'REQ-8 DNS - DNS AAAA record. IPv6 DNS record for DNS AAAA record visibility counting.',
            'cname_record': 'REQ-8 DNS - DNS CNAME record. DNS alias record for DNS alias visibility measurement.',
            'mx_record': 'REQ-8 DNS - DNS MX record. Mail exchange record for DNS MX record visibility counting.',
            'ns_record': 'REQ-8 DNS - DNS NS record. Name server record for DNS NS record visibility measurement.',
            'ptr_record': 'REQ-8 DNS - DNS PTR record. Reverse DNS record for DNS PTR record visibility counting.',
            'dns_query': 'REQ-8 DNS - DNS query event. DNS lookup activity for DNS query visibility measurement.',
            'dns_response': 'REQ-8 DNS - DNS response event. DNS resolution response for DNS response visibility counting.',
            
            # Domain classification
            'internal_domain': 'REQ-8 INTERNAL - Internal domain name. Corporate internal domain for internal domain visibility measurement.',
            'external_domain': 'REQ-8 EXTERNAL - External domain name. External domain access for external domain visibility counting.',
            'corporate_domain': 'REQ-8 INTERNAL - Corporate domain name. Company domain for corporate domain visibility measurement.',
            'public_domain': 'REQ-8 EXTERNAL - Public domain name. Internet domain for public domain visibility counting.',
            'private_domain': 'REQ-8 INTERNAL - Private domain name. Private domain for internal domain visibility measurement.',
            
            # Domain resolution and connectivity
            'domain_resolution': 'REQ-8 RESOLUTION - Domain name resolution. DNS resolution success for domain resolution visibility.',
            'name_resolution': 'REQ-8 RESOLUTION - Name resolution event. Hostname resolution for name resolution visibility measurement.',
            'dns_lookup': 'REQ-8 RESOLUTION - DNS lookup event. DNS query activity for DNS lookup visibility counting.',
            'reverse_dns': 'REQ-8 RESOLUTION - Reverse DNS lookup. IP to hostname resolution for reverse DNS visibility measurement.',
            'forward_dns': 'REQ-8 RESOLUTION - Forward DNS lookup. Hostname to IP resolution for forward DNS visibility counting.',
            'nxdomain': 'REQ-8 RESOLUTION - Non-existent domain. DNS NXDOMAIN response for domain existence visibility measurement.',
            
            # Domain membership and authentication
            'domain_controller': 'REQ-8 DOMAIN_AUTH - Domain controller. AD domain controller for domain authentication visibility.',
            'active_directory': 'REQ-8 DOMAIN_AUTH - Active Directory domain. Windows domain for AD domain visibility measurement.',
            'domain_membership': 'REQ-8 DOMAIN_AUTH - Domain membership. System domain membership for domain member visibility counting.',
            'kerberos_realm': 'REQ-8 DOMAIN_AUTH - Kerberos realm. Authentication realm for Kerberos domain visibility measurement.',
            'distinguished_name': 'REQ-8 DOMAIN_AUTH - AD distinguished name. LDAP DN for AD object domain visibility counting.'
        }
    }
}

# FLATTENED KEYWORD LIST WITH REQUIREMENT CONTEXT
ALL_AO1_REQUIREMENTS_KEYWORDS = {}
for category, category_data in AO1_REQUIREMENTS_KEYWORDS.items():
    requirement = category_data['requirement']
    vendors = category_data['vendors']
    calculation = category_data['calculation']
    
    for keyword, context in category_data['keywords'].items():
        ALL_AO1_REQUIREMENTS_KEYWORDS[keyword] = {
            'category': category,
            'requirement': requirement,
            'vendors': vendors,
            'calculation': calculation,
            'context': context
        }

def get_keyword_requirement_context(keyword):
    """
    Returns the AO1 requirement context for why a keyword matters
    
    Args:
        keyword (str): Keyword found in BigQuery schema
        
    Returns:
        dict: Context explaining which AO1 requirement this keyword supports
    """
    return ALL_AO1_REQUIREMENTS_KEYWORDS.get(keyword.lower(), {
        'category': 'unknown',
        'requirement': 'No AO1 requirement mapping identified',
        'vendors': [],
        'calculation': 'Not applicable for AO1 calculations',
        'context': 'This keyword is not relevant for AO1 visibility measurements'
    })

def find_keywords_for_requirement(requirement_number):
    """
    Find all keywords relevant to a specific AO1 requirement
    
    Args:
        requirement_number (str): Requirement number (e.g., "REQ-1", "REQ-2")
        
    Returns:
        list: Keywords that support the specified requirement
    """
    relevant_keywords = []
    
    for keyword, data in ALL_AO1_REQUIREMENTS_KEYWORDS.items():
        if requirement_number.upper() in data['requirement'].upper():
            relevant_keywords.append({
                'keyword': keyword,
                'context': data['context'],
                'vendors': data['vendors'],
                'calculation': data['calculation']
            })
    
    return relevant_keywords

def explain_bigquery_field_ao1_relevance(field_name, table_name, dataset_name):
    """
    Explains how a BigQuery field supports specific AO1 requirements
    
    Args:
        field_name (str): BigQuery column name
        table_name (str): BigQuery table name  
        dataset_name (str): BigQuery dataset name
        
    Returns:
        str: Complete explanation of AO1 requirement support
    """
    context = get_keyword_requirement_context(field_name)
    
    if context['category'] == 'unknown':
        return f"Field '{field_name}' in {dataset_name}.{table_name} does not directly support any AO1 requirements."
    
    return f"""
FIELD: {field_name} (in {dataset_name}.{table_name})
AO1 REQUIREMENT: {context['requirement']}
RELEVANT VENDORS: {', '.join(context['vendors'])}
CALCULATION METHOD: {context['calculation']}
FIELD PURPOSE: {context['context']}
    """

# EXPORT FUNCTIONS FOR AO1 MAPPING SCRIPT
__all__ = [
    'AO1_REQUIREMENTS_KEYWORDS',
    'ALL_AO1_REQUIREMENTS_KEYWORDS',
    'get_keyword_requirement_context',
    'find_keywords_for_requirement',
    'explain_bigquery_field_ao1_relevance'
]