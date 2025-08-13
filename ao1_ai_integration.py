#!/usr/bin/env python3

import asyncio
import logging
import json
import threading
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import statistics
import hashlib

from enhanced_ai_intelligence import (
    AO1SuperIntelligentEngine, 
    AIInsight,
    AO1VisibilityPatternRecognizer,
    AO1AssetGraphAnalyzer,
    AO1VisibilityAnomalyDetector
)

logger = logging.getLogger(__name__)

@dataclass
class AO1DiscoveryResult:
    discovery_stats: Dict[str, Any]
    ai_insights: List[AIInsight]
    visibility_analysis: Dict[str, Any]
    anomaly_detection: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    recommendations: List[str]
    confidence_summary: Dict[str, float]
    visibility_metrics: Dict[str, Any]

class AO1AIContentMatcher:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.super_engine = AO1SuperIntelligentEngine(config)
        self.ai_enabled = config.get('enable_ai_classification', True)
        self.fallback_matcher = None
        
        self.classification_cache = {}
        self.performance_stats = {
            'ai_classifications': 0,
            'fallback_classifications': 0,
            'cache_hits': 0,
            'total_processing_time': 0.0,
            'visibility_enhancements': 0
        }
        
    async def analyze_column_with_ao1_ai(self, column_name: str, sample_values: List[str], 
                                       table_context: Dict = None) -> Optional[Tuple[str, float, Dict[str, Any]]]:
        start_time = datetime.now()
        
        cache_key = f"ao1:{column_name}:{hash(tuple(sample_values[:5]))}"
        if cache_key in self.classification_cache:
            self.performance_stats['cache_hits'] += 1
            return self.classification_cache[cache_key]
        
        try:
            if self.ai_enabled:
                result = await self.super_engine.enhanced_visibility_classification(
                    column_name, sample_values, table_context
                )
                
                field_type = result['field_type']
                confidence = result['confidence']
                metadata = result['metadata']
                
                self.performance_stats['ai_classifications'] += 1
                
                if metadata.get('visibility_score', 0) > 0.6:
                    self.performance_stats['visibility_enhancements'] += 1
                
                if confidence > 0.5:
                    classification_result = (field_type, confidence, metadata)
                    self.classification_cache[cache_key] = classification_result
                    
                    processing_time = (datetime.now() - start_time).total_seconds()
                    self.performance_stats['total_processing_time'] += processing_time
                    
                    return classification_result
            
            if self.fallback_matcher:
                result = self.fallback_matcher.analyze_column_intelligently(
                    column_name, sample_values, table_context
                )
                self.performance_stats['fallback_classifications'] += 1
                return result
            
        except Exception as e:
            logger.warning(f"AO1 AI classification failed for {column_name}: {e}")
            if self.fallback_matcher:
                return self.fallback_matcher.analyze_column_intelligently(
                    column_name, sample_values, table_context
                )
        
        return None
    
    def set_fallback_matcher(self, fallback_matcher):
        self.fallback_matcher = fallback_matcher
    
    def get_ao1_performance_stats(self) -> Dict[str, Any]:
        total_classifications = (self.performance_stats['ai_classifications'] + 
                               self.performance_stats['fallback_classifications'])
        
        return {
            'total_classifications': total_classifications,
            'ai_classification_rate': (self.performance_stats['ai_classifications'] / 
                                     max(total_classifications, 1)),
            'visibility_enhancement_rate': (self.performance_stats['visibility_enhancements'] / 
                                          max(self.performance_stats['ai_classifications'], 1)),
            'cache_hit_rate': (self.performance_stats['cache_hits'] / 
                             max(total_classifications, 1)),
            'avg_processing_time_ms': (self.performance_stats['total_processing_time'] / 
                                     max(self.performance_stats['ai_classifications'], 1) * 1000),
            'performance_stats': self.performance_stats.copy()
        }

class AO1EnhancedDiscoveryEngine:
    def __init__(self, project_id: str, config: Dict[str, Any], 
                 cache_manager=None, original_content_matcher=None, intelligence_engine=None):
        self.project_id = project_id
        self.config = config
        self.cache_manager = cache_manager
        self.intelligence_engine = intelligence_engine
        
        self.ai_content_matcher = AO1AIContentMatcher(config)
        self.super_engine = AO1SuperIntelligentEngine(config)
        
        if original_content_matcher:
            self.ai_content_matcher.set_fallback_matcher(original_content_matcher)
        
        self.discovered_assets = []
        self.processing_lock = threading.RLock()
        
        self.ai_insights = []
        self.visibility_analysis = {}
        self.anomaly_results = {}
        
        logger.info("AO1 AI-Enhanced Discovery Engine initialized")
    
    async def execute_ao1_enhanced_discovery(self, intelligence_result: Dict[str, Any] = None) -> AO1DiscoveryResult:
        logger.info("Starting AO1 AI-enhanced discovery process...")
        start_time = datetime.now()
        
        try:
            logger.info("Phase 1: AO1 visibility-focused field discovery")
            discovery_stats = await self._execute_ao1_field_discovery()
            
            logger.info("Phase 2: AO1 visibility relationship analysis")
            if len(self.discovered_assets) > 1:
                self.visibility_analysis = await self.super_engine.analyze_asset_visibility_relationships(
                    self.discovered_assets
                )
            
            logger.info("Phase 3: AO1 visibility anomaly detection")
            if len(self.discovered_assets) > 5:
                self.anomaly_results = await self.super_engine.detect_comprehensive_visibility_anomalies(
                    self.discovered_assets
                )
            
            logger.info("Phase 4: Generating AO1 visibility insights")
            ai_insights = await self._generate_ao1_insights()
            
            logger.info("Phase 5: Creating AO1 visibility recommendations")
            recommendations = await self._generate_ao1_recommendations()
            
            processing_time = (datetime.now() - start_time).total_seconds()
            performance_metrics = {
                'total_processing_time': processing_time,
                'assets_processed': len(self.discovered_assets),
                'ai_performance': self.super_engine.get_ao1_performance_summary(),
                'content_matcher_performance': self.ai_content_matcher.get_ao1_performance_stats(),
                'processing_rate': len(self.discovered_assets) / processing_time if processing_time > 0 else 0
            }
            
            visibility_metrics = self._calculate_visibility_metrics()
            confidence_summary = self._calculate_ao1_confidence_summary()
            
            result = AO1DiscoveryResult(
                discovery_stats=discovery_stats,
                ai_insights=ai_insights,
                visibility_analysis=self.visibility_analysis,
                anomaly_detection=self.anomaly_results,
                performance_metrics=performance_metrics,
                recommendations=recommendations,
                confidence_summary=confidence_summary,
                visibility_metrics=visibility_metrics
            )
            
            logger.info(f"AO1 AI-enhanced discovery completed in {processing_time:.2f} seconds")
            logger.info(f"Processed {len(self.discovered_assets)} assets with visibility analysis")
            
            return result
            
        except Exception as e:
            logger.error(f"AO1 AI-enhanced discovery failed: {e}")
            return AO1DiscoveryResult(
                discovery_stats={'error': str(e)},
                ai_insights=[],
                visibility_analysis={},
                anomaly_detection={},
                performance_metrics={},
                recommendations=[],
                confidence_summary={},
                visibility_metrics={}
            )
    
    async def _execute_ao1_field_discovery(self) -> Dict[str, Any]:
        from gcp_client import BigQueryClientManager
        client_manager = BigQueryClientManager(self.project_id)
        
        chronicle_client_manager = None
        try:
            chronicle_client_manager = BigQueryClientManager("chronicle-fisv")
        except:
            logger.warning("Chronicle access not available")
        
        source_tables = {
            'cmdb': 'prj-fisv.SAS_BI.V_DIM_ENDPOINT',
            'splunk': 'prj-fisv.SAS_BI.V_SPL_ENDPOINT_LOG',
            'crowdstrike': 'prj-fisv.SAS_BI.V_DIM_ENDPOINTAGENT'
        }
        
        if chronicle_client_manager:
            source_tables['chronicle'] = 'chronicle-fisv.datalake.events'
        
        total_assets = 0
        ai_classified_fields = 0
        visibility_enhanced_assets = 0
        
        for source_name, table_path in source_tables.items():
            try:
                client_mgr = chronicle_client_manager if source_name == 'chronicle' else client_manager
                
                assets = await self._process_table_with_ao1_ai(client_mgr, table_path, source_name)
                
                self.discovered_assets.extend(assets)
                total_assets += len(assets)
                
                for asset in assets:
                    if asset.get('ao1_enhanced', False):
                        ai_classified_fields += 1
                    if asset.get('visibility_score', 0) > 0.7:
                        visibility_enhanced_assets += 1
                
                logger.info(f"Processed {len(assets)} assets from {source_name} with AO1 AI enhancement")
                
            except Exception as e:
                logger.error(f"Failed to process {source_name} with AO1 AI: {e}")
        
        return {
            'total_assets': total_assets,
            'ai_enhanced_assets': ai_classified_fields,
            'visibility_enhanced_assets': visibility_enhanced_assets,
            'sources_processed': len(source_tables),
            'ai_classification_rate': ai_classified_fields / max(total_assets, 1),
            'visibility_enhancement_rate': visibility_enhanced_assets / max(total_assets, 1)
        }
    
    async def _process_table_with_ao1_ai(self, client_manager, table_path: str, source_name: str) -> List[Dict[str, Any]]:
        assets = []
        
        with client_manager.get_client() as client:
            try:
                table_ref = client.get_table(table_path)
                if not table_ref.schema:
                    return assets
                
                columns = [field.name for field in table_ref.schema]
                
                sample_query = f"""
                SELECT {', '.join([f'`{col}`' for col in columns[:20]])}
                FROM `{table_path}`
                WHERE RAND() < 0.01
                LIMIT 100
                """
                
                job = client.query(sample_query)
                results = list(job.result())
                
                if not results:
                    return assets
                
                field_mappings = {}
                ao1_metadata = {}
                
                for col_idx, column_name in enumerate(columns[:20]):
                    sample_values = []
                    for row in results:
                        if col_idx < len(row) and row[col_idx] is not None:
                            sample_values.append(str(row[col_idx]))
                    
                    if sample_values:
                        analysis_result = await self.ai_content_matcher.analyze_column_with_ao1_ai(
                            column_name, sample_values, 
                            {'table_name': table_path.split('.')[-1], 'source': source_name}
                        )
                        
                        if analysis_result:
                            field_type, confidence, metadata = analysis_result
                            if confidence > 0.6:
                                field_mappings[field_type] = column_name
                                ao1_metadata[field_type] = {
                                    'confidence': confidence,
                                    'ao1_enhanced': metadata.get('ao1_enhanced', False),
                                    'visibility_score': metadata.get('visibility_score', 0),
                                    'log_visibility_score': metadata.get('log_visibility_score', 0),
                                    'cmdb_alignment_score': metadata.get('cmdb_alignment_score', 0),
                                    'security_relevance': metadata.get('security_relevance', 0)
                                }
                
                if 'hostname' in field_mappings:
                    hostname_col = field_mappings['hostname']
                    
                    extraction_query = f"""
                    SELECT *
                    FROM `{table_path}`
                    WHERE `{hostname_col}` IS NOT NULL
                    AND TRIM(`{hostname_col}`) != ''
                    LIMIT 10000
                    """
                    
                    extract_job = client.query(extraction_query)
                    extract_results = list(extract_job.result())
                    
                    all_columns = [field.name for field in table_ref.schema]
                    
                    for row in extract_results:
                        if not row or not row[all_columns.index(hostname_col)]:
                            continue
                        
                        asset = {
                            'master_asset_id': f"ao1_asset_{len(assets)}_{source_name}",
                            'source': source_name,
                            'ao1_enhanced': True,
                            'ao1_metadata': ao1_metadata,
                            'discovery_timestamp': datetime.now().isoformat()
                        }
                        
                        for field_type, column_name in field_mappings.items():
                            col_idx = all_columns.index(column_name)
                            if col_idx < len(row) and row[col_idx]:
                                asset[field_type] = str(row[col_idx]).strip()
                        
                        self._set_visibility_flags(asset, source_name)
                        self._calculate_asset_visibility_score(asset, ao1_metadata)
                        
                        if asset.get('hostname'):
                            assets.append(asset)
                
            except Exception as e:
                logger.error(f"AO1 AI processing failed for {table_path}: {e}")
        
        return assets
    
    def _set_visibility_flags(self, asset: Dict[str, Any], source_name: str):
        if source_name == 'cmdb':
            asset['found_in_cmdb'] = True
        elif source_name == 'splunk':
            asset['found_in_splunk'] = True
            asset['in_splunk'] = True
        elif source_name == 'chronicle':
            asset['found_in_chronicle'] = True
            asset['in_chronicle'] = True
        elif source_name == 'crowdstrike':
            asset['found_in_crowdstrike'] = True
            asset['has_crowdstrike'] = True
            asset['edr_coverage'] = True
    
    def _calculate_asset_visibility_score(self, asset: Dict[str, Any], ao1_metadata: Dict[str, Any]):
        visibility_factors = []
        
        log_sources = sum([
            asset.get('found_in_splunk', False),
            asset.get('found_in_chronicle', False),
            asset.get('in_gso', False)
        ])
        log_score = min(1.0, log_sources / 3.0)
        visibility_factors.append(('log_coverage', log_score, 0.4))
        
        cmdb_score = 1.0 if asset.get('found_in_cmdb') else 0.0
        visibility_factors.append(('cmdb_coverage', cmdb_score, 0.3))
        
        security_coverage = sum([
            asset.get('edr_coverage', False),
            asset.get('tanium_coverage', False),
            asset.get('dlp_coverage', False)
        ])
        security_score = min(1.0, security_coverage / 3.0)
        visibility_factors.append(('security_coverage', security_score, 0.2))
        
        field_completeness = len([f for f in ['hostname', 'ip_address', 'infrastructure_type', 
                                            'system_classification'] if asset.get(f)]) / 4.0
        visibility_factors.append(('field_completeness', field_completeness, 0.1))
        
        total_score = sum(score * weight for _, score, weight in visibility_factors)
        asset['visibility_score'] = total_score
        
        if ao1_metadata:
            ai_enhancement_score = statistics.mean([
                meta.get('visibility_score', 0) for meta in ao1_metadata.values()
            ])
            asset['ai_visibility_enhancement'] = ai_enhancement_score
    
    async def _generate_ao1_insights(self) -> List[AIInsight]:
        insights = []
        
        if self.discovered_assets:
            visibility_scores = [asset.get('visibility_score', 0) for asset in self.discovered_assets]
            avg_visibility = statistics.mean(visibility_scores)
            
            high_visibility_assets = sum(1 for score in visibility_scores if score > 0.8)
            low_visibility_assets = sum(1 for score in visibility_scores if score < 0.3)
            
            insights.append(AIInsight(
                insight_type="ao1_visibility_analysis",
                confidence=0.95,
                content=f"Average visibility score: {avg_visibility:.2f}, {high_visibility_assets} high-visibility assets, {low_visibility_assets} low-visibility assets",
                evidence=[
                    f"Analyzed {len(self.discovered_assets)} assets for visibility",
                    f"Visibility score range: {min(visibility_scores):.2f} - {max(visibility_scores):.2f}"
                ],
                recommendations=[
                    "Focus on improving visibility for low-scoring assets",
                    "Leverage high-visibility assets as templates for best practices"
                ],
                metadata={'avg_visibility': avg_visibility, 'high_visibility_count': high_visibility_assets}
            ))
            
            log_coverage = sum(1 for asset in self.discovered_assets 
                             if asset.get('found_in_splunk') or asset.get('found_in_chronicle'))
            log_coverage_rate = log_coverage / len(self.discovered_assets)
            
            cmdb_coverage = sum(1 for asset in self.discovered_assets if asset.get('found_in_cmdb'))
            cmdb_coverage_rate = cmdb_coverage / len(self.discovered_assets)
            
            security_coverage = sum(1 for asset in self.discovered_assets 
                                  if asset.get('edr_coverage') or asset.get('dlp_coverage'))
            security_coverage_rate = security_coverage / len(self.discovered_assets)
            
            insights.append(AIInsight(
                insight_type="ao1_coverage_analysis",
                confidence=0.9,
                content=f"Coverage rates - Log: {log_coverage_rate:.1%}, CMDB: {cmdb_coverage_rate:.1%}, Security: {security_coverage_rate:.1%}",
                evidence=[
                    f"Log coverage: {log_coverage}/{len(self.discovered_assets)} assets",
                    f"CMDB coverage: {cmdb_coverage}/{len(self.discovered_assets)} assets",
                    f"Security coverage: {security_coverage}/{len(self.discovered_assets)} assets"
                ],
                recommendations=self._generate_coverage_recommendations(log_coverage_rate, cmdb_coverage_rate, security_coverage_rate)
            ))
        
        if self.visibility_analysis:
            visibility_clusters = self.visibility_analysis.get('visibility_clusters', [])
            visibility_gaps = self.visibility_analysis.get('visibility_gaps', [])
            
            if visibility_clusters:
                insights.append(AIInsight(
                    insight_type="ao1_relationship_analysis",
                    confidence=0.85,
                    content=f"Identified {len(visibility_clusters)} visibility clusters with {len(visibility_gaps)} assets having visibility gaps",
                    evidence=[
                        f"Visibility network analysis completed",
                        f"Found {len(visibility_gaps)} isolated assets"
                    ],
                    recommendations=[
                        "Review isolated assets for missing log sources",
                        "Investigate visibility clusters for optimization opportunities"
                    ]
                ))
        
        if self.anomaly_results:
            anomaly_summary = self.anomaly_results.get('anomaly_summary', {})
            critical_anomalies = anomaly_summary.get('critical_anomalies', 0)
            
            if critical_anomalies > 0:
                insights.append(AIInsight(
                    insight_type="ao1_anomaly_detection",
                    confidence=0.8,
                    content=f"Detected {critical_anomalies} critical visibility anomalies requiring immediate attention",
                    evidence=[
                        f"Total anomalies: {anomaly_summary.get('total_anomalies', 0)}",
                        f"Critical issues: {critical_anomalies}"
                    ],
                    recommendations=self.anomaly_results.get('recommendations', [])
                ))
        
        return insights
    
    def _generate_coverage_recommendations(self, log_rate: float, cmdb_rate: float, security_rate: float) -> List[str]:
        recommendations = []
        
        if log_rate < 0.7:
            recommendations.append("Improve log collection coverage - below 70% threshold")
        
        if cmdb_rate < 0.8:
            recommendations.append("Update CMDB with missing asset information")
        
        if security_rate < 0.6:
            recommendations.append("Deploy security agents to uncovered assets")
        
        if log_rate > 0.9 and cmdb_rate > 0.9:
            recommendations.append("Excellent coverage achieved - focus on data quality")
        
        return recommendations
    
    async def _generate_ao1_recommendations(self) -> List[str]:
        recommendations = []
        
        ai_performance = self.super_engine.get_ao1_performance_summary()
        if ai_performance.get('avg_visibility_score', 0) < 0.7:
            recommendations.append("Enhance visibility instrumentation - AI analysis shows gaps")
        
        content_performance = self.ai_content_matcher.get_ao1_performance_stats()
        if content_performance.get('visibility_enhancement_rate', 0) < 0.6:
            recommendations.append("Increase visibility-focused AI classification usage")
        
        if self.discovered_assets:
            visibility_gaps = sum(1 for asset in self.discovered_assets 
                                if asset.get('visibility_score', 0) < 0.3)
            
            if visibility_gaps > len(self.discovered_assets) * 0.2:
                recommendations.append("Critical: 20%+ of assets have poor visibility - immediate action required")
        
        if self.visibility_analysis:
            network_gaps = len(self.visibility_analysis.get('visibility_gaps', []))
            if network_gaps > 10:
                recommendations.append("Review network visibility architecture - many isolated assets detected")
        
        if self.anomaly_results:
            critical_count = self.anomaly_results.get('anomaly_summary', {}).get('critical_anomalies', 0)
            if critical_count > 5:
                recommendations.append("Address critical visibility anomalies immediately")
        
        if not recommendations:
            recommendations = [
                "AO1 visibility analysis completed successfully",
                "Continue monitoring visibility metrics and asset coverage",
                "Consider expanding AI-driven visibility analysis capabilities"
            ]
        
        return recommendations
    
    def _calculate_visibility_metrics(self) -> Dict[str, Any]:
        if not self.discovered_assets:
            return {}
        
        total_assets = len(self.discovered_assets)
        
        log_coverage = {
            'splunk': sum(1 for asset in self.discovered_assets if asset.get('found_in_splunk')),
            'chronicle': sum(1 for asset in self.discovered_assets if asset.get('found_in_chronicle')),
            'gso': sum(1 for asset in self.discovered_assets if asset.get('in_gso'))
        }
        
        security_coverage = {
            'edr': sum(1 for asset in self.discovered_assets if asset.get('edr_coverage')),
            'dlp': sum(1 for asset in self.discovered_assets if asset.get('dlp_coverage')),
            'tanium': sum(1 for asset in self.discovered_assets if asset.get('tanium_coverage'))
        }
        
        cmdb_coverage = sum(1 for asset in self.discovered_assets if asset.get('found_in_cmdb'))
        
        visibility_scores = [asset.get('visibility_score', 0) for asset in self.discovered_assets]
        
        from collections import defaultdict
        infrastructure_breakdown = defaultdict(int)
        for asset in self.discovered_assets:
            infra_type = asset.get('infrastructure_type', 'unknown')
            infrastructure_breakdown[infra_type] += 1
        
        return {
            'total_assets': total_assets,
            'log_coverage': log_coverage,
            'security_coverage': security_coverage,
            'cmdb_coverage': cmdb_coverage,
            'visibility_score_stats': {
                'mean': statistics.mean(visibility_scores),
                'median': statistics.median(visibility_scores),
                'min': min(visibility_scores),
                'max': max(visibility_scores)
            },
            'coverage_rates': {
                'log_total': sum(log_coverage.values()) / total_assets,
                'security_total': sum(security_coverage.values()) / total_assets,
                'cmdb_rate': cmdb_coverage / total_assets
            },
            'infrastructure_breakdown': dict(infrastructure_breakdown)
        }
    
    def _calculate_ao1_confidence_summary(self) -> Dict[str, float]:
        confidence_factors = {}
        
        ai_performance = self.super_engine.get_ao1_performance_summary()
        if ai_performance.get('status') != 'no_data':
            confidence_factors['ai_classification'] = ai_performance.get('avg_confidence', 0.5)
            confidence_factors['visibility_enhancement'] = ai_performance.get('avg_visibility_score', 0.5)
        
        content_performance = self.ai_content_matcher.get_ao1_performance_stats()
        confidence_factors['content_matching'] = content_performance.get('ai_classification_rate', 0.5)
        confidence_factors['visibility_focus'] = content_performance.get('visibility_enhancement_rate', 0.5)
        
        overall_confidence = statistics.mean(confidence_factors.values()) if confidence_factors else 0.5
        confidence_factors['overall'] = overall_confidence
        
        return confidence_factors