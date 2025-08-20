import asyncio
import logging
import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add gcp module to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from discovery.quantum_discovery import QuantumDiscoveryEngine
from storage.quantum_database import QuantumDatabase
from core.quantum_types import DiscoveryMetrics
from gcp.client import BigQueryClientManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AO1VisibilityOrchestrator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.project_ids = config['project_ids']
        self.output_dir = Path(config.get('output_dir', 'visibility_output'))
        self.output_dir.mkdir(exist_ok=True)
        
        # Test authentication before proceeding
        self._test_authentication()
        
        self.discovery_engine = QuantumDiscoveryEngine(self.project_ids, config)
        self.database = QuantumDatabase(str(self.output_dir / "ao1_visibility.duckdb"))
        
        self.start_time = datetime.now()
        self.metrics = {}
    
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
    
    async def execute_discovery(self) -> Dict[str, Any]:
        logger.info("=" * 80)
        logger.info("AO1 LOG VISIBILITY MEASUREMENT SYSTEM")
        logger.info("Quantum Discovery Engine v2.0")
        logger.info("=" * 80)
        
        logger.info(f"Discovering assets across {len(self.project_ids)} projects")
        logger.info(f"Projects: {', '.join(self.project_ids)}")
        
        try:
            assets = await self.discovery_engine.discover_all_assets()
            
            if not assets:
                logger.warning("No assets discovered. Check if tables contain hostname data.")
                return {
                    'discovery_metadata': {
                        'timestamp': datetime.now().isoformat(),
                        'projects': self.project_ids,
                        'processing_time_seconds': (datetime.now() - self.start_time).total_seconds(),
                        'total_assets': 0,
                        'stored_assets': 0,
                        'status': 'No assets found'
                    }
                }
            
            logger.info(f"Storing {len(assets)} assets in database")
            stored_count = self.database.store_assets(assets)
            
            logger.info("Analyzing coverage and gaps")
            coverage_analysis = self.database.analyze_coverage()
            
            logger.info("Generating visibility report")
            visibility_report = self.database.get_visibility_report()
            
            metrics_summary = self.discovery_engine.get_metrics_summary()
            
            self.database.store_metrics(self.discovery_engine.metrics)
            
            processing_time = (datetime.now() - self.start_time).total_seconds()
            
            results = {
                'discovery_metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'projects': self.project_ids,
                    'processing_time_seconds': processing_time,
                    'total_assets': len(assets),
                    'stored_assets': stored_count,
                    'status': 'Success'
                },
                'metrics_summary': metrics_summary,
                'coverage_analysis': coverage_analysis,
                'visibility_report': visibility_report
            }
            
            self._save_results(results)
            self._generate_executive_report(results)
            
            return results
            
        except Exception as e:
            logger.error(f"Discovery failed: {e}")
            
            # Check if it's an authentication issue
            if "403" in str(e) or "permission" in str(e).lower():
                logger.error("\n❌ PERMISSION ERROR")
                logger.error("The service account doesn't have sufficient permissions.")
                logger.error("Required permissions:")
                logger.error("- bigquery.datasets.get")
                logger.error("- bigquery.tables.list")
                logger.error("- bigquery.tables.get")
                logger.error("- bigquery.jobs.create")
                logger.error("\nGrant these permissions or use 'BigQuery Data Viewer' role")
            
            raise
    
    def _save_results(self, results: Dict[str, Any]):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        results_file = self.output_dir / f"discovery_results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        csv_file = self.output_dir / f"assets_{timestamp}.csv"
        self.database.export_to_csv(str(csv_file))
        
        logger.info(f"Results saved to {results_file}")
        logger.info(f"Assets exported to {csv_file}")
    
    def _generate_executive_report(self, results: Dict[str, Any]):
        report_file = self.output_dir / "executive_report.md"
        
        with open(report_file, 'w') as f:
            f.write("# AO1 LOG VISIBILITY MEASUREMENT - EXECUTIVE REPORT\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## EXECUTIVE SUMMARY\n\n")
            
            metrics = results.get('metrics_summary', {})
            
            if metrics.get('total_assets', 0) == 0:
                f.write("⚠️ **No assets discovered**\n\n")
                f.write("Possible reasons:\n")
                f.write("- No tables contain hostname data\n")
                f.write("- Insufficient permissions\n")
                f.write("- Tables are empty\n\n")
                return
            
            f.write(f"- **Total Assets Discovered**: {metrics['total_assets']:,}\n")
            f.write(f"- **Projects Scanned**: {len(results['discovery_metadata']['projects'])}\n")
            f.write(f"- **Processing Time**: {results['discovery_metadata']['processing_time_seconds']:.1f} seconds\n\n")
            
            f.write("### Coverage Metrics\n\n")
            for coverage_type, value in metrics.get('coverage', {}).items():
                f.write(f"- **{coverage_type.replace('_', ' ').title()}**: {value}\n")
            f.write("\n")
            
            f.write("## INFRASTRUCTURE DISTRIBUTION\n\n")
            infra_dist = metrics.get('distributions', {}).get('infrastructure', {})
            if infra_dist:
                for infra_type, count in infra_dist.items():
                    percentage = (count / metrics['total_assets']) * 100
                    f.write(f"- **{infra_type}**: {count:,} ({percentage:.1f}%)\n")
            else:
                f.write("No infrastructure type data available\n")
            f.write("\n")
            
            f.write("## REGIONAL DISTRIBUTION\n\n")
            regional_dist = metrics.get('distributions', {}).get('region', {})
            if regional_dist:
                for region, count in regional_dist.items():
                    percentage = (count / metrics['total_assets']) * 100
                    f.write(f"- **{region.upper()}**: {count:,} ({percentage:.1f}%)\n")
            else:
                f.write("No regional data available\n")
            f.write("\n")
            
            f.write("## SYSTEM CLASSIFICATION\n\n")
            sys_dist = metrics.get('distributions', {}).get('system_class', {})
            if sys_dist:
                for sys_class, count in sys_dist.items():
                    percentage = (count / metrics['total_assets']) * 100
                    f.write(f"- **{sys_class.replace('_', ' ').title()}**: {count:,} ({percentage:.1f}%)\n")
            else:
                f.write("No system classification data available\n")
            f.write("\n")
            
            f.write("## SECURITY COVERAGE GAPS\n\n")
            gaps = metrics.get('gaps', {})
            f.write(f"- **Assets without EDR/Tanium**: {gaps.get('security', 0):,}\n")
            f.write(f"- **Assets without Splunk/GSO Logging**: {gaps.get('logging', 0):,}\n")
            f.write(f"- **Assets with Low Visibility (<50%)**: {gaps.get('compliance', 0):,}\n\n")
            
            coverage = results.get('coverage_analysis', {}).get('coverage', {})
            if coverage:
                f.write("## DETAILED COVERAGE METRICS\n\n")
                f.write("| Coverage Type | Count | Percentage | Gap |\n")
                f.write("|--------------|-------|------------|-----|\n")
                for coverage_type, stats in coverage.items():
                    f.write(f"| {coverage_type.replace('_', ' ').title()} | ")
                    f.write(f"{stats['count']:,} | ")
                    f.write(f"{stats['percentage']:.1f}% | ")
                    f.write(f"{stats['gap_count']:,} |\n")
                f.write("\n")
            
            f.write("## RECOMMENDATIONS\n\n")
            f.write("1. **Immediate Actions**:\n")
            f.write("   - Deploy EDR agents to uncovered critical assets\n")
            f.write("   - Enable Splunk/GSO logging for all production systems\n")
            f.write("   - Update CMDB with missing assets\n\n")
            f.write("2. **Short-term (30 days)**:\n")
            f.write("   - Achieve 95% EDR coverage across all infrastructure\n")
            f.write("   - Implement DLP agents on sensitive data systems\n")
            f.write("   - Complete Tanium deployment for endpoint management\n\n")
            f.write("3. **Long-term (90 days)**:\n")
            f.write("   - Achieve 100% logging compliance in GSO and Splunk\n")
            f.write("   - Full CMDB synchronization with discovered assets\n")
            f.write("   - Implement continuous visibility monitoring\n\n")
            
            f.write("## AUTHENTICATION USED\n\n")
            if os.path.exists("gcp_prod_key.json"):
                f.write("- **Method**: Service Account Key (gcp_prod_key.json)\n")
            elif os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
                f.write(f"- **Method**: Service Account Key (Environment Variable)\n")
                f.write(f"- **Path**: {os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')}\n")
            else:
                f.write("- **Method**: Default Application Credentials (gcloud)\n")
            
            f.write(f"\n## PROJECTS ANALYZED\n\n")
            for project in results['discovery_metadata']['projects']:
                f.write(f"- {project}\n")
        
        logger.info(f"Executive report generated: {report_file}")

def verify_prerequisites():
    """Verify all prerequisites are met"""
    logger.info("Verifying prerequisites...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        logger.error(f"Python 3.8+ required. Current version: {sys.version}")
        return False
    
    # Check required packages
    required_packages = {
        'google.cloud.bigquery': 'google-cloud-bigquery',
        'duckdb': 'duckdb',
        'numpy': 'numpy',
        'yaml': 'pyyaml'
    }
    
    missing_packages = []
    for module, package in required_packages.items():
        try:
            __import__(module)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Missing required packages: {', '.join(missing_packages)}")
        logger.error(f"Install with: pip install {' '.join(missing_packages)}")
        return False
    
    logger.info("✅ All prerequisites met")
    return True