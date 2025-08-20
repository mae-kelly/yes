import sys
import os
sys.path.insert(0, '/Users/maeve.kelly/Downloads/logLens2')

from discovery.enhanced_host_discovery import EnhancedHostDiscoveryEngine
from smart_claude_intelligence import ClaudeLevelIntelligence
from bigquery_intelligence_trainer import BigQueryIntelligenceTrainer
import yaml
import asyncio
import logging
from pathlib import Path
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntegratedIntelligentDiscovery:
    def __init__(self, config_path: str = '/Users/maeve.kelly/Downloads/logLens2/config.yaml'):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.project_ids = self.config['project_ids']
        self.intelligence = ClaudeLevelIntelligence()
        self.trainer = BigQueryIntelligenceTrainer(self.project_ids)
        self.discovery_engine = EnhancedHostDiscoveryEngine(self.project_ids, self.config)
        
        self.output_dir = Path(self.config.get('output_dir', 'intelligent_discovery_output'))
        self.output_dir.mkdir(exist_ok=True)
        
    async def run_intelligent_discovery(self):
        logger.info("Starting Intelligent Discovery with Learning...")
        
        logger.info("Phase 1: Loading or training intelligence model...")
        if not self.trainer.load_trained_model():
            logger.info("No trained model found. Training on BigQuery data...")
            await self.trainer.train_on_bigquery_data(sample_size=1000)
        else:
            logger.info("Loaded existing trained model")
            logger.info("Running incremental training...")
            await self.trainer.train_on_bigquery_data(sample_size=200)
        
        logger.info("Phase 2: Discovering hosts with enhanced intelligence...")
        hosts = await self.discovery_engine.discover_all_hosts()
        
        logger.info("Phase 3: Applying intelligent analysis to discovered hosts...")
        intelligent_results = self._analyze_hosts_intelligently(hosts)
        
        logger.info("Phase 4: Generating insights and recommendations...")
        insights = self._generate_insights(intelligent_results)
        
        self._save_results(intelligent_results, insights)
        
        return intelligent_results, insights
    
    def _analyze_hosts_intelligently(self, hosts: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        results = {
            'total_hosts': len(hosts),
            'high_confidence_hosts': [],
            'medium_confidence_hosts': [],
            'low_confidence_hosts': [],
            'critical_findings': [],
            'by_confidence': defaultdict(list),
            'by_risk': defaultdict(list),
            'detailed_analysis': {}
        }
        
        for hostname, host_data in hosts.items():
            concept = self.intelligence.knowledge_graph.understand_entity(host_data)
            
            query_context = {
                'intent': 'comprehensive_assessment',
                'target': 'host',
                'expected_output': 'risk_and_compliance'
            }
            
            reasoning = self.intelligence.reasoning_engine.reason_about_data(query_context, host_data)
            
            analysis = {
                'hostname': hostname,
                'data': host_data,
                'concept': {
                    'type': concept.concept_type,
                    'confidence': concept.confidence,
                    'inferences': concept.inferences
                },
                'reasoning': reasoning,
                'risk_score': self._calculate_risk_score(concept, reasoning),
                'recommendations': self._generate_recommendations(concept, reasoning)
            }
            
            results['detailed_analysis'][hostname] = analysis
            
            if concept.confidence >= 0.8:
                results['high_confidence_hosts'].append(hostname)
            elif concept.confidence >= 0.6:
                results['medium_confidence_hosts'].append(hostname)
            else:
                results['low_confidence_hosts'].append(hostname)
            
            results['by_confidence'][f"{int(concept.confidence * 100)}%"].append(hostname)
            
            if 'security_gap_critical' in concept.inferences:
                results['critical_findings'].append({
                    'hostname': hostname,
                    'issue': 'Critical security gap',
                    'confidence': concept.confidence,
                    'details': reasoning['explanation']
                })
            
            risk_category = 'high' if analysis['risk_score'] > 70 else 'medium' if analysis['risk_score'] > 40 else 'low'
            results['by_risk'][risk_category].append(hostname)
        
        return results
    
    def _calculate_risk_score(self, concept, reasoning) -> float:
        base_risk = 30
        
        risk_factors = {
            'security_gap_critical': 30,
            'no_endpoint_protection': 25,
            'visibility_gap_high': 20,
            'outdated_patches': 15,
            'no_logging': 20,
            'production_system': 10,
            'requires_immediate_action': 25
        }
        
        for inference in concept.inferences:
            base_risk += risk_factors.get(inference, 0)
        
        confidence_factor = (1 - concept.confidence) * 20
        base_risk += confidence_factor
        
        return min(100, max(0, base_risk))
    
    def _generate_recommendations(self, concept, reasoning) -> List[Dict[str, str]]:
        recommendations = []
        
        if 'security_gap_critical' in concept.inferences:
            recommendations.append({
                'priority': 'CRITICAL',
                'action': 'Deploy EDR/Tanium coverage immediately',
                'reason': 'Production system without endpoint protection'
            })
        
        if 'visibility_gap_high' in concept.inferences:
            recommendations.append({
                'priority': 'HIGH',
                'action': 'Enable Splunk or GSO logging',
                'reason': 'No security event logging configured'
            })
        
        if 'outdated_patches' in concept.inferences:
            recommendations.append({
                'priority': 'HIGH',
                'action': 'Apply security patches',
                'reason': 'Patches are more than 90 days old'
            })
        
        if concept.confidence < 0.6:
            recommendations.append({
                'priority': 'MEDIUM',
                'action': 'Enrich asset data in CMDB',
                'reason': f'Low data confidence ({concept.confidence:.1%})'
            })
        
        return recommendations
    
    def _generate_insights(self, results: Dict[str, Any]) -> Dict[str, Any]:
        insights = {
            'summary': {
                'total_hosts': results['total_hosts'],
                'high_confidence': len(results['high_confidence_hosts']),
                'critical_issues': len(results['critical_findings']),
                'average_confidence': self._calculate_average_confidence(results)
            },
            'key_findings': [],
            'trends': [],
            'recommendations': []
        }
        
        if results['critical_findings']:
            insights['key_findings'].append({
                'finding': f"{len(results['critical_findings'])} hosts with critical security gaps",
                'impact': 'HIGH',
                'affected_hosts': [f['hostname'] for f in results['critical_findings'][:5]]
            })
        
        confidence_distribution = results['by_confidence']
        if confidence_distribution:
            insights['trends'].append({
                'trend': 'Confidence Distribution',
                'data': dict(confidence_distribution)
            })
        
        risk_distribution = results['by_risk']
        if risk_distribution.get('high', []):
            insights['recommendations'].append({
                'priority': 'IMMEDIATE',
                'action': f"Address {len(risk_distribution['high'])} high-risk hosts",
                'hosts': risk_distribution['high'][:10]
            })
        
        low_confidence_count = len(results['low_confidence_hosts'])
        if low_confidence_count > results['total_hosts'] * 0.3:
            insights['recommendations'].append({
                'priority': 'STRATEGIC',
                'action': 'Improve data quality and completeness',
                'reason': f"{low_confidence_count} hosts ({low_confidence_count/results['total_hosts']:.1%}) have low confidence scores"
            })
        
        return insights
    
    def _calculate_average_confidence(self, results: Dict[str, Any]) -> float:
        total_confidence = 0
        count = 0
        
        for hostname, analysis in results['detailed_analysis'].items():
            total_confidence += analysis['concept']['confidence']
            count += 1
        
        return total_confidence / count if count > 0 else 0
    
    def _save_results(self, results: Dict[str, Any], insights: Dict[str, Any]):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        results_file = self.output_dir / f"intelligent_discovery_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump({
                'results': {k: v for k, v in results.items() if k != 'detailed_analysis'},
                'insights': insights,
                'timestamp': timestamp
            }, f, indent=2, default=str)
        
        logger.info(f"Saved results to {results_file}")
        
        detailed_file = self.output_dir / f"detailed_analysis_{timestamp}.json"
        with open(detailed_file, 'w') as f:
            json.dump(results['detailed_analysis'], f, indent=2, default=str)
        
        report_file = self.output_dir / f"intelligence_report_{timestamp}.md"
        self._generate_report(results, insights, report_file)
    
    def _generate_report(self, results: Dict[str, Any], insights: Dict[str, Any], report_file: Path):
        with open(report_file, 'w') as f:
            f.write("# Intelligent Host Discovery Report\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Executive Summary\n\n")
            summary = insights['summary']
            f.write(f"- **Total Hosts Discovered**: {summary['total_hosts']}\n")
            f.write(f"- **High Confidence Hosts**: {summary['high_confidence']}\n")
            f.write(f"- **Critical Issues Found**: {summary['critical_issues']}\n")
            f.write(f"- **Average Confidence**: {summary['average_confidence']:.1%}\n\n")
            
            f.write("## Key Findings\n\n")
            for finding in insights['key_findings']:
                f.write(f"### {finding['finding']}\n")
                f.write(f"- Impact: {finding['impact']}\n")
                f.write(f"- Affected Hosts: {', '.join(finding['affected_hosts'])}\n\n")
            
            f.write("## Critical Security Gaps\n\n")
            for critical in results['critical_findings'][:10]:
                f.write(f"- **{critical['hostname']}**: {critical['issue']} (Confidence: {critical['confidence']:.1%})\n")
            
            f.write("\n## Recommendations\n\n")
            for rec in insights['recommendations']:
                f.write(f"### {rec['priority']} Priority\n")
                f.write(f"- **Action**: {rec['action']}\n")
                if 'reason' in rec:
                    f.write(f"- **Reason**: {rec['reason']}\n")
                if 'hosts' in rec:
                    f.write(f"- **Affected Hosts**: {', '.join(rec['hosts'][:5])}\n")
                f.write("\n")
            
            f.write("## Confidence Analysis\n\n")
            f.write(f"- High Confidence (≥80%): {len(results['high_confidence_hosts'])} hosts\n")
            f.write(f"- Medium Confidence (60-80%): {len(results['medium_confidence_hosts'])} hosts\n")
            f.write(f"- Low Confidence (<60%): {len(results['low_confidence_hosts'])} hosts\n\n")
            
            f.write("## Risk Distribution\n\n")
            for risk_level, hosts in results['by_risk'].items():
                f.write(f"- {risk_level.title()} Risk: {len(hosts)} hosts\n")
        
        logger.info(f"Generated report: {report_file}")

async def main():
    discovery = IntegratedIntelligentDiscovery()
    results, insights = await discovery.run_intelligent_discovery()
    
    print("\n" + "=" * 60)
    print("INTELLIGENT DISCOVERY COMPLETE")
    print("=" * 60)
    print(f"Total Hosts: {results['total_hosts']}")
    print(f"Critical Issues: {len(results['critical_findings'])}")
    print(f"Average Confidence: {insights['summary']['average_confidence']:.1%}")
    print("\nTop Critical Findings:")
    for finding in results['critical_findings'][:3]:
        print(f"  - {finding['hostname']}: {finding['issue']}")
    print(f"\nResults saved to: {discovery.output_dir}")

if __name__ == "__main__":
    asyncio.run(main())