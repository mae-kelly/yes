"""
Perfect AO1 Field Discovery System
Enterprise-Grade BigQuery Analysis for AO1 Compliance

This system finds the exact fields needed for AO1 audit requirements by:
1. Understanding table business context and purpose
2. Analyzing field relevance with semantic understanding
3. Providing clear, actionable paragraph summaries
4. Prioritizing by data volume and business impact
5. Working in any corporate network environment
6. Generating executive-ready compliance reports
"""

import os
import sys
import json
import time
import logging
import getpass
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import numpy as np
import pandas as pd
import requests

# Corporate logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger('AO1Discovery')

# Configuration
PROJECT_ID = "prj-fisv-p-gcss-sas-dl9dd0f1df"
SERVICE_ACCOUNT_FILE = "gcp_prod_key.json"

@dataclass
class AO1Finding:
    """Perfect AO1 field finding with business context"""
    dataset: str
    table: str
    field_name: str
    field_path: str
    field_type: str
    requirement: str
    confidence_score: float
    match_type: str
    business_context: str
    table_purpose: str
    table_rows: int
    data_volume_gb: float
    why_relevant: str
    recommendation: str
    priority_score: float

class AO1RequirementsEngine:
    """Perfect AO1 requirements understanding engine"""
    
    def __init__(self):
        self.requirements = {
            'REQ-1': {
                'name': 'Global View',
                'purpose': 'Asset identification for counting unique logging assets vs CMDB',
                'key_concepts': ['hostname', 'computer_name', 'device_name', 'asset_id', 'ip_address', 'mac_address', 'serial_number'],
                'table_indicators': ['cmdb', 'asset', 'inventory', 'device', 'computer', 'host', 'server', 'endpoint', 'workstation'],
                'business_value': 'Enables accurate asset counting and CMDB comparison for visibility measurement'
            },
            'REQ-2': {
                'name': 'Infrastructure Type',
                'purpose': 'Classification by deployment model (On-Prem, Cloud, SaaS, API)',
                'key_concepts': ['cloud', 'aws', 'azure', 'gcp', 'datacenter', 'virtual_machine', 'container', 'saas', 'api'],
                'table_indicators': ['cloud', 'infrastructure', 'deployment', 'platform', 'service', 'vm', 'container', 'kubernetes'],
                'business_value': 'Categorizes assets by infrastructure type for targeted visibility strategies'
            },
            'REQ-3': {
                'name': 'Regional/Country View',
                'purpose': 'Geographic location classification for regional visibility statements',
                'key_concepts': ['region', 'country', 'location', 'datacenter', 'zone', 'site', 'facility', 'office'],
                'table_indicators': ['region', 'location', 'geographic', 'geo', 'site', 'facility', 'datacenter', 'office', 'branch'],
                'business_value': 'Enables geographic visibility reporting and regional compliance measurement'
            },
            'REQ-4': {
                'name': 'Business/Application View',
                'purpose': 'Organizational classification by Business Unit and Application',
                'key_concepts': ['business_unit', 'application', 'department', 'organization', 'cost_center', 'owner'],
                'table_indicators': ['application', 'business', 'organization', 'department', 'division', 'unit', 'team', 'project'],
                'business_value': 'Links technical assets to business ownership for accountability and reporting'
            },
            'REQ-5': {
                'name': 'System Classification',
                'purpose': 'Server function and OS type classification',
                'key_concepts': ['windows', 'linux', 'unix', 'web_server', 'database', 'operating_system', 'server_type'],
                'table_indicators': ['system', 'server', 'os', 'operating', 'database', 'web', 'function', 'role', 'type'],
                'business_value': 'Categorizes systems by function and OS for targeted monitoring strategies'
            },
            'REQ-6': {
                'name': 'Security Control Coverage',
                'purpose': 'Agent presence measurement (EDR, Tanium, DLP) for coverage calculation',
                'key_concepts': ['edr', 'crowdstrike', 'tanium', 'agent_id', 'endpoint_security', 'dlp', 'protection'],
                'table_indicators': ['security', 'agent', 'endpoint', 'edr', 'protection', 'crowdstrike', 'tanium', 'dlp'],
                'business_value': 'Measures security tool coverage to identify protection gaps'
            },
            'REQ-7': {
                'name': 'Logging Compliance',
                'purpose': 'GSO (Chronicle) and Splunk platform compliance measurement',
                'key_concepts': ['splunk', 'chronicle', 'sourcetype', 'index', 'log_source', 'ingestion', 'parsing'],
                'table_indicators': ['log', 'event', 'audit', 'splunk', 'chronicle', 'siem', 'monitoring', 'ingestion'],
                'business_value': 'Validates logging platform compliance and data ingestion completeness'
            },
            'REQ-8': {
                'name': 'Domain Visibility',
                'purpose': 'Asset visibility by hostname and domain for network-based identification',
                'key_concepts': ['domain', 'fqdn', 'dns_name', 'hostname', 'dns_resolution', 'nameserver'],
                'table_indicators': ['domain', 'dns', 'network', 'hostname', 'fqdn', 'resolution', 'nameserver'],
                'business_value': 'Enables network-based asset identification and DNS-driven visibility'
            }
        }

class PerfectTableAnalyzer:
    """Analyzes table business context and AO1 relevance perfectly"""
    
    def __init__(self, requirements_engine: AO1RequirementsEngine):
        self.requirements = requirements_engine.requirements
        
    def analyze_table_context(self, dataset_name: str, table_name: str, table_description: str = "") -> Dict[str, Any]:
        """Perfect table context analysis"""
        full_identifier = "{}.{}".format(dataset_name, table_name).lower()
        
        context = {
            'primary_requirements': [],
            'secondary_requirements': [],
            'business_purpose': 'unknown',
            'ao1_relevance': 'low',
            'confidence_multipliers': {},
            'why_relevant': 'Table name does not clearly indicate AO1 relevance'
        }
        
        requirement_scores = {}
        
        # Analyze against each AO1 requirement
        for req_id, req_data in self.requirements.items():
            score = 0.0
            matches = []
            
            # Check table indicators (high weight)
            for indicator in req_data['table_indicators']:
                if indicator in full_identifier:
                    score += 2.0
                    matches.append(indicator)
            
            # Check key concepts (medium weight)
            for concept in req_data['key_concepts']:
                if concept in full_identifier:
                    score += 1.0
                    matches.append(concept)
            
            if score > 0:
                requirement_scores[req_id] = {
                    'score': score,
                    'matches': matches,
                    'requirement_name': req_data['name'],
                    'purpose': req_data['purpose']
                }
        
        # Determine primary requirements (score >= 2.0)
        for req_id, data in requirement_scores.items():
            if data['score'] >= 2.0:
                context['primary_requirements'].append(req_id)
                context['confidence_multipliers'][req_id] = min(3.0, 1.0 + data['score'] * 0.5)
                context['ao1_relevance'] = 'high'
                context['business_purpose'] = data['purpose']
                context['why_relevant'] = "Table name clearly indicates {} data based on keywords: {}".format(
                    data['requirement_name'], ', '.join(data['matches'][:3])
                )
            elif data['score'] >= 1.0:
                context['secondary_requirements'].append(req_id)
                context['confidence_multipliers'][req_id] = min(2.0, 1.0 + data['score'] * 0.3)
                if context['ao1_relevance'] == 'low':
                    context['ao1_relevance'] = 'medium'
                    context['business_purpose'] = data['purpose']
                    context['why_relevant'] = "Table name suggests {} data based on keywords: {}".format(
                        data['requirement_name'], ', '.join(data['matches'][:2])
                    )
        
        return context

class PerfectFieldAnalyzer:
    """Perfect field analysis with business context understanding"""
    
    def __init__(self, requirements_engine: AO1RequirementsEngine):
        self.requirements = requirements_engine.requirements
        
    def analyze_field(self, field_name: str, field_type: str, table_context: Dict[str, Any]) -> Dict[str, Any]:
        """Perfect field analysis with business context"""
        field_lower = field_name.lower().strip()
        
        analysis = {
            'is_ao1_relevant': False,
            'requirement': 'NONE',
            'confidence_score': 0.0,
            'match_type': 'NO_MATCH',
            'why_relevant': 'Field does not match any AO1 keywords',
            'recommendation': 'Not recommended for AO1 compliance measurement'
        }
        
        best_score = 0.0
        best_requirement = None
        best_matches = []
        
        # Analyze against each requirement
        for req_id, req_data in self.requirements.items():
            score = 0.0
            matches = []
            
            # Exact match (highest score)
            for concept in req_data['key_concepts']:
                if field_lower == concept.lower():
                    score += 10.0
                    matches.append(('exact', concept))
                elif concept.lower() in field_lower:
                    score += 5.0
                    matches.append(('contains', concept))
                elif field_lower in concept.lower() and len(field_lower) >= 3:
                    score += 3.0
                    matches.append(('contained', concept))
            
            # Apply table context multiplier
            if req_id in table_context.get('confidence_multipliers', {}):
                context_multiplier = table_context['confidence_multipliers'][req_id]
                score *= context_multiplier
                matches.append(('context_boost', context_multiplier))
            
            if score > best_score:
                best_score = score
                best_requirement = req_id
                best_matches = matches
        
        # Determine if field is AO1 relevant
        if best_score >= 5.0:
            analysis['is_ao1_relevant'] = True
            analysis['requirement'] = best_requirement
            analysis['confidence_score'] = min(1.0, best_score / 30.0)  # Normalize to 0-1
            
            # Determine match type
            if best_score >= 25.0:
                analysis['match_type'] = 'PERFECT'
            elif best_score >= 15.0:
                analysis['match_type'] = 'EXCELLENT'
            elif best_score >= 10.0:
                analysis['match_type'] = 'GOOD'
            else:
                analysis['match_type'] = 'FAIR'
            
            # Generate explanation
            req_data = self.requirements[best_requirement]
            match_types = [match[0] for match in best_matches if match[0] != 'context_boost']
            
            if 'exact' in match_types:
                analysis['why_relevant'] = "Field '{}' exactly matches AO1 requirement {} ({}) keywords".format(
                    field_name, best_requirement, req_data['name']
                )
                analysis['recommendation'] = "HIGHLY RECOMMENDED - Perfect match for {} measurement".format(req_data['name'])
            elif 'contains' in match_types:
                analysis['why_relevant'] = "Field '{}' contains AO1 requirement {} ({}) keywords".format(
                    field_name, best_requirement, req_data['name']
                )
                analysis['recommendation'] = "RECOMMENDED - Good candidate for {} measurement".format(req_data['name'])
            else:
                analysis['why_relevant'] = "Field '{}' partially matches AO1 requirement {} ({}) concepts".format(
                    field_name, best_requirement, req_data['name']
                )
                analysis['recommendation'] = "CONSIDER - May be useful for {} measurement pending validation".format(req_data['name'])
        
        return analysis

class PerfectAO1Discovery:
    """Perfect AO1 field discovery system"""
    
    def __init__(self):
        print("PERFECT AO1 FIELD DISCOVERY SYSTEM")
        print("Enterprise AO1 Compliance Field Identification")
        print("=" * 60)
        
        self.requirements_engine = AO1RequirementsEngine()
        self.table_analyzer = PerfectTableAnalyzer(self.requirements_engine)
        self.field_analyzer = PerfectFieldAnalyzer(self.requirements_engine)
        self.client = None
        
        self._setup_enterprise_environment()
        
    def _setup_enterprise_environment(self):
        """Setup enterprise environment quickly"""
        # Handle proxy if needed
        if not self._test_connection():
            self._setup_proxy()
        
        # Authenticate BigQuery
        self._authenticate_bigquery()
    
    def _test_connection(self) -> bool:
        """Quick connection test"""
        try:
            response = requests.get('http://httpbin.org/get', timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _setup_proxy(self):
        """Quick proxy setup"""
        configure = input("Configure corporate proxy? (y/n): ").lower().strip()
        if configure == 'y':
            http_proxy = input("HTTP_PROXY: ").strip()
            https_proxy = input("HTTPS_PROXY: ").strip()
            
            if http_proxy:
                os.environ['HTTP_PROXY'] = http_proxy
                os.environ['http_proxy'] = http_proxy
            if https_proxy:
                os.environ['HTTPS_PROXY'] = https_proxy
                os.environ['https_proxy'] = https_proxy
    
    def _authenticate_bigquery(self):
        """Authenticate with BigQuery"""
        try:
            from google.cloud import bigquery
            from google.oauth2 import service_account
            
            if os.path.exists(SERVICE_ACCOUNT_FILE):
                credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
                self.client = bigquery.Client(project=PROJECT_ID, credentials=credentials)
            else:
                self.client = bigquery.Client(project=PROJECT_ID)
            
            # Test connection
            list(self.client.list_datasets(max_results=1))
            print("✓ BigQuery: Connected successfully")
            
        except Exception as e:
            print("✗ BigQuery: Connection failed - {}".format(e))
            sys.exit(1)
    
    def discover_perfect_ao1_fields(self) -> List[AO1Finding]:
        """Discover perfect AO1 fields with business context"""
        print("\nDISCOVERING AO1 FIELDS...")
        
        all_findings = []
        datasets = [d.dataset_id for d in self.client.list_datasets()]
        
        total_tables = 0
        for dataset_id in datasets:
            try:
                tables = list(self.client.list_tables(dataset_id))
                total_tables += len(tables)
            except:
                continue
        
        print("Analyzing {} tables across {} datasets...".format(total_tables, len(datasets)))
        
        processed = 0
        for dataset_id in datasets:
            try:
                tables = list(self.client.list_tables(dataset_id))
                
                for table_ref in tables:
                    processed += 1
                    if processed % 25 == 0:
                        print("  Progress: {}/{} tables ({:.1f}%)".format(processed, total_tables, processed/total_tables*100))
                    
                    findings = self._analyze_table_perfectly(dataset_id, table_ref.table_id)
                    all_findings.extend(findings)
                    
            except Exception as e:
                continue
        
        print("✓ Discovery complete: {} AO1-relevant fields found".format(len(all_findings)))
        return all_findings
    
    def _analyze_table_perfectly(self, dataset_id: str, table_id: str) -> List[AO1Finding]:
        """Perfect table analysis"""
        try:
            table_ref = self.client.dataset(dataset_id).table(table_id)
            table = self.client.get_table(table_ref)
            
            # Analyze table business context
            table_context = self.table_analyzer.analyze_table_context(dataset_id, table_id)
            
            findings = []
            
            def analyze_field_recursive(field, parent_path=""):
                field_path = "{}.{}".format(parent_path, field.name) if parent_path else field.name
                
                # Analyze field with business context
                field_analysis = self.field_analyzer.analyze_field(field.name, field.field_type, table_context)
                
                if field_analysis['is_ao1_relevant']:
                    # Calculate data volume
                    table_size_gb = (table.num_bytes or 0) / (1024**3)
                    
                    # Calculate priority score (combines confidence, table size, and business context)
                    priority_score = (
                        field_analysis['confidence_score'] * 0.4 +
                        min(1.0, (table.num_rows or 0) / 1000000) * 0.3 +  # Normalize rows to 0-1
                        (1.0 if table_context['ao1_relevance'] == 'high' else 0.5 if table_context['ao1_relevance'] == 'medium' else 0.2) * 0.3
                    )
                    
                    finding = AO1Finding(
                        dataset=dataset_id,
                        table=table_id,
                        field_name=field.name,
                        field_path=field_path,
                        field_type=field.field_type,
                        requirement=field_analysis['requirement'],
                        confidence_score=field_analysis['confidence_score'],
                        match_type=field_analysis['match_type'],
                        business_context=table_context['business_purpose'],
                        table_purpose=table_context['ao1_relevance'],
                        table_rows=table.num_rows or 0,
                        data_volume_gb=table_size_gb,
                        why_relevant=field_analysis['why_relevant'],
                        recommendation=field_analysis['recommendation'],
                        priority_score=priority_score
                    )
                    findings.append(finding)
                
                # Handle nested fields
                if field.field_type in ['RECORD', 'STRUCT'] and field.fields:
                    for nested_field in field.fields:
                        analyze_field_recursive(nested_field, field_path)
            
            # Analyze all fields
            for field in table.schema:
                analyze_field_recursive(field)
            
            return findings
            
        except Exception as e:
            return []
    
    def generate_perfect_report(self, findings: List[AO1Finding]):
        """Generate perfect AO1 report with paragraph summaries"""
        if not findings:
            print("\nPERFECT AO1 ANALYSIS RESULTS")
            print("=" * 60)
            print("No AO1-relevant fields discovered in accessible datasets.")
            print("Recommendation: Review field naming conventions and data architecture.")
            return
        
        # Sort by priority score (highest first)
        findings.sort(key=lambda x: x.priority_score, reverse=True)
        
        # Group by requirement
        by_requirement = defaultdict(list)
        for finding in findings:
            by_requirement[finding.requirement].append(finding)
        
        print("\nPERFECT AO1 FIELD DISCOVERY RESULTS")
        print("=" * 60)
        print("Total Discoveries: {} fields across {} requirements".format(len(findings), len(by_requirement)))
        
        # Executive Summary
        print("\nEXECUTIVE SUMMARY:")
        total_data_volume = sum(f.data_volume_gb for f in findings)
        high_confidence = len([f for f in findings if f.confidence_score >= 0.8])
        perfect_matches = len([f for f in findings if f.match_type == 'PERFECT'])
        
        print("• {} high-confidence field matches identified for AO1 compliance".format(high_confidence))
        print("• {} perfect matches requiring immediate implementation".format(perfect_matches))
        print("• {:.1f} GB of data available across identified tables".format(total_data_volume))
        print("• {}/8 AO1 requirements have viable field candidates".format(len(by_requirement)))
        
        # Detailed findings by requirement
        for req_id in ['REQ-1', 'REQ-2', 'REQ-3', 'REQ-4', 'REQ-5', 'REQ-6', 'REQ-7', 'REQ-8']:
            req_findings = by_requirement.get(req_id, [])
            
            if not req_findings:
                req_info = self.requirements_engine.requirements[req_id]
                print("\n{} - {}: NO FIELDS IDENTIFIED".format(req_id, req_info['name']))
                print("   Purpose: {}".format(req_info['purpose']))
                print("   Recommendation: Review data sources for fields like: {}".format(
                    ', '.join(req_info['key_concepts'][:5])
                ))
                continue
            
            req_info = self.requirements_engine.requirements[req_id]
            print("\n{} - {}: {} FIELDS IDENTIFIED".format(req_id, req_info['name'], len(req_findings)))
            print("   Purpose: {}".format(req_info['purpose']))
            print("   Business Value: {}".format(req_info['business_value']))
            
            # Show top findings
            top_findings = sorted(req_findings, key=lambda x: x.priority_score, reverse=True)[:5]
            
            for i, finding in enumerate(top_findings, 1):
                print("\n   {}. FIELD: '{}' in {}.{}".format(i, finding.field_name, finding.dataset, finding.table))
                print("      Data Volume: {:,} rows ({:.2f} GB)".format(finding.table_rows, finding.data_volume_gb))
                print("      Confidence: {:.1%} | Match Type: {} | Priority: {:.2f}".format(
                    finding.confidence_score, finding.match_type, finding.priority_score))
                print("      Analysis: {}".format(finding.why_relevant))
                print("      Recommendation: {}".format(finding.recommendation))
        
        # Strategic recommendations
        print("\nSTRATEGIC RECOMMENDATIONS:")
        
        perfect_fields = [f for f in findings[:10] if f.match_type == 'PERFECT']
        if perfect_fields:
            print("\n1. IMMEDIATE IMPLEMENTATION:")
            print("   Deploy these {} perfect matches immediately for AO1 compliance:".format(len(perfect_fields)))
            for f in perfect_fields[:3]:
                print("   • {}.{}.{} - {} coverage".format(f.dataset, f.table, f.field_name, f.requirement))
        
        high_volume_fields = sorted([f for f in findings if f.table_rows > 100000], 
                                   key=lambda x: x.table_rows, reverse=True)[:5]
        if high_volume_fields:
            print("\n2. HIGH-IMPACT OPPORTUNITIES:")
            print("   Focus on these high-volume tables for maximum visibility impact:")
            for f in high_volume_fields:
                print("   • {}.{} - {:,} rows of {} data".format(
                    f.dataset, f.table, f.table_rows, f.requirement))
        
        missing_reqs = set(['REQ-1', 'REQ-2', 'REQ-3', 'REQ-4', 'REQ-5', 'REQ-6', 'REQ-7', 'REQ-8']) - set(by_requirement.keys())
        if missing_reqs:
            print("\n3. COVERAGE GAPS:")
            print("   Address these {} missing requirements:".format(len(missing_reqs)))
            for req in sorted(missing_reqs):
                req_info = self.requirements_engine.requirements[req]
                print("   • {} ({}): Look for fields like {}".format(
                    req, req_info['name'], ', '.join(req_info['key_concepts'][:3])
                ))
    
    def save_perfect_results(self, findings: List[AO1Finding]):
        """Save perfect results with paragraph summaries"""
        if not findings:
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create detailed report with paragraphs
        report_data = []
        
        for finding in findings:
            # Create paragraph summary
            paragraph_summary = self._create_paragraph_summary(finding)
            
            report_data.append({
                'Requirement': finding.requirement,
                'Requirement_Name': self.requirements_engine.requirements[finding.requirement]['name'],
                'Dataset': finding.dataset,
                'Table': finding.table,
                'Field_Name': finding.field_name,
                'Field_Path': finding.field_path,
                'Field_Type': finding.field_type,
                'Match_Type': finding.match_type,
                'Confidence_Score': f"{finding.confidence_score:.1%}",
                'Priority_Score': f"{finding.priority_score:.2f}",
                'Table_Rows': f"{finding.table_rows:,}",
                'Data_Volume_GB': f"{finding.data_volume_gb:.2f}",
                'Business_Context': finding.business_context,
                'Why_Relevant': finding.why_relevant,
                'Recommendation': finding.recommendation,
                'Paragraph_Summary': paragraph_summary,
                'Analysis_Date': timestamp
            })
        
        # Sort by priority
        report_data.sort(key=lambda x: float(x['Priority_Score']), reverse=True)
        
        # Save comprehensive report
        df = pd.DataFrame(report_data)
        filename = "AO1_Perfect_Field_Discovery_{}.csv".format(timestamp)
        df.to_csv(filename, index=False)
        
        # Save executive summary
        self._save_executive_summary(findings, timestamp)
        
        print("\nRESULTS SAVED:")
        print("• Detailed Report: {}".format(filename))
        print("• Executive Summary: AO1_Executive_Summary_{}.txt".format(timestamp))
        print("• Total Records: {}".format(len(report_data)))
    
    def _create_paragraph_summary(self, finding: AO1Finding) -> str:
        """Create perfect paragraph summary for each finding"""
        req_info = self.requirements_engine.requirements[finding.requirement]
        
        summary = "The field '{}' in table {}.{} is {} for AO1 {} compliance. ".format(
            finding.field_name, finding.dataset, finding.table, 
            "highly recommended" if finding.match_type == 'PERFECT' else "recommended",
            finding.requirement
        )
        
        summary += "This field {} and supports {} measurement. ".format(
            finding.why_relevant.lower(),
            req_info['name']
        )
        
        if finding.table_rows > 100000:
            summary += "The table contains {:,} rows of data, providing substantial volume for visibility analysis. ".format(
                finding.table_rows
            )
        elif finding.table_rows > 0:
            summary += "The table contains {:,} rows of data. ".format(finding.table_rows)
        
        summary += "Business value: {} ".format(req_info['business_value'])
        
        summary += "Implementation guidance: {}".format(finding.recommendation)
        
        return summary
    
    def _save_executive_summary(self, findings: List[AO1Finding], timestamp: str):
        """Save executive summary report"""
        filename = "AO1_Executive_Summary_{}.txt".format(timestamp)
        
        with open(filename, 'w') as f:
            f.write("AO1 FIELD DISCOVERY EXECUTIVE SUMMARY\n")
            f.write("=" * 50 + "\n")
            f.write("Analysis Date: {}\n\n".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            
            # Key metrics
            by_req = defaultdict(list)
            for finding in findings:
                by_req[finding.requirement].append(finding)
            
            f.write("KEY FINDINGS:\n")
            f.write("• Total AO1-relevant fields identified: {}\n".format(len(findings)))
            f.write("• Requirements with field coverage: {}/8\n".format(len(by_req)))
            f.write("• High-confidence matches: {}\n".format(len([f for f in findings if f.confidence_score >= 0.8])))
            f.write("• Perfect matches for immediate use: {}\n".format(len([f for f in findings if f.match_type == 'PERFECT'])))
            f.write("• Total data volume available: {:.1f} GB\n\n".format(sum(f.data_volume_gb for f in findings)))
            
            # Top recommendations
            f.write("TOP RECOMMENDATIONS:\n")
            top_5 = sorted(findings, key=lambda x: x.priority_score, reverse=True)[:5]
            for i, finding in enumerate(top_5, 1):
                f.write("{}. {}.{}.{} - {} ({:.1%} confidence)\n".format(
                    i, finding.dataset, finding.table, finding.field_name, 
                    finding.requirement, finding.confidence_score
                ))
            
            f.write("\nNEXT STEPS:\n")
            f.write("1. Implement perfect matches immediately\n")
            f.write("2. Validate high-confidence candidates\n")
            f.write("3. Address coverage gaps for missing requirements\n")
            f.write("4. Focus on high-volume tables for maximum impact\n")

def main():
    """Perfect main execution"""
    try:
        discovery = PerfectAO1Discovery()
        findings = discovery.discover_perfect_ao1_fields()
        discovery.generate_perfect_report(findings)
        discovery.save_perfect_results(findings)
        
        print("\nPERFECT AO1 DISCOVERY COMPLETE!")
        print("Review the generated reports for detailed implementation guidance.")
        
    except KeyboardInterrupt:
        print("\nDiscovery interrupted by user")
    except Exception as e:
        print("\nError: {}".format(e))

if __name__ == "__main__":
    main()