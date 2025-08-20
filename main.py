#!/usr/bin/env python3

import asyncio
import argparse
import yaml
import sys
import logging
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Import the enhanced discovery engine
from discovery.enhanced_host_discovery import EnhancedHostDiscoveryEngine

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HostDiscoveryOrchestrator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.project_ids = config['project_ids']
        self.output_dir = Path(config.get('output_dir', 'host_discovery_output'))
        self.output_dir.mkdir(exist_ok=True)
        
        # Test authentication before proceeding
        self._test_authentication()
        
        self.discovery_engine = EnhancedHostDiscoveryEngine(self.project_ids, config)
        self.start_time = datetime.now()
    
    def _test_authentication(self):
        """Test BigQuery authentication for all projects"""
        logger.info("=" * 80)
        logger.info("TESTING BIGQUERY AUTHENTICATION")
        logger.info("=" * 80)
        
        # Check for authentication files
        auth_files = [
            "gcp_prod_key.json",
            os.path.join("gcp", "gcp_prod_key.json"),
            os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', '')
        ]
        
        auth_found = False
        for auth_file in auth_files:
            if auth_file and os.path.exists(auth_file):
                logger.info(f"✅ Found authentication file: {auth_file}")
                auth_found = True
                break
        
        if not auth_found:
            logger.warning("⚠️  No authentication file found. Will try default credentials.")
            logger.info("To use a service account, place 'gcp_prod_key.json' in the project directory")
        
        # Test connection to each project
        successful_projects = []
        failed_projects = []
        
        for project_id in self.project_ids:
            try:
                logger.info(f"\nTesting connection to project: {project_id}")
                
                # Simple import to test BigQuery
                from gcp.client import BigQueryClientManager
                manager = BigQueryClientManager(project_id)
                
                if manager.test_connection():
                    project_info = manager.get_project_info()
                    logger.info(f"✅ Connected to: {project_info['friendly_name']}")
                    successful_projects.append(project_id)
                else:
                    logger.error(f"❌ Failed to connect to project: {project_id}")
                    failed_projects.append(project_id)
                    
            except Exception as e:
                logger.error(f"❌ Authentication failed for {project_id}: {e}")
                failed_projects.append(project_id)
        
        logger.info("\n" + "=" * 80)
        logger.info("AUTHENTICATION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"✅ Successful: {len(successful_projects)} projects")
        logger.info(f"❌ Failed: {len(failed_projects)} projects")
        
        if failed_projects:
            logger.error(f"Failed projects: {', '.join(failed_projects)}")
            logger.error("\nTo fix authentication issues:")
            logger.error("1. Place service account key as 'gcp_prod_key.json' in project directory")
            logger.error("2. Or set GOOGLE_APPLICATION_CREDENTIALS environment variable")
            logger.error("3. Or run: gcloud auth application-default login")
            
            if not successful_projects:
                logger.error("\n❌ No projects accessible. Exiting.")
                sys.exit(1)
            else:
                logger.warning(f"\n⚠️  Continuing with {len(successful_projects)} accessible projects")
                self.project_ids = successful_projects
        else:
            logger.info("\n✅ All projects accessible!")
        
        logger.info("=" * 80 + "\n")
    
    async def execute_host_discovery(self) -> Dict[str, Any]:
        """Execute the comprehensive host discovery"""
        logger.info("=" * 80)
        logger.info("COMPREHENSIVE HOST DISCOVERY SYSTEM")
        logger.info("Enhanced BigQuery Scanner v3.0")
        logger.info("=" * 80)
        
        logger.info(f"🎯 Target: Find ALL hosts across ALL tables in ALL datasets")
        logger.info(f"🔍 Projects: {', '.join(self.project_ids)}")
        logger.info(f"📊 Columns to collect: 17 specific attributes per host")
        logger.info(f"🔗 Merge strategy: Combine data from multiple tables per host")
        
        try:
            # Execute discovery
            hosts = await self.discovery_engine.discover_all_hosts()
            
            if not hosts:
                logger.warning("⚠️  No hosts discovered. Check if tables contain host columns.")
                return self._create_empty_results()
            
            logger.info(f"✅ Successfully discovered {len(hosts):,} unique hosts")
            
            # Generate comprehensive outputs
            results = self._generate_comprehensive_results(hosts)
            
            # Save all outputs
            self._save_all_outputs(hosts, results)
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Host discovery failed: {e}")
            
            # Check if it's an authentication issue
            if "403" in str(e) or "permission" in str(e).lower():
                self._handle_permission_error()
            
            raise
    
    def _create_empty_results(self) -> Dict[str, Any]:
        """Create empty results structure"""
        return {
            'discovery_metadata': {
                'timestamp': datetime.now().isoformat(),
                'projects': self.project_ids,
                'processing_time_seconds': (datetime.now() - self.start_time).total_seconds(),
                'total_hosts': 0,
                'status': 'No hosts found'
            },
            'summary': {
                'total_hosts': 0,
                'coverage': {},
                'distributions': {}
            }
        }
    
    def _generate_comprehensive_results(self, hosts: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive results from discovered hosts"""
        processing_time = (datetime.now() - self.start_time).total_seconds()
        
        # Get metrics from discovery engine
        if hasattr(self.discovery_engine, 'metrics'):
            metrics = self.discovery_engine.metrics
        else:
            self.discovery_engine._calculate_host_metrics()
            metrics = self.discovery_engine.metrics
        
        results = {
            'discovery_metadata': {
                'timestamp': datetime.now().isoformat(),
                'projects': self.project_ids,
                'processing_time_seconds': processing_time,
                'total_hosts': len(hosts),
                'tables_processed': len(self.discovery_engine.processed_tables),
                'status': 'Success'
            },
            'summary': {
                'total_hosts': metrics['total_hosts'],
                'average_completeness': metrics['average_completeness'],
                'high_completeness_hosts': metrics['high_completeness_hosts'],
                'low_completeness_hosts': metrics['low_completeness_hosts'],
                'coverage': metrics['coverage'],
                'distributions': metrics['distributions']
            },
            'detailed_metrics': metrics,
            'sample_hosts': self._get_sample_hosts(hosts, 10)
        }
        
        return results
    
    def _get_sample_hosts(self, hosts: Dict[str, Dict[str, Any]], sample_size: int = 10) -> List[Dict[str, Any]]:
        """Get sample hosts for the report"""
        sample_hosts = []
        
        # Sort by completeness and take top samples
        sorted_hosts = sorted(
            hosts.items(), 
            key=lambda x: x[1].get('data_completeness', 0), 
            reverse=True
        )
        
        for hostname, host_data in sorted_hosts[:sample_size]:
            sample_host = {
                'hostname': hostname,
                'completeness': host_data.get('data_completeness', 0),
                'source_tables': len(host_data.get('source_tables', set())),
            }
            
            # Add key fields
            for field in ['infrastructure_type', 'region', 'business_unit', 'edr_coverage', 'logging_in_splunk']:
                sample_host[field] = host_data.get(field, '')
            
            sample_hosts.append(sample_host)
        
        return sample_hosts
    
    def _save_all_outputs(self, hosts: Dict[str, Dict[str, Any]], results: Dict[str, Any]):
        """Save all output files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. Main results JSON
        results_file = self.output_dir / f"host_discovery_results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"📄 Results saved: {results_file}")
        
        # 2. Comprehensive hosts CSV
        csv_file = self.output_dir / f"all_hosts_{timestamp}.csv"
        self.discovery_engine.export_to_csv(str(csv_file))
        logger.info(f"📊 Hosts CSV saved: {csv_file}")
        
        # 3. Executive summary report
        self._generate_executive_report(results)
        
        # 4. Technical details report
        self._generate_technical_report(hosts, results)
        
        # 5. Coverage analysis spreadsheet
        self._generate_coverage_spreadsheet(results)
    
    def _generate_executive_report(self, results: Dict[str, Any]):
        """Generate executive summary report"""
        report_file = self.output_dir / "EXECUTIVE_SUMMARY.md"
        
        with open(report_file, 'w') as f:
            f.write("# HOST DISCOVERY - EXECUTIVE SUMMARY\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## KEY FINDINGS\n\n")
            
            summary = results.get('summary', {})
            total_hosts = summary.get('total_hosts', 0)
            
            if total_hosts == 0:
                f.write("⚠️ **NO HOSTS DISCOVERED**\n\n")
                f.write("### Possible Issues:\n")
                f.write("- No tables contain columns with 'host' in the name\n")
                f.write("- Insufficient permissions to access data\n")
                f.write("- All relevant tables are empty\n\n")
                return
            
            f.write(f"✅ **{total_hosts:,} UNIQUE HOSTS** discovered across all projects\n\n")
            f.write(f"- **Processing Time:** {results['discovery_metadata']['processing_time_seconds']:.1f} seconds\n")
            f.write(f"- **Projects Scanned:** {len(results['discovery_metadata']['projects'])}\n")
            f.write(f"- **Tables Processed:** {results['discovery_metadata']['tables_processed']:,}\n")
            f.write(f"- **Average Data Completeness:** {summary.get('average_completeness', 0):.1%}\n\n")
            
            f.write("## COVERAGE ANALYSIS\n\n")
            coverage = summary.get('coverage', {})
            
            f.write("| Security Control | Coverage | Hosts | Gap |\n")
            f.write("|------------------|----------|-------|-----|\n")
            
            coverage_order = ['edr_coverage', 'tanium_coverage', 'dlp_agent_coverage', 'logging_in_splunk', 'logging_in_gso']
            coverage_names = {
                'edr_coverage': 'EDR Protection',
                'tanium_coverage': 'Tanium Management',
                'dlp_agent_coverage': 'DLP Protection',
                'logging_in_splunk': 'Splunk Logging',
                'logging_in_gso': 'GSO Logging'
            }
            
            for cov_type in coverage_order:
                if cov_type in coverage:
                    stats = coverage[cov_type]
                    name = coverage_names.get(cov_type, cov_type)
                    f.write(f"| {name} | {stats['percentage']:.1f}% | {stats['count']:,} | {stats['gap_count']:,} |\n")
            
            f.write("\n## INFRASTRUCTURE BREAKDOWN\n\n")
            infra_dist = summary.get('distributions', {}).get('infrastructure_type', {})
            if infra_dist:
                for infra_type, count in sorted(infra_dist.items(), key=lambda x: x[1], reverse=True):
                    percentage = (count / total_hosts) * 100
                    f.write(f"- **{infra_type.title()}**: {count:,} hosts ({percentage:.1f}%)\n")
            else:
                f.write("*Infrastructure type data not available*\n")
            
            f.write("\n## REGIONAL DISTRIBUTION\n\n")
            region_dist = summary.get('distributions', {}).get('region', {})
            if region_dist:
                for region, count in sorted(region_dist.items(), key=lambda x: x[1], reverse=True):
                    percentage = (count / total_hosts) * 100
                    f.write(f"- **{region.upper()}**: {count:,} hosts ({percentage:.1f}%)\n")
            else:
                f.write("*Regional data not available*\n")
            
            f.write("\n## DATA QUALITY\n\n")
            f.write(f"- **High Completeness (≥80%)**: {summary.get('high_completeness_hosts', 0):,} hosts\n")
            f.write(f"- **Low Completeness (<50%)**: {summary.get('low_completeness_hosts', 0):,} hosts\n")
            f.write(f"- **Average Completeness**: {summary.get('average_completeness', 0):.1%}\n\n")
            
            f.write("## IMMEDIATE ACTIONS REQUIRED\n\n")
            
            # Identify critical gaps
            critical_gaps = []
            for cov_type, stats in coverage.items():
                if stats['percentage'] < 80:  # Less than 80% coverage
                    gap_count = stats['gap_count']
                    coverage_name = coverage_names.get(cov_type, cov_type)
                    critical_gaps.append(f"**{coverage_name}**: {gap_count:,} hosts without coverage ({100-stats['percentage']:.1f}% gap)")
            
            if critical_gaps:
                f.write("### Security Coverage Gaps:\n")
                for gap in critical_gaps:
                    f.write(f"- {gap}\n")
            else:
                f.write("✅ All security controls have >80% coverage\n")
            
            f.write("\n### Recommendations:\n")
            f.write("1. **Immediate**: Deploy missing security agents to uncovered hosts\n")
            f.write("2. **Week 1**: Enable logging for all production systems\n")
            f.write("3. **Week 2**: Validate and update CMDB with discovered hosts\n")
            f.write("4. **Month 1**: Achieve 95% coverage across all security controls\n\n")
            
            f.write("---\n")
            f.write("*Report generated by Enhanced Host Discovery System*\n")
        
        logger.info(f"📋 Executive report saved: {report_file}")
    
    def _generate_technical_report(self, hosts: Dict[str, Dict[str, Any]], results: Dict[str, Any]):
        """Generate detailed technical report"""
        report_file = self.output_dir / "TECHNICAL_DETAILS.md"
        
        with open(report_file, 'w') as f:
            f.write("# HOST DISCOVERY - TECHNICAL REPORT\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## DISCOVERY PROCESS\n\n")
            f.write("### Projects Scanned:\n")
            for project in results['discovery_metadata']['projects']:
                f.write(f"- `{project}`\n")
            
            f.write(f"\n### Processing Statistics:\n")
            f.write(f"- **Tables Processed:** {results['discovery_metadata']['tables_processed']:,}\n")
            f.write(f"- **Processing Time:** {results['discovery_metadata']['processing_time_seconds']:.1f} seconds\n")
            f.write(f"- **Hosts Discovered:** {results['discovery_metadata']['total_hosts']:,}\n")
            
            f.write("\n## SAMPLE HOST DATA\n\n")
            sample_hosts = results.get('sample_hosts', [])
            if sample_hosts:
                f.write("| Hostname | Completeness | Tables | Infrastructure | Region | EDR |\n")
                f.write("|----------|--------------|--------|----------------|--------|-----|\n")
                for host in sample_hosts[:5]:
                    f.write(f"| {host['hostname'][:30]} | {host['completeness']:.1%} | {host['source_tables']} | ")
                    f.write(f"{host.get('infrastructure_type', 'N/A')} | {host.get('region', 'N/A')} | ")
                    f.write(f"{host.get('edr_coverage', 'N/A')} |\n")
            
            f.write("\n## DATA QUALITY ANALYSIS\n\n")
            
            # Field completeness analysis
            field_completeness = {}
            total_hosts = len(hosts)
            
            target_fields = ['infrastructure_type', 'region', 'country', 'business_unit', 'edr_coverage', 'logging_in_splunk']
            
            for field in target_fields:
                populated = sum(1 for h in hosts.values() if h.get(field) not in [None, '', 'null', 'unknown'])
                field_completeness[field] = (populated / total_hosts) * 100 if total_hosts > 0 else 0
            
            f.write("### Field Completeness:\n")
            for field, completeness in sorted(field_completeness.items(), key=lambda x: x[1], reverse=True):
                f.write(f"- **{field}**: {completeness:.1f}% complete\n")
            
            f.write("\n## MERGE ANALYSIS\n\n")
            
            # Analyze hosts that were merged from multiple tables
            multi_table_hosts = [h for h in hosts.values() if len(h.get('source_tables', set())) > 1]
            
            f.write(f"- **Hosts found in multiple tables:** {len(multi_table_hosts):,}\n")
            f.write(f"- **Single-table hosts:** {len(hosts) - len(multi_table_hosts):,}\n")
            
            if multi_table_hosts:
                avg_tables = sum(len(h.get('source_tables', set())) for h in multi_table_hosts) / len(multi_table_hosts)
                f.write(f"- **Average tables per multi-table host:** {avg_tables:.1f}\n")
            
            f.write("\n## NEXT STEPS\n\n")
            f.write("1. Review executive summary for business impact\n")
            f.write("2. Analyze CSV export for detailed host inventory\n")
            f.write("3. Cross-reference with existing CMDB\n")
            f.write("4. Plan security agent deployment for uncovered hosts\n")
            f.write("5. Implement automated discovery to keep data current\n")
        
        logger.info(f"📋 Technical report saved: {report_file}")
    
    def _generate_coverage_spreadsheet(self, results: Dict[str, Any]):
        """Generate coverage analysis spreadsheet"""
        try:
            coverage_file = self.output_dir / "coverage_analysis.xlsx"
            
            # Create summary sheet
            summary_data = []
            coverage = results.get('summary', {}).get('coverage', {})
            
            for coverage_type, stats in coverage.items():
                summary_data.append({
                    'Security Control': coverage_type.replace('_', ' ').title(),
                    'Covered Hosts': stats['count'],
                    'Total Hosts': stats['count'] + stats['gap_count'],
                    'Coverage %': stats['percentage'],
                    'Gap Count': stats['gap_count']
                })
            
            summary_df = pd.DataFrame(summary_data)
            
            # Create distribution sheets
            distributions = results.get('summary', {}).get('distributions', {})
            
            with pd.ExcelWriter(coverage_file, engine='openpyxl') as writer:
                summary_df.to_excel(writer, sheet_name='Coverage Summary', index=False)
                
                for dist_type, dist_data in distributions.items():
                    if dist_data:
                        dist_df = pd.DataFrame([
                            {'Type': k, 'Count': v} 
                            for k, v in dist_data.items()
                        ])
                        sheet_name = dist_type.replace('_', ' ').title()[:31]  # Excel sheet name limit
                        dist_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            logger.info(f"📊 Coverage spreadsheet saved: {coverage_file}")
            
        except ImportError:
            logger.warning("⚠️  openpyxl not available, skipping Excel export")
        except Exception as e:
            logger.error(f"❌ Failed to create coverage spreadsheet: {e}")
    
    def _handle_permission_error(self):
        """Handle permission errors with helpful guidance"""
        logger.error("\n❌ PERMISSION ERROR")
        logger.error("The service account doesn't have sufficient permissions.")
        logger.error("\nRequired BigQuery permissions:")
        logger.error("- bigquery.datasets.get")
        logger.error("- bigquery.datasets.list") 
        logger.error("- bigquery.tables.list")
        logger.error("- bigquery.tables.get")
        logger.error("- bigquery.jobs.create")
        logger.error("- bigquery.data.get")
        logger.error("\nRecommended roles:")
        logger.error("- BigQuery Data Viewer")
        logger.error("- BigQuery Job User")
        logger.error("\nGrant these permissions or contact your GCP administrator")

def load_config(config_path: str) -> dict:
    """Load configuration from YAML file"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Enhanced Host Discovery System - Comprehensive BigQuery Scanner'
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
        '--sample-size',
        type=int,
        help='Override max sample size per table'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    return parser.parse_args()

async def main():
    """Main entry point"""
    import os
    
    args = parse_arguments()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load configuration
    try:
        config = load_config(args.config)
    except FileNotFoundError:
        logger.error(f"❌ Configuration file not found: {args.config}")
        sys.exit(1)
    
    # Apply command line overrides
    if args.projects:
        config['project_ids'] = args.projects
    
    if args.output:
        config['output_dir'] = args.output
    
    if args.sample_size:
        config.setdefault('discovery_settings', {})['max_sample_size'] = args.sample_size
    
    # Validate configuration
    if not config.get('project_ids'):
        logger.error("❌ No project IDs configured. Please update config.yaml or use --projects")
        sys.exit(1)
    
    # Display startup information
    print("\n" + "=" * 80)
    print("ENHANCED HOST DISCOVERY SYSTEM")
    print("Comprehensive BigQuery Scanner v3.0")
    print("=" * 80)
    print(f"\n🎯 Mission: Find ALL hosts in ALL tables across ALL projects")
    print(f"📋 Projects: {', '.join(config['project_ids'])}")
    print(f"📁 Output: {config.get('output_dir', 'host_discovery_output')}")
    print(f"📊 Max samples per table: {config.get('discovery_settings', {}).get('max_sample_size', 50000):,}")
    print("=" * 80 + "\n")
    
    # Execute discovery
    orchestrator = HostDiscoveryOrchestrator(config)
    
    try:
        results = await orchestrator.execute_host_discovery()
        
        # Display final results
        print("\n" + "=" * 80)
        print("🎉 HOST DISCOVERY COMPLETE!")
        print("=" * 80)
        
        summary = results.get('summary', {})
        total_hosts = summary.get('total_hosts', 0)
        
        if total_hosts > 0:
            print(f"\n✅ Successfully discovered {total_hosts:,} unique hosts")
            print(f"⏱️  Processing time: {results['discovery_metadata']['processing_time_seconds']:.1f} seconds")
            print(f"📊 Average data completeness: {summary.get('average_completeness', 0):.1%}")
            
            # Show top coverage gaps
            coverage = summary.get('coverage', {})
            print(f"\n📈 Coverage highlights:")
            for cov_type, stats in list(coverage.items())[:3]:
                print(f"   {cov_type}: {stats['percentage']:.1f}% ({stats['count']:,} hosts)")
            
            print(f"\n📁 Output files generated:")
            output_dir = Path(config.get('output_dir', 'host_discovery_output'))
            print(f"   📋 Executive Summary: {output_dir}/EXECUTIVE_SUMMARY.md")
            print(f"   📊 Host Data CSV: {output_dir}/all_hosts_*.csv")
            print(f"   📄 Technical Report: {output_dir}/TECHNICAL_DETAILS.md")
            print(f"   📈 Coverage Analysis: {output_dir}/coverage_analysis.xlsx")
        else:
            print(f"\n⚠️  No hosts discovered")
            print(f"   Check if your tables contain columns with 'host' in the name")
            print(f"   Verify authentication and permissions")
        
        print("\n" + "=" * 80)
        print("🎯 MISSION ACCOMPLISHED!")
        print("=" * 80 + "\n")
        
    except KeyboardInterrupt:
        logger.warning("⚠️  Discovery interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ Discovery failed: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())