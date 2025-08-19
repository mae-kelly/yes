# ai/intelligence.py

import asyncio
import logging
import statistics
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from core.types import QuantumDiscovery, HyperAsset

logger = logging.getLogger(__name__)

class RecommendationEngine:
    def __init__(self, config):
        self.config = config
    
    async def generate_recommendations(self, discovery: QuantumDiscovery, 
                                     insights: List[Dict[str, Any]]) -> List[str]:
        recommendations = []
        
        high_priority_insights = [i for i in insights if i.get('priority') == 'critical']
        
        if high_priority_insights:
            recommendations.append("Address critical security and compliance gaps immediately")
        
        coverage_insights = [i for i in insights if i.get('type') == 'security_coverage_analysis']
        if coverage_insights:
            recommendations.append("Implement comprehensive security tool deployment strategy")
        
        visibility_insights = [i for i in insights if 'visibility' in i.get('type', '')]
        if visibility_insights:
            recommendations.append("Enhance asset visibility and monitoring capabilities")
        
        recommendations.append("Establish continuous compliance monitoring program")
        recommendations.append("Develop incident response procedures for high-risk assets")
        
        return recommendations

class QuantumIntelligenceEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.intelligence_models = self._initialize_intelligence_models()
        self.insight_generators = self._initialize_insight_generators()
        self.recommendation_engine = self._initialize_recommendation_engine()
        
        self.analysis_cache = {}
        self.insights_history = []
        self.intelligence_metrics = {
            'insights_generated': 0,
            'recommendations_created': 0,
            'patterns_identified': 0,
            'anomalies_detected': 0,
            'correlations_found': 0
        }
    
    def _initialize_intelligence_models(self) -> Dict[str, Any]:
        return {
            'visibility_analyzer': VisibilityAnalyzer(),
            'security_analyzer': SecurityCoverageAnalyzer(),
            'risk_analyzer': RiskAssessmentAnalyzer(),
            'compliance_analyzer': ComplianceAnalyzer(),
            'pattern_analyzer': PatternAnalyzer(),
            'anomaly_detector': AnomalyDetector(),
            'correlation_engine': CorrelationEngine()
        }
    
    def _initialize_insight_generators(self) -> Dict[str, callable]:
        return {
            'asset_visibility_insights': self._generate_visibility_insights,
            'security_coverage_insights': self._generate_security_insights,
            'risk_assessment_insights': self._generate_risk_insights,
            'compliance_status_insights': self._generate_compliance_insights,
            'operational_insights': self._generate_operational_insights,
            'strategic_insights': self._generate_strategic_insights
        }
    
    def _initialize_recommendation_engine(self) -> RecommendationEngine:
        return RecommendationEngine(self.config)
    
    async def generate_insights(self, quantum_discovery: QuantumDiscovery) -> List[Dict[str, Any]]:
        logger.info("Generating comprehensive intelligence insights")
        
        if not quantum_discovery.hyper_assets:
            return []
        
        all_insights = []
        
        for insight_type, generator in self.insight_generators.items():
            try:
                insights = await generator(quantum_discovery)
                if insights:
                    all_insights.extend(insights)
                    self.intelligence_metrics['insights_generated'] += len(insights)
            except Exception as e:
                logger.error(f"Insight generation failed for {insight_type}: {e}")
        
        strategic_recommendations = await self.recommendation_engine.generate_recommendations(
            quantum_discovery, all_insights
        )
        
        quantum_discovery.strategic_recommendations = strategic_recommendations
        self.intelligence_metrics['recommendations_created'] += len(strategic_recommendations)
        
        self.insights_history.extend(all_insights)
        
        logger.info(f"Generated {len(all_insights)} insights and {len(strategic_recommendations)} recommendations")
        return all_insights
    
    async def _generate_visibility_insights(self, discovery: QuantumDiscovery) -> List[Dict[str, Any]]:
        insights = []
        assets = discovery.hyper_assets
        
        if not assets:
            return insights
        
        asset_count = len(assets)
        visibility_scores = [asset.visibility_score for asset in assets.values()]
        avg_visibility = statistics.mean(visibility_scores) if visibility_scores else 0.0
        
        insights.append({
            'type': 'asset_visibility_overview',
            'title': 'Asset Visibility Analysis',
            'content': f"Discovered {asset_count:,} assets with average visibility score of {avg_visibility:.2f}",
            'confidence': 0.95,
            'priority': 'high',
            'metrics': {
                'total_assets': asset_count,
                'avg_visibility_score': avg_visibility,
                'high_visibility_assets': len([s for s in visibility_scores if s > 0.8]),
                'medium_visibility_assets': len([s for s in visibility_scores if 0.5 <= s <= 0.8]),
                'low_visibility_assets': len([s for s in visibility_scores if s < 0.5])
            },
            'business_impact': 'critical',
            'actionable_items': self._generate_visibility_actions(visibility_scores)
        })
        
        visibility_distribution = self._analyze_visibility_distribution(visibility_scores)
        if visibility_distribution['needs_attention']:
            insights.append({
                'type': 'visibility_distribution_alert',
                'title': 'Visibility Distribution Concern',
                'content': visibility_distribution['message'],
                'confidence': 0.9,
                'priority': 'high',
                'metrics': visibility_distribution['metrics'],
                'recommended_actions': visibility_distribution['actions']
            })
        
        return insights
    
    async def _generate_security_insights(self, discovery: QuantumDiscovery) -> List[Dict[str, Any]]:
        insights = []
        assets = discovery.hyper_assets.values()
        
        security_coverage = self._analyze_security_coverage(assets)
        
        insights.append({
            'type': 'security_coverage_analysis',
            'title': 'Security Tool Coverage Assessment',
            'content': f"Security coverage analysis across {len(assets)} assets",
            'confidence': 0.9,
            'priority': 'critical',
            'metrics': security_coverage['metrics'],
            'coverage_breakdown': security_coverage['breakdown'],
            'security_gaps': security_coverage['gaps'],
            'improvement_opportunities': security_coverage['opportunities']
        })
        
        critical_gaps = self._identify_critical_security_gaps(assets)
        if critical_gaps:
            insights.append({
                'type': 'critical_security_gaps',
                'title': 'Critical Security Coverage Gaps',
                'content': f"Identified {len(critical_gaps)} assets with critical security gaps",
                'confidence': 0.95,
                'priority': 'critical',
                'affected_assets': critical_gaps,
                'immediate_actions_required': True,
                'business_risk': 'high'
            })
        
        return insights
    
    async def _generate_risk_insights(self, discovery: QuantumDiscovery) -> List[Dict[str, Any]]:
        insights = []
        assets = list(discovery.hyper_assets.values())
        
        risk_analysis = self._comprehensive_risk_analysis(assets)
        
        insights.append({
            'type': 'comprehensive_risk_assessment',
            'title': 'Enterprise Risk Analysis',
            'content': f"Risk assessment completed for {len(assets)} assets",
            'confidence': 0.9,
            'priority': 'high',
            'risk_metrics': risk_analysis['metrics'],
            'risk_distribution': risk_analysis['distribution'],
            'high_risk_assets': risk_analysis['high_risk_assets'],
            'risk_mitigation_priorities': risk_analysis['priorities']
        })
        
        business_critical_risks = self._identify_business_critical_risks(assets)
        if business_critical_risks:
            insights.append({
                'type': 'business_critical_risks',
                'title': 'Business-Critical Risk Alerts',
                'content': f"Identified {len(business_critical_risks)} business-critical risk scenarios",
                'confidence': 0.95,
                'priority': 'critical',
                'critical_risks': business_critical_risks,
                'executive_attention_required': True,
                'financial_impact_potential': 'high'
            })
        
        return insights
    
    async def _generate_compliance_insights(self, discovery: QuantumDiscovery) -> List[Dict[str, Any]]:
        insights = []
        assets = list(discovery.hyper_assets.values())
        
        compliance_analysis = self._analyze_compliance_posture(assets)
        
        insights.append({
            'type': 'compliance_posture_assessment',
            'title': 'Regulatory Compliance Analysis',
            'content': f"Compliance assessment for {len(assets)} assets across multiple frameworks",
            'confidence': 0.85,
            'priority': 'high',
            'compliance_metrics': compliance_analysis['metrics'],
            'framework_scores': compliance_analysis['frameworks'],
            'non_compliant_assets': compliance_analysis['non_compliant'],
            'remediation_timeline': compliance_analysis['timeline']
        })
        
        return insights
    
    async def _generate_operational_insights(self, discovery: QuantumDiscovery) -> List[Dict[str, Any]]:
        insights = []
        assets = list(discovery.hyper_assets.values())
        
        operational_metrics = self._calculate_operational_metrics(assets)
        
        insights.append({
            'type': 'operational_efficiency_analysis',
            'title': 'Operational Insights and Metrics',
            'content': f"Operational analysis across {len(assets)} managed assets",
            'confidence': 0.8,
            'priority': 'medium',
            'operational_metrics': operational_metrics,
            'efficiency_opportunities': self._identify_efficiency_opportunities(assets),
            'resource_optimization': self._analyze_resource_optimization(assets)
        })
        
        return insights
    
    async def _generate_strategic_insights(self, discovery: QuantumDiscovery) -> List[Dict[str, Any]]:
        insights = []
        assets = list(discovery.hyper_assets.values())
        
        strategic_analysis = self._perform_strategic_analysis(assets)
        
        insights.append({
            'type': 'strategic_technology_insights',
            'title': 'Strategic Technology Portfolio Analysis',
            'content': f"Strategic assessment of technology portfolio and architecture",
            'confidence': 0.8,
            'priority': 'medium',
            'strategic_metrics': strategic_analysis['metrics'],
            'technology_trends': strategic_analysis['trends'],
            'modernization_opportunities': strategic_analysis['modernization'],
            'investment_recommendations': strategic_analysis['investments']
        })
        
        return insights
    
    def _analyze_security_coverage(self, assets) -> Dict[str, Any]:
        total_assets = len(assets)
        
        coverage_counts = {
            'edr_coverage': sum(1 for a in assets if a.edr_coverage),
            'dlp_coverage': sum(1 for a in assets if a.dlp_coverage),
            'tanium_coverage': sum(1 for a in assets if a.tanium_coverage),
            'splunk_coverage': sum(1 for a in assets if a.splunk_coverage),
            'chronicle_coverage': sum(1 for a in assets if a.chronicle_coverage),
            'crowdstrike_coverage': sum(1 for a in assets if a.crowdstrike_coverage),
            'cmdb_visibility': sum(1 for a in assets if a.cmdb_visibility)
        }
        
        coverage_percentages = {k: (v / total_assets * 100) if total_assets > 0 else 0 
                              for k, v in coverage_counts.items()}
        
        gaps = [k for k, v in coverage_percentages.items() if v < 80]
        opportunities = [k for k, v in coverage_percentages.items() if 60 <= v < 90]
        
        return {
            'metrics': coverage_counts,
            'breakdown': coverage_percentages,
            'gaps': gaps,
            'opportunities': opportunities
        }
    
    def _identify_critical_security_gaps(self, assets) -> List[Dict[str, Any]]:
        critical_gaps = []
        
        for asset in assets:
            gap_count = 0
            missing_tools = []
            
            security_tools = [
                ('edr_coverage', 'EDR'),
                ('dlp_coverage', 'DLP'),
                ('splunk_coverage', 'SPLUNK'),
                ('chronicle_coverage', 'CHRONICLE')
            ]
            
            for attr, tool_name in security_tools:
                if not getattr(asset, attr, False):
                    gap_count += 1
                    missing_tools.append(tool_name)
            
            criticality = getattr(asset, 'criticality', '').lower()
            if gap_count >= 3 or (gap_count >= 2 and 'critical' in criticality):
                critical_gaps.append({
                    'hostname': asset.hostname,
                    'asset_id': asset.id,
                    'missing_tools': missing_tools,
                    'gap_count': gap_count,
                    'criticality': criticality,
                    'business_unit': asset.business_unit
                })
        
        return critical_gaps
    
    def _comprehensive_risk_analysis(self, assets) -> Dict[str, Any]:
        risk_scores = []
        high_risk_assets = []
        
        for asset in assets:
            risk_factors = []
            risk_score = 0.0
            
            if not asset.edr_coverage:
                risk_score += 0.3
                risk_factors.append('No EDR coverage')
            
            if not asset.chronicle_coverage and not asset.splunk_coverage:
                risk_score += 0.2
                risk_factors.append('No SIEM coverage')
            
            if not asset.cmdb_visibility:
                risk_score += 0.1
                risk_factors.append('Not in CMDB')
            
            criticality = getattr(asset, 'criticality', '').lower()
            if 'critical' in criticality or 'high' in criticality:
                risk_score *= 1.5
                risk_factors.append('High criticality asset')
            
            risk_scores.append(risk_score)
            
            if risk_score > 0.7:
                high_risk_assets.append({
                    'hostname': asset.hostname,
                    'risk_score': risk_score,
                    'risk_factors': risk_factors,
                    'business_unit': asset.business_unit
                })
        
        avg_risk = statistics.mean(risk_scores) if risk_scores else 0.0
        
        distribution = {
            'high_risk': len([s for s in risk_scores if s > 0.7]),
            'medium_risk': len([s for s in risk_scores if 0.3 <= s <= 0.7]),
            'low_risk': len([s for s in risk_scores if s < 0.3])
        }
        
        return {
            'metrics': {'average_risk_score': avg_risk, 'total_assets_assessed': len(assets)},
            'distribution': distribution,
            'high_risk_assets': high_risk_assets,
            'priorities': self._generate_risk_priorities(high_risk_assets)
        }
    
    def _generate_risk_priorities(self, high_risk_assets) -> List[str]:
        priorities = []
        
        if high_risk_assets:
            priorities.append(f"Immediate attention required for {len(high_risk_assets)} high-risk assets")
            
            business_units = set(asset.get('business_unit', 'Unknown') for asset in high_risk_assets)
            priorities.append(f"Risk spans {len(business_units)} business units")
            
            priorities.append("Implement emergency security controls for critical assets")
            priorities.append("Establish incident response procedures for high-risk scenarios")
        
        return priorities
    
    def _identify_business_critical_risks(self, assets) -> List[Dict[str, Any]]:
        critical_risks = []
        
        critical_assets = [a for a in assets if 'critical' in getattr(a, 'criticality', '').lower()]
        
        for asset in critical_assets:
            security_coverage = sum([
                asset.edr_coverage, asset.dlp_coverage, asset.chronicle_coverage, 
                asset.splunk_coverage, asset.cmdb_visibility
            ])
            
            if security_coverage < 3:
                critical_risks.append({
                    'type': 'inadequate_security_coverage',
                    'hostname': asset.hostname,
                    'business_unit': asset.business_unit,
                    'coverage_score': security_coverage,
                    'potential_impact': 'Business continuity risk'
                })
        
        return critical_risks
    
    def _analyze_compliance_posture(self, assets) -> Dict[str, Any]:
        compliant_assets = 0
        partially_compliant = 0
        non_compliant = 0
        
        frameworks = {
            'security_logging': 0,
            'endpoint_protection': 0,
            'asset_inventory': 0,
            'access_controls': 0
        }
        
        for asset in assets:
            compliance_score = 0
            
            if asset.chronicle_coverage or asset.splunk_coverage:
                compliance_score += 1
                frameworks['security_logging'] += 1
            
            if asset.edr_coverage or asset.crowdstrike_coverage:
                compliance_score += 1
                frameworks['endpoint_protection'] += 1
            
            if asset.cmdb_visibility:
                compliance_score += 1
                frameworks['asset_inventory'] += 1
            
            if asset.business_unit and asset.owner:
                compliance_score += 1
                frameworks['access_controls'] += 1
            
            if compliance_score >= 3:
                compliant_assets += 1
            elif compliance_score >= 2:
                partially_compliant += 1
            else:
                non_compliant += 1
        
        return {
            'metrics': {
                'compliant_assets': compliant_assets,
                'partially_compliant': partially_compliant,
                'non_compliant': non_compliant,
                'compliance_rate': (compliant_assets / len(assets) * 100) if assets else 0
            },
            'frameworks': {k: (v / len(assets) * 100) if assets else 0 for k, v in frameworks.items()},
            'non_compliant': non_compliant,
            'timeline': self._generate_compliance_timeline()
        }
    
    def _generate_compliance_timeline(self) -> Dict[str, str]:
        return {
            'immediate': 'Address critical compliance gaps (0-30 days)',
            'short_term': 'Implement missing security controls (1-3 months)',
            'medium_term': 'Achieve full compliance framework alignment (3-6 months)',
            'long_term': 'Maintain continuous compliance monitoring (ongoing)'
        }
    
    def _calculate_operational_metrics(self, assets) -> Dict[str, Any]:
        total_assets = len(assets)
        
        business_units = set(a.business_unit for a in assets if a.business_unit)
        regions = set(a.global_region for a in assets if a.global_region)
        environments = set(a.environment for a in assets if a.environment)
        
        infrastructure_types = Counter(a.infrastructure_type for a in assets if a.infrastructure_type)
        
        return {
            'total_managed_assets': total_assets,
            'business_units_covered': len(business_units),
            'geographic_regions': len(regions),
            'environments_managed': len(environments),
            'infrastructure_distribution': dict(infrastructure_types),
            'management_complexity_score': self._calculate_complexity_score(assets)
        }
    
    def _calculate_complexity_score(self, assets) -> float:
        factors = [
            len(set(a.business_unit for a in assets if a.business_unit)),
            len(set(a.global_region for a in assets if a.global_region)),
            len(set(a.infrastructure_type for a in assets if a.infrastructure_type)),
            len(set(a.environment for a in assets if a.environment))
        ]
        
        return sum(factors) / len(assets) if assets else 0
    
    def _identify_efficiency_opportunities(self, assets) -> List[str]:
        opportunities = []
        
        unmanaged_count = sum(1 for a in assets if not a.cmdb_visibility)
        if unmanaged_count > 0:
            opportunities.append(f"Bring {unmanaged_count} unmanaged assets into CMDB")
        
        missing_owners = sum(1 for a in assets if not a.owner)
        if missing_owners > 0:
            opportunities.append(f"Assign ownership for {missing_owners} assets")
        
        return opportunities
    
    def _analyze_resource_optimization(self, assets) -> Dict[str, Any]:
        return {
            'consolidation_opportunities': self._identify_consolidation_opportunities(assets),
            'standardization_needs': self._identify_standardization_needs(assets),
            'automation_potential': self._assess_automation_potential(assets)
        }
    
    def _identify_consolidation_opportunities(self, assets) -> List[str]:
        opportunities = []
        
        infrastructure_distribution = Counter(a.infrastructure_type for a in assets if a.infrastructure_type)
        if len(infrastructure_distribution) > 5:
            opportunities.append("Consider infrastructure type consolidation")
        
        return opportunities
    
    def _identify_standardization_needs(self, assets) -> List[str]:
        needs = []
        
        os_types = set(a.system_classification for a in assets if a.system_classification)
        if len(os_types) > 10:
            needs.append("Standardize operating system portfolio")
        
        return needs
    
    def _assess_automation_potential(self, assets) -> Dict[str, Any]:
        return {
            'automatable_tasks': ['Security tool deployment', 'Asset discovery', 'Compliance monitoring'],
            'automation_score': 0.7,
            'roi_potential': 'high'
        }
    
    def _perform_strategic_analysis(self, assets) -> Dict[str, Any]:
        cloud_adoption = sum(1 for a in assets if 'cloud' in getattr(a, 'infrastructure_type', '').lower())
        cloud_percentage = (cloud_adoption / len(assets) * 100) if assets else 0
        
        return {
            'metrics': {
                'cloud_adoption_rate': cloud_percentage,
                'modernization_index': self._calculate_modernization_index(assets),
                'technology_diversity': self._calculate_technology_diversity(assets)
            },
            'trends': {
                'cloud_migration': 'accelerating' if cloud_percentage > 30 else 'emerging',
                'hybrid_infrastructure': cloud_percentage > 10 and cloud_percentage < 90
            },
            'modernization': self._identify_modernization_opportunities(assets),
            'investments': self._recommend_strategic_investments(assets)
        }
    
    def _calculate_modernization_index(self, assets) -> float:
        modern_indicators = 0
        total_assets = len(assets)
        
        for asset in assets:
            if 'cloud' in getattr(asset, 'infrastructure_type', '').lower():
                modern_indicators += 1
            if getattr(asset, 'edr_coverage', False):
                modern_indicators += 0.5
            if getattr(asset, 'chronicle_coverage', False):
                modern_indicators += 0.5
        
        return (modern_indicators / total_assets) if total_assets > 0 else 0
    
    def _calculate_technology_diversity(self, assets) -> float:
        unique_types = set(a.infrastructure_type for a in assets if a.infrastructure_type)
        return len(unique_types) / len(assets) if assets else 0
    
    def _identify_modernization_opportunities(self, assets) -> List[str]:
        opportunities = []
        
        legacy_count = sum(1 for a in assets if not a.edr_coverage and not a.chronicle_coverage)
        if legacy_count > 0:
            opportunities.append(f"Modernize security stack for {legacy_count} legacy assets")
        
        return opportunities
    
    def _recommend_strategic_investments(self, assets) -> List[str]:
        investments = []
        
        security_gaps = sum(1 for a in assets if not a.edr_coverage)
        if security_gaps > len(assets) * 0.3:
            investments.append("Invest in comprehensive EDR deployment")
        
        visibility_gaps = sum(1 for a in assets if not a.cmdb_visibility)
        if visibility_gaps > len(assets) * 0.2:
            investments.append("Invest in asset discovery and inventory automation")
        
        return investments
    
    def _analyze_visibility_distribution(self, visibility_scores: List[float]) -> Dict[str, Any]:
        if not visibility_scores:
            return {'needs_attention': False}
        
        low_visibility_count = len([s for s in visibility_scores if s < 0.4])
        total_count = len(visibility_scores)
        low_visibility_percentage = (low_visibility_count / total_count) * 100
        
        needs_attention = low_visibility_percentage > 30
        
        return {
            'needs_attention': needs_attention,
            'message': f"{low_visibility_percentage:.1f}% of assets have low visibility scores" if needs_attention else "",
            'metrics': {
                'low_visibility_count': low_visibility_count,
                'low_visibility_percentage': low_visibility_percentage
            },
            'actions': ['Improve monitoring coverage', 'Deploy additional security tools'] if needs_attention else []
        }
    
    def _generate_visibility_actions(self, visibility_scores: List[float]) -> List[str]:
        actions = []
        
        if not visibility_scores:
            return actions
        
        avg_score = statistics.mean(visibility_scores)
        
        if avg_score < 0.6:
            actions.append("Implement comprehensive asset discovery")
            actions.append("Deploy additional monitoring tools")
        
        low_count = len([s for s in visibility_scores if s < 0.3])
        if low_count > 0:
            actions.append(f"Address {low_count} assets with critically low visibility")
        
        return actions
    
    def get_intelligence_summary(self) -> Dict[str, Any]:
        return {
            'intelligence_metrics': self.intelligence_metrics,
            'insights_generated': len(self.insights_history),
            'analysis_models_active': len(self.intelligence_models),
            'cache_efficiency': len(self.analysis_cache)
        }

class VisibilityAnalyzer:
    def analyze(self, assets):
        pass

class SecurityCoverageAnalyzer:
    def analyze(self, assets):
        pass

class RiskAssessmentAnalyzer:
    def analyze(self, assets):
        pass

class ComplianceAnalyzer:
    def analyze(self, assets):
        pass

class PatternAnalyzer:
    def analyze(self, assets):
        pass

class AnomalyDetector:
    def detect(self, assets):
        pass

class CorrelationEngine:
    def correlate(self, assets):
        pass

IntelligenceEngine = QuantumIntelligenceEngine