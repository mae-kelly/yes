#!/usr/bin/env python3

import asyncio
import argparse
import yaml
import sys
import logging
from pathlib import Path
from datetime import datetime

from main import AO1VisibilityOrchestrator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config(config_path: str) -> dict:
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def parse_arguments():
    parser = argparse.ArgumentParser(
        description='AO1 Log Visibility Measurement System - Quantum Discovery Engine'
    )
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Configuration file path (default: config.yaml)'
    )
    parser.add_argument(
        '--projects',
        nargs='+',
        help='Override project IDs from config'
    )
    parser.add_argument(
        '--output',
        help='Override output directory from config'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Perform discovery without storing results'
    )
    parser.add_argument(
        '--report-only',
        action='store_true',
        help='Generate report from existing database'
    )
    parser.add_argument(
        '--coverage-analysis',
        action='store_true',
        help='Run coverage analysis only'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    return parser.parse_args()

async def main():
    args = parse_arguments()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    config = load_config(args.config)
    
    if args.projects:
        config['project_ids'] = args.projects
    
    if args.output:
        config['output_dir'] = args.output
    
    if args.report_only:
        logger.info("Generating report from existing database...")
        from storage.quantum_database import QuantumDatabase
        
        output_dir = Path(config.get('output_dir', 'visibility_output'))
        db = QuantumDatabase(str(output_dir / "ao1_visibility.duckdb"))
        
        coverage_analysis = db.analyze_coverage()
        visibility_report = db.get_visibility_report()
        
        print("\n" + "=" * 80)
        print("COVERAGE ANALYSIS")
        print("=" * 80)
        
        if 'coverage' in coverage_analysis:
            for coverage_type, stats in coverage_analysis['coverage'].items():
                print(f"{coverage_type.replace('_', ' ').title():30} {stats['percentage']:6.1f}% ({stats['count']:,}/{coverage_analysis['total_hosts']:,})")
        
        print("\n" + "=" * 80)
        print("VISIBILITY SUMMARY")
        print("=" * 80)
        
        if 'summary' in visibility_report:
            summary = visibility_report['summary']
            print(f"Total Assets:                  {summary[0]:,}")
            print(f"Average Visibility Score:      {summary[1]:.2f}")
            print(f"High Visibility (>=80%):       {summary[2]:,}")
            print(f"Low Visibility (<50%):         {summary[3]:,}")
            print(f"In CMDB:                       {summary[4]:,}")
            print(f"Has Logging:                   {summary[5]:,}")
        
        db.close()
        return
    
    if args.coverage_analysis:
        logger.info("Running coverage analysis...")
        from storage.quantum_database import QuantumDatabase
        
        output_dir = Path(config.get('output_dir', 'visibility_output'))
        db = QuantumDatabase(str(output_dir / "ao1_visibility.duckdb"))
        
        coverage = db.analyze_coverage()
        
        print("\n" + "=" * 80)
        print("COVERAGE GAPS ANALYSIS")
        print("=" * 80)
        
        if 'infrastructure_gaps' in coverage:
            print("\nInfrastructure Gaps:")
            for gap in coverage['infrastructure_gaps']:
                print(f"  {gap[0]:20} Total: {gap[1]:6,}  No EDR: {gap[2]:6,}  No Splunk: {gap[3]:6,}")
        
        if 'regional_gaps' in coverage:
            print("\nRegional Gaps:")
            for gap in coverage['regional_gaps']:
                print(f"  {gap[0]:20} Total: {gap[1]:6,}  No CMDB: {gap[2]:6,}")
        
        db.close()
        return
    
    if not config.get('project_ids'):
        logger.error("No project IDs configured. Please update config.yaml or use --projects")
        sys.exit(1)
    
    print("\n" + "=" * 80)
    print("AO1 LOG VISIBILITY MEASUREMENT SYSTEM")
    print("Quantum Discovery Engine v2.0")
    print("=" * 80)
    print(f"\nConfiguration:")
    print(f"  Projects:     {', '.join(config['project_ids'])}")
    print(f"  Output:       {config.get('output_dir', 'visibility_output')}")
    print(f"  Sample Size:  {config.get('discovery_settings', {}).get('max_sample_size', 10000):,}")
    print(f"  Workers:      {config.get('discovery_settings', {}).get('max_workers', 32)}")
    print("=" * 80 + "\n")
    
    if args.dry_run:
        logger.info("DRY RUN MODE - Discovery will not save results")
        config['dry_run'] = True
    
    orchestrator = AO1VisibilityOrchestrator(config)
    
    try:
        results = await orchestrator.execute_discovery()
        
        print("\n" + "=" * 80)
        print("DISCOVERY COMPLETE")
        print("=" * 80)
        
        metrics = results.get('metrics_summary', {})
        print(f"\nAssets Discovered:    {metrics.get('total_assets', 0):,}")
        print(f"Processing Time:      {results['discovery_metadata']['processing_time_seconds']:.1f} seconds")
        
        print("\nCoverage Metrics:")
        for coverage_type, value in metrics.get('coverage', {}).items():
            print(f"  {coverage_type:20} {value}")
        
        print("\nGaps Identified:")
        for gap_type, count in metrics.get('gaps', {}).items():
            print(f"  {gap_type:20} {count:,}")
        
        print("\nOutput Files:")
        output_dir = Path(config.get('output_dir', 'visibility_output'))
        print(f"  Database:     {output_dir}/ao1_visibility.duckdb")
        print(f"  Report:       {output_dir}/executive_report.md")
        print(f"  Results:      {output_dir}/discovery_results_*.json")
        print(f"  Assets CSV:   {output_dir}/assets_*.csv")
        
        print("\n" + "=" * 80)
        print("SUCCESS: Visibility measurement complete")
        print("=" * 80 + "\n")
        
    except KeyboardInterrupt:
        logger.warning("Discovery interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Discovery failed: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())