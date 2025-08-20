from claude_intelligence import ClaudeLevelIntelligence
from discovery.quantum_discovery import QuantumDiscoveryEngine
from gcp.client import BigQueryClientManager
import yaml
import asyncio

class EnhancedDiscoveryWithClaude:
    def __init__(self, config_path='config.yaml'):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.intelligence = ClaudeLevelIntelligence()
        self.project_ids = self.config['project_ids']
        
    async def discover_with_understanding(self):
        discovery = QuantumDiscoveryEngine(self.project_ids, self.config)
        assets = await discovery.discover_all_assets()
        
        enhanced_assets = {}
        for asset_id, asset in assets.items():
            asset_data = {
                'hostname': asset.hostname,
                'infrastructure_type': asset.infrastructure_type,
                'region': asset.region,
                'business_unit': asset.business_unit,
                'edr_coverage': asset.edr_coverage,
                'tanium_coverage': asset.tanium_coverage,
                'splunk_logging': asset.splunk_logging,
                'gso_logging': asset.gso_logging,
                'cmdb_visibility': asset.cmdb_visibility
            }
            
            concept = self.intelligence.knowledge_graph.understand_entity(asset_data)
            
            query_context = {
                'intent': 'security_assessment',
                'target': 'asset',
                'expected_output': 'risk_analysis'
            }
            
            reasoning = self.intelligence.reasoning_engine.reason_about_data(query_context, asset_data)
            
            enhanced_assets[asset_id] = {
                'original': asset,
                'semantic_understanding': concept,
                'reasoning': reasoning,
                'risk_score': self._calculate_risk_score(concept, reasoning),
                'recommendations': self._generate_recommendations(concept, reasoning)
            }
        
        return enhanced_assets
    
    def _calculate_risk_score(self, concept, reasoning):
        base_score = 50
        
        if 'production_system' in concept.inferences:
            base_score += 20
        
        if 'security_gap_critical' in concept.inferences:
            base_score += 30
        
        if 'visibility_gap_high' in concept.inferences:
            base_score += 20
        
        confidence_adjustment = (1 - reasoning['confidence']) * 10
        base_score += confidence_adjustment
        
        return min(100, max(0, base_score))
    
    def _generate_recommendations(self, concept, reasoning):
        recommendations = []
        
        if 'security_gap_critical' in concept.inferences:
            recommendations.append({
                'priority': 'CRITICAL',
                'action': 'Deploy EDR coverage immediately',
                'reason': reasoning['explanation']
            })
        
        if 'visibility_gap_high' in concept.inferences:
            recommendations.append({
                'priority': 'HIGH',
                'action': 'Enable comprehensive logging',
                'reason': 'Missing visibility into system activities'
            })
        
        if 'production_system' in concept.inferences and 'legacy_system' in concept.inferences:
            recommendations.append({
                'priority': 'MEDIUM',
                'action': 'Plan migration to modern infrastructure',
                'reason': 'Legacy production systems pose increased risk'
            })
        
        return recommendations

    def analyze_table_intelligently(self, table_path):
        parts = table_path.split('.')
        project_id = parts[0]
        
        manager = BigQueryClientManager(project_id)
        
        with manager.get_client() as client:
            table = client.get_table(table_path)
            
            columns = [field.name for field in table.schema]
            
            query = f"SELECT * FROM `{table_path}` LIMIT 100"
            query_job = client.query(query)
            results = list(query_job.result())
            
            sample_data = []
            for row in results:
                row_dict = {}
                for col in columns:
                    row_dict[col] = getattr(row, col, None)
                sample_data.append(row_dict)
            
            table_metadata = {
                'table_name': table_path,
                'columns': columns,
                'row_count': table.num_rows
            }
            
            understanding = self.intelligence.understand_table_semantically(table_metadata, sample_data)
            
            return {
                'table_path': table_path,
                'understanding': understanding,
                'purpose': understanding['mental_model']['purpose'],
                'confidence': understanding['understanding_confidence'],
                'recommendations': self._generate_table_recommendations(understanding)
            }
    
    def _generate_table_recommendations(self, understanding):
        recommendations = []
        
        purpose = understanding['mental_model']['purpose']['primary']
        
        if purpose == 'event_logging' and not any('severity' in col for col in understanding['column_semantics']):
            recommendations.append('Consider adding severity classification to events')
        
        if purpose == 'asset_inventory' and not any('criticality' in col for col in understanding['column_semantics']):
            recommendations.append('Add criticality ratings to assets')
        
        if understanding['understanding_confidence'] < 0.7:
            recommendations.append('Table structure may benefit from clearer naming conventions')
        
        return recommendations

async def main():
    enhancer = EnhancedDiscoveryWithClaude()
    
    print("Starting Claude-Enhanced Discovery...")
    assets = await enhancer.discover_with_understanding()
    
    critical_risks = []
    for asset_id, enhanced in assets.items():
        if enhanced['risk_score'] > 80:
            critical_risks.append({
                'hostname': enhanced['original'].hostname,
                'risk_score': enhanced['risk_score'],
                'reasoning': enhanced['reasoning']['explanation'],
                'recommendations': enhanced['recommendations']
            })
    
    print(f"\nDiscovered {len(assets)} assets")
    print(f"Critical risks found: {len(critical_risks)}")
    
    for risk in critical_risks[:5]:
        print(f"\n{risk['hostname']} - Risk Score: {risk['risk_score']}")
        print(f"  Reasoning: {risk['reasoning']}")
        for rec in risk['recommendations']:
            print(f"  [{rec['priority']}] {rec['action']}")

if __name__ == "__main__":
    asyncio.run(main())