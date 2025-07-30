#!/usr/bin/env python3
"""
AO1 Report Generator
===================
Professional reporting with strategic insights.
"""

import os
from datetime import datetime
from typing import Dict, List
from ao1_config_and_logging import logger, AO1_REQUIREMENTS_META

class AO1ReportGenerator:
    """Smart report generator with business insights."""
    
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def generate_report(self, scan_results: Dict, stats: Dict, 
                       output_dir: str = ".") -> str:
        """Generate comprehensive AO1 report."""
        
        # Organize results by requirement
        req_results = self._organize_by_requirement(scan_results)
        
        # Generate insights
        insights = self._generate_insights(scan_results, req_results, stats)
        
        # Create report content
        content = self._create_report_content(req_results, insights, stats)
        
        # Write report
        filename = f"AO1_Discovery_Report_{self.timestamp}.txt"
        filepath = os.path.join(output_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Report generated: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return ""
    
    def _organize_by_requirement(self, scan_results: Dict) -> Dict:
        """Organize results by AO1 requirement."""
        req_results = {}
        
        # Initialize requirements
        for req_id in AO1_REQUIREMENTS_META.keys():
            req_results[req_id] = []
        
        # Categorize findings
        for dataset_results in scan_results.values():
            for analysis in dataset_results:
                for req in analysis.matching_requirements:
                    req_id = req.split(':')[0]
                    if req_id in req_results:
                        req_results[req_id].append(analysis)
        
        # Sort each requirement by priority
        for req_id in req_results:
            req_results[req_id].sort(
                key=lambda x: (x.strategic_priority, x.row_count), 
                reverse=True
            )
        
        return req_results
    
    def _generate_insights(self, scan_results: Dict, req_results: Dict, 
                          stats: Dict) -> Dict:
        """Generate strategic insights."""
        total_findings = sum(len(results) for results in scan_results.values())
        
        # High-value opportunities
        high_value = []
        for dataset_results in scan_results.values():
            for analysis in dataset_results:
                if (analysis.match_type == 'EXACT' and 
                    analysis.row_count > 100000 and
                    analysis.confidence >= 95):
                    high_value.append(analysis)
        
        high_value.sort(key=lambda x: x.strategic_priority, reverse=True)
        
        # Coverage analysis
        coverage = {}
        for req_id, req_meta in AO1_REQUIREMENTS_META.items():
            findings = req_results.get(req_id, [])
            exact = len([f for f in findings if f.match_type == 'EXACT'])
            high_conf = len([f for f in findings if f.confidence >= 80])
            
            coverage[req_id] = {
                'name': req_meta['name'],
                'priority': req_meta['priority'],
                'total': len(findings),
                'exact': exact,
                'high_confidence': high_conf,
                'score': min(100, exact * 20 + high_conf * 5)
            }
        
        # Quick wins
        quick_wins = []
        for dataset_results in scan_results.values():
            for analysis in dataset_results:
                if (analysis.match_type == 'EXACT' and
                    analysis.confidence >= 95 and
                    analysis.row_count > 50000):
                    quick_wins.append(analysis)
        
        quick_wins.sort(key=lambda x: x.strategic_priority, reverse=True)
        
        return {
            'total_findings': total_findings,
            'high_value_opportunities': high_value[:10],
            'coverage_analysis': coverage,
            'quick_wins': quick_wins[:5],
            'datasets_analyzed': stats.get('datasets_scanned', 0),
            'success_rate': (total_findings / max(stats.get('fields_analyzed', 1), 1)) * 100
        }
    
    def _create_report_content(self, req_results: Dict, insights: Dict, 
                              stats: Dict) -> str:
        """Create comprehensive report content."""
        content = []
        
        # Header
        content.extend([
            "AO1 BIGQUERY FIELD DISCOVERY REPORT",
            "=" * 80,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Project: prj-fisv-p-gcss-sas-d19dd0f1df",
            ""
        ])
        
        # Executive Summary
        content.extend([
            "EXECUTIVE SUMMARY",
            "=" * 40,
            "",
            f"Total AO1 fields discovered: {insights['total_findings']:,}",
            f"Datasets analyzed: {insights['datasets_analyzed']}",
            f"Success rate: {insights['success_rate']:.2f}%",
            f"High-value opportunities: {len(insights['high_value_opportunities'])}",
            ""
        ])
        
        # Coverage Analysis
        content.extend([
            "AO1 REQUIREMENTS COVERAGE",
            "-" * 35,
            ""
        ])
        
        for req_id, analysis in insights['coverage_analysis'].items():
            priority_marker = "🔴" if analysis['priority'] == 'HIGH' else "🟡"
            content.append(
                f"{priority_marker} {req_id} {analysis['name']}: "
                f"{analysis['total']} candidates "
                f"({analysis['exact']} exact) - "
                f"Score: {analysis['score']}/100"
            )
        
        content.append("")
        
        # Strategic Recommendations
        if insights['quick_wins']:
            content.extend([
                "IMMEDIATE IMPLEMENTATION PRIORITIES",
                "-" * 45,
                ""
            ])
            
            for i, analysis in enumerate(insights['quick_wins'], 1):
                content.extend([
                    f"{i}. {analysis.dataset_name}.{analysis.table_name}.{analysis.field_name}",
                    f"   Volume: {analysis.row_count:,} rows | "
                    f"Confidence: {analysis.confidence:.1f}% | "
                    f"Type: {analysis.match_type}",
                    f"   {analysis.recommendation}",
                    ""
                ])
        
        # Detailed Findings
        content.extend([
            "",
            "DETAILED FINDINGS BY REQUIREMENT",
            "=" * 50,
            ""
        ])
        
        for req_id, req_meta in AO1_REQUIREMENTS_META.items():
            findings = req_results.get(req_id, [])
            
            content.extend([
                f"{req_id}: {req_meta['name']} ({req_meta['priority']} PRIORITY)",
                "-" * 60,
                f"Purpose: {req_meta['description']}",
                ""
            ])
            
            if not findings:
                content.extend([
                    "No matching fields found.",
                    "Recommendation: Expand search scope or verify data sources.",
                    ""
                ])
                continue
            
            # Summary stats
            exact = len([f for f in findings if f.match_type == 'EXACT'])
            ml_id = len([f for f in findings if f.match_type == 'ML_IDENTIFIED'])
            partial = len([f for f in findings if f.match_type == 'PARTIAL'])
            suspected = len([f for f in findings if f.match_type == 'SUSPECTED'])
            
            content.extend([
                f"SUMMARY: {len(findings)} total candidates",
                f"  EXACT: {exact} | ML: {ml_id} | PARTIAL: {partial} | SUSPECTED: {suspected}",
                "",
                "TOP RECOMMENDATIONS:",
                ""
            ])
            
            # Top 10 fields for this requirement
            for i, analysis in enumerate(findings[:10], 1):
                content.extend([
                    f"{i}. {analysis.field_name} in {analysis.dataset_name}.{analysis.table_name}",
                    f"   Data: {analysis.row_count:,} rows | "
                    f"Match: {analysis.match_type} | "
                    f"Confidence: {analysis.confidence:.1f}%",
                    f"   Business Context: {analysis.business_context}",
                    f"   Recommendation: {analysis.recommendation}",
                    ""
                ])
        
        # Implementation Roadmap
        content.extend([
            "",
            "IMPLEMENTATION ROADMAP",
            "=" * 30,
            "",
            "PHASE 1 (0-30 days): Quick Wins",
            "- Deploy exact matches with high data volumes",
            "- Focus on HIGH priority requirements (REQ-1, REQ-6, REQ-7)",
            "- Establish baseline measurements",
            "",
            "PHASE 2 (30-60 days): Comprehensive Coverage", 
            "- Implement ML-identified and high-confidence matches",
            "- Validate data quality and field mappings",
            "- Expand to all 8 requirements",
            "",
            "PHASE 3 (60-90 days): Optimization",
            "- Review suspected matches manually",
            "- Optimize based on initial results",
            "- Complete AO1 visibility implementation"
        ])
        
        return "\n".join(content)

def get_report_generator():
    """Get configured report generator."""
    return AO1ReportGenerator()