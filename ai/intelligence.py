import asyncio
import logging
import statistics
from typing import Dict, List, Any, Optional
from datetime import datetime
from core.types import QuantumDiscovery, HyperAsset

logger = logging.getLogger(__name__)

class QuantumIntelligenceEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
    async def generate_insights(self, quantum_discovery: QuantumDiscovery) -> List[Dict[str, Any]]:
        insights = []
        
        if not quantum_discovery.hyper_assets:
            return insights
        
        asset_count = len(quantum_discovery.hyper_assets)
        visibility_scores = [asset.visibility_score for asset in quantum_discovery.hyper_assets.values()]
        avg_visibility = statistics.mean(visibility_scores) if visibility_scores else 0.0
        
        insights.append({
            'type': 'asset_visibility_analysis',
            'content': f"Discovered {asset_count:,} hyper assets with average visibility score {avg_visibility:.2f}",
            'confidence': 0.95,
            'metrics': {
                'total_assets': asset_count,
                'avg_visibility': avg_visibility,
                'high_visibility_assets': len([s for s in visibility_scores if s > 0.8]),
                'low_visibility_assets': len([s for s in visibility_scores if s < 0.4])
            },
            'cybersecurity_relevance': 'high'
        })
        
        edr_coverage = len([a for a in quantum_discovery.hyper_assets.values() if a.edr_coverage])
        dlp_coverage = len([a for a in quantum_discovery.hyper_assets.values() if a.dlp_coverage])
        siem_coverage = len([a for a in quantum_discovery.hyper_assets.values() if a.splunk_coverage or a.chronicle_coverage])
        
        insights.append({
            'type': 'security_coverage_analysis',
            'content': f"Security coverage: EDR {edr_coverage}/{asset_count}, DLP {dlp_coverage}/{asset_count}, SIEM {siem_coverage}/{asset_count}",
            'confidence': 0.9,
            'security_metrics': {
                'edr_coverage_ratio': edr_coverage / asset_count if asset_count > 0 else 0,
                'dlp_coverage_ratio': dlp_coverage / asset_count if asset_count > 0 else 0,
                'siem_coverage_ratio': siem_coverage / asset_count if asset_count > 0 else 0
            },
            'cybersecurity_relevance': 'critical'
        })
        
        critical_assets = len([a for a in quantum_discovery.hyper_assets.values() 
                             if a.application_class and 'critical' in a.application_class.lower()])
        
        if critical_assets > 0:
            insights.append({
                'type': 'critical_asset_analysis',
                'content': f"Identified {critical_assets} critical assets requiring enhanced security monitoring",
                'confidence': 0.85,
                'risk_metrics': {
                    'critical_asset_count': critical_assets,
                    'critical_asset_ratio': critical_assets / asset_count
                },
                'cybersecurity_relevance': 'critical',
                'recommendations': [
                    'Implement enhanced monitoring for critical assets',
                    'Ensure comprehensive security control coverage',
                    'Establish priority incident response procedures'
                ]
            })
        
        intelligence_scores = [asset.intelligence_quotient for asset in quantum_discovery.hyper_assets.values()]
        avg_intelligence = statistics.mean(intelligence_scores) if intelligence_scores else 0.0
        
        insights.append({
            'type': 'intelligence_quality_analysis',
            'content': f"Average intelligence quotient: {avg_intelligence:.2f} across all discovered assets",
            'confidence': 0.9,
            'quality_metrics': {
                'avg_intelligence_quotient': avg_intelligence,
                'high_intelligence_assets': len([s for s in intelligence_scores if s > 0.8]),
                'data_quality_score': avg_intelligence
            },
            'cybersecurity_relevance': 'medium'
        })
        
        return insights

IntelligenceEngine = QuantumIntelligenceEngine