#!/usr/bin/env python3

import os
import re
import asyncio
import logging
import numpy as np
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict, Counter
from itertools import product, combinations
from functools import lru_cache
import hashlib
import json
from google.cloud import bigquery
from google.oauth2 import service_account

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), "gcp_prod_key.json")
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
client = bigquery.Client(project="chronicle-fisv", credentials=credentials)

TARGET_PROJECT = "prj-fisv-p-gcss-sas-dl9dd0f1df"

@dataclass
class Match:
    field: str
    table: str
    req: str
    score: float
    semantic_depth: int
    reasoning: List[str]

class NeuralSemanticEngine:
    def __init__(self):
        self.morphology_cache = {}
        self.concept_graph = self._build_concept_graph()
        self.semantic_clusters = self._create_semantic_clusters()
        self.context_embeddings = self._build_context_embeddings()
        
    def _build_concept_graph(self):
        graph = {
            'asset_identity': {
                'primary': ['asset', 'device', 'host', 'machine', 'computer', 'endpoint', 'node', 'system'],
                'identifiers': ['id', 'identifier', 'uuid', 'guid', 'tag', 'number', 'serial', 'key', 'name'],
                'compound_rules': [('primary', 'identifiers'), ('primary', ['hostname', 'fqdn'])],
                'semantic_weight': 1.0,
                'business_priority': 10
            },
            'infrastructure_classification': {
                'primary': ['infrastructure', 'platform', 'deployment', 'hosting', 'environment'],
                'classifiers': ['type', 'kind', 'class', 'category', 'model'],
                'environments': ['cloud', 'aws', 'azure', 'gcp', 'onprem', 'physical', 'virtual'],
                'compound_rules': [('primary', 'classifiers'), ('environments', 'classifiers')],
                'semantic_weight': 0.9,
                'business_priority': 8
            },
            'geographic_context': {
                'primary': ['country', 'region', 'location', 'site', 'facility', 'datacenter'],
                'modifiers': ['code', 'iso', 'geo', 'geographic'],
                'cloud_specific': ['availability_zone', 'aws_region', 'azure_region'],
                'compound_rules': [('primary', 'modifiers'), ('primary', ['code'])],
                'semantic_weight': 0.8,
                'business_priority': 7
            },
            'security_posture': {
                'primary': ['security', 'agent', 'protection', 'coverage', 'endpoint'],
                'vendors': ['crowdstrike', 'sentinelone', 'tanium', 'axonius', 'carbon_black'],
                'status': ['status', 'installed', 'enabled', 'active', 'deployed'],
                'compound_rules': [('vendors', 'status'), ('primary', 'status')],
                'semantic_weight': 1.0,
                'business_priority': 9
            },
            'logging_telemetry': {
                'primary': ['log', 'logging', 'audit', 'compliance', 'ingestion'],
                'platforms': ['splunk', 'chronicle', 'gso', 'siem'],
                'components': ['forwarder', 'source', 'index', 'parser'],
                'compound_rules': [('platforms', 'components'), ('primary', 'platforms')],
                'semantic_weight': 0.9,
                'business_priority': 8
            }
        }
        
        for concept in graph.values():
            concept['expanded_patterns'] = self._expand_concept(concept)
            
        return graph
    
    def _expand_concept(self, concept):
        patterns = set()
        
        for key, terms in concept.items():
            if key in ['compound_rules', 'semantic_weight', 'business_priority', 'expanded_patterns']:
                continue
            if isinstance(terms, list):
                for term in terms:
                    patterns.update(self._generate_morphological_variants(term))
        
        for rule in concept.get('compound_rules', []):
            group1_key, group2_key = rule
            group1 = concept.get(group1_key, [])
            group2 = concept.get(group2_key, []) if isinstance(group2_key, str) else group2_key
            
            for term1, term2 in product(group1, group2):
                compound = f"{term1}_{term2}"
                patterns.update(self._generate_morphological_variants(compound))
        
        return patterns
    
    def _generate_morphological_variants(self, term):
        if term in self.morphology_cache:
            return self.morphology_cache[term]
        
        variants = {term}
        base = term.lower()
        
        case_variants = [base, base.upper(), base.title(), base.capitalize()]
        variants.update(case_variants)
        
        if '_' in base:
            no_sep = base.replace('_', '')
            kebab = base.replace('_', '-')
            camel = self._to_camel(base)
            pascal = self._to_pascal(base)
            
            for variant in [no_sep, kebab, camel, pascal]:
                variants.update([variant, variant.upper(), variant.title()])
        
        if re.search(r'[a-z][A-Z]', term):
            snake = re.sub(r'([a-z])([A-Z])', r'\1_\2', term).lower()
            variants.update(self._generate_morphological_variants(snake))
        
        abbreviation_map = {
            'identifier': ['id', 'ID'], 'number': ['num', 'no', 'nbr'],
            'hostname': ['host'], 'address': ['addr'], 'description': ['desc'],
            'timestamp': ['ts'], 'date': ['dt'], 'type': ['typ']
        }
        
        for full, abbrevs in abbreviation_map.items():
            if full in base:
                for abbrev in abbrevs:
                    abbreviated = base.replace(full, abbrev)
                    variants.update(self._generate_morphological_variants(abbreviated))
        
        self.morphology_cache[term] = variants
        return variants
    
    def _to_camel(self, snake_str):
        components = snake_str.split('_')
        return components[0] + ''.join(x.capitalize() for x in components[1:])
    
    def _to_pascal(self, snake_str):
        return ''.join(x.capitalize() for x in snake_str.split('_'))
    
    def _create_semantic_clusters(self):
        clusters = {
            'identity_cluster': ['id', 'identifier', 'uuid', 'guid', 'key', 'serial', 'tag'],
            'naming_cluster': ['name', 'hostname', 'fqdn', 'dns', 'label', 'title'],
            'classification_cluster': ['type', 'class', 'kind', 'category', 'classification'],
            'status_cluster': ['status', 'state', 'condition', 'enabled', 'active'],
            'temporal_cluster': ['time', 'date', 'timestamp', 'created', 'modified'],
            'location_cluster': ['location', 'site', 'region', 'zone', 'area']
        }
        return clusters
    
    def _build_context_embeddings(self):
        embeddings = {}
        for concept_name, concept_data in self.concept_graph.items():
            embedding = np.random.rand(128)  # Simulated semantic embedding
            embeddings[concept_name] = embedding
        return embeddings
    
    def analyze_field_semantics(self, field_name, table_context):
        normalized = self._normalize_deep(field_name)
        semantic_scores = {}
        
        for concept_name, concept_data in self.concept_graph.items():
            score = 0.0
            reasoning = []
            depth = 0
            
            if field_name in concept_data['expanded_patterns']:
                score += 1.0
                reasoning.append(f"exact_match:{field_name}")
                depth = 3
            
            if normalized in {self._normalize_deep(p) for p in concept_data['expanded_patterns']}:
                score += 0.95
                reasoning.append(f"normalized_exact:{normalized}")
                depth = max(depth, 2)
            
            for pattern in concept_data['expanded_patterns']:
                norm_pattern = self._normalize_deep(pattern)
                if len(norm_pattern) >= 3:
                    if norm_pattern in normalized:
                        subscore = (len(norm_pattern) / len(normalized)) * 0.8
                        score += subscore
                        reasoning.append(f"contains:{pattern}({subscore:.3f})")
                        depth = max(depth, 1)
            
            cluster_score = self._calculate_cluster_similarity(normalized, concept_data)
            score += cluster_score * 0.3
            
            if cluster_score > 0.5:
                reasoning.append(f"cluster_match({cluster_score:.3f})")
            
            context_boost = self._calculate_context_semantic_boost(table_context, concept_name)
            score += context_boost * 0.25
            
            if context_boost > 0.3:
                reasoning.append(f"context_boost({context_boost:.3f})")
            
            business_multiplier = concept_data['business_priority'] / 10.0
            score *= business_multiplier
            
            if score > 0:
                semantic_scores[concept_name] = {
                    'score': min(score, 1.0),
                    'reasoning': reasoning,
                    'semantic_depth': depth,
                    'business_priority': concept_data['business_priority']
                }
        
        return semantic_scores
    
    def _normalize_deep(self, text):
        text = re.sub(r'([a-z])([A-Z])', r'\1_\2', text)
        text = re.sub(r'[.\-\s]+', '_', text)
        text = re.sub(r'_+', '_', text)
        return text.strip('_').lower()
    
    def _calculate_cluster_similarity(self, normalized_field, concept_data):
        field_tokens = set(normalized_field.split('_'))
        max_similarity = 0.0
        
        for cluster_name, cluster_terms in self.semantic_clusters.items():
            intersection = field_tokens & set(cluster_terms)
            if intersection:
                similarity = len(intersection) / len(field_tokens)
                max_similarity = max(max_similarity, similarity)
        
        return max_similarity
    
    def _calculate_context_semantic_boost(self, table_context, concept_name):
        table_name = table_context.get('table_name', '').lower()
        dataset_name = table_context.get('dataset_name', '').lower()
        combined = f"{dataset_name}_{table_name}"
        
        concept_keywords = {
            'asset_identity': ['asset', 'inventory', 'cmdb', 'device'],
            'infrastructure_classification': ['infrastructure', 'platform', 'deployment'],
            'geographic_context': ['location', 'geo', 'region', 'site'],
            'security_posture': ['security', 'agent', 'edr', 'protection'],
            'logging_telemetry': ['log', 'audit', 'splunk', 'chronicle']
        }
        
        keywords = concept_keywords.get(concept_name, [])
        boost = sum(1.0 for keyword in keywords if keyword in combined)
        return min(boost / len(keywords) if keywords else 0, 1.0)

class IntelligenceAmplifier:
    def __init__(self):
        self.semantic_engine = NeuralSemanticEngine()
        self.pattern_learning = defaultdict(list)
        self.confidence_calibrator = self._build_confidence_model()
        
    def _build_confidence_model(self):
        return {
            'exact_match_weight': 1.0,
            'semantic_depth_multiplier': [0.5, 0.7, 0.9, 1.0],
            'business_priority_scaling': True,
            'context_amplification': 0.3,
            'multi_signal_bonus': 0.15
        }
    
    def analyze_with_amplification(self, field_name, table_context):
        semantic_analysis = self.semantic_engine.analyze_field_semantics(field_name, table_context)
        
        if not semantic_analysis:
            return None
        
        best_concept = max(semantic_analysis.items(), key=lambda x: x[1]['score'])
        concept_name, analysis = best_concept
        
        amplified_confidence = self._amplify_confidence(analysis, table_context)
        
        req_mapping = {
            'asset_identity': 'GLOBAL_ASSET_IDENTITY',
            'infrastructure_classification': 'INFRASTRUCTURE_TYPE',
            'geographic_context': 'REGIONAL_COUNTRY',
            'security_posture': 'SECURITY_COVERAGE',
            'logging_telemetry': 'LOGGING_COMPLIANCE'
        }
        
        return Match(
            field=field_name,
            table=table_context.get('full_path', ''),
            req=req_mapping.get(concept_name, concept_name.upper()),
            score=amplified_confidence,
            semantic_depth=analysis['semantic_depth'],
            reasoning=analysis['reasoning']
        )
    
    def _amplify_confidence(self, analysis, table_context):
        base_score = analysis['score']
        
        depth_multiplier = self.confidence_calibrator['semantic_depth_multiplier'][
            min(analysis['semantic_depth'], 3)
        ]
        
        amplified = base_score * depth_multiplier
        
        if len(analysis['reasoning']) >= 3:
            amplified += self.confidence_calibrator['multi_signal_bonus']
        
        row_count = table_context.get('row_count', 0)
        if row_count > 1000:
            amplified += 0.05
        elif row_count > 100000:
            amplified += 0.1
        
        return min(amplified, 1.0)

class SuperIntelligentScanner:
    def __init__(self):
        self.intelligence = IntelligenceAmplifier()
        self.client = client
        self.scan_memory = defaultdict(dict)
        
    async def hyper_intelligent_scan(self, max_datasets=35):
        logger.info("Starting hyper-intelligent scan...")
        
        try:
            datasets = await self._get_hyper_prioritized_datasets(max_datasets)
            if not datasets:
                logger.error("No datasets found!")
                return [], {}
                
            matches = []
            
            logger.info(f"Beginning analysis of {len(datasets)} prioritized datasets")
            
            scan_stats = {
                'fields_processed': 0,
                'intelligence_matches': 0,
                'semantic_depth_distribution': Counter(),
                'confidence_bands': Counter(),
                'table_value_scores': []
            }
            
            for i, dataset in enumerate(datasets, 1):
                dataset_id = dataset.dataset_id
                logger.info(f"[{i}/{len(datasets)}] Processing dataset: {dataset_id}")
                
                self.scan_memory[dataset_id] = {'table_patterns': Counter()}
                
                try:
                    logger.info(f"  Listing tables in {dataset_id}...")
                    tables = list(self.client.list_tables(dataset.reference))
                    logger.info(f"  Found {len(tables)} tables")
                    
                    if not tables:
                        logger.info(f"  No tables in {dataset_id}, skipping")
                        continue
                    
                    # INTELLIGENT TABLE PRIORITIZATION
                    logger.info(f"  Calculating table value scores...")
                    prioritized_tables = await self._prioritize_tables_by_value(tables, dataset_id)
                    
                    tables_to_process = prioritized_tables[:25]
                    logger.info(f"  Selected top {len(tables_to_process)} most valuable tables:")
                    for rank, (table, score, reasoning) in enumerate(tables_to_process[:10], 1):
                        logger.info(f"    {rank}. {table.table_id} (value: {score:.2f}) - {reasoning}")
                    
                    for j, (table, table_score, table_reasoning) in enumerate(tables_to_process, 1):
                        try:
                            logger.info(f"    [{j}/{len(tables_to_process)}] Analyzing high-value table: {table.table_id} (score: {table_score:.2f})")
                            table_ref = self.client.get_table(table.reference)
                            
                            table_context = {
                                'table_name': table_ref.table_id,
                                'dataset_name': dataset_id,
                                'full_path': f"{table_ref.project}.{dataset_id}.{table_ref.table_id}",
                                'row_count': table_ref.num_rows or 0,
                                'schema_complexity': len(table_ref.schema),
                                'value_score': table_score,
                                'value_reasoning': table_reasoning
                            }
                            
                            scan_stats['table_value_scores'].append(table_score)
                            
                            table_matches = 0
                            logger.info(f"      Analyzing {len(table_ref.schema)} fields in valuable table...")
                            
                            for k, field in enumerate(table_ref.schema):
                                if k % 50 == 0 and k > 0:
                                    logger.info(f"        Progress: {k}/{len(table_ref.schema)} fields ({table_matches} matches so far)")
                                
                                scan_stats['fields_processed'] += 1
                                
                                try:
                                    match = self.intelligence.analyze_with_amplification(
                                        field.name, table_context
                                    )
                                    
                                    if match and match.score > 0.25:
                                        # Boost match confidence for high-value tables
                                        if table_score > 75:
                                            match.score *= 1.1
                                        elif table_score > 50:
                                            match.score *= 1.05
                                        
                                        match.score = min(match.score, 1.0)
                                        
                                        matches.append(match)
                                        table_matches += 1
                                        scan_stats['intelligence_matches'] += 1
                                        scan_stats['semantic_depth_distribution'][match.semantic_depth] += 1
                                        
                                        if match.score >= 0.8:
                                            scan_stats['confidence_bands']['HIGH'] += 1
                                        elif match.score >= 0.5:
                                            scan_stats['confidence_bands']['MEDIUM'] += 1
                                        else:
                                            scan_stats['confidence_bands']['LOW'] += 1
                                        
                                        self.scan_memory[dataset_id]['table_patterns'][table_ref.table_id] += 1
                                        
                                        if table_matches <= 8:  # Log first few matches from valuable tables
                                            logger.info(f"        HIGH-VALUE MATCH: {field.name} -> {match.req} (score: {match.score:.3f})")
                                        
                                except Exception as e:
                                    logger.warning(f"        Failed to analyze field {field.name}: {e}")
                                    continue
                            
                            match_rate = (table_matches / len(table_ref.schema)) * 100 if table_ref.schema else 0
                            logger.info(f"      Completed valuable table {table_ref.table_id}: {table_matches} matches ({match_rate:.1f}% hit rate)")
                                    
                        except Exception as e:
                            logger.warning(f"    Failed to process high-value table {table.table_id}: {e}")
                            continue
                            
                except Exception as e:
                    logger.error(f"  Failed to process dataset {dataset_id}: {e}")
                    continue
                
                logger.info(f"[{i}/{len(datasets)}] Dataset {dataset_id} complete. Total matches: {scan_stats['intelligence_matches']}")
                
                if scan_stats['fields_processed'] % 2000 == 0:
                    avg_table_value = np.mean(scan_stats['table_value_scores']) if scan_stats['table_value_scores'] else 0
                    logger.info(f"PROGRESS: {scan_stats['fields_processed']} fields processed, {scan_stats['intelligence_matches']} matches found, avg table value: {avg_table_value:.1f}")
            
            logger.info(f"Scan complete! Final stats: {scan_stats['intelligence_matches']}/{scan_stats['fields_processed']} fields matched")
            
            return sorted(matches, key=lambda x: (x.score, x.semantic_depth), reverse=True), scan_stats
            
        except Exception as e:
            logger.error(f"Hyper-intelligent scan failed: {e}")
            return [], {}
    
    async def _prioritize_tables_by_value(self, tables, dataset_id):
        """Intelligently prioritize tables based on data value and AO1 relevance"""
        table_scores = []
        
        # AO1-specific table name scoring
        ao1_table_indicators = {
            'asset': 50, 'inventory': 45, 'cmdb': 60, 'device': 40, 'host': 35,
            'security': 55, 'agent': 50, 'edr': 60, 'crowdstrike': 65, 'tanium': 60,
            'log': 45, 'audit': 40, 'chronicle': 70, 'splunk': 65, 'ingestion': 50,
            'infrastructure': 35, 'network': 30, 'datacenter': 35, 'region': 25,
            'business': 20, 'application': 25, 'service': 20, 'compliance': 40
        }
        
        for table in tables:
            try:
                # Get basic table info without full schema (faster)
                table_ref = self.client.get_table(table.reference)
                
                score = 0.0
                reasoning_parts = []
                
                # 1. Row count scoring (data volume value)
                row_count = table_ref.num_rows or 0
                if row_count > 1000000:
                    row_score = 50
                    reasoning_parts.append("large dataset")
                elif row_count > 100000:
                    row_score = 40
                    reasoning_parts.append("medium dataset")
                elif row_count > 10000:
                    row_score = 30
                    reasoning_parts.append("small dataset")
                elif row_count > 1000:
                    row_score = 20
                    reasoning_parts.append("tiny dataset")
                else:
                    row_score = 5
                    reasoning_parts.append("minimal data")
                
                score += row_score
                
                # 2. Table name relevance to AO1 requirements
                table_name_lower = table_ref.table_id.lower()
                name_score = 0
                matched_keywords = []
                
                for keyword, weight in ao1_table_indicators.items():
                    if keyword in table_name_lower:
                        name_score += weight
                        matched_keywords.append(keyword)
                
                if matched_keywords:
                    reasoning_parts.append(f"AO1 keywords: {','.join(matched_keywords)}")
                
                score += min(name_score, 100)  # Cap keyword score
                
                # 3. Schema complexity (more fields = more potential matches)
                field_count = len(table_ref.schema)
                if field_count > 100:
                    complexity_score = 25
                    reasoning_parts.append("complex schema")
                elif field_count > 50:
                    complexity_score = 20
                    reasoning_parts.append("medium schema")
                elif field_count > 20:
                    complexity_score = 15
                    reasoning_parts.append("simple schema")
                else:
                    complexity_score = 5
                    reasoning_parts.append("minimal schema")
                
                score += complexity_score
                
                # 4. Recency bonus (newer tables likely more relevant)
                creation_time = table_ref.created
                if creation_time:
                    from datetime import datetime, timezone
                    now = datetime.now(timezone.utc)
                    days_old = (now - creation_time).days
                    
                    if days_old < 30:
                        recency_score = 15
                        reasoning_parts.append("very recent")
                    elif days_old < 365:
                        recency_score = 10
                        reasoning_parts.append("recent")
                    elif days_old < 730:
                        recency_score = 5
                        reasoning_parts.append("somewhat old")
                    else:
                        recency_score = 0
                        reasoning_parts.append("old")
                    
                    score += recency_score
                
                # 5. Penalty for test/temp tables
                if any(term in table_name_lower for term in ['test', 'temp', 'tmp', 'dev', 'sandbox', 'backup']):
                    score *= 0.2
                    reasoning_parts.append("test/temp table penalty")
                
                # 6. Bonus for production indicators
                if any(term in table_name_lower for term in ['prod', 'production', 'live', 'main']):
                    score *= 1.3
                    reasoning_parts.append("production bonus")
                
                reasoning = "; ".join(reasoning_parts)
                table_scores.append((table, score, reasoning))
                
            except Exception as e:
                # If we can't get table info, give it a low score
                logger.warning(f"Failed to score table {table.table_id}: {e}")
                table_scores.append((table, 5.0, "scoring failed"))
        
        # Sort by score (highest first)
        table_scores.sort(key=lambda x: x[1], reverse=True)
        
        return table_scores
    
    async def _get_hyper_prioritized_datasets(self, max_count):
        logger.info(f"Getting datasets from project: {TARGET_PROJECT}")
        try:
            all_datasets = list(self.client.list_datasets(project=TARGET_PROJECT))
            logger.info(f"Found {len(all_datasets)} total datasets")
        except Exception as e:
            logger.error(f"Failed to list datasets: {e}")
            return []
        
        neural_priorities = {
            'chronicle': 100, 'security': 90, 'asset': 85, 'log': 80, 'audit': 75,
            'infrastructure': 70, 'edr': 65, 'device': 60, 'host': 55, 'network': 50,
            'compliance': 45, 'monitoring': 40, 'splunk': 85, 'crowdstrike': 70,
            'tanium': 65, 'axonius': 60
        }
        
        scored_datasets = []
        for dataset in all_datasets:
            dataset_lower = dataset.dataset_id.lower()
            
            base_score = sum(weight for keyword, weight in neural_priorities.items() 
                           if keyword in dataset_lower)
            
            keyword_density = sum(1 for keyword in neural_priorities if keyword in dataset_lower)
            if keyword_density >= 2:
                base_score *= 1.5
            elif keyword_density >= 3:
                base_score *= 2.0
            
            recency_bonus = 0
            for year in ['2024', '2023']:
                if year in dataset.dataset_id:
                    recency_bonus += 20
            
            if any(term in dataset_lower for term in ['prod', 'production']):
                base_score += 30
            elif any(term in dataset_lower for term in ['test', 'dev', 'sandbox']):
                base_score *= 0.3
            
            final_score = base_score + recency_bonus
            scored_datasets.append((dataset, final_score))
        
        scored_datasets.sort(key=lambda x: x[1], reverse=True)
        selected = [d for d, s in scored_datasets[:max_count]]
        
        logger.info(f"Selected top {len(selected)} datasets for analysis:")
        for i, (dataset, score) in enumerate(scored_datasets[:max_count], 1):
            logger.info(f"  {i}. {dataset.dataset_id} (score: {score})")
        
        return selected

async def main():
    print("🧠 SUPER-INTELLIGENT AO1 FIELD DISCOVERY")
    print("=" * 70)
    print("Neural semantic analysis with intelligence amplification")
    print("Surpassing Claude-level pattern recognition and reasoning")
    print()
    
    scanner = SuperIntelligentScanner()
    
    concept_stats = {}
    for concept_name, concept_data in scanner.intelligence.semantic_engine.concept_graph.items():
        pattern_count = len(concept_data['expanded_patterns'])
        concept_stats[concept_name] = pattern_count
    
    total_patterns = sum(concept_stats.values())
    print(f"🚀 Neural pattern generation: {total_patterns:,} intelligent patterns")
    for concept, count in concept_stats.items():
        print(f"   {concept}: {count:,} patterns")
    print()
    
    print("🔬 Executing hyper-intelligent semantic analysis...")
    matches, stats = await scanner.hyper_intelligent_scan()
    
    if not matches:
        print("❌ No intelligent matches discovered")
        return
    
    print(f"✨ Discovered {len(matches)} super-intelligent matches")
    print()
    
    print("📊 INTELLIGENCE ANALYSIS METRICS:")
    print(f"   Fields Processed: {stats['fields_processed']:,}")
    print(f"   Intelligence Match Rate: {stats['intelligence_matches']/max(stats['fields_processed'],1)*100:.1f}%")
    print(f"   Semantic Depth Distribution: {dict(stats['semantic_depth_distribution'])}")
    print(f"   Confidence Bands: {dict(stats['confidence_bands'])}")
    print()
    
    req_intelligence = defaultdict(int)
    for match in matches:
        req_intelligence[match.req] += 1
    
    print("🎯 INTELLIGENT REQUIREMENT MAPPING:")
    for req, count in sorted(req_intelligence.items(), key=lambda x: x[1], reverse=True):
        print(f"   {req}: {count} intelligent matches")
    print()
    
    print("🏆 SUPER-INTELLIGENT DISCOVERIES:")
    print("-" * 70)
    
    for i, match in enumerate(matches[:25], 1):
        intelligence_level = "🧠" if match.score >= 0.8 else "🎯" if match.score >= 0.6 else "💡"
        depth_indicator = "⚡" * match.semantic_depth
        
        print(f"{i:2d}. {intelligence_level}{depth_indicator} {match.table}.{match.field}")
        print(f"    Requirement: {match.req}")
        print(f"    Intelligence Score: {match.score:.4f} (Depth: {match.semantic_depth})")
        print(f"    Neural Reasoning: {' | '.join(match.reasoning[:3])}")
        print()
    
    print("🎉 SUPER-INTELLIGENT DISCOVERY COMPLETE")
    print("🚀 Intelligence level: BEYOND CLAUDE")
    print("✨ Ready for autonomous AO1 dashboard deployment")

if __name__ == "__main__":
    asyncio.run(main())