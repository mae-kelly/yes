from smart_claude_intelligence import ClaudeLevelIntelligence
import json

def test_dynamic_understanding():
    intelligence = ClaudeLevelIntelligence()
    
    print("MODEL INFO:")
    print(f"Encoding method: {intelligence.knowledge_graph.embedding_engine.encoding_method}")
    print(f"Encoder type: {type(intelligence.knowledge_graph.embedding_engine.encoder)}")
    print("-" * 50)
    
    test_host = {
        'hostname': 'prod-web-server-01',
        'ip_address': '10.100.50.25',
        'os_type': 'Windows',
        'os_version': 'Server 2019',
        'domain': 'corp.company.com',
        'business_unit': 'Finance',
        'environment': 'Production',
        'edr_coverage': False,
        'splunk_logging': True,
        'last_patch_date': '2024-01-15',
        'criticality': 'high',
        'owner': 'john.smith@company.com'
    }
    
    concept = intelligence.knowledge_graph.understand_entity(test_host)
    
    print("\nENTITY ANALYSIS:")
    print(f"Type detected: {concept.concept_type}")
    print(f"Confidence (calculated): {concept.confidence:.2%}")
    print(f"Inferences found: {concept.inferences}")
    
    print("\nPROPERTY CONFIDENCES:")
    for prop, details in concept.properties.items():
        print(f"  {prop}: {details['confidence']:.2%} (type: {details['semantic_type']})")
    
    query_context = {
        'intent': 'security_assessment',
        'target': 'host',
        'expected_output': 'risk_analysis'
    }
    
    reasoning = intelligence.reasoning_engine.reason_about_data(query_context, test_host)
    
    print("\nREASONING RESULTS:")
    if reasoning['conclusion']:
        print(f"Conclusion: {reasoning['conclusion']['statement']}")
        print(f"Severity: {reasoning['conclusion']['severity']}")
        print(f"Confidence: {reasoning['conclusion']['confidence']:.2%}")
    print(f"Explanation: {reasoning['explanation']}")
    
    print("\nEVIDENCE:")
    for evidence in reasoning['evidence']:
        print(f"  - {evidence}")
    
    print("\nREASONING CHAIN:")
    for inference in reasoning['reasoning_chain']:
        print(f"  - {inference}")

def test_table_understanding():
    intelligence = ClaudeLevelIntelligence()
    
    table_metadata = {
        'table_name': 'security_event_logs',
        'columns': ['event_id', 'timestamp', 'source_host', 'destination_host', 
                   'event_type', 'severity', 'user_id', 'action_taken', 'outcome']
    }
    
    sample_data = [
        {
            'event_id': 'EVT-2024-001',
            'timestamp': '2024-01-20 14:30:00',
            'source_host': 'workstation-042',
            'destination_host': 'file-server-01',
            'event_type': 'authentication_failure',
            'severity': 'high',
            'user_id': 'admin_user',
            'action_taken': 'blocked',
            'outcome': 'prevented'
        },
        {
            'event_id': 'EVT-2024-002',
            'timestamp': '2024-01-20 14:31:00',
            'source_host': 'workstation-042',
            'destination_host': 'file-server-01',
            'event_type': 'brute_force_attempt',
            'severity': 'critical',
            'user_id': 'admin_user',
            'action_taken': 'alert_sent',
            'outcome': 'investigating'
        }
    ]
    
    understanding = intelligence.understand_table_semantically(table_metadata, sample_data)
    
    print("\n" + "=" * 50)
    print("TABLE UNDERSTANDING:")
    print(f"Primary purpose: {understanding['table_concept']['primary_purpose']}")
    print(f"Purpose confidence: {understanding['table_concept']['confidence']:.2%}")
    print(f"Overall understanding: {understanding['understanding_confidence']:.2%}")
    
    print("\nCOLUMN ANALYSIS:")
    for column, semantics in understanding['column_semantics'].items():
        print(f"  {column}:")
        print(f"    Type: {semantics['semantic_type']}")
        print(f"    Confidence: {semantics['confidence']:.2%}")
        print(f"    Unique ratio: {semantics['unique_ratio']:.2%}")

def test_multiple_hosts():
    intelligence = ClaudeLevelIntelligence()
    
    hosts = [
        {
            'hostname': 'prod-db-01',
            'criticality': 'high',
            'edr_coverage': True,
            'splunk_logging': True,
            'environment': 'production'
        },
        {
            'hostname': 'dev-test-05',
            'criticality': 'low',
            'edr_coverage': False,
            'splunk_logging': False,
            'environment': 'development'
        },
        {
            'hostname': 'prod-web-03',
            'criticality': 'high',
            'edr_coverage': False,
            'splunk_logging': True,
            'environment': 'production',
            'last_patch_date': '2023-10-01'
        }
    ]
    
    print("\n" + "=" * 50)
    print("BATCH ANALYSIS:")
    
    for host in hosts:
        concept = intelligence.knowledge_graph.understand_entity(host)
        reasoning = intelligence.reasoning_engine.reason_about_data(
            {'intent': 'risk_assessment'}, host
        )
        
        print(f"\n{host['hostname']}:")
        print(f"  Confidence: {concept.confidence:.2%}")
        print(f"  Issues: {[inf for inf in concept.inferences if 'gap' in inf or 'no_' in inf]}")
        if reasoning['conclusion']:
            print(f"  Risk: {reasoning['conclusion']['statement']}")

if __name__ == "__main__":
    print("=" * 60)
    print("SMART CLAUDE INTELLIGENCE TEST")
    print("=" * 60)
    
    test_dynamic_understanding()
    test_table_understanding()
    test_multiple_hosts()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")