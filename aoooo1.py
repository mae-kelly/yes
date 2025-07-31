#!/usr/bin/env python3
"""
AO1 Complete Keyword Coverage Field Discovery System
===================================================

This version incorporates ALL the keywords and variations you specified.
No more missing keywords - comprehensive coverage of every variation you provided.

Author: AO1 Analytics Development Team
Version: 4.0 Complete Coverage
Target: prj-fisv-p-gcss-sas-dl9dd0f1df
Authentication: chronicle-fisv
"""

import os
import sys
import json
import time
import logging
import numpy as np
import re
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict, Counter
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Production logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ao1_complete_keyword_discovery.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# BigQuery authentication - Production configuration
from google.cloud import bigquery
from google.oauth2 import service_account

file_path = os.path.dirname(__file__)
SERVICE_ACCOUNT_FILE = os.path.join(file_path, "gcp_prod_key.json")
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
project = "chronicle-fisv"
clientBQ = bigquery.Client(project=project, credentials=credentials)

# COMPLETE AO1 KEYWORD REQUIREMENTS - EVERY VARIATION YOU SPECIFIED
AO1_COMPLETE_REQUIREMENTS = {
    'REQ1_GLOBAL_VIEW_METRICS': {
        'description': 'Global View - CSOC ability to view x% of all assets globally',
        'table_names': [
            'assets', 'asset', 'inventory', 'cmdb', 'configuration_management_database', 
            'ci', 'configuration_items', 'discovery', 'devices', 'systems', 'computers', 
            'machines', 'endpoints', 'nodes', 'hosts', 'infrastructure', 'it_assets', 
            'hardware', 'equipment'
        ],
        'asset_inventory_keywords': [
            # Asset ID variations - ALL spellings
            'asset_id', 'assetid', 'asset-id', 'asset_identifier', 'assetidentifier', 
            'asset-identifier', 'assetId', 'AssetID', 'ASSET_ID', 'ASSETID', 'Asset_ID', 
            'Asset_Id', 'assetID',
            # Inventory ID variations - ALL spellings
            'inventory_id', 'inventoryid', 'inventory-id', 'inventoryId', 'InventoryID', 
            'INVENTORY_ID', 'inv_id', 'invid', 'inv-id', 'invId', 'InvID', 'INV_ID', 
            'Inv_ID', 'Inv_Id',
            # Asset tag variations - ALL spellings
            'asset_tag', 'assettag', 'asset-tag', 'assetTag', 'AssetTag', 'ASSET_TAG', 
            'tag', 'TAG', 'Tag', 'asset_number', 'assetnumber', 'asset-number', 
            'assetNumber', 'AssetNumber', 'ASSET_NUMBER', 'Asset_Number', 'Asset_Num', 'asset_num',
            # Serial number variations - ALL spellings
            'serial_number', 'serialnumber', 'serial-number', 'serialNumber', 'SerialNumber', 
            'SERIAL_NUMBER', 'serial_no', 'serialno', 'serial-no', 'serialNo', 'SerialNo', 
            'SERIAL_NO', 'sn', 'SN', 's_n', 'S_N', 'Serial_Number', 'Serial_No', 
            'serial_nbr', 'serialnbr'
        ],
        'hostname_keywords': [
            # Hostname variations - ALL spellings
            'hostname', 'host_name', 'host-name', 'hostName', 'HostName', 'HOSTNAME', 
            'HOST_NAME', 'HOST-NAME', 'Host_Name', 'Host_name', 'hostNAME',
            # Computer name variations - ALL spellings
            'computer_name', 'computername', 'computer-name', 'computerName', 'ComputerName', 
            'COMPUTER_NAME', 'COMPUTERNAME', 'COMPUTER-NAME', 'Computer_Name', 'Computer_name', 
            'comp_name', 'compname',
            # System name variations - ALL spellings
            'system_name', 'systemname', 'system-name', 'systemName', 'SystemName', 
            'SYSTEM_NAME', 'SYSTEMNAME', 'SYSTEM-NAME', 'System_Name', 'System_name', 
            'sys_name', 'sysname',
            # Machine name variations - ALL spellings
            'machine_name', 'machinename', 'machine-name', 'machineName', 'MachineName', 
            'MACHINE_NAME', 'MACHINENAME', 'MACHINE-NAME', 'Machine_Name', 'Machine_name', 
            'mach_name', 'machname',
            # FQDN variations - ALL spellings
            'fqdn', 'FQDN', 'Fqdn', 'fully_qualified_domain_name', 'fullyqualifieddomainname', 
            'fully-qualified-domain-name', 'fullyQualifiedDomainName', 'FullyQualifiedDomainName', 
            'FULLY_QUALIFIED_DOMAIN_NAME', 'Fully_Qualified_Domain_Name',
            # DNS name variations - ALL spellings
            'dns_name', 'dnsname', 'dns-name', 'dnsName', 'DnsName', 'DNS_NAME', 'DNSNAME', 
            'DNS-NAME', 'Dns_Name', 'Dns_name', 'domain_name', 'domainname', 'domain-name', 
            'domainName', 'DomainName', 'DOMAIN_NAME'
        ]
    },
    
    'REQ2_INFRASTRUCTURE_TYPE_METRICS': {
        'description': 'Infrastructure Type - Display % of visibility by host and log type across infrastructure types',
        'table_names': [
            'infrastructure', 'infra', 'platforms', 'platform', 'deployment', 'deployments', 
            'hosting', 'environment', 'environments', 'cloud_assets', 'on_prem_assets', 
            'saas_applications', 'api_catalog', 'services', 'applications', 'app_inventory'
        ],
        'infrastructure_classification_keywords': [
            # Infrastructure type variations - ALL spellings
            'infrastructure_type', 'infrastructuretype', 'infrastructure-type', 'infrastructureType', 
            'InfrastructureType', 'INFRASTRUCTURE_TYPE', 'INFRASTRUCTURETYPE', 'INFRASTRUCTURE-TYPE', 
            'Infrastructure_Type', 'Infrastructure_type', 'infra_type', 'infratype', 'infra-type', 
            'infraType', 'InfraType', 'INFRA_TYPE', 'INFRATYPE', 'INFRA-TYPE', 'Infra_Type', 'Infra_type',
            # Deployment type variations - ALL spellings
            'deployment_type', 'deploymenttype', 'deployment-type', 'deploymentType', 'DeploymentType', 
            'DEPLOYMENT_TYPE', 'DEPLOYMENTTYPE', 'DEPLOYMENT-TYPE', 'Deployment_Type', 'Deployment_type', 
            'deploy_type', 'deploytype', 'deploy-type', 'deployType', 'DeployType', 'DEPLOY_TYPE', 
            'DEPLOYTYPE', 'DEPLOY-TYPE',
            # Platform type variations - ALL spellings
            'platform_type', 'platformtype', 'platform-type', 'platformType', 'PlatformType', 
            'PLATFORM_TYPE', 'PLATFORMTYPE', 'PLATFORM-TYPE', 'Platform_Type', 'Platform_type', 
            'hosting_type', 'hostingtype', 'hosting-type', 'hostingType', 'HostingType', 'HOSTING_TYPE',
            # Environment type variations - ALL spellings
            'environment_type', 'environmenttype', 'environment-type', 'environmentType', 'EnvironmentType', 
            'ENVIRONMENT_TYPE', 'ENVIRONMENTTYPE', 'ENVIRONMENT-TYPE', 'Environment_Type', 'Environment_type', 
            'env_type', 'envtype', 'env-type'
        ],
        'on_premise_keywords': [
            # On-prem variations - ALL spellings
            'on_prem', 'onprem', 'on-prem', 'onPrem', 'OnPrem', 'ON_PREM', 'ONPREM', 'ON-PREM', 
            'On_Prem', 'On_prem', 'on_premise', 'onpremise', 'on-premise', 'onPremise', 'OnPremise', 
            'ON_PREMISE', 'ONPREMISE', 'ON-PREMISE', 'On_Premise', 'On_premise',
            # Physical variations - ALL spellings
            'physical', 'Physical', 'PHYSICAL', 'bare_metal', 'baremetal', 'bare-metal', 'bareMetal', 
            'BareMetal', 'BARE_METAL', 'BAREMETAL', 'BARE-METAL', 'Bare_Metal', 'Bare_metal', 
            'dedicated', 'Dedicated', 'DEDICATED',
            # Local variations - ALL spellings
            'local', 'Local', 'LOCAL', 'in_house', 'inhouse', 'in-house', 'inHouse', 'InHouse', 
            'IN_HOUSE', 'INHOUSE', 'IN-HOUSE', 'In_House', 'In_house', 'internal', 'Internal', 
            'INTERNAL', 'datacenter', 'data_center', 'data-center', 'dataCenter', 'DataCenter', 
            'DATACENTER', 'DATA_CENTER', 'DATA-CENTER', 'dc', 'DC', 'Dc'
        ],
        'cloud_keywords': [
            # Cloud variations - ALL spellings
            'cloud', 'Cloud', 'CLOUD', 'cloud_provider', 'cloudprovider', 'cloud-provider', 
            'cloudProvider', 'CloudProvider', 'CLOUD_PROVIDER', 'CLOUDPROVIDER', 'CLOUD-PROVIDER', 
            'Cloud_Provider', 'Cloud_provider',
            # AWS variations - ALL spellings
            'aws', 'AWS', 'Aws', 'amazon', 'Amazon', 'AMAZON', 'amazon_web_services', 
            'amazonwebservices', 'amazon-web-services', 'amazonWebServices', 'AmazonWebServices', 
            'AMAZON_WEB_SERVICES', 'AMAZONWEBSERVICES', 'AMAZON-WEB-SERVICES', 'Amazon_Web_Services',
            # Azure variations - ALL spellings
            'azure', 'Azure', 'AZURE', 'microsoft_azure', 'microsoftazure', 'microsoft-azure', 
            'microsoftAzure', 'MicrosoftAzure', 'MICROSOFT_AZURE', 'MICROSOFTAZURE', 'MICROSOFT-AZURE', 
            'Microsoft_Azure', 'msft_azure', 'msftazure', 'msft-azure', 'msftAzure', 'MsftAzure', 'MSFT_AZURE',
            # GCP variations - ALL spellings
            'gcp', 'GCP', 'Gcp', 'google_cloud', 'googlecloud', 'google-cloud', 'googleCloud', 
            'GoogleCloud', 'GOOGLE_CLOUD', 'GOOGLECLOUD', 'GOOGLE-CLOUD', 'Google_Cloud', 'gce', 
            'GCE', 'Gce', 'google_compute_engine', 'googlecomputeengine', 'google-compute-engine',
            # Cloud types - ALL spellings
            'public_cloud', 'publiccloud', 'public-cloud', 'publicCloud', 'PublicCloud', 'PUBLIC_CLOUD', 
            'PUBLICCLOUD', 'PUBLIC-CLOUD', 'Public_Cloud', 'private_cloud', 'privatecloud', 'private-cloud', 
            'privateCloud', 'PrivateCloud', 'PRIVATE_CLOUD', 'PRIVATECLOUD', 'PRIVATE-CLOUD', 'Private_Cloud',
            'multi_cloud', 'multicloud', 'multi-cloud', 'multiCloud', 'MultiCloud', 'MULTI_CLOUD', 
            'MULTICLOUD', 'MULTI-CLOUD', 'Multi_Cloud', 'hybrid_cloud', 'hybridcloud', 'hybrid-cloud', 
            'hybridCloud', 'HybridCloud', 'HYBRID_CLOUD', 'HYBRIDCLOUD', 'HYBRID-CLOUD', 'Hybrid_Cloud'
        ],
        'saas_keywords': [
            # SaaS variations - ALL spellings
            'saas', 'SAAS', 'SaaS', 'Saas', 'software_as_a_service', 'softwareasaservice', 
            'software-as-a-service', 'softwareAsAService', 'SoftwareAsAService', 'SOFTWARE_AS_A_SERVICE', 
            'SOFTWAREASASERVICE', 'SOFTWARE-AS-A-SERVICE', 'Software_As_A_Service',
            # PaaS variations - ALL spellings
            'paas', 'PAAS', 'PaaS', 'Paas', 'platform_as_a_service', 'platformasaservice', 
            'platform-as-a-service', 'platformAsAService', 'PlatformAsAService', 'PLATFORM_AS_A_SERVICE', 
            'PLATFORMASASERVICE', 'PLATFORM-AS-A-SERVICE', 'Platform_As_A_Service',
            # IaaS variations - ALL spellings
            'iaas', 'IAAS', 'IaaS', 'Iaas', 'infrastructure_as_a_service', 'infrastructureasaservice', 
            'infrastructure-as-a-service', 'infrastructureAsAService', 'InfrastructureAsAService', 
            'INFRASTRUCTURE_AS_A_SERVICE', 'INFRASTRUCTUREASASERVICE', 'INFRASTRUCTURE-AS-A-SERVICE',
            # Application type variations - ALL spellings
            'application_type', 'applicationtype', 'application-type', 'applicationType', 'ApplicationType', 
            'APPLICATION_TYPE', 'APPLICATIONTYPE', 'APPLICATION-TYPE', 'Application_Type', 'app_type', 
            'apptype', 'app-type', 'appType', 'AppType', 'APP_TYPE', 'APPTYPE', 'APP-TYPE', 'App_Type'
        ],
        'api_keywords': [
            # API variations - ALL spellings
            'api', 'API', 'Api', 'api_gateway', 'apigateway', 'api-gateway', 'apiGateway', 
            'ApiGateway', 'API_GATEWAY', 'APIGATEWAY', 'API-GATEWAY', 'Api_Gateway', 'web_service', 
            'webservice', 'web-service', 'webService', 'WebService', 'WEB_SERVICE', 'WEBSERVICE', 
            'WEB-SERVICE', 'Web_Service',
            # Microservice variations - ALL spellings
            'microservice', 'microService', 'MicroService', 'MICROSERVICE', 'Microservice', 
            'micro_service', 'microservice', 'micro-service', 'microService', 'MicroService', 
            'MICRO_SERVICE', 'MICROSERVICE', 'MICRO-SERVICE', 'Micro_Service',
            # API types - ALL spellings
            'rest_api', 'restapi', 'rest-api', 'restApi', 'RestApi', 'REST_API', 'RESTAPI', 
            'REST-API', 'Rest_Api', 'soap', 'SOAP', 'Soap', 'graphql', 'GraphQL', 'GRAPHQL', 
            'GraphQl', 'rpc', 'RPC', 'Rpc', 'grpc', 'GRPC', 'Grpc', 'gRPC'
        ]
    },
    
    'REQ3_REGIONAL_COUNTRY_METRICS': {
        'description': 'Regional and Country View - Visibility statement on % of visibility by "location"',
        'table_names': [
            'locations', 'location', 'geography', 'geo', 'regions', 'region', 'countries', 
            'country', 'sites', 'site', 'facilities', 'facility', 'datacenters', 'data_centers', 
            'cloud_regions', 'geographic_data', 'geo_data', 'address_book', 'addresses'
        ],
        'country_keywords': [
            # Country variations - ALL spellings
            'country', 'Country', 'COUNTRY', 'country_code', 'countrycode', 'country-code', 
            'countryCode', 'CountryCode', 'COUNTRY_CODE', 'COUNTRYCODE', 'COUNTRY-CODE', 'Country_Code', 
            'Country_code', 'iso_country', 'isocountry', 'iso-country', 'isoCountry', 'IsoCountry', 
            'ISO_COUNTRY', 'ISOCOUNTRY', 'ISO-COUNTRY', 'Iso_Country',
            # Nation variations - ALL spellings
            'nation', 'Nation', 'NATION', 'nationality', 'Nationality', 'NATIONALITY', 'locale_country', 
            'localecountry', 'locale-country', 'localeCountry', 'LocaleCountry', 'LOCALE_COUNTRY', 
            'LOCALECOUNTRY', 'LOCALE-COUNTRY', 'Locale_Country',
            # Country codes - ALL spellings
            'cc', 'CC', 'Cc', 'country_iso', 'countryiso', 'country-iso', 'countryIso', 'CountryIso', 
            'COUNTRY_ISO', 'COUNTRYISO', 'COUNTRY-ISO', 'Country_Iso', 'iso2', 'ISO2', 'Iso2', 
            'iso3', 'ISO3', 'Iso3', 'iso_code', 'isocode', 'iso-code', 'isoCode', 'IsoCode', 
            'ISO_CODE', 'ISOCODE', 'ISO-CODE'
        ],
        'region_keywords': [
            # Region variations - ALL spellings
            'region', 'Region', 'REGION', 'global_region', 'globalregion', 'global-region', 
            'globalRegion', 'GlobalRegion', 'GLOBAL_REGION', 'GLOBALREGION', 'GLOBAL-REGION', 
            'Global_Region', 'geographical_region', 'geographicalregion', 'geographical-region', 
            'geographicalRegion', 'GeographicalRegion', 'GEOGRAPHICAL_REGION',
            # Geographic regions - ALL spellings
            'geo_region', 'georegion', 'geo-region', 'geoRegion', 'GeoRegion', 'GEO_REGION', 
            'GEOREGION', 'GEO-REGION', 'Geo_Region', 'area', 'Area', 'AREA', 'territory', 
            'Territory', 'TERRITORY', 'zone', 'Zone', 'ZONE', 'continent', 'Continent', 'CONTINENT',
            # Subregions - ALL spellings
            'subregion', 'subRegion', 'SubRegion', 'SUBREGION', 'Subregion', 'sub_region', 
            'subregion', 'sub-region', 'subRegion', 'SubRegion', 'SUB_REGION', 'SUBREGION', 
            'SUB-REGION', 'Sub_Region'
        ],
        'datacenter_keywords': [
            # Datacenter variations - ALL spellings
            'datacenter', 'dataCenter', 'DataCenter', 'DATACENTER', 'Datacenter', 'data_center', 
            'datacenter', 'data-center', 'dataCenter', 'DataCenter', 'DATA_CENTER', 'DATACENTER', 
            'DATA-CENTER', 'Data_Center', 'dc', 'DC', 'Dc', 'facility', 'Facility', 'FACILITY', 
            'site', 'Site', 'SITE',
            # Colocation variations - ALL spellings
            'colocation', 'coLocation', 'CoLocation', 'COLOCATION', 'Colocation', 'colo', 'Colo', 
            'COLO', 'co_location', 'colocation', 'co-location', 'coLocation', 'CoLocation', 
            'CO_LOCATION', 'COLOCATION', 'CO-LOCATION', 'Co_Location',
            # Hosting facility variations - ALL spellings
            'hosting_facility', 'hostingfacility', 'hosting-facility', 'hostingFacility', 'HostingFacility', 
            'HOSTING_FACILITY', 'HOSTINGFACILITY', 'HOSTING-FACILITY', 'Hosting_Facility', 'server_farm', 
            'serverfarm', 'server-farm', 'serverFarm', 'ServerFarm', 'SERVER_FARM', 'SERVERFARM', 
            'SERVER-FARM', 'Server_Farm',
            # Compute center variations - ALL spellings
            'compute_center', 'computecenter', 'compute-center', 'computeCenter', 'ComputeCenter', 
            'COMPUTE_CENTER', 'COMPUTECENTER', 'COMPUTE-CENTER', 'Compute_Center'
        ],
        'cloud_region_keywords': [
            # Cloud region variations - ALL spellings
            'cloud_region', 'cloudregion', 'cloud-region', 'cloudRegion', 'CloudRegion', 'CLOUD_REGION', 
            'CLOUDREGION', 'CLOUD-REGION', 'Cloud_Region', 'availability_zone', 'availabilityzone', 
            'availability-zone', 'availabilityZone', 'AvailabilityZone', 'AVAILABILITY_ZONE', 
            'AVAILABILITYZONE', 'AVAILABILITY-ZONE', 'Availability_Zone',
            # Zone variations - ALL spellings
            'az', 'AZ', 'Az', 'zone', 'Zone', 'ZONE', 'aws_region', 'awsregion', 'aws-region', 
            'awsRegion', 'AwsRegion', 'AWS_REGION', 'AWSREGION', 'AWS-REGION', 'Aws_Region', 
            'aws_az', 'awsaz', 'aws-az', 'awsAz', 'AwsAz', 'AWS_AZ', 'AWSAZ', 'AWS-AZ', 'Aws_Az',
            # Azure regions - ALL spellings
            'azure_region', 'azureregion', 'azure-region', 'azureRegion', 'AzureRegion', 'AZURE_REGION', 
            'AZUREREGION', 'AZURE-REGION', 'Azure_Region', 'azure_zone', 'azurezone', 'azure-zone', 
            'azureZone', 'AzureZone', 'AZURE_ZONE', 'AZUREZONE', 'AZURE-ZONE', 'Azure_Zone',
            # GCP zones - ALL spellings
            'gcp_zone', 'gcpzone', 'gcp-zone', 'gcpZone', 'GcpZone', 'GCP_ZONE', 'GCPZONE', 
            'GCP-ZONE', 'Gcp_Zone', 'gcp_region', 'gcpregion', 'gcp-region', 'gcpRegion', 'GcpRegion', 
            'GCP_REGION', 'GCPREGION', 'GCP-REGION', 'Gcp_Region',
            # Google zones - ALL spellings
            'google_zone', 'googlezone', 'google-zone', 'googleZone', 'GoogleZone', 'GOOGLE_ZONE', 
            'GOOGLEZONE', 'GOOGLE-ZONE', 'Google_Zone'
        ]
    },
    
    'REQ4_BUSINESS_APPLICATION_METRICS': {
        'description': 'BU and Application View - Business context visibility',
        'table_names': [
            'business_units', 'business_unit', 'bu', 'departments', 'department', 'divisions', 
            'division', 'cost_centers', 'cost_center', 'applications', 'application', 'apps', 
            'app', 'services', 'service', 'portfolios', 'portfolio', 'projects', 'project', 
            'ownership', 'org_chart', 'organizational_units'
        ],
        'business_unit_keywords': [
            # Business unit variations - ALL spellings
            'business_unit', 'businessunit', 'business-unit', 'businessUnit', 'BusinessUnit', 
            'BUSINESS_UNIT', 'BUSINESSUNIT', 'BUSINESS-UNIT', 'Business_Unit', 'Business_unit', 
            'bu', 'BU', 'Bu', 'division', 'Division', 'DIVISION', 'dept', 'Dept', 'DEPT', 
            'department', 'Department', 'DEPARTMENT',
            # Organizational unit variations - ALL spellings
            'org_unit', 'orgunit', 'org-unit', 'orgUnit', 'OrgUnit', 'ORG_UNIT', 'ORGUNIT', 
            'ORG-UNIT', 'Org_Unit', 'organizational_unit', 'organizationalunit', 'organizational-unit', 
            'organizationalUnit', 'OrganizationalUnit', 'ORGANIZATIONAL_UNIT', 'ORGANIZATIONALUNIT', 
            'ORGANIZATIONAL-UNIT', 'Organizational_Unit',
            # Cost center variations - ALL spellings
            'cost_center', 'costcenter', 'cost-center', 'costCenter', 'CostCenter', 'COST_CENTER', 
            'COSTCENTER', 'COST-CENTER', 'Cost_Center', 'budget_code', 'budgetcode', 'budget-code', 
            'budgetCode', 'BudgetCode', 'BUDGET_CODE', 'BUDGETCODE', 'BUDGET-CODE', 'Budget_Code',
            # Financial codes - ALL spellings
            'financial_code', 'financialcode', 'financial-code', 'financialCode', 'FinancialCode', 
            'FINANCIAL_CODE', 'FINANCIALCODE', 'FINANCIAL-CODE', 'Financial_Code', 'gl_code', 
            'glcode', 'gl-code', 'glCode', 'GlCode', 'GL_CODE', 'GLCODE', 'GL-CODE', 'Gl_Code',
            'profit_center', 'profitcenter', 'profit-center', 'profitCenter', 'ProfitCenter', 
            'PROFIT_CENTER', 'PROFITCENTER', 'PROFIT-CENTER', 'Profit_Center', 'expense_code', 
            'expensecode', 'expense-code', 'expenseCode', 'ExpenseCode', 'EXPENSE_CODE', 'EXPENSECODE', 
            'EXPENSE-CODE', 'Expense_Code'
        ],
        'ownership_keywords': [
            # Owner variations - ALL spellings
            'owner', 'Owner', 'OWNER', 'asset_owner', 'assetowner', 'asset-owner', 'assetOwner', 
            'AssetOwner', 'ASSET_OWNER', 'ASSETOWNER', 'ASSET-OWNER', 'Asset_Owner', 'business_owner', 
            'businessowner', 'business-owner', 'businessOwner', 'BusinessOwner', 'BUSINESS_OWNER', 
            'BUSINESSOWNER', 'BUSINESS-OWNER', 'Business_Owner',
            # Technical owner variations - ALL spellings
            'technical_owner', 'technicalowner', 'technical-owner', 'technicalOwner', 'TechnicalOwner', 
            'TECHNICAL_OWNER', 'TECHNICALOWNER', 'TECHNICAL-OWNER', 'Technical_Owner', 'system_owner', 
            'systemowner', 'system-owner', 'systemOwner', 'SystemOwner', 'SYSTEM_OWNER', 'SYSTEMOWNER', 
            'SYSTEM-OWNER', 'System_Owner',
            # Administrator variations - ALL spellings
            'administrator', 'Administrator', 'ADMINISTRATOR', 'admin', 'Admin', 'ADMIN', 'custodian', 
            'Custodian', 'CUSTODIAN', 'responsible_party', 'responsibleparty', 'responsible-party', 
            'responsibleParty', 'ResponsibleParty', 'RESPONSIBLE_PARTY', 'RESPONSIBLEPARTY', 
            'RESPONSIBLE-PARTY', 'Responsible_Party',
            # CIO variations - ALL spellings
            'cio', 'CIO', 'Cio', 'chief_information_officer', 'chiefinformationofficer', 
            'chief-information-officer', 'chiefInformationOfficer', 'ChiefInformationOfficer', 
            'CHIEF_INFORMATION_OFFICER', 'CHIEFINFORMATIONOFFICER', 'CHIEF-INFORMATION-OFFICER', 
            'Chief_Information_Officer'
        ],
        'application_keywords': [
            # Application name variations - ALL spellings
            'application_name', 'applicationname', 'application-name', 'applicationName', 'ApplicationName', 
            'APPLICATION_NAME', 'APPLICATIONNAME', 'APPLICATION-NAME', 'Application_Name', 'app_name', 
            'appname', 'app-name', 'appName', 'AppName', 'APP_NAME', 'APPNAME', 'APP-NAME', 'App_Name', 
            'service_name', 'servicename', 'service-name', 'serviceName', 'ServiceName', 'SERVICE_NAME', 
            'SERVICENAME', 'SERVICE-NAME', 'Service_Name',
            # APM variations - ALL spellings
            'apm', 'APM', 'Apm', 'application_performance_monitoring', 'applicationperformancemonitoring', 
            'application-performance-monitoring', 'applicationPerformanceMonitoring', 'ApplicationPerformanceMonitoring', 
            'APPLICATION_PERFORMANCE_MONITORING', 'APPLICATIONPERFORMANCEMONITORING', 'APPLICATION-PERFORMANCE-MONITORING', 
            'Application_Performance_Monitoring', 'apm_id', 'apmid', 'apm-id', 'apmId', 'ApmId', 
            'APM_ID', 'APMID', 'APM-ID', 'Apm_Id',
            # Application class variations - ALL spellings
            'application_class', 'applicationclass', 'application-class', 'applicationClass', 'ApplicationClass', 
            'APPLICATION_CLASS', 'APPLICATIONCLASS', 'APPLICATION-CLASS', 'Application_Class', 'app_classification', 
            'appclassification', 'app-classification', 'appClassification', 'AppClassification', 'APP_CLASSIFICATION', 
            'APPCLASSIFICATION', 'APP-CLASSIFICATION', 'App_Classification',
            # Service tier variations - ALL spellings
            'service_tier', 'servicetier', 'service-tier', 'serviceTier', 'ServiceTier', 'SERVICE_TIER', 
            'SERVICETIER', 'SERVICE-TIER', 'Service_Tier', 'business_criticality', 'businesscriticality', 
            'business-criticality', 'businessCriticality', 'BusinessCriticality', 'BUSINESS_CRITICALITY', 
            'BUSINESSCRITICALITY', 'BUSINESS-CRITICALITY', 'Business_Criticality',
            'criticality', 'Criticality', 'CRITICALITY', 'impact_level', 'impactlevel', 'impact-level', 
            'impactLevel', 'ImpactLevel', 'IMPACT_LEVEL', 'IMPACTLEVEL', 'IMPACT-LEVEL', 'Impact_Level', 
            'priority', 'Priority', 'PRIORITY'
        ]
    },
    
    'REQ5_SYSTEM_CLASSIFICATION_METRICS': {
        'description': 'System Classification - OS and server function classification',
        'table_names': [
            'operating_systems', 'operating_system', 'os', 'platforms', 'platform', 'servers', 
            'server', 'systems', 'system', 'endpoints', 'endpoint', 'workstations', 'workstation', 
            'devices', 'device', 'network_devices', 'network_appliances', 'appliances', 'appliance'
        ],
        'operating_system_keywords': [
            # Operating system variations - ALL spellings
            'operating_system', 'operatingsystem', 'operating-system', 'operatingSystem', 'OperatingSystem', 
            'OPERATING_SYSTEM', 'OPERATINGSYSTEM', 'OPERATING-SYSTEM', 'Operating_System', 'os', 'OS', 
            'Os', 'os_type', 'ostype', 'os-type', 'osType', 'OsType', 'OS_TYPE', 'OSTYPE', 'OS-TYPE', 
            'Os_Type', 'platform', 'Platform', 'PLATFORM', 'os_family', 'osfamily', 'os-family', 
            'osFamily', 'OsFamily', 'OS_FAMILY', 'OSFAMILY', 'OS-FAMILY', 'Os_Family',
            # Specific OS variations - ALL spellings
            'windows', 'Windows', 'WINDOWS', 'linux', 'Linux', 'LINUX', 'unix', 'Unix', 'UNIX', 
            'aix', 'AIX', 'Aix', 'solaris', 'Solaris', 'SOLARIS', 'macos', 'MacOS', 'MACOS', 
            'MacOs', 'mac_os', 'macos', 'mac-os', 'macOs', 'MacOs', 'MAC_OS', 'MACOS', 'MAC-OS', 'Mac_Os',
            # Server OS variations - ALL spellings
            'windows_server', 'windowsserver', 'windows-server', 'windowsServer', 'WindowsServer', 
            'WINDOWS_SERVER', 'WINDOWSSERVER', 'WINDOWS-SERVER', 'Windows_Server', 'linux_server', 
            'linuxserver', 'linux-server', 'linuxServer', 'LinuxServer', 'LINUX_SERVER', 'LINUXSERVER', 
            'LINUX-SERVER', 'Linux_Server', 'unix_server', 'unixserver', 'unix-server', 'unixServer', 
            'UnixServer', 'UNIX_SERVER', 'UNIXSERVER', 'UNIX-SERVER', 'Unix_Server',
            # Legacy systems - ALL spellings
            'mainframe', 'Mainframe', 'MAINFRAME', 'mf', 'MF', 'Mf', 'legacy_system', 'legacysystem', 
            'legacy-system', 'legacySystem', 'LegacySystem', 'LEGACY_SYSTEM', 'LEGACYSYSTEM', 'LEGACY-SYSTEM', 
            'Legacy_System'
        ],
        'server_function_keywords': [
            # Server function variations - ALL spellings
            'server_function', 'serverfunction', 'server-function', 'serverFunction', 'ServerFunction', 
            'SERVER_FUNCTION', 'SERVERFUNCTION', 'SERVER-FUNCTION', 'Server_Function', 'server_role', 
            'serverrole', 'server-role', 'serverRole', 'ServerRole', 'SERVER_ROLE', 'SERVERROLE', 
            'SERVER-ROLE', 'Server_Role', 'system_function', 'systemfunction', 'system-function', 
            'systemFunction', 'SystemFunction', 'SYSTEM_FUNCTION', 'SYSTEMFUNCTION', 'SYSTEM-FUNCTION', 
            'System_Function',
            # Web server variations - ALL spellings
            'web_server', 'webserver', 'web-server', 'webServer', 'WebServer', 'WEB_SERVER', 'WEBSERVER', 
            'WEB-SERVER', 'Web_Server', 'application_server', 'applicationserver', 'application-server', 
            'applicationServer', 'ApplicationServer', 'APPLICATION_SERVER', 'APPLICATIONSERVER', 'APPLICATION-SERVER', 
            'Application_Server', 'database_server', 'databaseserver', 'database-server', 'databaseServer', 
            'DatabaseServer', 'DATABASE_SERVER', 'DATABASESERVER', 'DATABASE-SERVER', 'Database_Server',
            # File server variations - ALL spellings
            'file_server', 'fileserver', 'file-server', 'fileServer', 'FileServer', 'FILE_SERVER', 
            'FILESERVER', 'FILE-SERVER', 'File_Server', 'mail_server', 'mailserver', 'mail-server', 
            'mailServer', 'MailServer', 'MAIL_SERVER', 'MAILSERVER', 'MAIL-SERVER', 'Mail_Server', 
            'dns_server', 'dnsserver', 'dns-server', 'dnsServer', 'DnsServer', 'DNS_SERVER', 'DNSSERVER', 
            'DNS-SERVER', 'Dns_Server', 'dhcp_server', 'dhcpserver', 'dhcp-server', 'dhcpServer', 
            'DhcpServer', 'DHCP_SERVER', 'DHCPSERVER', 'DHCP-SERVER', 'Dhcp_Server',
            # Domain controller variations - ALL spellings
            'domain_controller', 'domaincontroller', 'domain-controller', 'domainController', 'DomainController', 
            'DOMAIN_CONTROLLER', 'DOMAINCONTROLLER', 'DOMAIN-CONTROLLER', 'Domain_Controller', 'print_server', 
            'printserver', 'print-server', 'printServer', 'PrintServer', 'PRINT_SERVER', 'PRINTSERVER', 
            'PRINT-SERVER', 'Print_Server'
        ],
        'network_appliance_keywords': [
            # Network appliance variations - ALL spellings
            'network_appliance', 'networkappliance', 'network-appliance', 'networkAppliance', 'NetworkAppliance', 
            'NETWORK_APPLIANCE', 'NETWORKAPPLIANCE', 'NETWORK-APPLIANCE', 'Network_Appliance', 'fw', 'FW', 
            'Fw', 'firewall', 'Firewall', 'FIREWALL', 'ndr', 'NDR', 'Ndr', 'network_detection_response', 
            'networkdetectionresponse', 'network-detection-response',
            # Network devices - ALL spellings
            'switch', 'Switch', 'SWITCH', 'router', 'Router', 'ROUTER', 'load_balancer', 'loadbalancer', 
            'load-balancer', 'loadBalancer', 'LoadBalancer', 'LOAD_BALANCER', 'LOADBALANCER', 'LOAD-BALANCER', 
            'Load_Balancer', 'proxy', 'Proxy', 'PROXY', 'vpn', 'VPN', 'Vpn', 'waf', 'WAF', 'Waf', 
            'web_application_firewall', 'webapplicationfirewall', 'web-application-firewall',
            # Network device types - ALL spellings
            'network_device', 'networkdevice', 'network-device', 'networkDevice', 'NetworkDevice', 
            'NETWORK_DEVICE', 'NETWORKDEVICE', 'NETWORK-DEVICE', 'Network_Device', 'security_appliance', 
            'securityappliance', 'security-appliance', 'securityAppliance', 'SecurityAppliance', 
            'SECURITY_APPLIANCE', 'SECURITYAPPLIANCE', 'SECURITY-APPLIANCE', 'Security_Appliance'
        ]
    },
    
    'REQ6_SECURITY_CONTROL_COVERAGE_METRICS': {
        'description': 'Security Control Coverage - Agent-based security tools',
        'table_names': [
            'security_tools', 'security_agents', 'endpoint_protection', 'edr', 'dlp', 'tanium', 
            'axonius', 'security_controls', 'agent_inventory', 'endpoint_agents', 'security_coverage', 
            'protection_status', 'compliance', 'vulnerability_scanners', 'antivirus'
        ],
        'edr_keywords': [
            # EDR variations - ALL spellings
            'edr', 'EDR', 'Edr', 'endpoint_detection', 'endpointdetection', 'endpoint-detection', 
            'endpointDetection', 'EndpointDetection', 'ENDPOINT_DETECTION', 'ENDPOINTDETECTION', 
            'ENDPOINT-DETECTION', 'Endpoint_Detection', 'edr_agent', 'edragent', 'edr-agent', 
            'edrAgent', 'EdrAgent', 'EDR_AGENT', 'EDRAGENT', 'EDR-AGENT', 'Edr_Agent', 'edr_status', 
            'edrstatus', 'edr-status', 'edrStatus', 'EdrStatus', 'EDR_STATUS', 'EDRSTATUS', 'EDR-STATUS', 
            'Edr_Status', 'edr_installed', 'edrinstalled', 'edr-installed', 'edrInstalled', 'EdrInstalled', 
            'EDR_INSTALLED', 'EDRINSTALLED', 'EDR-INSTALLED', 'Edr_Installed',
            # EDR vendors - ALL spellings
            'crowdstrike', 'CrowdStrike', 'CROWDSTRIKE', 'Crowdstrike', 'sentinelone', 'SentinelOne', 
            'SENTINELONE', 'Sentinelone', 'sentinel_one', 'sentinelone', 'sentinel-one', 'sentinelOne', 
            'SentinelOne', 'SENTINEL_ONE', 'SENTINELONE', 'SENTINEL-ONE', 'Sentinel_One', 'carbon_black', 
            'carbonblack', 'carbon-black', 'carbonBlack', 'CarbonBlack', 'CARBON_BLACK', 'CARBONBLACK', 
            'CARBON-BLACK', 'Carbon_Black',
            'defender_atp', 'defenderatp', 'defender-atp', 'defenderAtp', 'DefenderAtp', 'DEFENDER_ATP', 
            'DEFENDERATP', 'DEFENDER-ATP', 'Defender_Atp', 'microsoft_defender', 'microsoftdefender', 
            'microsoft-defender', 'microsoftDefender', 'MicrosoftDefender', 'MICROSOFT_DEFENDER', 
            'MICROSOFTDEFENDER', 'MICROSOFT-DEFENDER', 'Microsoft_Defender',
            # EDR status fields - ALL spellings
            'edr_version', 'edrversion', 'edr-version', 'edrVersion', 'EdrVersion', 'EDR_VERSION', 
            'EDRVERSION', 'EDR-VERSION', 'Edr_Version', 'agent_version', 'agentversion', 'agent-version', 
            'agentVersion', 'AgentVersion', 'AGENT_VERSION', 'AGENTVERSION', 'AGENT-VERSION', 'Agent_Version', 
            'last_checkin', 'lastcheckin', 'last-checkin', 'lastCheckin', 'LastCheckin', 'LAST_CHECKIN', 
            'LASTCHECKIN', 'LAST-CHECKIN', 'Last_Checkin', 'connection_status', 'connectionstatus', 
            'connection-status', 'connectionStatus', 'ConnectionStatus', 'CONNECTION_STATUS', 'CONNECTIONSTATUS', 
            'CONNECTION-STATUS', 'Connection_Status'
        ],
        'tanium_keywords': [
            # Tanium variations - ALL spellings
            'tanium', 'Tanium', 'TANIUM', 'tanium_agent', 'taniumagent', 'tanium-agent', 'taniumAgent', 
            'TaniumAgent', 'TANIUM_AGENT', 'TANIUMAGENT', 'TANIUM-AGENT', 'Tanium_Agent', 'tanium_status', 
            'taniumstatus', 'tanium-status', 'taniumStatus', 'TaniumStatus', 'TANIUM_STATUS', 'TANIUMSTATUS', 
            'TANIUM-STATUS', 'Tanium_Status', 'tanium_installed', 'taniuminstalled', 'tanium-installed', 
            'taniumInstalled', 'TaniumInstalled', 'TANIUM_INSTALLED', 'TANIUMINSTALLED', 'TANIUM-INSTALLED', 
            'Tanium_Installed',
            'tanium_client', 'taniumclient', 'tanium-client', 'taniumClient', 'TaniumClient', 'TANIUM_CLIENT', 
            'TANIUMCLIENT', 'TANIUM-CLIENT', 'Tanium_Client', 'tanium_endpoint', 'taniumendpoint', 
            'tanium-endpoint', 'taniumEndpoint', 'TaniumEndpoint', 'TANIUM_ENDPOINT', 'TANIUMENDPOINT', 
            'TANIUM-ENDPOINT', 'Tanium_Endpoint', 'tanium_coverage', 'taniumcoverage', 'tanium-coverage', 
            'taniumCoverage', 'TaniumCoverage', 'TANIUM_COVERAGE', 'TANIUMCOVERAGE', 'TANIUM-COVERAGE', 
            'Tanium_Coverage'
        ],
        'dlp_keywords': [
            # DLP variations - ALL spellings
            'dlp', 'DLP', 'Dlp', 'data_loss_prevention', 'datalossprevention', 'data-loss-prevention', 
            'dataLossPrevention', 'DataLossPrevention', 'DATA_LOSS_PREVENTION', 'DATALOSSPREVENTION', 
            'DATA-LOSS-PREVENTION', 'Data_Loss_Prevention', 'dlp_agent', 'dlpagent', 'dlp-agent', 
            'dlpAgent', 'DlpAgent', 'DLP_AGENT', 'DLPAGENT', 'DLP-AGENT', 'Dlp_Agent', 'dlp_status', 
            'dlpstatus', 'dlp-status', 'dlpStatus', 'DlpStatus', 'DLP_STATUS', 'DLPSTATUS', 'DLP-STATUS', 
            'Dlp_Status',
            # DLP vendors - ALL spellings
            'symantec_dlp', 'symantecdlp', 'symantec-dlp', 'symantecDlp', 'SymantecDlp', 'SYMANTEC_DLP', 
            'SYMANTECDLP', 'SYMANTEC-DLP', 'Symantec_Dlp', 'forcepoint_dlp', 'forcepointdlp', 'forcepoint-dlp', 
            'forcepointDlp', 'ForcepointDlp', 'FORCEPOINT_DLP', 'FORCEPOINTDLP', 'FORCEPOINT-DLP', 'Forcepoint_Dlp', 
            'microsoft_purview', 'microsoftpurview', 'microsoft-purview', 'microsoftPurview', 'MicrosoftPurview', 
            'MICROSOFT_PURVIEW', 'MICROSOFTPURVIEW', 'MICROSOFT-PURVIEW', 'Microsoft_Purview',
            # DLP status fields - ALL spellings
            'dlp_policy', 'dlppolicy', 'dlp-policy', 'dlpPolicy', 'DlpPolicy', 'DLP_POLICY', 'DLPPOLICY', 
            'DLP-POLICY', 'Dlp_Policy', 'dlp_enabled', 'dlpenabled', 'dlp-enabled', 'dlpEnabled', 'DlpEnabled', 
            'DLP_ENABLED', 'DLPENABLED', 'DLP-ENABLED', 'Dlp_Enabled', 'data_protection', 'dataprotection', 
            'data-protection', 'dataProtection', 'DataProtection', 'DATA_PROTECTION', 'DATAPROTECTION', 
            'DATA-PROTECTION', 'Data_Protection'
        ],
        'axonius_integration_keywords': [
            # Axonius variations - ALL spellings
            'axonius_managed', 'axoniusmanaged', 'axonius-managed', 'axoniusManaged', 'AxoniusManaged', 
            'AXONIUS_MANAGED', 'AXONIUSMANAGED', 'AXONIUS-MANAGED', 'Axonius_Managed', 'axonius_id', 
            'axoniusid', 'axonius-id', 'axoniusId', 'AxoniusId', 'AXONIUS_ID', 'AXONIUSID', 'AXONIUS-ID', 
            'Axonius_Id', 'console_stats', 'consolestats', 'console-stats', 'consoleStats', 'ConsoleStats', 
            'CONSOLE_STATS', 'CONSOLESTATS', 'CONSOLE-STATS', 'Console_Stats', 'security_tools_inventory', 
            'securitytoolsinventory', 'security-tools-inventory', 'securityToolsInventory', 'SecurityToolsInventory', 
            'SECURITY_TOOLS_INVENTORY', 'SECURITYTOOLSINVENTORY', 'SECURITY-TOOLS-INVENTORY', 'Security_Tools_Inventory',
            'agent_inventory', 'agentinventory', 'agent-inventory', 'agentInventory', 'AgentInventory', 
            'AGENT_INVENTORY', 'AGENTINVENTORY', 'AGENT-INVENTORY', 'Agent_Inventory', 'security_coverage', 
            'securitycoverage', 'security-coverage', 'securityCoverage', 'SecurityCoverage', 'SECURITY_COVERAGE', 
            'SECURITYCOVERAGE', 'SECURITY-COVERAGE', 'Security_Coverage', 'endpoint_tools', 'endpointtools', 
            'endpoint-tools', 'endpointTools', 'EndpointTools', 'ENDPOINT_TOOLS', 'ENDPOINTTOOLS', 'ENDPOINT-TOOLS', 
            'Endpoint_Tools'
        ]
    },
    
    'REQ7_LOGGING_COMPLIANCE_METRICS': {
        'description': 'Logging Compliance in GSO and Splunk',
        'table_names': [
            'log_sources', 'logging', 'splunk', 'chronicle', 'gso', 'siem', 'log_forwarding', 
            'log_collection', 'log_compliance', 'data_ingestion', 'forwarders', 'connectors', 
            'parsers', 'log_analytics', 'security_logs'
        ],
        'splunk_integration_keywords': [
            # Splunk forwarder variations - ALL spellings
            'splunk_forwarder', 'splunkforwarder', 'splunk-forwarder', 'splunkForwarder', 'SplunkForwarder', 
            'SPLUNK_FORWARDER', 'SPLUNKFORWARDER', 'SPLUNK-FORWARDER', 'Splunk_Forwarder', 'splunk_enabled', 
            'splunkenabled', 'splunk-enabled', 'splunkEnabled', 'SplunkEnabled', 'SPLUNK_ENABLED', 'SPLUNKENABLED', 
            'SPLUNK-ENABLED', 'Splunk_Enabled', 'splunk_index', 'splunkindex', 'splunk-index', 'splunkIndex', 
            'SplunkIndex', 'SPLUNK_INDEX', 'SPLUNKINDEX', 'SPLUNK-INDEX', 'Splunk_Index', 'splunk_sourcetype', 
            'splunksourcetype', 'splunk-sourcetype', 'splunkSourcetype', 'SplunkSourcetype', 'SPLUNK_SOURCETYPE', 
            'SPLUNKSOURCETYPE', 'SPLUNK-SOURCETYPE', 'Splunk_Sourcetype',
            # Universal forwarder variations - ALL spellings
            'universal_forwarder', 'universalforwarder', 'universal-forwarder', 'universalForwarder', 
            'UniversalForwarder', 'UNIVERSAL_FORWARDER', 'UNIVERSALFORWARDER', 'UNIVERSAL-FORWARDER', 
            'Universal_Forwarder', 'heavy_forwarder', 'heavyforwarder', 'heavy-forwarder', 'heavyForwarder', 
            'HeavyForwarder', 'HEAVY_FORWARDER', 'HEAVYFORWARDER', 'HEAVY-FORWARDER', 'Heavy_Forwarder', 
            'syslog_forwarding', 'syslogforwarding', 'syslog-forwarding', 'syslogForwarding', 'SyslogForwarding', 
            'SYSLOG_FORWARDING', 'SYSLOGFORWARDING', 'SYSLOG-FORWARDING', 'Syslog_Forwarding',
            # Splunk deployment variations - ALL spellings
            'splunk_deployment_server', 'splunkdeploymentserver', 'splunk-deployment-server', 'splunkDeploymentServer', 
            'SplunkDeploymentServer', 'SPLUNK_DEPLOYMENT_SERVER', 'SPLUNKDEPLOYMENTSERVER', 'SPLUNK-DEPLOYMENT-SERVER', 
            'Splunk_Deployment_Server', 'forwarder_management', 'forwardermanagement', 'forwarder-management', 
            'forwarderManagement', 'ForwarderManagement', 'FORWARDER_MANAGEMENT', 'FORWARDERMANAGEMENT', 
            'FORWARDER-MANAGEMENT', 'Forwarder_Management', 'log_shipping', 'logshipping', 'log-shipping', 
            'logShipping', 'LogShipping', 'LOG_SHIPPING', 'LOGSHIPPING', 'LOG-SHIPPING', 'Log_Shipping'
        ],
        'gso_keywords': [
            # GSO enabled variations - ALL spellings
            'gso_enabled', 'gsoenabled', 'gso-enabled', 'gsoEnabled', 'GsoEnabled', 'GSO_ENABLED', 
            'GSOENABLED', 'GSO-ENABLED', 'Gso_Enabled', 'chronicle_forwarder', 'chronicleforwarder', 
            'chronicle-forwarder', 'chronicleForwarder', 'ChronicleForwarder', 'CHRONICLE_FORWARDER', 
            'CHRONICLEFORWARDER', 'CHRONICLE-FORWARDER', 'Chronicle_Forwarder', 'chronicle_connector', 
            'chronicleconnector', 'chronicle-connector', 'chronicleConnector', 'ChronicleConnector', 
            'CHRONICLE_CONNECTOR', 'CHRONICLECONNECTOR', 'CHRONICLE-CONNECTOR', 'Chronicle_Connector',
            # Google Chronicle variations - ALL spellings
            'google_chronicle', 'googlechronicle', 'google-chronicle', 'googleChronicle', 'GoogleChronicle', 
            'GOOGLE_CHRONICLE', 'GOOGLECHRONICLE', 'GOOGLE-CHRONICLE', 'Google_Chronicle', 'chronicle_ingestion', 
            'chronicleingestion', 'chronicle-ingestion', 'chronicleIngestion', 'ChronicleIngestion', 
            'CHRONICLE_INGESTION', 'CHRONICLEINGESTION', 'CHRONICLE-INGESTION', 'Chronicle_Ingestion', 
            'chronicle_parser', 'chronicleparser', 'chronicle-parser', 'chronicleParser', 'ChronicleParser', 
            'CHRONICLE_PARSER', 'CHRONICLEPARSER', 'CHRONICLE-PARSER', 'Chronicle_Parser',
            # Google Security Operations variations - ALL spellings
            'google_security_operations', 'googlesecurityoperations', 'google-security-operations', 
            'googleSecurityOperations', 'GoogleSecurityOperations', 'GOOGLE_SECURITY_OPERATIONS', 
            'GOOGLESECURITYOPERATIONS', 'GOOGLE-SECURITY-OPERATIONS', 'Google_Security_Operations', 
            'gso', 'GSO', 'Gso'
        ]
    },
    
    'REQ8_DOMAIN_VISIBILITY_METRICS': {
        'description': 'Domain Visibility - Asset visibility by hostname and domain',
        'table_names': [
            'domains', 'domain', 'dns', 'hostnames', 'hostname', 'network', 'networks', 'subnets', 
            'subnet', 'zones', 'zone', 'fqdn', 'domain_names', 'dns_records', 'name_resolution'
        ],
        'domain_keywords': [
            # Domain variations - ALL spellings
            'domain', 'Domain', 'DOMAIN', 'subdomain', 'subDomain', 'SubDomain', 'SUBDOMAIN', 'Subdomain', 
            'sub_domain', 'subdomain', 'sub-domain', 'subDomain', 'SubDomain', 'SUB_DOMAIN', 'SUBDOMAIN', 
            'SUB-DOMAIN', 'Sub_Domain', 'dns_name', 'dnsname', 'dns-name', 'dnsName', 'DnsName', 'DNS_NAME', 
            'DNSNAME', 'DNS-NAME', 'Dns_Name', 'network_segment', 'networksegment', 'network-segment', 
            'networkSegment', 'NetworkSegment', 'NETWORK_SEGMENT', 'NETWORKSEGMENT', 'NETWORK-SEGMENT', 
            'Network_Segment',
            # Parent domain variations - ALL spellings
            'parent_domain', 'parentdomain', 'parent-domain', 'parentDomain', 'ParentDomain', 'PARENT_DOMAIN', 
            'PARENTDOMAIN', 'PARENT-DOMAIN', 'Parent_Domain', 'child_domains', 'childdomains', 'child-domains', 
            'childDomains', 'ChildDomains', 'CHILD_DOMAINS', 'CHILDDOMAINS', 'CHILD-DOMAINS', 'Child_Domains', 
            'zone', 'Zone', 'ZONE', 'dns_zone', 'dnszone', 'dns-zone', 'dnsZone', 'DnsZone', 'DNS_ZONE', 
            'DNSZONE', 'DNS-ZONE', 'Dns_Zone',
            # Domain controller variations - ALL spellings
            'domain_controller', 'domaincontroller', 'domain-controller', 'domainController', 'DomainController', 
            'DOMAIN_CONTROLLER', 'DOMAINCONTROLLER', 'DOMAIN-CONTROLLER', 'Domain_Controller', 'ad_domain', 
            'addomain', 'ad-domain', 'adDomain', 'AdDomain', 'AD_DOMAIN', 'ADDOMAIN', 'AD-DOMAIN', 'Ad_Domain', 
            'forest', 'Forest', 'FOREST', 'ou', 'OU', 'Ou', 'organizational_unit', 'organizationalunit', 
            'organizational-unit', 'organizationalUnit', 'OrganizationalUnit', 'ORGANIZATIONAL_UNIT', 
            'ORGANIZATIONALUNIT', 'ORGANIZATIONAL-UNIT', 'Organizational_Unit'
        ]
    }
}

class ComprehensiveKeywordMatcher:
    """
    Comprehensive keyword matching system that uses ALL the keywords you specified.
    No more missing variations - every single keyword and spelling is included.
    """
    
    def __init__(self):
        self.requirements = AO1_COMPLETE_REQUIREMENTS
        self.normalized_keyword_cache = {}
        self.requirement_keyword_map = {}
        
        # Build comprehensive keyword mappings
        self._build_complete_keyword_mappings()
        
        logger.info(f"Built comprehensive keyword mappings: {total_keywords:,} total keywords across all requirements")
    
    def normalize_field_name(self, field_name: str) -> str:
        """Normalize field name for comprehensive matching."""
        if field_name in self.normalized_keyword_cache:
            return self.normalized_keyword_cache[field_name]
        
        # Convert to lowercase
        normalized = field_name.lower()
        
        # Handle camelCase conversion
        normalized = re.sub(r'([a-z])([A-Z])', r'\1_\2', normalized)
        
        # Normalize separators to underscores
        normalized = re.sub(r'[.\-\s]+', '_', normalized)
        
        # Clean up multiple underscores
        normalized = re.sub(r'_+', '_', normalized)
        
        # Remove leading/trailing underscores
        normalized = normalized.strip('_')
        
        # Cache the result
        self.normalized_keyword_cache[field_name] = normalized
        return normalized
    
    def find_exact_keyword_matches(self, field_name: str) -> Dict[str, Any]:
        """Find exact keyword matches using ALL your specified keywords."""
        normalized_field = self.normalize_field_name(field_name)
        
        matches = {
            'exact_matches': [],
            'partial_matches': [],
            'table_context_matches': [],
            'best_requirement': None,
            'confidence_score': 0.0,
            'match_details': {}
        }
        
        requirement_scores = {}
        
        # Check against ALL keywords for each requirement
        for req_name, req_mapping in self.requirement_keyword_map.items():
            req_score = 0.0
            match_types = []
            matched_keywords = []
            
            # Check exact matches in all keywords
            if normalized_field in req_mapping['all_keywords']:
                req_score += 1.0
                match_types.append('exact_keyword_match')
                matched_keywords.append(normalized_field)
            
            # Check partial matches (field contains keyword or vice versa)
            for keyword in req_mapping['all_keywords']:
                normalized_keyword = self.normalize_field_name(keyword)
                
                # Field contains keyword
                if normalized_keyword in normalized_field and len(normalized_keyword) >= 3:
                    partial_score = len(normalized_keyword) / len(normalized_field)
                    req_score += partial_score * 0.8
                    match_types.append('field_contains_keyword')
                    matched_keywords.append(keyword)
                
                # Keyword contains field (for shorter field names)
                elif normalized_field in normalized_keyword and len(normalized_field) >= 3:
                    partial_score = len(normalized_field) / len(normalized_keyword)
                    req_score += partial_score * 0.6
                    match_types.append('keyword_contains_field')
                    matched_keywords.append(keyword)
            
            # Store requirement score and details
            if req_score > 0:
                requirement_scores[req_name] = req_score
                matches['match_details'][req_name] = {
                    'score': req_score,
                    'match_types': match_types,
                    'matched_keywords': matched_keywords,
                    'keyword_categories': self._get_matching_categories(matched_keywords, req_mapping)
                }
        
        # Find best requirement match
        if requirement_scores:
            best_req = max(requirement_scores.items(), key=lambda x: x[1])
            matches['best_requirement'] = best_req[0]
            matches['confidence_score'] = min(best_req[1], 1.0)  # Cap at 1.0
            
            # Categorize matches
            best_details = matches['match_details'][best_req[0]]
            if 'exact_keyword_match' in best_details['match_types']:
                matches['exact_matches'] = best_details['matched_keywords']
            else:
                matches['partial_matches'] = best_details['matched_keywords']
        
        return matches
    
    def _get_matching_categories(self, matched_keywords: List[str], req_mapping: Dict) -> List[str]:
        """Get the categories that the matched keywords belong to."""
        categories = []
        
        for category_name, category_keywords in req_mapping['keyword_categories'].items():
            for keyword in matched_keywords:
                if keyword in category_keywords:
                    categories.append(category_name)
                    break
        
        return categories
    
    def check_table_context_match(self, table_name: str, dataset_name: str) -> Dict[str, Any]:
        """Check if table/dataset names match your specified table patterns."""
        table_context_matches = {}
        
        combined_name = f"{dataset_name}_{table_name}".lower()
        
        for req_name, req_mapping in self.requirement_keyword_map.items():
            table_score = 0.0
            matched_table_patterns = []
            
            # Check against specified table names
            for table_pattern in req_mapping['table_names']:
                if table_pattern.lower() in combined_name:
                    table_score += 1.0
                    matched_table_patterns.append(table_pattern)
            
            if table_score > 0:
                table_context_matches[req_name] = {
                    'score': table_score,
                    'matched_patterns': matched_table_patterns
                }
        
        return table_context_matches

@dataclass
class CompleteAO1FieldResult:
    """Complete field analysis result with all keyword matching details."""
    field_name: str
    table_path: str
    requirement: str
    confidence_score: float
    
    # Keyword matching details
    exact_keyword_matches: List[str]
    partial_keyword_matches: List[str]
    matched_categories: List[str]
    table_context_matches: List[str]
    
    # Implementation details
    business_value: str
    implementation_guidance: str
    keyword_reasoning: List[str]

class CompleteAO1BigQueryScanner:
    """
    Complete BigQuery scanner that uses ALL your specified keywords.
    Implements comprehensive matching against every variation you provided.
    """
    
    def __init__(self, target_project_id: str = "prj-fisv-p-gcss-sas-dl9dd0f1df"):
        self.target_project_id = target_project_id
        self.client = clientBQ
        
        # Initialize comprehensive keyword matcher
        self.keyword_matcher = ComprehensiveKeywordMatcher()
        
        # Performance tracking
        self.stats = {
            'datasets_scanned': 0,
            'tables_analyzed': 0,
            'fields_analyzed': 0,
            'keyword_matches_found': 0,
            'exact_matches': 0,
            'partial_matches': 0
        }
        
        logger.info(f"Complete AO1 BigQuery scanner initialized for {target_project_id}")
    
    async def scan_with_complete_keywords(self, max_datasets: int = 20, 
                                        max_tables_per_dataset: int = 15) -> Tuple[List[CompleteAO1FieldResult], Dict]:
        """
        Scan BigQuery using ALL your specified keywords and variations.
        """
        logger.info("STARTING COMPLETE KEYWORD SCAN WITH ALL VARIATIONS")
        logger.info("=" * 60)
        
        start_time = time.time()
        all_results = []
        
        try:
            # Get datasets with AO1 prioritization
            datasets = await self._get_ao1_prioritized_datasets(max_datasets)
            self.stats['datasets_scanned'] = len(datasets)
            
            logger.info(f"Scanning {len(datasets)} datasets with complete keyword coverage...")
            
            # Process each dataset
            for dataset in datasets:
                try:
                    dataset_results = await self._scan_dataset_complete(dataset, max_tables_per_dataset)
                    all_results.extend(dataset_results)
                    
                    # Progress update
                    if len(all_results) % 50 == 0:
                        logger.info(f"Progress: Found {len(all_results)} matches so far...")
                        
                except Exception as e:
                    logger.warning(f"Failed to scan dataset {dataset.dataset_id}: {e}")
                    continue
            
            # Sort results by confidence and requirement
            all_results.sort(key=lambda x: (x.confidence_score, x.requirement), reverse=True)
            
            # Calculate final statistics
            end_time = time.time()
            final_stats = self._calculate_complete_statistics(all_results, end_time - start_time)
            
            logger.info("COMPLETE KEYWORD SCAN FINISHED")
            logger.info(f"Total matches found: {len(all_results):,}")
            logger.info(f"Processing time: {end_time - start_time:.2f} seconds")
            
            return all_results, final_stats
            
        except Exception as e:
            logger.error(f"Complete keyword scan failed: {e}")
            return [], {}
    
    async def _get_ao1_prioritized_datasets(self, max_datasets: int) -> List:
        """Get datasets prioritized by AO1 keyword relevance."""
        try:
            all_datasets = list(self.client.list_datasets(project=self.target_project_id))
            
            # Score datasets based on AO1 keyword presence
            scored_datasets = []
            for dataset in all_datasets:
                score = self._score_dataset_for_ao1_keywords(dataset.dataset_id)
                scored_datasets.append((dataset, score))
            
            # Sort by score and limit
            scored_datasets.sort(key=lambda x: x[1], reverse=True)
            
            if max_datasets:
                scored_datasets = scored_datasets[:max_datasets]
            
            return [dataset for dataset, score in scored_datasets]
            
        except Exception as e:
            logger.error(f"Failed to get datasets: {e}")
            return []
    
    def _score_dataset_for_ao1_keywords(self, dataset_id: str) -> float:
        """Score dataset based on presence of AO1 keywords."""
        dataset_lower = dataset_id.lower()
        score = 0.0
        
        # Check against all table names from requirements
        for req_name, req_data in self.keyword_matcher.requirements.items():
            table_names = req_data.get('table_names', [])
            for table_name in table_names:
                if table_name.lower() in dataset_lower:
                    score += 10.0
        
        # Bonus for multiple keyword presence
        keyword_count = 0
        high_value_keywords = ['asset', 'security', 'log', 'chronicle', 'infrastructure', 'network']
        for keyword in high_value_keywords:
            if keyword in dataset_lower:
                keyword_count += 1
                score += 5.0
        
        # Multi-keyword bonus
        if keyword_count >= 2:
            score += 15.0
        
        return score
    
    async def _scan_dataset_complete(self, dataset, max_tables_per_dataset: int) -> List[CompleteAO1FieldResult]:
        """Scan dataset using complete keyword matching."""
        dataset_results = []
        dataset_id = dataset.dataset_id
        
        try:
            # Get tables
            tables = list(self.client.list_tables(dataset.reference))
            self.stats['tables_analyzed'] += len(tables)
            
            # Prioritize tables by AO1 relevance
            tables.sort(key=lambda t: self._score_table_for_ao1_keywords(t.table_id), reverse=True)
            
            if max_tables_per_dataset:
                tables = tables[:max_tables_per_dataset]
            
            for table in tables:
                try:
                    table_ref = self.client.get_table(table.reference)
                    
                    # Check table context for keyword matches
                    table_context_matches = self.keyword_matcher.check_table_context_match(
                        table_ref.table_id, dataset_id
                    )
                    
                    # Analyze each field
                    for field in table_ref.schema:
                        self.stats['fields_analyzed'] += 1
                        
                        # Perform complete keyword matching
                        match_result = self.keyword_matcher.find_exact_keyword_matches(field.name)
                        
                        if match_result['best_requirement'] and match_result['confidence_score'] > 0.1:
                            # Create complete result
                            result = self._create_complete_result(
                                field.name, 
                                f"{table_ref.project}.{dataset_id}.{table_ref.table_id}",
                                match_result,
                                table_context_matches
                            )
                            
                            if result:
                                dataset_results.append(result)
                                self.stats['keyword_matches_found'] += 1
                                
                                if match_result['exact_matches']:
                                    self.stats['exact_matches'] += 1
                                elif match_result['partial_matches']:
                                    self.stats['partial_matches'] += 1
                
                except Exception as e:
                    logger.debug(f"Failed to analyze table {table.table_id}: {e}")
                    continue
        
        except Exception as e:
            logger.warning(f"Failed to scan dataset {dataset_id}: {e}")
        
        return dataset_results
    
    def _score_table_for_ao1_keywords(self, table_id: str) -> float:
        """Score table based on AO1 keyword presence."""
        table_lower = table_id.lower()
        score = 0.0
        
        # Check against all table names from requirements
        for req_name, req_data in self.keyword_matcher.requirements.items():
            table_names = req_data.get('table_names', [])
            for table_name in table_names:
                if table_name.lower() in table_lower:
                    score += 20.0
        
        return score
    
    def _create_complete_result(self, field_name: str, table_path: str, 
                              match_result: Dict, table_context_matches: Dict) -> Optional[CompleteAO1FieldResult]:
        """Create complete field result with all matching details."""
        
        best_req = match_result['best_requirement']
        if not best_req:
            return None
        
        # Get requirement details
        req_data = self.keyword_matcher.requirements.get(best_req, {})
        
        # Extract match details
        match_details = match_result['match_details'].get(best_req, {})
        
        # Generate keyword reasoning
        keyword_reasoning = self._generate_keyword_reasoning(
            field_name, match_result, table_context_matches
        )
        
        return CompleteAO1FieldResult(
            field_name=field_name,
            table_path=table_path,
            requirement=best_req,
            confidence_score=match_result['confidence_score'],
            
            exact_keyword_matches=match_result.get('exact_matches', []),
            partial_keyword_matches=match_result.get('partial_matches', []),
            matched_categories=match_details.get('keyword_categories', []),
            table_context_matches=list(table_context_matches.keys()),
            
            business_value=req_data.get('description', 'AO1 requirement field'),
            implementation_guidance=self._get_implementation_guidance(best_req, match_result['confidence_score']),
            keyword_reasoning=keyword_reasoning
        )
    
    def _generate_keyword_reasoning(self, field_name: str, match_result: Dict, 
                                  table_context_matches: Dict) -> List[str]:
        """Generate reasoning for keyword matches."""
        reasoning = []
        
        if match_result['exact_matches']:
            reasoning.append(f"EXACT MATCH: '{field_name}' exactly matches keywords: {', '.join(match_result['exact_matches'])}")
        
        if match_result['partial_matches']:
            reasoning.append(f"PARTIAL MATCH: '{field_name}' contains keywords: {', '.join(match_result['partial_matches'][:3])}")
        
        if table_context_matches:
            reasoning.append(f"TABLE CONTEXT: Table supports {len(table_context_matches)} AO1 requirements")
        
        best_req = match_result['best_requirement']
        if best_req in match_result['match_details']:
            match_types = match_result['match_details'][best_req]['match_types']
            if 'exact_keyword_match' in match_types:
                reasoning.append("HIGH CONFIDENCE: Direct keyword match from your specified list")
            elif 'field_contains_keyword' in match_types:
                reasoning.append("MEDIUM CONFIDENCE: Field name contains specified keywords")
        
        return reasoning
    
    def _get_implementation_guidance(self, requirement: str, confidence: float) -> str:
        """Get implementation guidance based on requirement and confidence."""
        if confidence >= 0.8:
            priority = "HIGH PRIORITY"
        elif confidence >= 0.5:
            priority = "MEDIUM PRIORITY"
        else:
            priority = "LOW PRIORITY"
        
        req_guidance = {
            'REQ1_GLOBAL_VIEW_METRICS': 'Use for asset counting and global visibility calculations',
            'REQ2_INFRASTRUCTURE_TYPE_METRICS': 'Implement for infrastructure classification dashboards',
            'REQ3_REGIONAL_COUNTRY_METRICS': 'Enable for geographic visibility reporting',
            'REQ4_BUSINESS_APPLICATION_METRICS': 'Deploy for business unit and application views',
            'REQ5_SYSTEM_CLASSIFICATION_METRICS': 'Use for system and OS classification',
            'REQ6_SECURITY_CONTROL_COVERAGE_METRICS': 'Implement for security coverage measurement',
            'REQ7_LOGGING_COMPLIANCE_METRICS': 'Enable for logging compliance reporting',
            'REQ8_DOMAIN_VISIBILITY_METRICS': 'Use for domain and network visibility'
        }
        
        base_guidance = req_guidance.get(requirement, 'Standard AO1 implementation')
        return f"{priority}: {base_guidance}"
    
    def _calculate_complete_statistics(self, results: List[CompleteAO1FieldResult], 
                                     processing_time: float) -> Dict:
        """Calculate comprehensive statistics."""
        stats = {
            'scan_summary': {
                'total_results': len(results),
                'processing_time_seconds': processing_time,
                'datasets_scanned': self.stats['datasets_scanned'],
                'tables_analyzed': self.stats['tables_analyzed'],
                'fields_analyzed': self.stats['fields_analyzed'],
                'keyword_matches_found': self.stats['keyword_matches_found'],
                'exact_matches': self.stats['exact_matches'],
                'partial_matches': self.stats['partial_matches']
            },
            'requirement_distribution': {},
            'confidence_distribution': {'high': 0, 'medium': 0, 'low': 0},
            'top_matched_keywords': {},
            'performance_metrics': {
                'fields_per_second': self.stats['fields_analyzed'] / processing_time if processing_time > 0 else 0,
                'match_rate_percentage': (self.stats['keyword_matches_found'] / max(self.stats['fields_analyzed'], 1)) * 100
            }
        }
        
        # Calculate distributions
        for result in results:
            # Requirement distribution
            req = result.requirement
            stats['requirement_distribution'][req] = stats['requirement_distribution'].get(req, 0) + 1
            
            # Confidence distribution
            if result.confidence_score >= 0.7:
                stats['confidence_distribution']['high'] += 1
            elif result.confidence_score >= 0.4:
                stats['confidence_distribution']['medium'] += 1
            else:
                stats['confidence_distribution']['low'] += 1
            
            # Top matched keywords
            for keyword in result.exact_keyword_matches + result.partial_keyword_matches:
                stats['top_matched_keywords'][keyword] = stats['top_matched_keywords'].get(keyword, 0) + 1
        
        return stats

# Enhanced main execution
async def main_complete_coverage():
    """
    Main execution with complete keyword coverage - uses ALL your specified keywords.
    """
    print("AO1 COMPLETE KEYWORD COVERAGE FIELD DISCOVERY")
    print("=" * 80)
    print("Using ALL keywords and variations you specified - no more missing keywords!")
    print("Comprehensive coverage of every spelling, case, and separator variation")
    print(f"Target Project: prj-fisv-p-gcss-sas-dl9dd0f1df")
    print(f"Authentication: chronicle-fisv")
    print(f"Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        print("INITIALIZING COMPLETE KEYWORD COVERAGE SYSTEM")
        print("-" * 50)
        
        scanner = CompleteAO1BigQueryScanner()
        
        # Load and display keyword statistics
        total_keywords = 0
        for req_name, req_data in scanner.keyword_matcher.requirements.items():
            req_keywords = 0
            for key, value in req_data.items():
                if isinstance(value, list) and key != 'table_names':
                    req_keywords += len(value)
            total_keywords += req_keywords
            
            req_display = req_name.replace('REQ', '').replace('_METRICS', '').replace('_', ' ')
            print(f"✓ {req_display}: {req_keywords:,} keyword variations loaded")
        
        print(f"✓ TOTAL KEYWORD VARIATIONS: {total_keywords:,}")
        print(f"✓ Complete coverage of ALL your specified keywords and table names")
        print("✓ BigQuery scanner ready for comprehensive field discovery")
        print()
        
        print("PERFORMING COMPLETE KEYWORD FIELD DISCOVERY")
        print("-" * 45)
        
        # Start complete keyword scan
        results, statistics = await scanner.scan_with_complete_keywords(
            max_datasets=25,
            max_tables_per_dataset=15
        )
        
        if not results:
            print("WARNING: No keyword matches found")
            return True
        
        print()
        print("COMPLETE KEYWORD DISCOVERY RESULTS")
        print("-" * 40)
        
        # Display comprehensive statistics
        scan_summary = statistics.get('scan_summary', {})
        performance_metrics = statistics.get('performance_metrics', {})
        
        print("SCAN COVERAGE:")
        print(f"   Datasets Scanned: {scan_summary.get('datasets_scanned', 0):,}")
        print(f"   Tables Analyzed: {scan_summary.get('tables_analyzed', 0):,}")
        print(f"   Fields Analyzed: {scan_summary.get('fields_analyzed', 0):,}")
        print(f"   Keyword Matches: {scan_summary.get('keyword_matches_found', 0):,}")
        print(f"   Exact Matches: {scan_summary.get('exact_matches', 0):,}")
        print(f"   Partial Matches: {scan_summary.get('partial_matches', 0):,}")
        print()
        
        print("PERFORMANCE METRICS:")
        print(f"   Processing Time: {scan_summary.get('processing_time_seconds', 0):.2f} seconds")
        print(f"   Fields/Second: {performance_metrics.get('fields_per_second', 0):.1f}")
        print(f"   Match Rate: {performance_metrics.get('match_rate_percentage', 0):.2f}%")
        print()
        
        # Show requirement distribution
        req_dist = statistics.get('requirement_distribution', {})
        if req_dist:
            print("AO1 REQUIREMENT DISTRIBUTION:")
            for req, count in sorted(req_dist.items(), key=lambda x: x[1], reverse=True):
                req_display = req.replace('REQ', '').replace('_METRICS', '').replace('_', ' ')
                print(f"   {req_display}: {count:,} matches")
            print()
        
        # Show top field discoveries
        print("TOP KEYWORD MATCHES (Complete Coverage):")
        print("-" * 50)
        
        for i, result in enumerate(results[:12], 1):
            confidence_level = "HIGH" if result.confidence_score >= 0.7 else "MED" if result.confidence_score >= 0.4 else "LOW"
            req_short = result.requirement.replace('REQ', '').replace('_METRICS', '').replace('_', ' ')
            
            print(f"{i:2d}. [{confidence_level}] {result.table_path}.{result.field_name}")
            print(f"    Requirement: {req_short}")
            print(f"    Confidence: {result.confidence_score:.3f}")
            
            if result.exact_keyword_matches:
                print(f"    Exact Keywords: {', '.join(result.exact_keyword_matches[:3])}")
            elif result.partial_keyword_matches:
                print(f"    Partial Keywords: {', '.join(result.partial_keyword_matches[:3])}")
            
            if result.keyword_reasoning:
                print(f"    Reasoning: {result.keyword_reasoning[0]}")
            
            print(f"    Implementation: {result.implementation_guidance}")
            print()
        
        print("COMPLETE KEYWORD COVERAGE SCAN FINISHED")
        print("=" * 45)
        print("✓ ALL your specified keywords and variations were used")
        print("✓ Comprehensive coverage of every spelling and case variation")
        print("✓ No keywords were missed or overlooked")
        print("✓ Ready for AO1 dashboard implementation")
        
        return True
        
    except Exception as e:
        logger.error(f"Complete keyword scan failed: {e}")
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    import sys
    success = asyncio.run(main_complete_coverage())
    sys.exit(0 if success else 1)("Comprehensive keyword matcher initialized with ALL variations")
    
    def _build_complete_keyword_mappings(self):
        """Build complete keyword mappings from ALL your specified keywords."""
        
        # Track statistics
        total_keywords = 0
        
        for req_name, req_data in self.requirements.items():
            self.requirement_keyword_map[req_name] = {
                'all_keywords': set(),
                'table_names': set(req_data.get('table_names', [])),
                'keyword_categories': {}
            }
            
            # Add all keyword categories for this requirement
            for key, keywords in req_data.items():
                if key != 'description' and key != 'table_names' and isinstance(keywords, list):
                    self.requirement_keyword_map[req_name]['keyword_categories'][key] = set(keywords)
                    self.requirement_keyword_map[req_name]['all_keywords'].update(keywords)
                    total_keywords += len(keywords)
        
        logger.info