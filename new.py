return SequenceMatcher(None, struct1, struct2).ratio()

    def _graph_similarity(self, tokens1, tokens2):
        if not tokens1 or not tokens2:
            return 0.0
        
        connected_pairs = 0
        total_pairs = 0
        
        for token1 in tokens1:
            for token2 in tokens2:
                total_pairs += 1
                for domain_graph in self.context_graphs.values():
                    if isinstance(domain_graph, dict):
                        if token1 in domain_graph and token2 in domain_graph[token1]:
                            connected_pairs += 1
                            break
                    elif NETWORKX_AVAILABLE and hasattr(domain_graph, 'has_edge'):
                        if domain_graph.has_node(token1) and domain_graph.has_node(token2):
                            if domain_graph.has_edge(token1, token2):
                                connected_pairs += 1
                                break
        
        return connected_pairs / total_pairs if total_pairs > 0 else 0.0

    def _generate_match_evidence(self, comp1, comp2, similarities):
        evidence = []
        
        if similarities['token_overlap'] > 0.3:
            common_tokens = set(comp1['tokens']).intersection(set(comp2['tokens']))
            if common_tokens:
                evidence.append(f"Strong token overlap: {', '.join(list(common_tokens)[:3])}")
        
        if similarities['pattern_match'] > 0.4:
            common_patterns = set(comp1['patterns']).intersection(set(comp2['patterns']))
            if common_patterns:
                evidence.append(f"Pattern alignment: {', '.join(list(common_patterns)[:2])}")
        
        if similarities['domain_alignment'] > 0.3:
            common_domains = set(comp1['domains']).intersection(set(comp2['domains']))
            if common_domains:
                evidence.append(f"Domain correlation: {', '.join(list(common_domains)[:2])}")
        
        if similarities['embedding_cosine'] > 0.5:
            evidence.append("High semantic vector similarity")
        
        if similarities['abbreviation'] > 0.7:
            evidence.append("Abbreviation expansion match")
        
        if similarities.get('ml_enhanced', 0) > 0.6:
            evidence.append("Machine learning enhanced match")
        
        if similarities['structural'] > 0.8:
            evidence.append("Strong structural similarity")
        
        if similarities.get('ngram', 0) > 0.4:
            evidence.append("N-gram pattern match")
        
        return evidence

    def ultra_intelligent_match(self, target, candidates, threshold=0.25):
        results = []
        
        logger.info(f"🎯 Performing ultra-intelligent matching for '{target}' against {len(candidates)} candidates")
        
        for candidate in candidates:
            similarity_data = self.calculate_multidimensional_similarity(target, candidate)
            
            if similarity_data['final_score'] >= threshold:
                results.append({
                    'candidate': candidate,
                    'confidence': similarity_data['final_score'],
                    'evidence': similarity_data['match_evidence'],
                    'breakdown': similarity_data['component_scores'],
                    'match_type': similarity_data['match_type'],
                    'ml_confidence': similarity_data.get('confidence', 0.0)
                })
        
        results = sorted(results, key=lambda x: (-x['confidence'], -x['ml_confidence']))
        
        logger.info(f"✅ Found {len(results)} matches above threshold {threshold}")
        return results

class DataDrivenMetricsRecommender:
    def __init__(self, mapping_results_file: str = "security_mapping_results.json", original_data_file: str = "new.json"):
        logger.info("🚀 Initializing Data-Driven Metrics Recommender with advanced analytics...")
        
        self.mapping_results_file = mapping_results_file
        self.original_data_file = original_data_file
        self.mapping_data = None
        self.original_data = None
        
        self.nlp_matcher = UltraIntelligentNLPMatcher()
        
        if SKLEARN_AVAILABLE:
            self.data_analyzer = pd.DataFrame()
            logger.info("✅ Pandas data analysis ready")
        
        if SCIPY_AVAILABLE:
            self.stats_engine = stats
            logger.info("✅ SciPy statistical analysis ready")
        
        self._initialize_ao1_requirements()
        self._initialize_recommendation_engine()
        self.load_results()
        
        logger.info("🎯 Data-Driven Metrics Recommender fully initialized!")

    def _initialize_ao1_requirements(self):
        logger.info("📋 Loading official AO1 Log Visibility Measurement requirements...")
        
        self.ao1_visibility_requirements = {
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
        
        self.ao1_metric_requirements = self.ao1_visibility_requirements
        
        logger.info(f"✅ Loaded {sum(len(reqs) for reqs in self.ao1_visibility_requirements.values())} official AO1 visibility requirements")

    def _initialize_recommendation_engine(self):
        logger.info("🧠 Initializing advanced recommendation engine...")
        
        self.recommendation_stats = {
            'total_recommendations': 0,
            'high_confidence_matches': 0,
            'ultra_semantic_matches': 0,
            'ml_enhanced_matches': 0
        }
        
        self.scoring_weights = {
            'base_feasibility': 0.25,
            'intelligence_score': 0.20,
            'table_size_score': 0.15,
            'domain_relevance': 0.15,
            'pattern_quality': 0.10,
            'semantic_strength': 0.10,
            'ml_confidence': 0.05
        }
        
        self.priority_matrix = {
            'CRITICAL': 1.0,
            'HIGH': 0.8,
            'MEDIUM': 0.6,
            'LOW': 0.4
        }
        
        self.complexity_factors = {
            'LOW': 1.0,
            'MEDIUM': 0.85,
            'HIGH': 0.7,
            'VERY_HIGH': 0.5
        }
        
        logger.info("✅ Advanced recommendation engine initialized")

    def __getattr__(self, name):
        if name == 'ao1_metric_requirements':
            return getattr(self, 'ao1_visibility_requirements', {})
        if name == 'ao1_visibility_requirements':
            return {}
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def load_results(self):
        try:
            logger.info(f"📂 Loading mapping results from {self.mapping_results_file}")
            with open(self.mapping_results_file, 'r') as f:
                self.mapping_data = json.load(f)
            logger.info("✅ Mapping results loaded successfully")
            
            logger.info(f"📂 Loading original data from {self.original_data_file}")
            with open(self.original_data_file, 'r') as f:
                self.original_data = json.load(f)
            logger.info("✅ Original data loaded successfully")
            
            self._validate_data_structure()
            
        except FileNotFoundError as e:
            logger.error(f"❌ File not found: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON format: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Error loading data: {e}")
            raise

    def _validate_data_structure(self):
        required_keys = ['matches', 'log_types']
        
        if 'matches' not in self.mapping_data:
            logger.warning("⚠️ 'matches' key not found in mapping data")
        elif 'log_types' not in self.mapping_data['matches']:
            logger.warning("⚠️ 'log_types' key not found in matches")
        
        if 'datasets' not in self.original_data:
            logger.warning("⚠️ 'datasets' key not found in original data")
        
        logger.info("✅ Data structure validation completed")

    def get_table_size_info(self, dataset_id: str, table_id: str) -> Dict[str, Any]:
        if ('datasets' in self.original_data and 
            dataset_id in self.original_data['datasets'] and
            'tables' in self.original_data['datasets'][dataset_id] and
            table_id in self.original_data['datasets'][dataset_id]['tables']):
            
            table_info = self.original_data['datasets'][dataset_id]['tables'][table_id]
            
            size_info = {
                'row_count': 0,
                'size_bytes': 0,
                'size_category': 'unknown',
                'data_quality_score': 0.0,
                'freshness_score': 0.0
            }
            
            if 'table_info' in table_info:
                table_metadata = table_info['table_info']
                
                for field in ['num_rows', 'row_count', 'rows', 'numRows', 'rowCount', 'record_count']:
                    if field in table_metadata and table_metadata[field] is not None:
                        try:
                            size_info['row_count'] = int(table_metadata[field])
                            break
                        except (ValueError, TypeError):
                            continue
                
                for field in ['num_bytes', 'size_bytes', 'bytes', 'numBytes', 'sizeBytes', 'table_size']:
                    if field in table_metadata and table_metadata[field] is not None:
                        try:
                            size_info['size_bytes'] = int(table_metadata[field])
                            break
                        except (ValueError, TypeError):
                            continue
            
            if size_info['row_count'] == 0 and 'sample_data' in table_info:
                sample_count = len(table_info['sample_data']) if table_info['sample_data'] else 0
                if sample_count > 0:
                    estimation_factor = min(max(sample_count * 100, 1000), 1000000)
                    size_info['row_count'] = estimation_factor
            
            if size_info['row_count'] > 1000000000:
                size_info['size_category'] = 'ultra_massive'
                size_info['priority_score'] = 10
            elif size_info['row_count'] > 100000000:
                size_info['size_category'] = 'massive'
                size_info['priority_score'] = 9
            elif size_info['row_count'] > 10000000:
                size_info['size_category'] = 'very_large'
                size_info['priority_score'] = 8
            elif size_info['row_count'] > 1000000:
                size_info['size_category'] = 'large'
                size_info['priority_score'] = 7
            elif size_info['row_count'] > 100000:
                size_info['size_category'] = 'medium_large'
                size_info['priority_score'] = 6
            elif size_info['row_count'] > 10000:
                size_info['size_category'] = 'medium'
                size_info['priority_score'] = 5
            elif size_info['row_count'] > 1000:
                size_info['size_category'] = 'small_medium'
                size_info['priority_score'] = 4
            elif size_info['row_count'] > 100:
                size_info['size_category'] = 'small'
                size_info['priority_score'] = 3
            elif size_info['row_count'] > 10:
                size_info['size_category'] = 'very_small'
                size_info['priority_score'] = 2
            elif size_info['row_count'] > 0:
                size_info['size_category'] = 'minimal'
                size_info['priority_score'] = 1
            else:
                size_info['size_category'] = 'empty'
                size_info['priority_score'] = 0
            
            size_info['data_quality_score'] = self._calculate_data_quality_score(table_info)
            size_info['freshness_score'] = self._calculate_freshness_score(table_info)
            
            return size_info
        
        return {
            'row_count': 0, 'size_bytes': 0, 'size_category': 'unknown', 
            'priority_score': 0, 'data_quality_score': 0.0, 'freshness_score': 0.0
        }

    def _calculate_data_quality_score(self, table_info):
        quality_score = 0.0
        
        if 'schema' in table_info or 'columns' in table_info:
            quality_score += 0.3
        
        if 'sample_data' in table_info and table_info['sample_data']:
            quality_score += 0.2
            
            sample_size = len(table_info['sample_data'])
            if sample_size > 10:
                quality_score += 0.1
            if sample_size > 100:
                quality_score += 0.1
        
        if 'table_info' in table_info:
            metadata_fields = len(table_info['table_info'])
            quality_score += min(metadata_fields / 20, 0.3)
        
        return min(quality_score, 1.0)

    def _calculate_freshness_score(self, table_info):
        freshness_score = 0.5
        
        timestamp_fields = [
            'last_modified', 'lastModified', 'modified_time', 'modifiedTime',
            'created_time', 'createdTime', 'creation_time', 'updated_at'
        ]
        
        if 'table_info' in table_info:
            for field in timestamp_fields:
                if field in table_info['table_info']:
                    try:
                        timestamp_value = table_info['table_info'][field]
                        if timestamp_value:
                            freshness_score = 0.8
                            break
                    except:
                        continue
        
        return freshness_score

    def get_available_data_sources(self) -> Dict[str, Dict[str, Any]]:
        logger.info("🔍 Analyzing available data sources...")
        
        available_sources = {}
        
        for role, requirements in self.mapping_data['matches']['log_types'].items():
            available_sources[role] = {}
            
            for log_type, matches in requirements.items():
                if matches['table_names']:
                    tables_info = []
                    
                    for table_match in matches['table_names']:
                        table_columns = []
                        for column_match in matches['column_names']:
                            if (column_match['dataset_id'] == table_match['dataset_id'] and 
                                column_match['table_id'] == table_match['table_id']):
                                table_columns.append(column_match['name'])
                        
                        size_info = self.get_table_size_info(table_match['dataset_id'], table_match['table_id'])
                        
                        tables_info.append({
                            'table_name': table_match['name'],
                            'dataset': table_match['dataset_id'],
                            'table_id': table_match['table_id'],
                            'columns': table_columns,
                            'column_count': len(table_columns),
                            'row_count': size_info['row_count'],
                            'size_bytes': size_info['size_bytes'],
                            'size_category': size_info['size_category'],
                            'size_priority_score': size_info['priority_score'],
                            'data_quality_score': size_info['data_quality_score'],
                            'freshness_score': size_info['freshness_score']
                        })
                    
                    tables_info.sort(key=lambda x: (
                        x['size_priority_score'], 
                        x['data_quality_score'], 
                        x['freshness_score'],
                        x['column_count']
                    ), reverse=True)
                    
                    available_sources[role][log_type] = {
                        'tables': tables_info,
                        'total_columns': len(matches['column_names']),
                        'total_tables': len(tables_info),
                        'max_rows': max((t['row_count'] for t in tables_info), default=0),
                        'avg_quality': statistics.mean([t['data_quality_score'] for t in tables_info]) if tables_info else 0
                    }
        
        logger.info(f"✅ Analyzed {sum(len(sources) for sources in available_sources.values())} data source categories")
        return available_sources

    def map_metrics_to_data(self) -> Dict[str, List[Dict[str, Any]]]:
        logger.info("🎯 Performing ultra-intelligent AO1 metrics mapping...")
        
        available_sources = self.get_available_data_sources()
        ao1_visibility_recommendations = {}
        
        total_mappings = 0
        
        for role, log_types in available_sources.items():
            ao1_visibility_recommendations[role] = []
            
            if role in self.ao1_visibility_requirements:
                ao1_requirements = self.ao1_visibility_requirements[role]
                
                for log_type, data_info in log_types.items():
                    for table_info in data_info['tables']:
                        table_columns = [col.lower() for col in table_info['columns']]
                        
                        for visibility_factor, factor_info in ao1_requirements.items():
                            
                            visibility_matches = []
                            
                            for synonym in factor_info['synonyms']:
                                synonym_results = self.nlp_matcher.ultra_intelligent_match(
                                    synonym, table_columns, threshold=0.15
                                )
                                for result in synonym_results:
                                    visibility_matches.append({
                                        'matched_column': result['candidate'],
                                        'ao1_requirement': visibility_factor,
                                        'match_term': synonym,
                                        'match_type': result['match_type'],
                                        'confidence': result['confidence'],
                                        'evidence': result['evidence'],
                                        'ml_confidence': result.get('ml_confidence', 0.0)
                                    })
                            
                            for partial in factor_info['partial_matches']:
                                for column in table_columns:
                                    if partial.lower() in column.lower():
                                        match_quality = len(partial) / len(column)
                                        confidence = 0.7 + (match_quality * 0.2)
                                        
                                        visibility_matches.append({
                                            'matched_column': column,
                                            'ao1_requirement': visibility_factor,
                                            'match_term': partial,
                                            'match_type': 'partial',
                                            'confidence': confidence,
                                            'evidence': ['partial_word_match'],
                                            'ml_confidence': match_quality
                                        })
                            
                            if visibility_matches:
                                feasibility_components = self._calculate_advanced_feasibility(
                                    visibility_matches, table_info, factor_info
                                )
                                
                                intelligence_score = self._calculate_comprehensive_intelligence_score(
                                    visibility_matches, table_info, factor_info
                                )
                                
                                recommendation = {
                                    'ao1_visibility_factor': visibility_factor,
                                    'log_type': log_type,
                                    'table_name': table_info['table_name'],
                                    'dataset': table_info['dataset'],
                                    'table_id': table_info['table_id'],
                                    'row_count': table_info['row_count'],
                                    'size_category': table_info['size_category'],
                                    'size_priority_score': table_info['size_priority_score'],
                                    'data_quality_score': table_info['data_quality_score'],
                                    'freshness_score': table_info['freshness_score'],
                                    'column_count': table_info['column_count'],
                                    'feasibility_score': feasibility_components['final_score'],
                                    'intelligence_score': intelligence_score,
                                    'confidence_score': feasibility_components['confidence'],
                                    'description': factor_info['description'],
                                    'visibility_query': factor_info['visibility_query'],
                                    'business_impact': factor_info['business_impact'],
                                    'threat_context': factor_info['threat_context'],
                                    'priority': factor_info.get('priority', 'MEDIUM'),
                                    'complexity': factor_info.get('complexity', 'MEDIUM'),
                                    'matched_columns': visibility_matches,
                                    'column_match_count': len(visibility_matches),
                                    'implementation_difficulty': self._determine_implementation_difficulty(
                                        feasibility_components['final_score'], intelligence_score, factor_info
                                    ),
                                    'recommendation_rank': self._calculate_recommendation_rank(
                                        feasibility_components, intelligence_score, table_info, factor_info
                                    )
                                }
                                
                                ao1_visibility_recommendations[role].append(recommendation)
                                total_mappings += 1
        
        logger.info(f"✅ Generated {total_mappings} intelligent AO1 visibility recommendations")
        return ao1_visibility_recommendations

    def _calculate_advanced_feasibility(self, visibility_matches, table_info, factor_info):
        components = {
            'base_confidence': 0.0,
            'size_factor': 0.0,
            'quality_factor': 0.0,
            'coverage_factor': 0.0,
            'ml_factor': 0.0,
            'priority_factor': 0.0
        }
        
        if visibility_matches:
            components['base_confidence'] = statistics.mean([m['confidence'] for m in visibility_matches])
        
        size_score = table_info['size_priority_score']
        components['size_factor'] = min(size_score / 10, 1.0)
        
        components['quality_factor'] = table_info['data_quality_score']
        
        components['coverage_factor'] = min(len(visibility_matches) / 5, 1.0)
        
        ml_confidences = [m.get('ml_confidence', 0) for m in visibility_matches]
        if ml_confidences:
            components['ml_factor'] = statistics.mean(ml_confidences)
        
        priority = factor_info.get('priority', 'MEDIUM')
        components['priority_factor'] = self.priority_matrix.get(priority, 0.6)
        
        complexity = factor_info.get('complexity', 'MEDIUM')
        complexity_multiplier = self.complexity_factors.get(complexity, 0.85)
        
        weighted_score = (
            components['base_confidence'] * 0.25 +
            components['size_factor'] * 0.20 +
            components['quality_factor'] * 0.15 +
            components['coverage_factor'] * 0.15 +
            components['ml_factor'] * 0.15 +
            components['priority_factor'] * 0.10
        ) * complexity_multiplier
        
        components['final_score'] = min(weighted_score, 1.0)
        components['confidence'] = self._calculate_feasibility_confidence(components)
        
        return components

    def _calculate_comprehensive_intelligence_score(self, visibility_matches, table_info, factor_info):
        intelligence_components = []
        
        if visibility_matches:
            ultra_semantic_count = sum(1 for m in visibility_matches if m['match_type'] == 'ultra_semantic')
            semantic_count = sum(1 for m in visibility_matches if m['match_type'] == 'semantic')
            
            match_intelligence = (ultra_semantic_count * 1.0 + semantic_count * 0.7) / len(visibility_matches)
            intelligence_components.append(match_intelligence)
        
        data_intelligence = (
            min(table_info['size_priority_score'] / 10, 1.0) * 0.4 +
            table_info['data_quality_score'] * 0.3 +
            table_info['freshness_score'] * 0.3
        )
        intelligence_components.append(data_intelligence)
        
        priority = factor_info.get('priority', 'MEDIUM')
        domain_intelligence = self.priority_matrix.get(priority, 0.6)
        intelligence_components.append(domain_intelligence)
        
        coverage_intelligence = min(len(visibility_matches) / 3, 1.0)
        intelligence_components.append(coverage_intelligence)
        
        if intelligence_components:
            final_intelligence = statistics.mean(intelligence_components)
        else:
            final_intelligence = 0.0
        
        return round(final_intelligence, 3)

    def _calculate_feasibility_confidence(self, components):
        confidence_factors = []
        
        if components['base_confidence'] > 0:
            confidence_factors.append(components['base_confidence'])
        
        data_confidence = (components['size_factor'] + components['quality_factor']) / 2
        confidence_factors.append(data_confidence)
        
        confidence_factors.append(components['coverage_factor'])
        
        if components['ml_factor'] > 0:
            confidence_factors.append(components['ml_factor'])
        
        return statistics.mean(confidence_factors) if confidence_factors else 0.0

    def _determine_implementation_difficulty(self, feasibility_score, intelligence_score, factor_info):
        complexity = factor_info.get('complexity', 'MEDIUM')
        priority = factor_info.get('priority', 'MEDIUM')
        
        combined_score = (feasibility_score + intelligence_score) / 2
        
        if combined_score > 0.8 and complexity == 'LOW':
            return 'AO1_Trivial'
        elif combined_score > 0.7 and complexity in ['LOW', 'MEDIUM']:
            return 'AO1_Easy'
        elif combined_score > 0.5:
            return 'AO1_Medium'
        elif combined_score > 0.3:
            return 'AO1_Hard'
        else:
            return 'AO1_Very_Hard'

    def _calculate_recommendation_rank(self, feasibility_components, intelligence_score, table_info, factor_info):
        ranking_factors = {
            'feasibility': feasibility_components['final_score'] * 0.25,
            'intelligence': intelligence_score * 0.20,
            'priority': self.priority_matrix.get(factor_info.get('priority', 'MEDIUM'), 0.6) * 0.20,
            'data_size': min(table_info['size_priority_score'] / 10, 1.0) * 0.15,
            'data_quality': table_info['data_quality_score'] * 0.10,
            'complexity_bonus': (1.0 - self.complexity_factors.get(factor_info.get('complexity', 'MEDIUM'), 0.85)) * 0.10
        }
        
        final_rank = sum(ranking_factors.values())
        return round(final_rank, 3)

    def prioritize_recommendations(self, recommendations: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        logger.info("🏆 Prioritizing recommendations with advanced analytics...")
        
        all_recommendations = []
        
        for role, role_recommendations in recommendations.items():
            for rec in role_recommendations:
                rec['role'] = role
                all_recommendations.append(rec)
        
        prioritized = sorted(all_recommendations, key=lambda x: (
            -x.get('recommendation_rank', 0),
            -x['feasibility_score'],
            -x.get('intelligence_score', 0),
            -x['size_priority_score'],
            -x.get('confidence_score', 0),
            x['implementation_difficulty']
        ))
        
        self.recommendation_stats.update({
            'total_recommendations': len(prioritized),
            'high_confidence_matches': len([r for r in prioritized if r.get('confidence_score', 0) > 0.8]),
            'ultra_semantic_matches': len([r for r in prioritized if any(m['match_type'] == 'ultra_semantic' for m in r['matched_columns'])]),
            'ml_enhanced_matches': len([r for r in prioritized if any(m.get('ml_confidence', 0) > 0.5 for m in r['matched_columns'])])
        })
        
        logger.info(f"✅ Prioritized {len(prioritized)} recommendations with advanced scoring")
        return prioritized

    def generate_implementation_guide(self, recommendations: List[Dict[str, Any]]) -> str:
        guide = []
        guide.append("=" * 100)
        guide.append("🎯 ULTRA-INTELLIGENT AO1 VISIBILITY METRICS IMPLEMENTATION GUIDE")
        guide.append("=" * 100)
        guide.append("")
        
        guide.append("🧠 ADVANCED AI ANALYSIS SUMMARY:")
        guide.append("-" * 70)
        
        difficulty_counts = Counter(r['implementation_difficulty'] for r in recommendations)
        priority_counts = Counter(r.get('priority', 'UNKNOWN') for r in recommendations)
        
        guide.append(f"📊 Total AO1 Visibility Metrics Discovered: {len(recommendations)}")
        guide.append(f"🚀 Ultra-Semantic AI Matches: {self.recommendation_stats['ultra_semantic_matches']}")
        guide.append(f"🤖 ML-Enhanced Matches: {self.recommendation_stats['ml_enhanced_matches']}")
        guide.append(f"🎯 High-Confidence Matches: {self.recommendation_stats['high_confidence_matches']}")
        guide.append("")
        
        guide.append("📈 IMPLEMENTATION DIFFICULTY DISTRIBUTION:")
        for difficulty, count in difficulty_counts.most_common():
            percentage = (count / len(recommendations)) * 100
            display_name = difficulty.replace('AO1_', '')
            guide.append(f"   • {display_name}: {count} metrics ({percentage:.1f}%)")
        guide.append("")
        
        guide.append("⚡ PRIORITY DISTRIBUTION:")
        for priority, count in priority_counts.most_common():
            percentage = (count / len(recommendations)) * 100
            guide.append(f"   • {priority}: {count} metrics ({percentage:.1f}%)")
        guide.append("")
        
        if recommendations:
            avg_feasibility = statistics.mean(r['feasibility_score'] for r in recommendations)
            avg_intelligence = statistics.mean(r.get('intelligence_score', 0) for r in recommendations)
            avg_confidence = statistics.mean(r.get('confidence_score', 0) for r in recommendations)
            
            guide.append("🎯 ADVANCED SCORING STATISTICS:")
            guide.append(f"   • Average Feasibility Score: {avg_feasibility:.3f}")
            guide.append(f"   • Average Intelligence Score: {avg_intelligence:.3f}")
            guide.append(f"   • Average Confidence Score: {avg_confidence:.3f}")
            guide.append("")
        
        for difficulty in ['AO1_Trivial', 'AO1_Easy', 'AO1_Medium', 'AO1_Hard']:
            difficulty_recs = [r for r in recommendations if r['implementation_difficulty'] == difficulty]
            if difficulty_recs:
                display_name = difficulty.replace('AO1_', '').upper()
                guide.append(f"🎯 {display_name} IMPLEMENTATION METRICS:")
                guide.append("-" * 80)
                
                for i, rec in enumerate(difficulty_recs[:10], 1):
                    guide.append(f"{i}. 🎯 {rec['ao1_visibility_factor']} ({rec['role']} - {rec['log_type']})")
                    guide.append(f"   📊 Data Source: {rec['dataset']}.{rec['table_name']}")
                    guide.append(f"   📈 Table Statistics: {rec['row_count']:,} rows ({rec['size_category']})")
                    guide.append(f"   🎯 AO1 Description: {rec['description']}")
                    guide.append(f"   💡 Visibility Query: {rec['visibility_query']}")
                    guide.append(f"   💼 Business Impact: {rec['business_impact']}")
                    guide.append(f"   ⚠️  Threat Context: {rec['threat_context']}")
                    guide.append(f"   🏆 Priority Level: {rec.get('priority', 'MEDIUM')}")
                    
                    guide.append(f"   🤖 AI Scores: Feasibility={rec['feasibility_score']:.3f}, Intelligence={rec.get('intelligence_score', 0):.3f}, Confidence={rec.get('confidence_score', 0):.3f}")
                    guide.append(f"   🏅 Recommendation Rank: {rec.get('recommendation_rank', 0):.3f}")
                    
                    if rec['matched_columns']:
                        guide.append("   🔑 Ultra-Intelligent Column Matches:")
                        for col_match in rec['matched_columns'][:5]:
                            match_indicator = {
                                'ultra_semantic': '🧠🚀',
                                'semantic': '🧠',
                                'partial': '📝',
                                'synonym': '🎯'
                            }.get(col_match['match_type'], '❓')
                            
                            confidence_pct = int(col_match['confidence'] * 100)
                            ml_conf = col_match.get('ml_confidence', 0)
                            evidence_str = ', '.join(col_match['evidence'][:2]) if col_match['evidence'] else 'direct_match'
                            
                            guide.append(f"     {match_indicator} '{col_match['matched_column']}' ← {col_match['match_term']}")
                            guide.append(f"       📊 Match: {confidence_pct}% confidence, ML: {ml_conf:.2f}, Evidence: {evidence_str}")
                    
                    guide.append("")
                
                if len(difficulty_recs) > 10:
                    guide.append(f"   ... and {len(difficulty_recs) - 10} more {display_name.lower()} metrics available")
                    guide.append("")
        
        guide.append("🚀 ADVANCED IMPLEMENTATION RECOMMENDATIONS:")
        guide.append("-" * 80)
        
        top_by_feasibility = sorted(recommendations, key=lambda x: x['feasibility_score'], reverse=True)[:3]
        top_by_intelligence = sorted(recommendations, key=lambda x: x.get('intelligence_score', 0), reverse=True)[:3]
        top_by_priority = [r for r in recommendations if r.get('priority') == 'CRITICAL'][:3]
        
        if top_by_feasibility:
            guide.append("🏆 TOP 3 BY FEASIBILITY:")
            for i, rec in enumerate(top_by_feasibility, 1):
                guide.append(f"   {i}. {rec['ao1_visibility_factor']} (Score: {rec['feasibility_score']:.3f})")
        
        if top_by_intelligence:
            guide.append("🧠 TOP 3 BY AI INTELLIGENCE:")
            for i, rec in enumerate(top_by_intelligence, 1):
                guide.append(f"   {i}. {rec['ao1_visibility_factor']} (Score: {rec.get('intelligence_score', 0):.3f})")
        
        if top_by_priority:
            guide.append("⚡ CRITICAL PRIORITY METRICS:")
            for i, rec in enumerate(top_by_priority, 1):
                guide.append(f"   {i}. {rec['ao1_visibility_factor']} (Priority: {rec.get('priority')})")
        
        guide.append("")
        guide.append("📊 For detailed analysis and interactive visualizations, see the generated JSON report.")
        
        return "\n".join(guide)

    def generate_quick_start_recommendations(self) -> str:
        logger.info("⚡ Generating ultra-intelligent quick start recommendations...")
        
        recommendations = self.map_metrics_to_data()
        prioritized = self.prioritize_recommendations(recommendations)
        
        quick_start = []
        quick_start.append("🚀 ULTRA-INTELLIGENT AO1 VISIBILITY QUICK START")
        quick_start.append("=" * 100)
        quick_start.append("")
        
        trivial_wins = [r for r in prioritized if r['implementation_difficulty'] == 'AO1_Trivial'][:3]
        easy_wins = [r for r in prioritized if r['implementation_difficulty'] == 'AO1_Easy'][:5]
        high_impact = [r for r in prioritized if r.get('priority') in ['CRITICAL', 'HIGH']][:5]
        
        if trivial_wins:
            quick_start.append("⚡ INSTANT IMPLEMENTATION - ZERO COMPLEXITY:")
            quick_start.append("-" * 70)
            
            for i, rec in enumerate(trivial_wins, 1):
                quick_start.append(f"{i}. 🚀 DEPLOY NOW: {rec['ao1_visibility_factor']}")
                quick_start.append(f"   📊 Data Source: {rec['dataset']}.{rec['table_name']}")
                quick_start.append(f"   📈 Scale: {rec['row_count']:,} rows ({rec['size_category']})")
                quick_start.append(f"   🎯 Measures: {rec['description']}")
                quick_start.append(f"   💡 Key Question: {rec['visibility_query']}")
                quick_start.append(f"   💼 Business Value: {rec['business_impact']}")
                quick_start.append(f"   ⚠️  Security Context: {rec['threat_context']}")
                quick_start.append(f"   🤖 AI Confidence: {rec['feasibility_score']:.3f} | Intelligence: {rec.get('intelligence_score', 0):.3f}")
                
                if rec['matched_columns']:
                    top_matches = sorted(rec['matched_columns'], key=lambda x: x['confidence'], reverse=True)[:3]
                    quick_start.append("   🔑 Key Columns:")
                    for match in top_matches:
                        conf_pct = int(match['confidence'] * 100)
                        match_type = match['match_type'].replace('_', ' ').title()
                        quick_start.append(f"     • '{match['matched_column']}' ({match_type}, {conf_pct}% confidence)")
                
                quick_start.append("")
        
        if easy_wins:
            quick_start.append("⚡ EASY WINS - HIGH IMPACT, LOW EFFORT:")
            quick_start.append("-" * 70)
            
            for i, rec in enumerate(easy_wins, 1):
                quick_start.append(f"{i}. ⚡ IMPLEMENT: {rec['ao1_visibility_factor']}")
                quick_start.append(f"   📊 Source: {rec['dataset']}.{rec['table_name']} ({rec['row_count']:,} rows)")
                quick_start.append(f"   🎯 Capability: {rec['description']}")
                quick_start.append(f"   💼 Impact: {rec['business_impact']}")
                quick_start.append(f"   🏆 Priority: {rec.get('priority', 'MEDIUM')} | Rank: {rec.get('recommendation_rank', 0):.3f}")
                
                ultra_matches = [m for m in rec['matched_columns'] if m['match_type'] == 'ultra_semantic']
                if ultra_matches:
                    quick_start.append(f"   🧠🚀 Ultra-AI Matches: {len(ultra_matches)} detected")
                
                quick_start.append("")
        
        if high_impact and not (set(high_impact) <= set(trivial_wins + easy_wins)):
            quick_start.append("🎯 CRITICAL PRIORITY METRICS:")
            quick_start.append("-" * 70)
            
            critical_not_easy = [r for r in high_impact if r not in trivial_wins + easy_wins][:3]
            for i, rec in enumerate(critical_not_easy, 1):
                quick_start.append(f"{i}. 🎯 PRIORITY: {rec['ao1_visibility_factor']}")
                quick_start.append(f"   💼 Impact: {rec['business_impact']}")
                quick_start.append(f"   ⚠️  Threat: {rec['threat_context']}")
                quick_start.append(f"   🤖 Feasibility: {rec['feasibility_score']:.3f} | Difficulty: {rec['implementation_difficulty'].replace('AO1_', '')}")
                quick_start.append("")
        
        if not trivial_wins and not easy_wins:
            quick_start.append("⚠️  NO TRIVIAL OR EASY IMPLEMENTATIONS FOUND")
            quick_start.append("🔧 RECOMMENDED ACTIONS:")
            quick_start.append("   • Review data source integration and column naming conventions")
            quick_start.append("   • Consider data enrichment or additional log source integration")
            quick_start.append("   • Focus on medium-complexity options with highest business impact")
            quick_start.append("")
            
            medium_recs = [r for r in prioritized if r['implementation_difficulty'] == 'AO1_Medium'][:3]
            if medium_recs:
                quick_start.append("🔧 BEST MEDIUM-COMPLEXITY OPTIONS:")
                for i, rec in enumerate(medium_recs, 1):
                    quick_start.append(f"   {i}. {rec['ao1_visibility_factor']} (Feasibility: {rec['feasibility_score']:.3f})")
        
        quick_start.append("📊 ADVANCED ANALYTICS SUMMARY:")
        quick_start.append("-" * 70)
        quick_start.append(f"🎯 Total Metrics Analyzed: {len(prioritized)}")
        quick_start.append(f"🧠 Ultra-Semantic Matches: {self.recommendation_stats['ultra_semantic_matches']}")
        quick_start.append(f"🤖 ML-Enhanced Matches: {self.recommendation_stats['ml_enhanced_matches']}")
        quick_start.append(f"🏆 High-Confidence Matches: {self.recommendation_stats['high_confidence_matches']}")
        
        if prioritized:
            avg_feasibility = statistics.mean(r['feasibility_score'] for r in prioritized)
            avg_intelligence = statistics.mean(r.get('intelligence_score', 0) for r in prioritized)
            quick_start.append(f"📈 Average Feasibility Score: {avg_feasibility:.3f}")
            quick_start.append(f"🧠 Average Intelligence Score: {avg_intelligence:.3f}")
        
        logger.info("✅ Ultra-intelligent quick start recommendations generated")
        return "\n".join(quick_start)

    def save_recommendations(self, output_file: str = "ultra_intelligent_ao1_visibility_recommendations.json"):
        logger.info(f"💾 Saving ultra-intelligent recommendations to {output_file}...")
        
        recommendations = self.map_metrics_to_data()
        prioritized = self.prioritize_recommendations(recommendations)
        
        analytics = self._generate_comprehensive_analytics(prioritized)
        
        output_data = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'version': '2.0.0',
                'analysis_type': 'ultra_intelligent_ao1_visibility',
                'total_processing_time': time.time(),
                'libraries_used': self._get_library_status()
            },
            'executive_summary': {
                'total_metrics_discovered': len(prioritized),
                'implementation_ready': len([r for r in prioritized if r['implementation_difficulty'] in ['AO1_Trivial', 'AO1_Easy']]),
                'high_priority_metrics': len([r for r in prioritized if r.get('priority') in ['CRITICAL', 'HIGH']]),
                'average_feasibility_score': statistics.mean([r['feasibility_score'] for r in prioritized]) if prioritized else 0,
                'average_intelligence_score': statistics.mean([r.get('intelligence_score', 0) for r in prioritized]) if prioritized else 0,
                'recommendation_confidence': statistics.mean([r.get('confidence_score', 0) for r in prioritized]) if prioritized else 0
            },
            'advanced_analytics': analytics,
            'ai_analysis_summary': {
                'ultra_semantic_matches': self.recommendation_stats['ultra_semantic_matches'],
                'ml_enhanced_matches': self.recommendation_stats['ml_enhanced_matches'],
                'high_confidence_matches': self.recommendation_stats['high_confidence_matches'],
                'nlp_engine_performance': {
                    'cache_size': len(self.nlp_matcher.similarity_cache),
                    'security_taxonomy_domains': len(self.nlp_matcher.security_taxonomy),
                    'semantic_embeddings': len(self.nlp_matcher.semantic_embeddings),
                    'abbreviation_mappings': len(self.nlp_matcher.abbreviation_engine),
                    'ml_models_active': SKLEARN_AVAILABLE
                }
            },
            'implementation_roadmap': self._generate_implementation_roadmap(prioritized),
            'recommendations_by_role': recommendations,
            'prioritized_recommendations': prioritized,
            'data_quality_assessment': self._assess_data_quality(recommendations),
            'risk_assessment': self._generate_risk_assessment(prioritized)
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, default=str, ensure_ascii=False)
            
            logger.info(f"✅ Ultra-intelligent AO1 visibility recommendations saved to {output_file}")
            
            self._log_summary_statistics(output_data)
            
        except Exception as e:
            logger.error(f"❌ Failed to save recommendations: {e}")
            raise

    def _generate_comprehensive_analytics(self, prioritized):
        analytics = {}
        
        if not prioritized:
            return analytics
        
        analytics['distributions'] = {
            'by_difficulty': dict(Counter(r['implementation_difficulty'] for r in prioritized)),
            'by_priority': dict(Counter(r.get('priority', 'UNKNOWN') for r in prioritized)),
            'by_role': dict(Counter(r['role'] for r in prioritized)),
            'by_size_category': dict(Counter(r['size_category'] for r in prioritized))
        }
        
        feasibility_scores = [r['feasibility_score'] for r in prioritized]
        intelligence_scores = [r.get('intelligence_score', 0) for r in prioritized]
        
        analytics['score_statistics'] = {
            'feasibility': {
                'mean': statistics.mean(feasibility_scores),
                'median': statistics.median(feasibility_scores),
                'std_dev': statistics.stdev(feasibility_scores) if len(feasibility_scores) > 1 else 0,
                'min': min(feasibility_scores),
                'max': max(feasibility_scores)
            },
            'intelligence': {
                'mean': statistics.mean(intelligence_scores),
                'median': statistics.median(intelligence_scores),
                'std_dev': statistics.stdev(intelligence_scores) if len(intelligence_scores) > 1 else 0,
                'min': min(intelligence_scores),
                'max': max(intelligence_scores)
            }
        }
        
        analytics['top_performers'] = {
            'highest_feasibility': sorted(prioritized, key=lambda x: x['feasibility_score'], reverse=True)[:5],
            'highest_intelligence': sorted(prioritized, key=lambda x: x.get('intelligence_score', 0), reverse=True)[:5],
            'best_overall_rank': sorted(prioritized, key=lambda x: x.get('recommendation_rank', 0), reverse=True)[:5]
        }
        
        data_sources = {}
        for rec in prioritized:
            source_key = f"{rec['dataset']}.{rec['table_name']}"
            if source_key not in data_sources:
                data_sources[source_key] = {
                    'metrics_count': 0,
                    'avg_feasibility': 0,
                    'total_rows': rec['row_count'],
                    'size_category': rec['size_category']
                }
            data_sources[source_key]['metrics_count'] += 1
        
        for source_key in data_sources:
            relevant_recs = [r for r in prioritized if f"{r['dataset']}.{r['table_name']}" == source_key]
            data_sources[source_key]['avg_feasibility'] = statistics.mean([r['feasibility_score'] for r in relevant_recs])
        
        analytics['data_source_analysis'] = data_sources
        
        return analytics

    def _generate_implementation_roadmap(self, prioritized):
        roadmap = {
            'phase_1_immediate': [],
            'phase_2_short_term': [],
            'phase_3_medium_term': [],
            'phase_4_long_term': []
        }
        
        phase_1_candidates = [
            r for r in prioritized 
            if r['implementation_difficulty'] == 'AO1_Trivial' and r.get('priority') in ['CRITICAL', 'HIGH']
        ][:5]
        roadmap['phase_1_immediate'] = [
            {
                'metric': r['ao1_visibility_factor'],
                'role': r['role'],
                'feasibility': r['feasibility_score'],
                'business_impact': r['business_impact'],
                'estimated_effort': 'Few hours to 1 day'
            } for r in phase_1_candidates
        ]
        
        phase_2_candidates = [
            r for r in prioritized 
            if r['implementation_difficulty'] == 'AO1_Easy'
        ][:8]
        roadmap['phase_2_short_term'] = [
            {
                'metric': r['ao1_visibility_factor'],
                'role': r['role'],
                'feasibility': r['feasibility_score'],
                'business_impact': r['business_impact'],
                'estimated_effort': '1-3 days'
            } for r in phase_2_candidates
        ]
        
        phase_3_candidates = [
            r for r in prioritized 
            if r['implementation_difficulty'] == 'AO1_Medium' and r.get('priority') in ['CRITICAL', 'HIGH']
        ][:10]
        roadmap['phase_3_medium_term'] = [
            {
                'metric': r['ao1_visibility_factor'],
                'role': r['role'],
                'feasibility': r['feasibility_score'],
                'business_impact': r['business_impact'],
                'estimated_effort': '1-2 weeks'
            } for r in phase_3_candidates
        ]
        
        phase_4_candidates = [
            r for r in prioritized 
            if r['implementation_difficulty'] in ['AO1_Hard', 'AO1_Very_Hard']
        ][:5]
        roadmap['phase_4_long_term'] = [
            {
                'metric': r['ao1_visibility_factor'],
                'role': r['role'],
                'feasibility': r['feasibility_score'],
                'business_impact': r['business_impact'],
                'estimated_effort': '1+ months'
            } for r in phase_4_candidates
        ]
        
        return roadmap

    def _assess_data_quality(self, recommendations):
        all_tables = {}
        
        for role_recs in recommendations.values():
            for rec in role_recs:
                table_key = f"{rec['dataset']}.{rec['table_name']}"
                if table_key not in all_tables:
                    all_tables[table_key] = {
                        'row_count': rec['row_count'],
                        'size_category': rec['size_category'],
                        'data_quality_score': rec.get('data_quality_score', 0.0),
                        'freshness_score': rec.get('freshness_score', 0.0),
                        'column_count': rec.get('column_count', 0),
                        'metrics_supported': 0
                    }
                all_tables[table_key]['metrics_supported'] += 1
        
        quality_scores = [t['data_quality_score'] for t in all_tables.values()]
        freshness_scores = [t['freshness_score'] for t in all_tables.values()]
        
        return {
            'total_tables_analyzed': len(all_tables),
            'average_data_quality': statistics.mean(quality_scores) if quality_scores else 0,
            'average_freshness': statistics.mean(freshness_scores) if freshness_scores else 0,
            'high_quality_tables': len([t for t in all_tables.values() if t['data_quality_score'] > 0.7]),
            'large_tables': len([t for t in all_tables.values() if t['size_category'] in ['large', 'very_large', 'massive', 'ultra_massive']]),
            'multi_metric_tables': len([t for t in all_tables.values() if t['metrics_supported'] > 1])
        }

    def _generate_risk_assessment(self, prioritized):
        risks = {
            'data_availability_risk': 'LOW',
            'implementation_complexity_risk': 'LOW',
            'data_quality_risk': 'LOW',
            'resource_requirement_risk': 'LOW'
        }
        
        empty_tables = len([r for r in prioritized if r['size_category'] in ['empty', 'minimal']])
        if empty_tables > len(prioritized) * 0.3:
            risks['data_availability_risk'] = 'HIGH'
        elif empty_tables > len(prioritized) * 0.15:
            risks['data_availability_risk'] = 'MEDIUM'
        
        hard_implementations = len([r for r in prioritized if r['implementation_difficulty'] in ['AO1_Hard', 'AO1_Very_Hard']])
        if hard_implementations > len(prioritized) * 0.5:
            risks['implementation_complexity_risk'] = 'HIGH'
        elif hard_implementations > len(prioritized) * 0.25:
            risks['implementation_complexity_risk'] = 'MEDIUM'
        
        low_quality = len([r for r in prioritized if r.get('data_quality_score', 0) < 0.5])
        if low_quality > len(prioritized) * 0.4:
            risks['data_quality_risk'] = 'HIGH'
        elif low_quality > len(prioritized) * 0.2:
            risks['data_quality_risk'] = 'MEDIUM'
        
        high_resource = len([r for r in prioritized if r.get('priority') == 'CRITICAL' and r['implementation_difficulty'] in ['AO1_Medium', 'AO1_Hard']])
        if high_resource > 10:
            risks['resource_requirement_risk'] = 'HIGH'
        elif high_resource > 5:
            risks['resource_requirement_risk'] = 'MEDIUM'
        
        return risks

    def _get_library_status(self):
        return {
            'sklearn': SKLEARN_AVAILABLE,
            'networkx': NETWORKX_AVAILABLE,
            'nltk': NLTK_AVAILABLE,
            'spacy': SPACY_AVAILABLE,
            'scipy': SCIPY_AVAILABLE,
            'plotly': PLOTLY_AVAILABLE,
            'matplotlib': MATPLOTLIB_AVAILABLE,
            'textdistance': TEXTDISTANCE_AVAILABLE,
            'fuzzywuzzy': FUZZYWUZZY_AVAILABLE
        }

    def _log_summary_statistics(self, output_data):
        logger.info("📊 ULTRA-INTELLIGENT ANALYSIS COMPLETE:")
        logger.info(f"   🎯 Total Metrics: {output_data['executive_summary']['total_metrics_discovered']}")
        logger.info(f"   ⚡ Ready to Implement: {output_data['executive_summary']['implementation_ready']}")
        logger.info(f"   🏆 High Priority: {output_data['executive_summary']['high_priority_metrics']}")
        logger.info(f"   🧠 Ultra-Semantic: {output_data['ai_analysis_summary']['ultra_semantic_matches']}")
        logger.info(f"   🤖 ML-Enhanced: {output_data['ai_analysis_summary']['ml_enhanced_matches']}")
        logger.info(f"   📈 Avg Feasibility: {output_data['executive_summary']['average_feasibility_score']:.3f}")
        logger.info(f"   🎯 Avg Intelligence: {output_data['executive_summary']['average_intelligence_score']:.3f}")

    def generate_advanced_visualizations(self, recommendations):
        if not PLOTLY_AVAILABLE:
            logger.warning("⚠️ Plotly not available for advanced visualizations")
            return None
        
        logger.info("📊 Generating advanced visualizations...")
        
        try:
            prioritized = self.prioritize_recommendations(recommendations)
            
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Feasibility Distribution', 'Implementation Difficulty', 
                              'Priority vs Feasibility', 'Data Source Analysis'),
                specs=[[{"type": "histogram"}, {"type": "pie"}],
                       [{"type": "scatter"}, {"type": "bar"}]]
            )
            
            feasibility_scores = [r['feasibility_score'] for r in prioritized]
            fig.add_trace(
                go.Histogram(x=feasibility_scores, name="Feasibility Scores", showlegend=False),
                row=1, col=1
            )
            
            difficulty_counts = Counter(r['implementation_difficulty'] for r in prioritized)
            fig.add_trace(
                go.Pie(labels=list(difficulty_counts.keys()), values=list(difficulty_counts.values()),
                       name="Difficulties", showlegend=False),
                row=1, col=2
            )
            
            priority_map = {'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
            x_vals = [priority_map.get(r.get('priority', 'MEDIUM'), 2) for r in prioritized]
            y_vals = [r['feasibility_score'] for r in prioritized]
            fig.add_trace(
                go.Scatter(x=x_vals, y=y_vals, mode='markers', name="Priority vs Feasibility", showlegend=False),
                row=2, col=1
            )
            
            data_sources = {}
            for rec in prioritized:
                source = rec['dataset']
                data_sources[source] = data_sources.get(source, 0) + 1
            
            fig.add_trace(
                go.Bar(x=list(data_sources.keys()), y=list(data_sources.values()),
                       name="Data Sources", showlegend=False),
                row=2, col=2
            )
            
            fig.update_layout(
                title_text="Ultra-Intelligent AO1 Visibility Metrics Analysis Dashboard",
                height=800
            )
            
            fig.write_html("ao1_visibility_dashboard.html")
            logger.info("✅ Advanced visualizations saved to ao1_visibility_dashboard.html")
            
            return fig
            
        except Exception as e:
            logger.error(f"❌ Failed to generate visualizations: {e}")
            return None

if __name__ == "__main__":
    try:
        logger.info("🚀 Initializing Ultra-Intelligent AO1 Visibility Analytics System...")
        
        analyzer = DataDrivenMetricsRecommender()
        
        logger.info("🔍 Performing ultra-intelligent analysis...")
        
        quick_start = analyzer.generate_quick_start_recommendations()
        print(quick_start)
        print("\n" + "="*100 + "\n")
        
        recommendations = analyzer.map_metrics_to_data()
        prioritized = analyzer.prioritize_recommendations(recommendations)
        full_guide = analyzer.generate_implementation_guide(prioritized)
        print(full_guide)
        
        analyzer.save_recommendations()
        
        analyzer.generate_advanced_visualizations(recommendations)
        
        logger.info("✅ Ultra-intelligent AO1 visibility analysis complete!")
        logger.info("📊 Check generated files for detailed analysis and visualizations")
        
    except KeyboardInterrupt:
        logger.info("⏹️ Analysis interrupted by user")
    except Exception as e:
        logger.error(f"❌ Critical error in ultra-intelligent analysis: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise
                'import json
import pandas as pd
import numpy as np
from collections import defaultdict, Counter, deque
from typing import Dict, List, Any, Set, Tuple, Optional, Union
import logging
import re
import math
import statistics
from difflib import SequenceMatcher
import unicodedata
import itertools
from functools import lru_cache, reduce
import hashlib
import pickle
import time
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

try:
    from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.cluster import KMeans, DBSCAN
    from sklearn.decomposition import PCA, TruncatedSVD
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    from sklearn.ensemble import RandomForestClassifier, IsolationForest
    from sklearn.neural_network import MLPClassifier
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False

try:
    import nltk
    from nltk.corpus import stopwords, wordnet
    from nltk.tokenize import word_tokenize, sent_tokenize
    from nltk.stem import PorterStemmer, WordNetLemmatizer
    from nltk.util import ngrams
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

try:
    from scipy import stats
    from scipy.spatial.distance import jaccard, hamming, euclidean
    from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
    from scipy.optimize import minimize
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    import seaborn as sns
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    from textdistance import levenshtein, jaro_winkler, cosine, jaccard as td_jaccard
    TEXTDISTANCE_AVAILABLE = True
except ImportError:
    TEXTDISTANCE_AVAILABLE = False

try:
    import fuzzywuzzy
    from fuzzywuzzy import fuzz, process
    FUZZYWUZZY_AVAILABLE = True
except ImportError:
    FUZZYWUZZY_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UltraIntelligentNLPMatcher:
    def __init__(self):
        logger.info("🚀 Initializing Ultra-Intelligent NLP Matcher with advanced ML capabilities...")
        
        self.security_taxonomy = self._build_comprehensive_security_taxonomy()
        self.semantic_embeddings = self._build_advanced_embeddings()
        self.pattern_library = self._build_pattern_library()
        self.abbreviation_engine = self._build_abbreviation_engine()
        self.context_graphs = self._build_context_graphs()
        self.linguistic_rules = self._build_linguistic_rules()
        self.domain_vectors = self._build_domain_vectors()
        self.similarity_cache = {}
        
        if SKLEARN_AVAILABLE:
            self.tfidf_vectorizer = TfidfVectorizer(ngram_range=(1, 3), max_features=10000)
            self.count_vectorizer = CountVectorizer(ngram_range=(1, 2))
            self.scaler = StandardScaler()
            self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
            logger.info("✅ Scikit-learn components initialized")
        
        if NLTK_AVAILABLE:
            try:
                self.stemmer = PorterStemmer()
                self.lemmatizer = WordNetLemmatizer()
                self.stop_words = set(stopwords.words('english'))
                logger.info("✅ NLTK components initialized")
            except:
                logger.warning("⚠️ NLTK data not found, downloading...")
                nltk.download('stopwords', quiet=True)
                nltk.download('wordnet', quiet=True)
                nltk.download('punkt', quiet=True)
        
        if NETWORKX_AVAILABLE:
            self.semantic_graph = self._build_semantic_network()
            logger.info("✅ NetworkX semantic graph initialized")
        
        self._initialize_ml_models()
        
        logger.info("🎯 Ultra-Intelligent NLP Matcher ready with all advanced capabilities!")

    def _build_comprehensive_security_taxonomy(self):
        return {
            'network': {
                'layer1_physical': ['fiber', 'copper', 'wireless', 'cable', 'coax', 'ethernet_cable', 'network_cable'],
                'layer2_datalink': ['mac', 'ethernet', 'switch', 'vlan', 'trunk', 'spanning_tree', 'arp', 'frame', 'bridge'],
                'layer3_network': ['ip', 'routing', 'subnet', 'gateway', 'router', 'ospf', 'bgp', 'rip', 'packet', 'icmp'],
                'layer4_transport': ['tcp', 'udp', 'port', 'socket', 'connection', 'session', 'flow', 'segment'],
                'layer5_session': ['session', 'dialog', 'connection_management', 'checkpoint', 'recovery'],
                'layer6_presentation': ['encryption', 'compression', 'translation', 'format', 'syntax'],
                'layer7_application': ['http', 'https', 'ftp', 'smtp', 'dns', 'dhcp', 'snmp', 'ssh', 'telnet', 'api'],
                'topology': ['source', 'destination', 'origin', 'target', 'from', 'to', 'via', 'through', 'path', 'route'],
                'metrics': ['bandwidth', 'throughput', 'latency', 'jitter', 'packet_loss', 'utilization', 'capacity'],
                'protocols': ['icmp', 'igmp', 'gre', 'ipsec', 'vpn', 'mpls', 'vxlan', 'geneve', 'nvgre'],
                'wireless': ['wifi', 'wlan', '802.11', 'ssid', 'bssid', 'wpa', 'wep', 'radius', 'bluetooth', '5g', 'lte'],
                'sdn': ['openflow', 'controller', 'southbound', 'northbound', 'programmable', 'centralized'],
                'monitoring': ['snmp', 'netflow', 'sflow', 'ipfix', 'packet_capture', 'mirroring', 'span']
            },
            'security': {
                'threats': ['malware', 'virus', 'trojan', 'worm', 'ransomware', 'spyware', 'adware', 'rootkit', 'botnet', 'apt', 'rat', 'backdoor'],
                'attacks': ['dos', 'ddos', 'mitm', 'phishing', 'spoofing', 'hijacking', 'injection', 'overflow', 'poisoning', 'replay', 'brute_force'],
                'vulnerabilities': ['cve', 'exploit', 'zero_day', 'buffer_overflow', 'sql_injection', 'xss', 'csrf', 'lfi', 'rfi', 'xxe', 'deserialization'],
                'controls': ['firewall', 'ids', 'ips', 'waf', 'proxy', 'antivirus', 'edr', 'dlp', 'sandbox', 'honeypot', 'deception'],
                'cryptography': ['encryption', 'decryption', 'hash', 'digest', 'signature', 'certificate', 'pki', 'ssl', 'tls', 'aes', 'rsa'],
                'analysis': ['forensics', 'incident', 'investigation', 'attribution', 'indicators', 'ioc', 'ttp', 'mitre', 'diamond_model'],
                'intelligence': ['threat_intel', 'feeds', 'reputation', 'blacklist', 'whitelist', 'indicators', 'yara', 'sigma', 'stix', 'taxii'],
                'frameworks': ['nist', 'iso27001', 'cis', 'owasp', 'sans', 'mitre_attack', 'kill_chain', 'diamond_model'],
                'governance': ['policy', 'compliance', 'audit', 'risk', 'assessment', 'framework', 'standard', 'regulation']
            },
            'identity': {
                'authentication': ['login', 'logon', 'signin', 'sso', 'mfa', '2fa', 'biometric', 'token', 'password', 'pin', 'otp'],
                'authorization': ['permission', 'privilege', 'access', 'role', 'group', 'policy', 'acl', 'rbac', 'abac', 'pbac'],
                'provisioning': ['create', 'modify', 'delete', 'disable', 'enable', 'suspend', 'unlock', 'reset', 'lifecycle'],
                'federation': ['saml', 'oauth', 'oidc', 'jwt', 'kerberos', 'ldap', 'ad', 'radius', 'tacacs', 'cas'],
                'lifecycle': ['joiner', 'mover', 'leaver', 'onboard', 'offboard', 'transfer', 'promote', 'terminate', 'birthright'],
                'attributes': ['username', 'email', 'domain', 'group', 'role', 'department', 'title', 'manager', 'employee_id'],
                'directory': ['active_directory', 'ldap', 'azure_ad', 'okta', 'ping', 'forgerock', 'sailpoint'],
                'privileged': ['pam', 'privileged_access', 'admin', 'root', 'sudo', 'elevation', 'just_in_time']
            },
            'data': {
                'classification': ['public', 'internal', 'confidential', 'restricted', 'secret', 'top_secret', 'pii', 'phi', 'pci'],
                'handling': ['create', 'read', 'update', 'delete', 'copy', 'move', 'share', 'print', 'download', 'export'],
                'protection': ['encryption', 'masking', 'tokenization', 'anonymization', 'pseudonymization', 'redaction', 'obfuscation'],
                'formats': ['json', 'xml', 'csv', 'pdf', 'doc', 'xls', 'txt', 'binary', 'compressed', 'archive', 'parquet'],
                'storage': ['database', 'file', 'object', 'block', 'cloud', 'on_premise', 'hybrid', 'backup', 'archive'],
                'governance': ['retention', 'disposal', 'archival', 'compliance', 'audit', 'lineage', 'catalog', 'quality'],
                'privacy': ['gdpr', 'ccpa', 'hipaa', 'pci_dss', 'sox', 'ferpa', 'consent', 'right_to_be_forgotten'],
                'lifecycle': ['creation', 'storage', 'usage', 'sharing', 'archival', 'destruction', 'retention']
            },
            'operations': {
                'monitoring': ['log', 'event', 'alert', 'alarm', 'notification', 'dashboard', 'metric', 'kpi', 'sla'],
                'analysis': ['correlation', 'aggregation', 'enrichment', 'normalization', 'parsing', 'filtering', 'machine_learning'],
                'response': ['incident', 'investigation', 'containment', 'eradication', 'recovery', 'lessons_learned', 'playbook'],
                'automation': ['orchestration', 'playbook', 'workflow', 'script', 'api', 'webhook', 'trigger', 'soar'],
                'maintenance': ['patch', 'update', 'upgrade', 'configuration', 'deployment', 'rollback', 'backup', 'disaster_recovery'],
                'compliance': ['audit', 'assessment', 'scan', 'validation', 'certification', 'attestation', 'evidence', 'controls'],
                'performance': ['capacity', 'utilization', 'throughput', 'response_time', 'availability', 'reliability'],
                'integration': ['api', 'webhook', 'etl', 'connector', 'adapter', 'middleware', 'message_queue']
            },
            'infrastructure': {
                'compute': ['server', 'vm', 'container', 'pod', 'node', 'cluster', 'hypervisor', 'docker', 'kubernetes', 'serverless'],
                'storage': ['disk', 'volume', 'partition', 'filesystem', 'raid', 'san', 'nas', 'object_store', 'block_storage'],
                'network': ['switch', 'router', 'firewall', 'load_balancer', 'proxy', 'gateway', 'bridge', 'hub', 'sdwan'],
                'cloud': ['aws', 'azure', 'gcp', 'hybrid', 'multi_cloud', 'saas', 'paas', 'iaas', 'serverless', 'edge'],
                'platforms': ['windows', 'linux', 'unix', 'macos', 'android', 'ios', 'embedded', 'iot', 'mainframe'],
                'services': ['web', 'database', 'application', 'middleware', 'message_queue', 'cache', 'cdn', 'microservices'],
                'orchestration': ['kubernetes', 'docker_swarm', 'nomad', 'mesos', 'openshift', 'rancher'],
                'automation': ['ansible', 'puppet', 'chef', 'terraform', 'cloudformation', 'arm', 'pulumi']
            },
            'application': {
                'architecture': ['monolith', 'microservices', 'soa', 'event_driven', 'serverless', 'mesh', 'layered'],
                'development': ['devops', 'cicd', 'agile', 'waterfall', 'scrum', 'kanban', 'lean', 'safe'],
                'security': ['sast', 'dast', 'iast', 'rasp', 'dependency_scanning', 'container_scanning', 'secrets_management'],
                'testing': ['unit', 'integration', 'system', 'acceptance', 'performance', 'security', 'chaos', 'fuzzing'],
                'deployment': ['blue_green', 'canary', 'rolling', 'ab_testing', 'feature_flags', 'dark_launch'],
                'monitoring': ['apm', 'logs', 'metrics', 'traces', 'synthetic', 'rum', 'uptime', 'sla']
            }
        }

    def _build_advanced_embeddings(self):
        embeddings = {}
        vector_dim = 256
        
        logger.info("🧠 Building advanced semantic embeddings...")
        
        for domain, categories in self.security_taxonomy.items():
            domain_base = hash(domain) % vector_dim
            for category, terms in categories.items():
                category_base = hash(category) % vector_dim
                for i, term in enumerate(terms):
                    vector = np.zeros(vector_dim)
                    vector[domain_base] = 1.0
                    vector[category_base] = 0.8
                    vector[(hash(term) + domain_base) % vector_dim] = 0.6
                    vector[(hash(term) + category_base) % vector_dim] = 0.4
                    
                    for j, other_term in enumerate(terms):
                        if i != j:
                            vector[(hash(other_term) + hash(term)) % vector_dim] = 0.2
                    
                    if np.linalg.norm(vector) > 0:
                        vector = vector / np.linalg.norm(vector)
                    
                    embeddings[term] = vector
                    
                    variations = self._generate_variations(term)
                    for variation in variations:
                        if variation not in embeddings:
                            var_vector = vector.copy()
                            var_vector[(hash(variation)) % vector_dim] = 0.3
                            if np.linalg.norm(var_vector) > 0:
                                var_vector = var_vector / np.linalg.norm(var_vector)
                            embeddings[variation] = var_vector
        
        if SKLEARN_AVAILABLE and embeddings:
            logger.info("🔬 Enhancing embeddings with TF-IDF...")
            terms = list(embeddings.keys())
            try:
                tfidf_matrix = self.tfidf_vectorizer.fit_transform(terms)
                for i, term in enumerate(terms):
                    tfidf_vec = tfidf_matrix[i].toarray().flatten()
                    if len(tfidf_vec) > 0:
                        combined = np.concatenate([embeddings[term], tfidf_vec[:min(64, len(tfidf_vec))]])
                        embeddings[term] = combined
            except Exception as e:
                logger.warning(f"TF-IDF enhancement failed: {e}")
        
        logger.info(f"✅ Built {len(embeddings)} advanced semantic embeddings")
        return embeddings
    
    def _generate_variations(self, term):
        variations = set()
        
        parts = re.split(r'[_\-\s]+', term)
        if len(parts) > 1:
            variations.update([
                ''.join(parts), '_'.join(parts), '-'.join(parts), ' '.join(parts),
                ''.join(p[0] for p in parts if p),
            ])
            
            for i in range(len(parts)):
                if len(parts[i]) > 3:
                    abbreviated = parts.copy()
                    abbreviated[i] = parts[i][:3]
                    variations.add('_'.join(abbreviated))
        
        if '_' in term:
            variations.update([
                term.replace('_', ''), term.replace('_', '-'), 
                term.replace('_', ' '), term.replace('_', '.')
            ])
        
        if len(term) > 6:
            variations.update([term[:4], term[:5], term[:6]])
            variations.update([term[-4:], term[-5:], term[-6:]])
        
        if TEXTDISTANCE_AVAILABLE:
            for var in list(variations)[:10]:
                if len(var) > 3:
                    variations.add(var.replace('ph', 'f'))
                    variations.add(var.replace('c', 'k'))
                    variations.add(var.replace('s', 'z'))
        
        if NLTK_AVAILABLE and hasattr(self, 'stemmer'):
            stemmed = self.stemmer.stem(term)
            if stemmed != term:
                variations.add(stemmed)
        
        return variations

    def _build_pattern_library(self):
        return {
            'ip_patterns': [
                r'(?:ip|addr|address)(?:_?(?:src|source|dst|dest|destination|client|server|remote|local|public|private|internal|external))?',
                r'(?:src|source|dst|dest|destination|client|server|remote|local)(?:_?(?:ip|addr|address))',
                r'(?:v4|v6|ipv4|ipv6)(?:_?(?:addr|address))?',
                r'(?:inet|internet)(?:_?(?:addr|address))?'
            ],
            'port_patterns': [
                r'(?:port|prt|portnum)(?:_?(?:src|source|dst|dest|destination|local|remote|listen|bind|target))?',
                r'(?:src|source|dst|dest|destination|local|remote)(?:_?(?:port|prt))',
                r'(?:listen|bind|target|service)(?:_?(?:port|prt))?'
            ],
            'time_patterns': [
                r'(?:time|timestamp|date|datetime|epoch|utc|gmt|created|modified|updated|start|end|begin|finish|occurred|when)',
                r'(?:create|mod|update|start|end|begin|finish|occur)(?:_?(?:time|date|timestamp))',
                r'(?:year|month|day|hour|minute|second|millisecond|microsecond|nanosecond)(?:s)?',
                r'(?:first|last|initial|final)(?:_?(?:seen|time|date))?'
            ],
            'user_patterns': [
                r'(?:user|usr|account|identity|subject|principal|actor|person|individual|entity)(?:_?(?:name|id|email|domain))?',
                r'(?:login|logon|signin|username|userid|email|upn|dn|cn|sam|guid|uuid)(?:_?(?:name|id))?',
                r'(?:employee|staff|admin|service)(?:_?(?:id|account|user))?'
            ],
            'action_patterns': [
                r'(?:action|operation|activity|event|command|request|response|result|outcome|status|verdict|decision)',
                r'(?:allow|deny|block|drop|permit|reject|accept|forward|route|redirect|proxy|pass|fail)',
                r'(?:success|fail|error|ok|pass|deny|grant|revoke|create|delete|modify|update|read|write)'
            ],
            'file_patterns': [
                r'(?:file|filename|filepath|path|document|doc|binary|executable|exe|dll|script|program)',
                r'(?:directory|folder|dir|location|parent|child|root|base|full)(?:_?(?:path|name))',
                r'(?:extension|ext|type|format|mime|content)(?:_?(?:type))?',
                r'(?:hash|checksum|md5|sha1|sha256|signature)(?:_?(?:value))?'
            ],
            'process_patterns': [
                r'(?:process|proc|program|application|app|service|daemon|task|job|thread|worker)',
                r'(?:pid|ppid|process_id|parent|child|executable|image|command|cmd)(?:_?(?:line|name|path))?',
                r'(?:start|stop|kill|terminate|suspend|resume)(?:_?(?:process|proc))?'
            ],
            'network_patterns': [
                r'(?:protocol|proto|transport|network|net|connection|conn|session|flow|stream|traffic)',
                r'(?:tcp|udp|icmp|http|https|ftp|ssh|dns|dhcp|smtp|pop|imap|snmp|ldap)',
                r'(?:packet|frame|segment|datagram|message|payload|header|body|data)',
                r'(?:bytes|size|length|bandwidth|throughput|latency|rtt)(?:_?(?:sent|received|total))?'
            ],
            'security_patterns': [
                r'(?:security|sec|threat|attack|malware|virus|signature|rule|policy|alert|alarm|incident)',
                r'(?:hash|checksum|digest|signature|certificate|key|token|credential|password|secret)',
                r'(?:encrypt|decrypt|cipher|crypto|ssl|tls|pki|x509|rsa|aes|sha|md5|hmac)',
                r'(?:vulnerability|exploit|cve|weakness|flaw|bug|issue)(?:_?(?:id|name|score))?'
            ],
            'size_patterns': [
                r'(?:size|bytes|length|count|volume|amount|quantity|total|sum|max|min|avg|mean)',
                r'(?:kb|mb|gb|tb|pb|kilobyte|megabyte|gigabyte|terabyte|petabyte)(?:s)?',
                r'(?:records|rows|entries|items|objects|files|documents)(?:_?(?:count|num|number))?'
            ],
            'geo_patterns': [
                r'(?:country|region|city|state|province|location|geo|geographic|latitude|longitude|coordinates)',
                r'(?:continent|timezone|locale|language|culture|iso|cc|country_code)',
                r'(?:lat|lon|lng|coord|gps|position)(?:_?(?:x|y|coordinate))?'
            ],
            'cloud_patterns': [
                r'(?:cloud|aws|azure|gcp|google|amazon|microsoft)(?:_?(?:service|resource|instance))?',
                r'(?:vpc|vnet|subnet|security_group|nacl|route|gateway)',
                r'(?:container|docker|kubernetes|k8s|pod|namespace|cluster)',
                r'(?:lambda|function|serverless|faas|microservice)'
            ],
            'database_patterns': [
                r'(?:database|db|sql|nosql|table|collection|index|query|transaction)',
                r'(?:select|insert|update|delete|create|drop|alter|grant|revoke)',
                r'(?:mysql|postgres|oracle|mssql|mongodb|cassandra|redis|elasticsearch)'
            ]
        }

    def _build_abbreviation_engine(self):
        base_abbrevs = {
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
            'rsa': 'rivest_shamir_adleman', 'pki': 'public_key_infrastructure'
        }
        
        extended_abbrevs = {}
        for abbrev, full in base_abbrevs.items():
            extended_abbrevs[abbrev] = full
            extended_abbrevs[abbrev.upper()] = full
            extended_abbrevs[abbrev.capitalize()] = full
            
            if '_' in full:
                parts = full.split('_')
                if len(parts) == 2:
                    extended_abbrevs[abbrev + '_' + parts[1]] = full
                    extended_abbrevs[parts[0] + '_' + abbrev] = full
                elif len(parts) == 3:
                    extended_abbrevs[abbrev + '_' + parts[1] + '_' + parts[2]] = full
        
        return extended_abbrevs

    def _build_context_graphs(self):
        graphs = {}
        
        if not NETWORKX_AVAILABLE:
            return self._build_simple_context_graphs()
        
        logger.info("🕸️ Building advanced semantic context graphs...")
        
        for domain, categories in self.security_taxonomy.items():
            G = nx.Graph()
            all_terms = []
            
            for category, terms in categories.items():
                all_terms.extend(terms)
                G.add_node(category, type='category', domain=domain)
                G.add_node(domain, type='domain')
                G.add_edge(category, domain, weight=1.0)
                
                for term in terms:
                    G.add_node(term, type='term', category=category, domain=domain)
                    G.add_edge(term, category, weight=0.8)
                    
                    for other_term in terms:
                        if term != other_term:
                            similarity = SequenceMatcher(None, term, other_term).ratio()
                            if similarity > 0.3:
                                G.add_edge(term, other_term, weight=similarity)
            
            for i, term1 in enumerate(all_terms):
                for j, term2 in enumerate(all_terms[i+1:], i+1):
                    if not G.has_edge(term1, term2):
                        similarity = self._calculate_semantic_similarity(term1, term2)
                        if similarity > 0.4:
                            G.add_edge(term1, term2, weight=similarity, type='semantic')
            
            graphs[domain] = G
        
        logger.info(f"✅ Built {len(graphs)} semantic context graphs")
        return graphs

    def _build_simple_context_graphs(self):
        graphs = {}
        
        for domain, categories in self.security_taxonomy.items():
            graph = defaultdict(set)
            all_terms = []
            
            for category, terms in categories.items():
                all_terms.extend(terms)
                for term in terms:
                    graph[term].add(category)
                    graph[category].add(domain)
                    for other_term in terms:
                        if term != other_term:
                            graph[term].add(other_term)
            
            for i, term1 in enumerate(all_terms):
                for j, term2 in enumerate(all_terms[i+1:], i+1):
                    similarity = SequenceMatcher(None, term1, term2).ratio()
                    if similarity > 0.6:
                        graph[term1].add(term2)
                        graph[term2].add(term1)
            
            graphs[domain] = graph
        
        return graphs

    def _build_semantic_network(self):
        if not NETWORKX_AVAILABLE:
            return None
        
        G = nx.Graph()
        
        for domain, categories in self.security_taxonomy.items():
            for category, terms in categories.items():
                for term in terms:
                    G.add_node(term, domain=domain, category=category)
        
        terms = list(G.nodes())
        for i, term1 in enumerate(terms):
            for j, term2 in enumerate(terms[i+1:], i+1):
                similarity = self._calculate_semantic_similarity(term1, term2)
                if similarity > 0.3:
                    G.add_edge(term1, term2, weight=similarity)
        
        return G

    def _build_linguistic_rules(self):
        return {
            'prefix_rules': {
                'un': 'negative', 'non': 'negative', 'anti': 'opposite', 'contra': 'against',
                'pre': 'before', 'post': 'after', 'sub': 'under', 'super': 'above',
                'inter': 'between', 'intra': 'within', 'extra': 'outside', 'ultra': 'beyond',
                'multi': 'many', 'single': 'one', 'uni': 'one', 'bi': 'two', 'tri': 'three',
                'auto': 'automatic', 'semi': 'partial', 'quasi': 'almost', 'pseudo': 'fake',
                'meta': 'about', 'micro': 'small', 'macro': 'large', 'mini': 'small',
                're': 'again', 'de': 'reverse', 'dis': 'not', 'mis': 'wrong',
                'over': 'excessive', 'under': 'insufficient', 'out': 'beyond'
            },
            'suffix_rules': {
                'ing': 'action', 'ed': 'past', 'er': 'agent', 'or': 'agent', 'ar': 'agent',
                'tion': 'process', 'sion': 'process', 'ment': 'result', 'ance': 'state',
                'ence': 'state', 'ness': 'quality', 'ity': 'quality', 'ty': 'quality',
                'able': 'capable', 'ible': 'capable', 'ful': 'full_of', 'less': 'without',
                'ous': 'having', 'ive': 'tendency', 'al': 'relating_to', 'ic': 'relating_to',
                'ly': 'manner', 'ward': 'direction', 'wise': 'manner', 'like': 'similar',
                'ism': 'doctrine', 'ist': 'believer', 'age': 'collection', 'dom': 'state',
                'ship': 'condition', 'hood': 'state', 'cy': 'quality'
            },
            'compound_rules': {
                'source_destination': {
                    'group1': ['src', 'source', 'from', 'origin', 'sender', 'client', 'incoming', 'input'],
                    'group2': ['dst', 'dest', 'destination', 'to', 'target', 'recipient', 'server', 'outgoing', 'output']
                },
                'input_output': {
                    'group1': ['in', 'input', 'incoming', 'inbound', 'ingress', 'receive', 'read', 'get'],
                    'group2': ['out', 'output', 'outgoing', 'outbound', 'egress', 'send', 'write', 'put']
                },
                'start_end': {
                    'group1': ['start', 'begin', 'initial', 'first', 'open', 'create', 'init', 'launch'],
                    'group2': ['end', 'finish', 'final', 'last', 'close', 'terminate', 'stop', 'shutdown']
                },
                'success_failure': {
                    'group1': ['success', 'ok', 'pass', 'accept', 'allow', 'grant', 'approve', 'yes', 'true'],
                    'group2': ['fail', 'error', 'deny', 'block', 'reject', 'refuse', 'no', 'false']
                },
                'create_destroy': {
                    'group1': ['create', 'add', 'insert', 'new', 'make', 'build', 'generate', 'produce'],
                    'group2': ['delete', 'remove', 'destroy', 'kill', 'drop', 'eliminate', 'purge', 'erase']
                },
                'read_write': {
                    'group1': ['read', 'get', 'fetch', 'retrieve', 'select', 'view', 'query', 'search'],
                    'group2': ['write', 'set', 'put', 'update', 'modify', 'change', 'insert', 'save']
                },
                'public_private': {
                    'group1': ['public', 'external', 'internet', 'wan', 'outside', 'open', 'global'],
                    'group2': ['private', 'internal', 'intranet', 'lan', 'inside', 'closed', 'local']
                },
                'high_low': {
                    'group1': ['high', 'max', 'maximum', 'top', 'upper', 'peak', 'critical'],
                    'group2': ['low', 'min', 'minimum', 'bottom', 'lower', 'baseline', 'normal']
                },
                'enable_disable': {
                    'group1': ['enable', 'activate', 'turn_on', 'start', 'open', 'unlock', 'allow'],
                    'group2': ['disable', 'deactivate', 'turn_off', 'stop', 'close', 'lock', 'block']
                }
            }
        }

    def _build_domain_vectors(self):
        vectors = {}
        vector_size = 128
        
        for domain, categories in self.security_taxonomy.items():
            domain_vector = np.zeros(vector_size)
            domain_hash_base = hash(domain) % vector_size
            domain_vector[domain_hash_base] = 1.0
            
            category_weights = []
            for category, terms in categories.items():
                category_hash = hash(category) % vector_size
                domain_vector[category_hash] = 0.7
                category_weights.append(len(terms))
                
                for term in terms:
                    term_hash = hash(term) % vector_size
                    domain_vector[term_hash] = max(domain_vector[term_hash], 0.3)
            
            if category_weights:
                weight_factor = statistics.mean(category_weights) / max(category_weights)
                domain_vector = domain_vector * weight_factor
                
                norm = np.linalg.norm(domain_vector)
                if norm > 0:
                    domain_vector = domain_vector / norm
            
            vectors[domain] = domain_vector
        
        return vectors

    def _initialize_ml_models(self):
        if not SKLEARN_AVAILABLE:
            logger.warning("⚠️ Scikit-learn not available, skipping ML model initialization")
            return
        
        logger.info("🤖 Initializing advanced ML models...")
        
        try:
            self.clustering_model = KMeans(n_clusters=10, random_state=42, n_init=10)
            self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
            self.neural_matcher = MLPClassifier(
                hidden_layer_sizes=(100, 50),
                max_iter=1000,
                random_state=42,
                early_stopping=True
            )
            self.pca = PCA(n_components=50)
            self.svd = TruncatedSVD(n_components=50)
            
            logger.info("✅ ML models initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize ML models: {e}")

    @lru_cache(maxsize=50000)
    def advanced_normalize(self, text):
        if not text:
            return ""
        
        text = unicodedata.normalize('NFKD', text)
        text = ''.join(c for c in text if not unicodedata.combining(c))
        text = text.lower()
        text = re.sub(r'[^\w\s]', '_', text)
        text = re.sub(r'_+', '_', text)
        text = text.strip('_')
        
        if NLTK_AVAILABLE and hasattr(self, 'stop_words'):
            words = text.split('_')
            words = [w for w in words if w not in self.stop_words and len(w) > 2]
            text = '_'.join(words)
        
        return text

    def ultra_stem(self, word):
        if not word:
            return word
        
        word = word.lower().strip()
        original_word = word
        
        if word in self.abbreviation_engine:
            return self.abbreviation_engine[word]
        
        if NLTK_AVAILABLE and hasattr(self, 'stemmer'):
            stemmed = self.stemmer.stem(word)
            if stemmed != word and len(stemmed) >= 3:
                word = stemmed
        
        for prefix, meaning in self.linguistic_rules['prefix_rules'].items():
            if word.startswith(prefix) and len(word) > len(prefix) + 2:
                word = word[len(prefix):]
                break
        
        for suffix, meaning in self.linguistic_rules['suffix_rules'].items():
            if word.endswith(suffix) and len(word) > len(suffix) + 2:
                stem = word[:-len(suffix)]
                if len(stem) >= 3:
                    word = stem
                break
        
        if len(word) > 8:
            vowels = 'aeiou'
            compressed = ''.join(c for i, c in enumerate(word) 
                               if i == 0 or c not in vowels or word[i-1] in vowels)
            if len(compressed) >= 4:
                word = compressed
        
        return word if word != original_word else original_word

    def extract_semantic_components(self, text):
        components = {
            'tokens': [],
            'patterns': [],
            'domains': [],
            'embeddings': [],
            'context': [],
            'variations': [],
            'ngrams': [],
            'pos_tags': [],
            'sentiment': 0.0,
            'complexity': 0.0
        }
        
        if not text:
            return components
        
        normalized = self.advanced_normalize(text)
        tokens = re.split(r'[_\s]+', normalized)
        components['tokens'] = [self.ultra_stem(token) for token in tokens if len(token) > 1]
        
        for pattern_type, patterns in self.pattern_library.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    components['patterns'].append(pattern_type)
        
        for domain in self.security_taxonomy:
            domain_score = 0
            for category in self.security_taxonomy[domain]:
                for token in components['tokens']:
                    if token in self.security_taxonomy[domain][category]:
                        domain_score += 1
            if domain_score > 0:
                components['domains'].append((domain, domain_score))
        
        components['domains'] = sorted(components['domains'], key=lambda x: x[1], reverse=True)
        components['domains'] = [d[0] for d in components['domains']]
        
        for token in components['tokens']:
            if token in self.semantic_embeddings:
                components['embeddings'].append(self.semantic_embeddings[token])
        
        for rule_type, rule_data in self.linguistic_rules['compound_rules'].items():
            group1_matches = sum(1 for token in components['tokens'] if token in rule_data['group1'])
            group2_matches = sum(1 for token in components['tokens'] if token in rule_data['group2'])
            if group1_matches > 0 or group2_matches > 0:
                components['context'].append({
                    'rule': rule_type,
                    'group1_score': group1_matches,
                    'group2_score': group2_matches
                })
        
        for token in components['tokens']:
            components['variations'].extend(self._generate_variations(token))
        
        if len(components['tokens']) > 1:
            for n in range(2, min(4, len(components['tokens']) + 1)):
                components['ngrams'].extend(list(ngrams(components['tokens'], n)))
        
        components['complexity'] = self._calculate_text_complexity(text, components)
        
        return components

    def _calculate_text_complexity(self, text, components):
        complexity = 0.0
        
        complexity += min(len(text) / 50, 1.0) * 0.2
        
        if components['tokens']:
            unique_tokens = len(set(components['tokens']))
            total_tokens = len(components['tokens'])
            complexity += (unique_tokens / total_tokens) * 0.3
        
        complexity += min(len(set(components['patterns'])) / 5, 1.0) * 0.2
        complexity += min(len(components['domains']) / 3, 1.0) * 0.3
        
        return min(complexity, 1.0)

    def _calculate_semantic_similarity(self, text1, text2):
        if not text1 or not text2:
            return 0.0
        
        if TEXTDISTANCE_AVAILABLE:
            try:
                return max(
                    jaro_winkler(text1, text2),
                    cosine(text1, text2),
                    td_jaccard(text1, text2)
                )
            except:
                pass
        
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    def calculate_multidimensional_similarity(self, text1, text2):
        cache_key = hashlib.md5(f"{text1}|{text2}".encode()).hexdigest()
        if cache_key in self.similarity_cache:
            return self.similarity_cache[cache_key]
        
        comp1 = self.extract_semantic_components(text1)
        comp2 = self.extract_semantic_components(text2)
        
        similarities = {}
        
        similarities['token_overlap'] = self._jaccard_similarity(
            set(comp1['tokens']), set(comp2['tokens'])
        )
        similarities['token_cosine'] = self._token_cosine_similarity(comp1['tokens'], comp2['tokens'])
        
        similarities['pattern_match'] = self._jaccard_similarity(
            set(comp1['patterns']), set(comp2['patterns'])
        )
        
        similarities['domain_alignment'] = self._jaccard_similarity(
            set(comp1['domains']), set(comp2['domains'])
        )
        
        if comp1['embeddings'] and comp2['embeddings']:
            similarities['embedding_cosine'] = self._cosine_similarity_multi(
                comp1['embeddings'], comp2['embeddings']
            )
        else:
            similarities['embedding_cosine'] = 0.0
        
        similarities['context_match'] = self._context_similarity(comp1['context'], comp2['context'])
        
        similarities['variation_overlap'] = self._jaccard_similarity(
            set(comp1['variations']), set(comp2['variations'])
        )
        
        similarities['edit_distance'] = self._calculate_semantic_similarity(text1, text2)
        similarities['abbreviation'] = self._abbreviation_similarity(text1, text2)
        similarities['phonetic'] = self._phonetic_similarity(text1, text2)
        similarities['structural'] = self._structural_similarity(text1, text2)
        similarities['ngram'] = self._ngram_similarity(comp1['ngrams'], comp2['ngrams'])
        
        if NETWORKX_AVAILABLE and hasattr(self, 'semantic_graph'):
            similarities['graph'] = self._graph_similarity_advanced(comp1['tokens'], comp2['tokens'])
        else:
            similarities['graph'] = self._graph_similarity(comp1['tokens'], comp2['tokens'])
        
        if SKLEARN_AVAILABLE:
            similarities['ml_enhanced'] = self._ml_similarity(text1, text2, comp1, comp2)
        else:
            similarities['ml_enhanced'] = 0.0
        
        similarities['complexity_adjusted'] = self._complexity_adjusted_similarity(comp1, comp2)
        
        weights = {
            'token_overlap': 0.12,
            'token_cosine': 0.10,
            'pattern_match': 0.10,
            'domain_alignment': 0.15,
            'embedding_cosine': 0.14,
            'context_match': 0.08,
            'variation_overlap': 0.06,
            'edit_distance': 0.06,
            'abbreviation': 0.05,
            'phonetic': 0.03,
            'structural': 0.03,
            'ngram': 0.04,
            'graph': 0.02,
            'ml_enhanced': 0.02,
            'complexity_adjusted': 0.02
        }
        
        final_score = sum(similarities[key] * weights[key] for key in similarities if key in weights)
        
        result = {
            'final_score': final_score,
            'component_scores': similarities,
            'match_evidence': self._generate_match_evidence(comp1, comp2, similarities),
            'confidence': self._calculate_confidence(similarities),
            'match_type': self._determine_match_type(final_score, similarities)
        }
        
        self.similarity_cache[cache_key] = result
        return result

    def _token_cosine_similarity(self, tokens1, tokens2):
        if not tokens1 or not tokens2:
            return 0.0
        
        if SKLEARN_AVAILABLE:
            try:
                all_tokens = list(set(tokens1 + tokens2))
                vec1 = np.array([tokens1.count(token) for token in all_tokens])
                vec2 = np.array([tokens2.count(token) for token in all_tokens])
                
                dot_product = np.dot(vec1, vec2)
                norm1 = np.linalg.norm(vec1)
                norm2 = np.linalg.norm(vec2)
                
                if norm1 > 0 and norm2 > 0:
                    return dot_product / (norm1 * norm2)
            except:
                pass
        
        return 0.0

    def _context_similarity(self, context1, context2):
        if not context1 or not context2:
            return 0.0
        
        rules1 = {ctx['rule'] for ctx in context1}
        rules2 = {ctx['rule'] for ctx in context2}
        
        return self._jaccard_similarity(rules1, rules2)

    def _ngram_similarity(self, ngrams1, ngrams2):
        if not ngrams1 or not ngrams2:
            return 0.0
        
        ngrams1_set = set(tuple(ng) if isinstance(ng, (list, tuple)) else ng for ng in ngrams1)
        ngrams2_set = set(tuple(ng) if isinstance(ng, (list, tuple)) else ng for ng in ngrams2)
        
        return self._jaccard_similarity(ngrams1_set, ngrams2_set)

    def _graph_similarity_advanced(self, tokens1, tokens2):
        if not self.semantic_graph or not tokens1 or not tokens2:
            return 0.0
        
        try:
            similarities = []
            for token1 in tokens1:
                for token2 in tokens2:
                    if token1 in self.semantic_graph and token2 in self.semantic_graph:
                        try:
                            path_length = nx.shortest_path_length(
                                self.semantic_graph, token1, token2
                            )
                            similarity = 1.0 / (1.0 + path_length)
                            similarities.append(similarity)
                        except nx.NetworkXNoPath:
                            continue
            
            return statistics.mean(similarities) if similarities else 0.0
            
        except Exception:
            return self._graph_similarity(tokens1, tokens2)

    def _ml_similarity(self, text1, text2, comp1, comp2):
        try:
            features1 = self._create_feature_vector(text1, comp1)
            features2 = self._create_feature_vector(text2, comp2)
            
            if len(features1) != len(features2):
                return 0.0
            
            features1 = np.array(features1).reshape(1, -1)
            features2 = np.array(features2).reshape(1, -1)
            
            similarity = cosine_similarity(features1, features2)[0, 0]
            return float(similarity)
            
        except Exception:
            return 0.0

    def _create_feature_vector(self, text, components):
        features = []
        
        features.extend([
            len(text),
            len(components['tokens']),
            len(set(components['tokens'])),
            len(components['patterns']),
            len(components['domains']),
            components['complexity']
        ])
        
        all_patterns = set()
        for patterns in self.pattern_library.values():
            all_patterns.update(patterns)
        
        for pattern_type in self.pattern_library.keys():
            features.append(1 if pattern_type in components['patterns'] else 0)
        
        for domain in self.security_taxonomy.keys():
            features.append(1 if domain in components['domains'] else 0)
        
        target_size = 50
        if len(features) < target_size:
            features.extend([0] * (target_size - len(features)))
        else:
            features = features[:target_size]
        
        return features

    def _complexity_adjusted_similarity(self, comp1, comp2):
        if comp1['complexity'] == 0 and comp2['complexity'] == 0:
            return 1.0
        
        complexity_diff = abs(comp1['complexity'] - comp2['complexity'])
        return 1.0 - complexity_diff

    def _calculate_confidence(self, similarities):
        non_zero_count = sum(1 for score in similarities.values() if score > 0)
        total_metrics = len(similarities)
        
        coverage = non_zero_count / total_metrics
        consistency = 1.0 - statistics.stdev(similarities.values()) if len(similarities) > 1 else 1.0
        
        return (coverage + consistency) / 2

    def _determine_match_type(self, final_score, similarities):
        if final_score > 0.8:
            return 'ultra_semantic'
        elif final_score > 0.6:
            return 'semantic'
        elif final_score > 0.4:
            return 'partial'
        else:
            return 'weak'

    def _jaccard_similarity(self, set1, set2):
        if not set1 and not set2:
            return 1.0
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0

    def _cosine_similarity_multi(self, embeddings1, embeddings2):
        if not embeddings1 or not embeddings2:
            return 0.0
        
        max_sim = 0.0
        for emb1 in embeddings1:
            for emb2 in embeddings2:
                sim = self._cosine_similarity(emb1, emb2)
                max_sim = max(max_sim, sim)
        
        return max_sim

    def _cosine_similarity(self, vec1, vec2):
        if isinstance(vec1, list):
            vec1 = np.array(vec1)
        if isinstance(vec2, list):
            vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        magnitude1 = np.linalg.norm(vec1)
        magnitude2 = np.linalg.norm(vec2)
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return float(dot_product / (magnitude1 * magnitude2))

    def _abbreviation_similarity(self, text1, text2):
        expanded1 = text1
        expanded2 = text2
        
        for abbrev, full in self.abbreviation_engine.items():
            pattern = r'\b' + re.escape(abbrev) + r'\b'
            expanded1 = re.sub(pattern, full, expanded1, flags=re.IGNORECASE)
            expanded2 = re.sub(pattern, full, expanded2, flags=re.IGNORECASE)
        
        if FUZZYWUZZY_AVAILABLE:
            return fuzz.ratio(expanded1.lower(), expanded2.lower()) / 100.0
        
        return SequenceMatcher(None, expanded1.lower(), expanded2.lower()).ratio()

    def _phonetic_similarity(self, text1, text2):
        def enhanced_soundex(word):
            if not word:
                return ""
            
            word = word.upper()
            soundex_code = word[0]
            
            mapping = {
                'BFPV': '1', 'CGJKQSXZ': '2', 'DT': '3', 'L': '4', 
                'MN': '5', 'R': '6', 'HW': '0'
            }
            
            prev_code = ''
            for char in word[1:]:
                for chars, code in mapping.items():
                    if char in chars:
                        if code != prev_code and code != '0':
                            soundex_code += code
                            prev_code = code
                        break
                else:
                    prev_code = ''
            
            soundex_code = soundex_code.ljust(4, '0')[:4]
            return soundex_code
        
        words1 = re.findall(r'\w+', text1)
        words2 = re.findall(r'\w+', text2)
        
        if not words1 or not words2:
            return 0.0
        
        matches = 0
        total_comparisons = 0
        
        for w1 in words1:
            for w2 in words2:
                total_comparisons += 1
                if enhanced_soundex(w1) == enhanced_soundex(w2):
                    matches += 1
        
        return matches / total_comparisons if total_comparisons > 0 else 0.0

    def _structural_similarity(self, text1, text2):
        def get_enhanced_structure(text):
            structure = []
            prev_type = None
            count = 0
            
            for char in text:
                if char.isalpha():
                    char_type = 'L'
                elif char.isdigit():
                    char_type = 'D'
                elif char in '_-':
                    char_type = 'S'
                elif char == '.':
                    char_type = 'P'
                else:
                    char_type = 'O'
                
                if char_type == prev_type:
                    count += 1
                else:
                    if prev_type is not None:
                        structure.append(f"{prev_type}{count}")
                    prev_type = char_type
                    count = 1
            
            if prev_type is not None:
                structure.append(f"{prev_type}{count}")
            
            return ''.join(structure)
        
        struct1 = get_enhanced_structure(text1)
        struct2 = get_enhanced_structure(text2)
        
        return SequenceMatcher(None, struct