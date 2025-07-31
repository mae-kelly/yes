import re
from typing import Dict, List, Set, Any
from collections import defaultdict, Counter
from itertools import product
from math import log10

class EnhancedSemanticEngine:
    def __init__(self):
        self.morphology_cache = {}
        self.concept_graph = self._build_enhanced_concept_graph()
        self.semantic_clusters = self._create_semantic_clusters()
        self.confidence_calibrator = self._initialize_calibrator()
        
        self.pattern_frequencies = Counter()
        self.learned_patterns = {}
        
    def _build_enhanced_concept_graph(self) -> Dict[str, Dict]:
        return {
            'asset_identity': {
                'primary': ['asset', 'device', 'host', 'machine', 'computer', 'endpoint', 'node', 'system'],
                'identifiers': ['id', 'identifier', 'uuid', 'guid', 'tag', 'number', 'serial', 'key', 'name'],
                'formats': ['hostname', 'fqdn', 'mac_address', 'ip_address'],
                'global_unique': ['global', 'unique'],
                'compound_rules': [
                    ('primary', 'identifiers'),
                    ('primary', 'formats'),
                    ('global_unique', 'identifiers')
                ],
                'semantic_weight': 1.0,
                'business_priority': 10,
                'validation_patterns': [
                    r'^[A-Z]{2,6}\d{4,}$',
                    r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$',
                    r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$'
                ]
            },
            'infrastructure_classification': {
                'primary': ['infrastructure', 'platform', 'deployment', 'hosting', 'environment'],
                'classifiers': ['type', 'kind', 'class', 'category', 'model', 'tier'],
                'environments': ['cloud', 'aws', 'azure', 'gcp', 'onprem', 'physical', 'virtual', 'hybrid'],
                'technologies': ['kubernetes', 'docker', 'vmware', 'container', 'serverless'],
                'compound_rules': [
                    ('primary', 'classifiers'),
                    ('environments', 'classifiers'),
                    ('technologies', 'classifiers')
                ],
                'semantic_weight': 0.9,
                'business_priority': 8,
                'validation_patterns': [
                    r'^(cloud|onprem|hybrid)$',
                    r'^(aws|azure|gcp|physical)$',
                    r'^(container|vm|bare_metal)$'
                ]
            },
            'geographic_context': {
                'primary': ['country', 'region', 'location', 'site', 'facility', 'datacenter'],
                'modifiers': ['code', 'iso', 'geo', 'geographic', 'zone'],
                'cloud_specific': ['availability_zone', 'aws_region', 'azure_region', 'gcp_zone'],
                'administrative': ['state', 'province', 'city', 'address'],
                'empty_group': [],
                'compound_rules': [
                    ('primary', 'modifiers'),
                    ('cloud_specific', 'empty_group'),
                    ('administrative', 'modifiers')
                ],
                'semantic_weight': 0.8,
                'business_priority': 7,
                'validation_patterns': [
                    r'^[A-Z]{2}$',
                    r'^[A-Z]{2}-[A-Z]{1,3}$',
                    r'^(us|eu|asia)-(east|west|central|north|south)-\d+[a-z]?$'
                ]
            },
            'security_posture': {
                'primary': ['security', 'agent', 'protection', 'coverage', 'endpoint', 'edr'],
                'vendors': ['crowdstrike', 'sentinelone', 'tanium', 'axonius', 'carbon_black', 'defender'],
                'status': ['status', 'installed', 'enabled', 'active', 'deployed', 'running'],
                'types': ['antivirus', 'firewall', 'dlp', 'threat', 'vulnerability'],
                'compound_rules': [
                    ('vendors', 'status'),
                    ('primary', 'status'),
                    ('types', 'status')
                ],
                'semantic_weight': 1.0,
                'business_priority': 9,
                'validation_patterns': [
                    r'^(installed|enabled|active|disabled|removed)$',
                    r'^[a-f0-9]{32,}$',
                    r'^\d+\.\d+\.\d+\.\d+$'
                ]
            },
            'logging_telemetry': {
                'primary': ['log', 'logging', 'audit', 'compliance', 'ingestion', 'telemetry'],
                'platforms': ['splunk', 'chronicle', 'gso', 'siem', 'elastic', 'datadog'],
                'components': ['forwarder', 'source', 'index', 'parser', 'collector'],
                'states': ['ingested', 'forwarded', 'indexed', 'parsed', 'processed'],
                'compound_rules': [
                    ('platforms', 'components'),
                    ('primary', 'platforms'),
                    ('components', 'states')
                ],
                'semantic_weight': 0.9,
                'business_priority': 8,
                'validation_patterns': [
                    r'^(forwarded|ingested|failed|pending)$',
                    r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$',
                    r'^[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+$'
                ]
            },
            'business_context': {
                'primary': ['business', 'organization', 'department', 'application', 'service'],
                'ownership': ['owner', 'team', 'group', 'responsible', 'contact'],
                'financial': ['cost', 'budget', 'billing', 'charge', 'expense'],
                'operational': ['function', 'purpose', 'role', 'mission', 'objective'],
                'compound_rules': [
                    ('primary', 'ownership'),
                    ('financial', 'primary'),
                    ('operational', 'primary')
                ],
                'semantic_weight': 0.7,
                'business_priority': 6,
                'validation_patterns': [
                    r'^[A-Z]{2,4}\d{3,}$',
                    r'^[a-zA-Z0-9\-_]+@[a-zA-Z0-9\-_]+\.[a-zA-Z]{2,}$'
                ]
            },
            'temporal_context': {
                'primary': ['time', 'date', 'timestamp', 'created', 'modified', 'updated'],
                'granularity': ['year', 'month', 'day', 'hour', 'minute', 'second'],
                'lifecycle': ['birth', 'death', 'start', 'end', 'first', 'last'],
                'frequency': ['daily', 'weekly', 'monthly', 'annual', 'periodic'],
                'compound_rules': [
                    ('primary', 'granularity'),
                    ('lifecycle', 'primary'),
                    ('frequency', 'primary')
                ],
                'semantic_weight': 0.6,
                'business_priority': 5,
                'validation_patterns': [
                    r'^\d{4}-\d{2}-\d{2}$',
                    r'^\d{10,13}$',
                    r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?Z?$'
                ]
            }
        }
    
    def _create_semantic_clusters(self) -> Dict[str, List[str]]:
        return {
            'identity_cluster': ['id', 'identifier', 'uuid', 'guid', 'key', 'serial', 'tag', 'name'],
            'naming_cluster': ['name', 'hostname', 'fqdn', 'dns', 'label', 'title', 'alias'],
            'classification_cluster': ['type', 'class', 'kind', 'category', 'classification', 'taxonomy'],
            'status_cluster': ['status', 'state', 'condition', 'enabled', 'active', 'running'],
            'temporal_cluster': ['time', 'date', 'timestamp', 'created', 'modified', 'updated'],
            'location_cluster': ['location', 'site', 'region', 'zone', 'area', 'facility'],
            'security_cluster': ['security', 'protection', 'agent', 'edr', 'antivirus', 'firewall'],
            'network_cluster': ['network', 'ip', 'mac', 'port', 'protocol', 'connection'],
            'system_cluster': ['system', 'os', 'platform', 'architecture', 'version', 'build'],
            'business_cluster': ['business', 'organization', 'department', 'team', 'owner', 'cost']
        }
    
    def _initialize_calibrator(self) -> Dict[str, Any]:
        return {
            'exact_match_weight': 1.0,
            'semantic_depth_multiplier': [0.4, 0.6, 0.8, 1.0],
            'business_priority_scaling': True,
            'context_amplification': 0.3,
            'multi_signal_bonus': 0.15,
            'data_pattern_boost': 0.25,
            'production_table_boost': 0.1,
            'large_table_boost': 0.05,
            'temperature_scaling': 1.2
        }
    
    def generate_morphological_variants(self, term: str, max_depth: int = 3) -> Set[str]:
        if term in self.morphology_cache:
            return self.morphology_cache[term]
        
        if max_depth <= 0:
            return {term}
        
        variants = {term}
        base = term.lower()
        
        variants.update([base, base.upper(), base.title(), base.capitalize()])
        
        if '_' in base:
            no_sep = base.replace('_', '')
            kebab = base.replace('_', '-')
            dot_sep = base.replace('_', '.')
            space_sep = base.replace('_', ' ')
            camel = self._to_camel_case(base)
            pascal = self._to_pascal_case(base)
            
            for variant in [no_sep, kebab, dot_sep, space_sep, camel, pascal]:
                if variant:
                    variants.update([variant, variant.upper(), variant.title()])
        
        if re.search(r'[a-z][A-Z]', term):
            snake = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', term).lower()
            if snake != term.lower() and snake not in self.morphology_cache:
                variants.update(self.generate_morphological_variants(snake, max_depth - 1))
        
        abbreviations = {
            'identifier': ['id', 'ID', 'ident'], 'number': ['num', 'no', 'nbr', '#'],
            'hostname': ['host', 'hn'], 'address': ['addr', 'add'],
            'description': ['desc', 'descr'], 'timestamp': ['ts', 'tstamp'],
            'date': ['dt'], 'type': ['typ'], 'configuration': ['config', 'cfg'],
            'information': ['info'], 'organization': ['org'], 'department': ['dept'],
            'application': ['app'], 'operating': ['os'], 'system': ['sys'],
            'security': ['sec'], 'network': ['net'], 'database': ['db']
        }
        
        for full_word, abbrevs in abbreviations.items():
            if full_word in base and max_depth > 1:
                for abbrev in abbrevs:
                    abbreviated = base.replace(full_word, abbrev)
                    if abbreviated != term and abbreviated not in self.morphology_cache:
                        variants.update(self.generate_morphological_variants(abbreviated, max_depth - 1))
            
            for abbrev in abbrevs:
                if abbrev.lower() in base and max_depth > 1:
                    expanded = base.replace(abbrev.lower(), full_word)
                    if expanded != term and expanded not in self.morphology_cache:
                        variants.update(self.generate_morphological_variants(expanded, max_depth - 1))
        
        if base.endswith('s') and len(base) > 3 and max_depth > 1:
            singular = base[:-1]
            if singular != base and singular not in self.morphology_cache:
                variants.update(self.generate_morphological_variants(singular, max_depth - 1))
        elif not base.endswith('s'):
            plural = base + 's'
            variants.add(plural)
        
        variants = {v for v in variants if v and len(v) > 0}
        self.morphology_cache[term] = variants
        return variants
    
    def _to_camel_case(self, snake_str: str) -> str:
        components = snake_str.split('_')
        return components[0] + ''.join(x.capitalize() for x in components[1:])
    
    def _to_pascal_case(self, snake_str: str) -> str:
        return ''.join(x.capitalize() for x in snake_str.split('_'))
    
    def analyze_field_semantics(self, field_name: str, table_context: Dict[str, Any]) -> Dict[str, Any]:
        normalized = self._normalize_field_name(field_name)
        semantic_scores = {}
        
        for concept_name, concept_data in self.concept_graph.items():
            score_components = {
                'exact_match': 0.0,
                'pattern_match': 0.0,
                'cluster_similarity': 0.0,
                'context_boost': 0.0,
                'validation_match': 0.0
            }
            
            reasoning = []
            depth = 0
            
            expanded_patterns = self._expand_concept_patterns(concept_data)
            if field_name in expanded_patterns:
                score_components['exact_match'] = 1.0
                reasoning.append(f"exact_match:{field_name}")
                depth = 3
            elif normalized in {self._normalize_field_name(p) for p in expanded_patterns}:
                score_components['exact_match'] = 0.95
                reasoning.append(f"normalized_exact:{normalized}")
                depth = max(depth, 2)
            
            for pattern in expanded_patterns:
                norm_pattern = self._normalize_field_name(pattern)
                if len(norm_pattern) >= 3:
                    if norm_pattern in normalized:
                        match_ratio = len(norm_pattern) / len(normalized)
                        subscore = match_ratio * 0.8
                        score_components['pattern_match'] = max(score_components['pattern_match'], subscore)
                        if subscore > 0.3:
                            reasoning.append(f"contains:{pattern}({subscore:.3f})")
                            depth = max(depth, 1)
            
            cluster_score = self._calculate_enhanced_cluster_similarity(normalized, concept_data)
            score_components['cluster_similarity'] = cluster_score * 0.4
            if cluster_score > 0.5:
                reasoning.append(f"cluster_match({cluster_score:.3f})")
            
            context_boost = self._calculate_context_boost(table_context, concept_name)
            score_components['context_boost'] = context_boost * 0.3
            if context_boost > 0.3:
                reasoning.append(f"context_boost({context_boost:.3f})")
            
            validation_score = self._validate_against_patterns(field_name, concept_data)
            score_components['validation_match'] = validation_score * 0.2
            if validation_score > 0.5:
                reasoning.append(f"validation_match({validation_score:.3f})")
            
            total_score = sum(score_components.values())
            
            business_multiplier = concept_data['business_priority'] / 10.0
            total_score *= business_multiplier
            
            if total_score > 0.1:
                semantic_scores[concept_name] = {
                    'score': min(total_score, 1.0),
                    'score_components': score_components,
                    'reasoning': reasoning,
                    'semantic_depth': depth,
                    'business_priority': concept_data['business_priority'],
                    'confidence_raw': total_score
                }
        
        return semantic_scores
    
    def _expand_concept_patterns(self, concept_data: Dict[str, Any]) -> Set[str]:
        if 'expanded_patterns' in concept_data:
            return concept_data['expanded_patterns']
        
        patterns = set()
        
        for key, terms in concept_data.items():
            if key in ['compound_rules', 'semantic_weight', 'business_priority', 'validation_patterns', 'expanded_patterns']:
                continue
            if isinstance(terms, list):
                for term in terms:
                    if isinstance(term, str):
                        patterns.update(self.generate_morphological_variants(term))
        
        for rule in concept_data.get('compound_rules', []):
            group1_key, group2_key = rule
            group1 = concept_data.get(group1_key, [])
            group2 = concept_data.get(group2_key, []) if isinstance(group2_key, str) else group2_key
            
            # Ensure group2 is a list
            if not isinstance(group2, list):
                group2 = list(group2) if group2 else []
            
            if isinstance(group1, list) and isinstance(group2, list):
                for term1, term2 in product(group1, group2):
                    if isinstance(term1, str) and isinstance(term2, str):
                        compound_patterns = [
                            f"{term1}_{term2}", f"{term2}_{term1}",
                            f"{term1}{term2}", f"{term2}{term1}",
                            f"{term1}-{term2}", f"{term2}-{term1}"
                        ]
                        for compound in compound_patterns:
                            patterns.update(self.generate_morphological_variants(compound))
        
        concept_data['expanded_patterns'] = patterns
        return patterns
    
    def _normalize_field_name(self, field_name: str) -> str:
        normalized = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', field_name)
        normalized = re.sub(r'[.\-\s/\\]+', '_', normalized)
        normalized = re.sub(r'_+', '_', normalized)
        return normalized.strip('_').lower()
    
    def _calculate_enhanced_cluster_similarity(self, normalized_field: str, concept_data: Dict[str, Any]) -> float:
        field_tokens = set(normalized_field.split('_'))
        max_similarity = 0.0
        
        for cluster_name, cluster_terms in self.semantic_clusters.items():
            exact_matches = field_tokens & set(cluster_terms)
            if exact_matches:
                exact_similarity = len(exact_matches) / len(field_tokens)
                max_similarity = max(max_similarity, exact_similarity)
            
            partial_matches = 0
            for field_token in field_tokens:
                for cluster_term in cluster_terms:
                    if cluster_term in field_token or field_token in cluster_term:
                        if abs(len(cluster_term) - len(field_token)) <= 2:
                            partial_matches += 0.5
            
            if partial_matches > 0:
                partial_similarity = partial_matches / len(field_tokens)
                max_similarity = max(max_similarity, partial_similarity * 0.7)
        
        return min(max_similarity, 1.0)
    
    def _calculate_context_boost(self, table_context: Dict[str, Any], concept_name: str) -> float:
        table_name = table_context.get('table_name', '').lower()
        dataset_name = table_context.get('dataset_name', '').lower()
        full_path = table_context.get('full_path', '').lower()
        
        combined_context = f"{dataset_name} {table_name} {full_path}"
        
        concept_keywords = {
            'asset_identity': ['asset', 'inventory', 'cmdb', 'device', 'host', 'computer', 'machine'],
            'infrastructure_classification': ['infrastructure', 'platform', 'deployment', 'cloud', 'aws', 'azure'],
            'geographic_context': ['location', 'geo', 'region', 'site', 'country', 'datacenter'],
            'security_posture': ['security', 'agent', 'edr', 'protection', 'crowdstrike', 'tanium'],
            'logging_telemetry': ['log', 'audit', 'splunk', 'chronicle', 'siem', 'ingestion'],
            'business_context': ['business', 'organization', 'department', 'application', 'cost'],
            'temporal_context': ['time', 'date', 'timestamp', 'created', 'modified', 'event']
        }
        
        keywords = concept_keywords.get(concept_name, [])
        if not keywords:
            return 0.0
        
        total_weight = 0.0
        for keyword in keywords:
            if keyword in combined_context:
                weight = 1.0 / max(len(keyword), 3)
                total_weight += weight
        
        boost = total_weight / len(keywords)
        
        table_metrics = table_context.get('table_metrics', {})
        if isinstance(table_metrics, dict):
            if table_metrics.get('row_count', 0) > 100000:
                boost *= 1.1
            if 'prod' in combined_context:
                boost *= 1.2
        
        return min(boost, 1.0)
    
    def _validate_against_patterns(self, field_name: str, concept_data: Dict[str, Any]) -> float:
        validation_patterns = concept_data.get('validation_patterns', [])
        if not validation_patterns:
            return 0.0
        
        field_lower = field_name.lower()
        
        pattern_indicators = {
            'uuid': ['uuid', 'guid', 'id'],
            'timestamp': ['time', 'date', 'created', 'modified'],
            'country_code': ['country', 'region', 'location'],
            'status': ['status', 'state', 'enabled'],
            'version': ['version', 'build', 'release']
        }
        
        score = 0.0
        for pattern in validation_patterns:
            for indicator_type, indicators in pattern_indicators.items():
                if any(indicator in field_lower for indicator in indicators):
                    if indicator_type in pattern.lower() or any(keyword in pattern for keyword in indicators):
                        score += 0.3
        
        return min(score, 1.0)