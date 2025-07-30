"""
Perfect AO1 Field Discovery System
Business-Focused BigQuery Analysis for Audit Compliance

This system analyzes BigQuery tables to identify the exact fields needed for AO1 audit requirements,
providing clear business summaries and actionable recommendations for each requirement.
"""

import os
import sys
import json
import time
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import requests

# BigQuery imports
from google.cloud import bigquery
from google.oauth2 import service_account
from google.cloud.exceptions import NotFound, Forbidden, BadRequest, ServerError

# Configuration
PROJECT_ID = "prj-fisv-p-gcss-sas-dl9dd0f1df"
SERVICE_ACCOUNT_FILE = "gcp_prod_key.json"

# Setup logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger('AO1Discovery')

@dataclass
class AO1Finding:
    """Perfect AO1 field finding with business context"""
    requirement: str
    requirement_name: str
    dataset: str
    table: str
    field_name: str
    field_type: str
    table_rows: int
    confidence: str
    business_context: str
    usage_recommendation: str
    table_purpose: str
    why_relevant: str

class AO1RequirementsAnalyzer:
    """Analyzes tables and fields against specific AO1 requirements"""
    
    def __init__(self):
        self.requirements = {
            'REQ-1': {
                'name': 'Global View - Asset Identification',
                'purpose': 'Count unique logging assets vs CMDB for visibility percentage',
                'key_fields': ['hostname', 'host_name', 'computer_name', 'device_name', 'asset_id', 'system_id', 'ip_address', 'mac_address', 'serial_number', 'uuid'],
                'table_types': ['cmdb', 'asset', 'inventory', 'device', 'computer', 'host', 'server', 'endpoint', 'workstation', 'system'],
                'business_goal': 'Identify primary asset identifiers to correlate log sources with CMDB records'
            },
            
            'REQ-2': {
                'name': 'Infrastructure Type - Deployment Classification',
                'purpose': 'Classify assets by deployment model (On-Prem, Cloud, SaaS, API)',
                'key_fields': ['cloud', 'aws', 'azure', 'gcp', 'datacenter', 'virtual_machine', 'vm', 'container', 'kubernetes', 'saas', 'application_type', 'deployment_type', 'platform', 'infrastructure_type'],
                'table_types': ['cloud', 'infrastructure', 'deployment', 'platform', 'service', 'application', 'vm', 'container'],
                'business_goal': 'Categorize infrastructure to show visibility across deployment models'
            },
            
            'REQ-3': {
                'name': 'Regional/Country View - Geographic Classification',
                'purpose': 'Show visibility by geographic location and region',
                'key_fields': ['region', 'country', 'location', 'datacenter', 'site', 'zone', 'office', 'facility', 'geographic_region', 'aws_region', 'azure_region', 'gcp_region'],
                'table_types': ['region', 'location', 'geographic', 'datacenter', 'site', 'facility', 'office'],
                'business_goal': 'Demonstrate geographic coverage of logging across all regions'
            },
            
            'REQ-4': {
                'name': 'Business/Application View - Organizational Structure',
                'purpose': 'Show visibility by business unit and application ownership',
                'key_fields': ['business_unit', 'bu', 'department', 'division', 'organization', 'application', 'app_name', 'service_name', 'owner', 'cost_center', 'project'],
                'table_types': ['business', 'application', 'app', 'organization', 'department', 'service', 'project'],
                'business_goal': 'Track logging coverage across business units and applications'
            },
            
            'REQ-5': {
                'name': 'System Classification - Server Function and OS',
                'purpose': 'Classify systems by function and operating system type',
                'key_fields': ['windows', 'linux', 'unix', 'operating_system', 'os_type', 'server_type', 'server_function', 'web_server', 'database_server', 'mail_server', 'dns_server', 'system_type'],
                'table_types': ['system', 'server', 'os', 'operating', 'database', 'web', 'mail', 'dns'],
                'business_goal': 'Show logging coverage across different system types and functions'
            },
            
            'REQ-6': {
                'name': 'Security Control Coverage - Agent Deployment',
                'purpose': 'Measure security agent coverage (EDR, Tanium, DLP)',
                'key_fields': ['edr', 'crowdstrike', 'falcon', 'tanium', 'dlp', 'agent_id', 'sensor_id', 'endpoint_security', 'antivirus', 'security_agent'],
                'table_types': ['security', 'agent', 'endpoint', 'edr', 'crowdstrike', 'tanium', 'dlp'],
                'business_goal': 'Demonstrate security tool coverage across the environment'
            },
            
            'REQ-7': {
                'name': 'Logging Compliance - Platform Coverage',
                'purpose': 'Show logging platform compliance (Splunk, Chronicle)',
                'key_fields': ['splunk', 'sourcetype', 'index', 'chronicle', 'log_source', 'event_source', 'data_source', 'ingestion', 'parser'],
                'table_types': ['log', 'event', 'splunk', 'chronicle', 'siem', 'logging', 'audit'],
                'business_goal': 'Validate that data is properly ingested into logging platforms'
            },
            
            'REQ-8': {
                'name': 'Domain Visibility - Network Asset Discovery',
                'purpose': 'Identify assets by hostname and domain for network visibility',
                'key_fields': ['domain', 'fqdn', 'dns_name', 'hostname', 'network_name', 'domain_name'],
                'table_types': ['domain', 'dns', 'network', 'hostname'],
                'business_goal': 'Map network assets through domain and hostname analysis'
            }
        }
    
    def analyze_table_relevance(self, dataset_name: str, table_name: str) -> Dict[str, Any]:
        """Analyze how relevant a table is to AO1 requirements"""
        table_full_name = "{}.{}".format(dataset_name, table_name).lower()
        
        relevance = {
            'is_ao1_relevant': False,
            'primary_requirements': [],
            'table_purpose': 'Unknown business purpose',
            'confidence_level': 'Low'
        }
        
        requirement_matches = {}
        
        for req_id, req_data in self.requirements.items():
            score = 0
            matched_types = []
            
            # Check if table name matches requirement table types
            for table_type in req_data['table_types']:
                if table_type in table_full_name:
                    score += 1
                    matched_types.append(table_type)
            
            if score > 0:
                requirement_matches[req_id] = {
                    'score': score,
                    'matched_types': matched_types,
                    'requirement_name': req_data['name'],
                    'business_goal': req_data['business_goal']
                }
        
        if requirement_matches:
            # Sort by relevance score
            sorted_matches = sorted(requirement_matches.items(), key=lambda x: x[1]['score'], reverse=True)
            
            relevance['is_ao1_relevant'] = True
            relevance['primary_requirements'] = [req_id for req_id, _ in sorted_matches[:2]]  # Top 2 matches
            
            # Set table purpose based on primary requirement
            primary_req = sorted_matches[0][1]
            relevance['table_purpose'] = primary_req['business_goal']
            relevance['confidence_level'] = 'High' if primary_req['score'] >= 2 else 'Medium'
        
        return relevance
    
    def analyze_field_relevance(self, field_name: str, field_type: str, table_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze field relevance to AO1 requirements with business context"""
        field_lower = field_name.lower().strip()
        
        field_analysis = {
            'matches': [],
            'best_requirement': None,
            'confidence': 'None',
            'business_value': 'Unknown'
        }
        
        requirement_scores = {}
        
        # Check field against each requirement
        for req_id, req_data in self.requirements.items():
            score = 0
            match_type = None
            
            # Exact match
            if field_lower in [kf.lower() for kf in req_data['key_fields']]:
                score = 10
                match_type = 'Exact Match'
            else:
                # Partial match
                for key_field in req_data['key_fields']:
                    if key_field in field_lower or field_lower in key_field:
                        if len(key_field) >= 3:  # Avoid false positives
                            score = max(score, 7)
                            match_type = 'Partial Match'
            
            # Boost score if field requirement matches table context
            if req_id in table_context.get('primary_requirements', []):
                score *= 2
                if match_type:
                    match_type += ' (Table Context Match)'
            
            if score > 0:
                requirement_scores[req_id] = {
                    'score': score,
                    'match_type': match_type,
                    'requirement_name': req_data['name'],
                    'business_goal': req_data['business_goal']
                }
        
        if requirement_scores:
            # Find best match
            best_req_id = max(requirement_scores.keys(), key=lambda k: requirement_scores[k]['score'])
            best_match = requirement_scores[best_req_id]
            
            field_analysis['best_requirement'] = best_req_id
            field_analysis['matches'] = list(requirement_scores.keys())
            
            # Set confidence level
            if best_match['score'] >= 15:
                field_analysis['confidence'] = 'Very High'
            elif best_match['score'] >= 10:
                field_analysis['confidence'] = 'High'
            elif best_match['score'] >= 7:
                field_analysis['confidence'] = 'Medium'
            else:
                field_analysis['confidence'] = 'Low'
            
            field_analysis['business_value'] = best_match['business_goal']
        
        return field_analysis

class PerfectAO1Analyzer:
    """Perfect AO1 analyzer focused on business outcomes"""
    
    def __init__(self):
        self.client = None
        self.requirements_analyzer = AO1RequirementsAnalyzer()
        self.findings = []
        
        # Authenticate
        self._authenticate_bigquery()
    
    def _authenticate_bigquery(self):
        """Authenticate with BigQuery"""
        try:
            credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
            self.client = bigquery.Client(project=PROJECT_ID, credentials=credentials)
            print("✓ BigQuery: Connected successfully")
        except Exception as e:
            print("✗ BigQuery: Authentication failed - {}".format(e))
            sys.exit(1)
    
    def scan_for_ao1_fields(self) -> List[AO1Finding]:
        """Scan BigQuery for AO1-relevant fields with business context"""
        print("PERFECT AO1 FIELD DISCOVERY")
        print("=" * 50)
        print("Scanning for fields that support AO1 audit requirements...")
        
        try:
            datasets = [d.dataset_id for d in self.client.list_datasets()]
            print("Found {} datasets to analyze".format(len(datasets)))
            
            total_tables = 0
            processed_tables = 0
            
            # Count tables
            for dataset_id in datasets:
                try:
                    tables = list(self.client.list_tables(dataset_id))
                    total_tables += len(tables)
                except:
                    continue
            
            print("Processing {} tables for AO1 relevance...".format(total_tables))
            
            # Analyze each table
            for dataset_id in datasets:
                try:
                    tables = list(self.client.list_tables(dataset_id))
                    
                    for table in tables:
                        processed_tables += 1
                        
                        if processed_tables % 25 == 0:
                            progress = (processed_tables / total_tables) * 100
                            print("Progress: {:.1f}% ({}/{})".format(progress, processed_tables, total_tables))
                        
                        # Analyze this table
                        self._analyze_table_for_ao1(dataset_id, table.table_id)
                        
                except Exception as e:
                    continue
            
            print("✓ Analysis complete: {} AO1 findings discovered".format(len(self.findings)))
            return self.findings
            
        except Exception as e:
            print("✗ Scan failed: {}".format(e))
            return []
    
    def _analyze_table_for_ao1(self, dataset_id: str, table_id: str):
        """Analyze a specific table for AO1 fields"""
        try:
            # Get table metadata
            table_ref = self.client.dataset(dataset_id).table(table_id)
            table = self.client.get_table(table_ref)
            
            # Analyze table business context
            table_context = self.requirements_analyzer.analyze_table_relevance(dataset_id, table_id)
            
            # Only analyze tables that are AO1-relevant or potentially relevant
            if not table_context['is_ao1_relevant'] and len(table_context['primary_requirements']) == 0:
                return
            
            # Analyze each field in the table
            for field in table.schema:
                self._analyze_field_for_ao1(field, dataset_id, table_id, table, table_context)
                
        except Exception as e:
            pass  # Skip problematic tables
    
    def _analyze_field_for_ao1(self, field, dataset_id: str, table_id: str, table, table_context: Dict[str, Any]):
        """Analyze a field for AO1 relevance"""
        field_analysis = self.requirements_analyzer.analyze_field_relevance(
            field.name, field.field_type, table_context
        )
        
        # Only include fields with medium or higher confidence
        if field_analysis['confidence'] in ['Medium', 'High', 'Very High']:
            
            # Create business recommendation
            recommendation = self._create_field_recommendation(
                field, dataset_id, table_id, table, field_analysis, table_context
            )
            
            finding = AO1Finding(
                requirement=field_analysis['best_requirement'],
                requirement_name=self.requirements_analyzer.requirements[field_analysis['best_requirement']]['name'],
                dataset=dataset_id,
                table=table_id,
                field_name=field.name,
                field_type=field.field_type,
                table_rows=table.num_rows or 0,
                confidence=field_analysis['confidence'],
                business_context=table_context['table_purpose'],
                usage_recommendation=recommendation['usage'],
                table_purpose=recommendation['table_purpose'],
                why_relevant=recommendation['relevance_explanation']
            )
            
            self.findings.append(finding)
    
    def _create_field_recommendation(self, field, dataset_id: str, table_id: str, table, 
                                   field_analysis: Dict[str, Any], table_context: Dict[str, Any]) -> Dict[str, str]:
        """Create business-focused recommendation for field usage"""
        req_id = field_analysis['best_requirement']
        req_data = self.requirements_analyzer.requirements[req_id]
        
        # Table size context
        size_context = ""
        if table.num_rows:
            if table.num_rows > 1000000:
                size_context = "large dataset ({:,} rows)".format(table.num_rows)
            elif table.num_rows > 10000:
                size_context = "medium dataset ({:,} rows)".format(table.num_rows)
            else:
                size_context = "small dataset ({:,} rows)".format(table.num_rows)
        else:
            size_context = "dataset size unknown"
        
        # Usage recommendation
        usage_template = "Use this field as a {} for {} analysis. This {} provides {} coverage."
        
        field_role = "primary identifier" if field_analysis['confidence'] == 'Very High' else \
                    "key field" if field_analysis['confidence'] == 'High' else \
                    "supporting field"
        
        coverage_type = "comprehensive" if table.num_rows and table.num_rows > 100000 else "targeted"
        
        usage = usage_template.format(
            field_role,
            req_data['name'].split(' - ')[1].lower(),
            size_context,
            coverage_type
        )
        
        # Table purpose explanation
        table_purpose = "This table appears to contain {} and is highly relevant for {} requirements.".format(
            table_context['table_purpose'].lower(),
            req_data['name']
        )
        
        # Why it's relevant
        relevance_explanation = "Field '{}' directly supports {} by providing {}. {}".format(
            field.name,
            req_data['purpose'].lower(),
            field_analysis['business_value'].lower(),
            "This is exactly the type of data needed for AO1 compliance measurement." if field_analysis['confidence'] == 'Very High' else
            "This field can contribute to AO1 visibility calculations."
        )
        
        return {
            'usage': usage,
            'table_purpose': table_purpose,
            'relevance_explanation': relevance_explanation
        }
    
    def generate_business_report(self, findings: List[AO1Finding]):
        """Generate business-focused report with clear summaries"""
        if not findings:
            print("\nAO1 FIELD DISCOVERY RESULTS")
            print("=" * 50)
            print("No AO1-relevant fields found in accessible datasets.")
            print("Recommendation: Review data ingestion and field naming conventions.")
            return
        
        # Group findings by requirement
        by_requirement = defaultdict(list)
        for finding in findings:
            by_requirement[finding.requirement].append(finding)
        
        # Sort findings within each requirement by table size (largest first)
        for req in by_requirement:
            by_requirement[req].sort(key=lambda x: x.table_rows, reverse=True)
        
        print("\nAO1 FIELD DISCOVERY RESULTS")
        print("=" * 50)
        print("Business-Focused Analysis for Audit Compliance")
        print("Total Discoveries: {} fields across {} requirements".format(len(findings), len(by_requirement)))
        
        # Generate requirement-by-requirement analysis
        for req_id in ['REQ-1', 'REQ-2', 'REQ-3', 'REQ-4', 'REQ-5', 'REQ-6', 'REQ-7', 'REQ-8']:
            req_findings = by_requirement.get(req_id, [])
            req_data = self.requirements_analyzer.requirements[req_id]
            
            print("\n{}".format("=" * 80))
            print("{}: {}".format(req_id, req_data['name']))
            print("Business Goal: {}".format(req_data['business_goal']))
            print("=" * 80)
            
            if not req_findings:
                print("STATUS: No suitable fields found for this requirement")
                print("IMPACT: Cannot measure {} compliance".format(req_data['name'].split(' - ')[1].lower()))
                print("RECOMMENDATION: Review data sources and field naming for {} data".format(req_data['purpose'].lower()))
                continue
            
            # Categorize findings by confidence
            very_high = [f for f in req_findings if f.confidence == 'Very High']
            high = [f for f in req_findings if f.confidence == 'High']
            medium = [f for f in req_findings if f.confidence == 'Medium']
            
            print("FINDINGS SUMMARY:")
            print("  Very High Confidence: {} fields".format(len(very_high)))
            print("  High Confidence: {} fields".format(len(high)))
            print("  Medium Confidence: {} fields".format(len(medium)))
            
            # Show top recommendations
            top_findings = req_findings[:5]  # Top 5 by table size
            
            print("\nTOP RECOMMENDED FIELDS:")
            for i, finding in enumerate(top_findings, 1):
                rows_display = "{:,} rows".format(finding.table_rows) if finding.table_rows > 0 else "size unknown"
                
                print("\n{}. FIELD: '{}' in {}.{} ({})".format(i, finding.field_name, finding.dataset, finding.table, rows_display))
                print("   CONFIDENCE: {}".format(finding.confidence))
                print("   BUSINESS CONTEXT: {}".format(finding.business_context))
                print("   USAGE: {}".format(finding.usage_recommendation))
                print("   WHY RELEVANT: {}".format(finding.why_relevant))
            
            if len(req_findings) > 5:
                print("\n   ... and {} additional fields available".format(len(req_findings) - 5))
        
        # Generate executive summary
        print("\n{}".format("=" * 80))
        print("EXECUTIVE SUMMARY")
        print("=" * 80)
        
        total_very_high = len([f for f in findings if f.confidence == 'Very High'])
        total_high = len([f for f in findings if f.confidence == 'High'])
        
        print("AO1 READINESS ASSESSMENT:")
        print("  Requirements with Data Available: {}/8 ({:.1f}%)".format(len(by_requirement), len(by_requirement)/8*100))
        print("  High-Quality Fields Ready for Use: {}".format(total_very_high + total_high))
        print("  Total Usable AO1 Fields: {}".format(len(findings)))
        
        # Data volume analysis
        total_rows = sum(f.table_rows for f in findings if f.table_rows > 0)
        print("  Total Data Volume: {:,} rows across all recommended tables".format(total_rows))
        
        print("\nNEXT STEPS:")
        print("1. PRIORITY: Focus on Very High and High confidence fields for immediate AO1 implementation")
        print("2. VALIDATION: Verify data quality and completeness in recommended tables")
        print("3. INTEGRATION: Use these fields to build AO1 visibility dashboards and reports")
        print("4. GAPS: Address requirements with no findings through data collection improvements")
    
    def save_business_results(self, findings: List[AO1Finding]):
        """Save results in business-friendly format"""
        if not findings:
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create detailed DataFrame with business summaries
        records = []
        for finding in findings:
            records.append({
                'AO1_Requirement': finding.requirement,
                'Requirement_Name': finding.requirement_name,
                'Field_Name': finding.field_name,
                'Dataset': finding.dataset,
                'Table': finding.table,
                'Field_Type': finding.field_type,
                'Table_Rows': finding.table_rows,
                'Confidence_Level': finding.confidence,
                'Business_Summary': "{} This field supports {} and should be used for AO1 compliance measurement.".format(
                    finding.why_relevant, finding.requirement_name.lower()
                ),
                'Usage_Recommendation': finding.usage_recommendation,
                'Table_Business_Purpose': finding.table_purpose,
                'Implementation_Priority': 'High' if finding.confidence in ['Very High', 'High'] else 'Medium',
                'Data_Volume_Category': 'Large' if finding.table_rows > 100000 else 'Medium' if finding.table_rows > 10000 else 'Small'
            })
        
        df = pd.DataFrame(records)
        
        # Sort by business priority
        priority_order = {'Very High': 4, 'High': 3, 'Medium': 2, 'Low': 1}
        df['_priority_sort'] = df['Confidence_Level'].map(priority_order)
        df = df.sort_values(['AO1_Requirement', '_priority_sort', 'Table_Rows'], ascending=[True, False, False])
        df = df.drop('_priority_sort', axis=1)
        
        # Save detailed results
        filename = "AO1_Field_Discovery_Results_{}.csv".format(timestamp)
        df.to_csv(filename, index=False)
        
        # Create executive summary
        summary_records = []
        by_req = df.groupby('AO1_Requirement')
        
        for req, group in by_req:
            very_high = len(group[group['Confidence_Level'] == 'Very High'])
            high = len(group[group['Confidence_Level'] == 'High'])
            medium = len(group[group['Confidence_Level'] == 'Medium'])
            total_rows = group['Table_Rows'].sum()
            
            top_field = group.iloc[0]  # Highest priority field
            
            summary_records.append({
                'AO1_Requirement': req,
                'Requirement_Name': top_field['Requirement_Name'],
                'Fields_Found': len(group),
                'Very_High_Confidence': very_high,
                'High_Confidence': high,
                'Medium_Confidence': medium,
                'Total_Data_Rows': total_rows,
                'Top_Recommended_Field': top_field['Field_Name'],
                'Top_Recommended_Table': "{}.{}".format(top_field['Dataset'], top_field['Table']),
                'Business_Impact': "Can measure {} compliance with {} high-quality fields covering {:,} rows of data.".format(
                    top_field['Requirement_Name'].split(' - ')[1].lower(),
                    very_high + high,
                    total_rows
                ),
                'Implementation_Status': 'Ready' if very_high + high > 0 else 'Needs Review'
            })
        
        summary_df = pd.DataFrame(summary_records)
        summary_filename = "AO1_Executive_Summary_{}.csv".format(timestamp)
        summary_df.to_csv(summary_filename, index=False)
        
        print("\nRESULTS SAVED:")
        print("  Detailed Analysis: {} ({} fields)".format(filename, len(df)))
        print("  Executive Summary: {} ({} requirements)".format(summary_filename, len(summary_df)))

def main():
    """Main execution"""
    print("PERFECT AO1 FIELD DISCOVERY SYSTEM")
    print("Business-Focused BigQuery Analysis")
    print("Finding the exact fields you need for AO1 compliance")
    print("=" * 60)
    
    try:
        analyzer = PerfectAO1Analyzer()
        
        # Scan for AO1 fields
        findings = analyzer.scan_for_ao1_fields()
        
        # Generate business report
        analyzer.generate_business_report(findings)
        
        # Save business-friendly results
        analyzer.save_business_results(findings)
        
        if findings:
            print("\nSUCCESS: AO1 field discovery complete!")
            print("Use the generated CSV files to implement your AO1 compliance measurement.")
        else:
            print("\nATTENTION: No AO1 fields found.")
            print("Consider reviewing data ingestion and field naming conventions.")
        
    except KeyboardInterrupt:
        print("\nScan interrupted by user")
    except Exception as e:
        print("\nError: {}".format(e))

if __name__ == "__main__":
    main()