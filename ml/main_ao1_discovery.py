#!/usr/bin/env python3
"""
Main AO1 Discovery System
=========================
Enterprise AO1 field discovery with advanced ML and corporate security.
"""

import sys
from datetime import datetime
from ao1_config_and_logging import logger, get_config
from ml_system import get_ml_system
from field_analyzer import get_field_analyzer
from bigquery_scanner import get_scanner
from report_generator import get_report_generator

def main():
    """Main AO1 discovery execution."""
    print("AO1 BIGQUERY FIELD DISCOVERY SYSTEM")
    print("=" * 60)
    print("Enterprise AO1 compliance field identification")
    print(f"Target: {get_config()['project_id']}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Step 1: Initialize ML system
        print("STEP 1: ML SYSTEM INITIALIZATION")
        print("-" * 40)
        ml_system = get_ml_system()
        print(f"ML Strategy: {ml_system.strategy}")
        print(f"Compute Device: {ml_system.device}")
        print()
        
        # Step 2: Initialize field analyzer
        print("STEP 2: AO1 FIELD ANALYZER")
        print("-" * 35)
        analyzer = get_field_analyzer(ml_system)
        print("Field analyzer initialized with business context")
        print("Analysis: Exact matching + ML semantic analysis")
        print()
        
        # Step 3: BigQuery scanning
        print("STEP 3: BIGQUERY SCANNING") 
        print("-" * 30)
        scanner = get_scanner()
        
        if not scanner.authenticate():
            print("ERROR: BigQuery authentication failed")
            print("Check service account file: gcp_prod_key.json")
            return False
        
        print("BigQuery authenticated successfully")
        
        # Configuration
        print("\nScan Configuration Options:")
        print("1. Quick scan (5 datasets, 10 tables each)")
        print("2. Standard scan (20 datasets, 50 tables each)")
        print("3. Deep scan (50 datasets, 100 tables each)")
        
        try:
            choice = input("Select scan depth (1-3, default=2): ").strip()
            
            if choice == "1":
                max_datasets, max_tables = 5, 10
            elif choice == "3":
                max_datasets, max_tables = 50, 100
            else:
                max_datasets, max_tables = 20, 50
                
        except (ValueError, KeyboardInterrupt):
            max_datasets, max_tables = 20, 50
        
        print(f"\nStarting scan: {max_datasets} datasets, {max_tables} tables each")
        print("Press Ctrl+C anytime to generate partial results")
        
        # Perform scan
        scan_results = scanner.scan_project(analyzer, max_datasets, max_tables)
        stats = scanner.get_stats()
        
        if not scan_results:
            print("\nNo AO1-relevant fields found")
            print("Recommendations:")
            print("- Expand scan scope (more datasets/tables)")
            print("- Verify data source naming conventions")
            print("- Check logging data ingestion")
            return True
        
        # Step 4: Generate report
        print("\nSTEP 4: REPORT GENERATION")
        print("-" * 30)
        report_gen = get_report_generator()
        report_file = report_gen.generate_report(scan_results, stats)
        
        if report_file:
            print(f"Report generated: {report_file}")
        
        # Step 5: Executive summary
        print("\nEXECUTIVE SUMMARY")
        print("-" * 25)
        total_findings = sum(len(results) for results in scan_results.values())
        high_priority = sum(
            1 for results in scan_results.values()
            for analysis in results
            if analysis.strategic_priority > 150
        )
        
        exact_matches = sum(
            1 for results in scan_results.values()
            for analysis in results 
            if analysis.match_type == 'EXACT'
        )
        
        print(f"AO1 fields discovered: {total_findings:,}")
        print(f"Exact keyword matches: {exact_matches}")
        print(f"High-priority fields: {high_priority}")
        print(f"Datasets with AO1 data: {len(scan_results)}")
        print(f"Success rate: {(total_findings/max(stats['fields_analyzed'],1))*100:.2f}%")
        
        # Top findings preview
        all_findings = []
        for results in scan_results.values():
            all_findings.extend(results)
        
        all_findings.sort(key=lambda x: x.strategic_priority, reverse=True)
        
        print(f"\nTOP 5 STRATEGIC RECOMMENDATIONS:")
        for i, finding in enumerate(all_findings[:5], 1):
            print(f"{i}. {finding.dataset_name}.{finding.table_name}.{finding.field_name}")
            print(f"   {finding.match_type} match | {finding.row_count:,} rows | {finding.confidence:.1f}% confidence")
            print(f"   {finding.recommendation}")
        
        print("\nNEXT STEPS:")
        print("1. Review detailed report for implementation guidance")
        print("2. Prioritize high-confidence exact matches")
        print("3. Validate field mappings and data quality")  
        print("4. Begin AO1 visibility measurement implementation")
        
        if report_file:
            print(f"\nDetailed analysis: {report_file}")
        
        print("\nAO1 FIELD DISCOVERY COMPLETE")
        return True
        
    except KeyboardInterrupt:
        print("\nScan interrupted by user")
        
        # Generate partial results if available
        try:
            if 'scanner' in locals() and hasattr(scanner, 'stats'):
                stats = scanner.get_stats()
                if stats['ao1_matches'] > 0:
                    print("Generating partial results...")
                    # Could add partial report generation here
                    
        except Exception as e:
            logger.debug(f"Partial results generation failed: {e}")
        
        return False
        
    except Exception as e:
        logger.error(f"Discovery failed: {e}")
        print(f"ERROR: {e}")
        print("Check log file for details: ao1_discovery.log")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)