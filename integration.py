from smart_claude_intelligence import ClaudeLevelIntelligence
import json

def test_genius_confidence():
    intelligence = ClaudeLevelIntelligence()
    
    print("GENIUS CONFIDENCE DEMONSTRATION")
    print("=" * 60)
    
    perfect_host = {
        'hostname': 'prod-web-server-01',
        'ip_address': '10.100.50.25',
        'os_type': 'Windows',
        'os_version': 'Server 2019',
        'domain': 'corp.company.com',
        'business_unit': 'Finance',
        'environment': 'production',
        'edr_coverage': True,
        'tanium_coverage': True,
        'splunk_logging': True,
        'gso_logging': True,
        'last_patch_date': '2024-11-15',
        'criticality': 'high',
        'owner': 'john.smith@company.com',
        'region': 'us-east-1',
        'datacenter': 'DC01',
        'cmdb_visibility': True,
        'asset_tag': 'AST-2024-1234',
        'serial_number': 'SN123456789',
        'department': 'IT Operations'
    }
    
    concept = intelligence.knowledge_graph.understand_entity(perfect_host)
    
    print("\nPERFECT HOST ANALYSIS:")
    print(f"Confidence: {concept.confidence:.2%}")
    print(f"Type: {concept.concept_type}")
    print(f"Inferences: {concept.inferences}")
    
    if concept.evidence and 'details' in concept.evidence[0]:
        details = concept.evidence[0]['details']
        print("\nCONFIDENCE BREAKDOWN:")
        for component, data in details.items():
            if isinstance(data, dict) and 'score' in data:
                print(f"  {component}: {data['score']:.2%}")
    
    problematic_host = {
        'hostname': 'prod-db-critical-01',
        'ip_address': '10.0.1.50',
        'environment': 'production',
        'criticality': 'critical',
        'edr_coverage': False,
        'tanium_coverage': False,
        'splunk_logging': False,
        'gso_logging': False,
        'last_patch_date': '2023-01-01',
        'os_type': 'Windows',
        'domain': 'corp.internal.com'
    }
    
    concept2 = intelligence.knowledge_graph.understand_entity(problematic_host)
    
    print("\n" + "-" * 60)
    print("\nPROBLEMATIC HOST ANALYSIS:")
    print(f"Confidence: {concept2.confidence:.2%}")
    print(f"Type: {concept2.concept_type}")
    print(f"Inferences: {concept2.inferences}")
    
    if concept2.evidence and 'details' in concept2.evidence[0]:
        details = concept2.evidence[0]['details']
        print("\nCONFIDENCE BREAKDOWN:")
        for component, data in details.items():
            if isinstance(data, dict) and 'score' in data:
                print(f"  {component}: {data['score']:.2%}")
    
    minimal_host = {
        'hostname': 'test-dev-99',
        'ip_address': '192.168.1.100'
    }
    
    concept3 = intelligence.knowledge_graph.understand_entity(minimal_host)
    
    print("\n" + "-" * 60)
    print("\nMINIMAL HOST ANALYSIS:")
    print(f"Confidence: {concept3.confidence:.2%}")
    print(f"Type: {concept3.concept_type}")
    print(f"Inferences: {concept3.inferences}")
    
    reasoning = intelligence.reasoning_engine.reason_about_data(
        {'intent': 'assessment'}, perfect_host
    )
    
    print("\n" + "=" * 60)
    print("REASONING CONFIDENCE:")
    print(f"Overall: {reasoning['confidence']:.2%}")
    print(f"Explanation: {reasoning['explanation']}")

def test_confidence_evolution():
    intelligence = ClaudeLevelIntelligence()
    
    print("\n" + "=" * 60)
    print("CONFIDENCE EVOLUTION TEST")
    print("=" * 60)
    
    hosts = [
        {'hostname': 'srv-01'},
        {'hostname': 'srv-01', 'ip_address': '10.0.0.1'},
        {'hostname': 'srv-01', 'ip_address': '10.0.0.1', 'os_type': 'Linux'},
        {'hostname': 'srv-01', 'ip_address': '10.0.0.1', 'os_type': 'Linux', 'environment': 'production'},
        {'hostname': 'srv-01', 'ip_address': '10.0.0.1', 'os_type': 'Linux', 'environment': 'production', 'edr_coverage': True},
        {'hostname': 'srv-01', 'ip_address': '10.0.0.1', 'os_type': 'Linux', 'environment': 'production', 'edr_coverage': True, 'splunk_logging': True}
    ]
    
    print("\nAdding fields progressively:")
    for i, host in enumerate(hosts):
        concept = intelligence.knowledge_graph.understand_entity(host)
        print(f"  Step {i+1} ({len(host)} fields): {concept.confidence:.2%}")

if __name__ == "__main__":
    test_genius_confidence()
    test_confidence_evolution()