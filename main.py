import asyncio
import logging
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

from discovery.quantum_discovery import QuantumDiscoveryEngine
from storage.quantum_database import QuantumDatabase
from core.quantum_types import DiscoveryMetrics

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
        
        self.discovery_engine = QuantumDiscoveryEngine(self.project_ids, config)
        self.database = QuantumDatabase(str(self.output_dir / "ao1_visibility.duckdb"))
        
        self.start_time = datetime.now()
        self.metrics = {}
    
    async def execute_discovery(self) -> Dict[str, Any]:
        logger.info("=" * 80)
        logger.info("AO1 LOG VISIBILITY MEASUREMENT SYSTEM")
        logger.info("Quantum Discovery Engine v2.0")
        logger.info("=" * 80)
        
        logger.info(f"Discovering assets across {len(self.project_ids)} projects")
        assets = await self.discovery_engine.discover_all_assets()
        
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
                'stored_assets': stored_count
            },
            'metrics_summary': metrics_summary,
            'coverage_analysis': coverage_analysis,
            'visibility_report': visibility_report
        }
        
        self._save_results(results)
        self._generate_executive_report(results)
        
        return results
    
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
            
            metrics = results['metrics_summary']
            f.write(f"- **Total Assets Discovered**: {metrics['total_assets']:,}\n")
            f.write(f"- **CMDB Coverage**: {metrics['coverage']['cmdb']}\n")
            f.write(f"- **URL/FQDN Coverage**: {metrics['coverage']['url_fqdn']}\n")
            f.write(f"- **Public IP Coverage**: {metrics['coverage']['public_ip']}\n")
            f.write(f"- **Endpoint Coverage**: {metrics['coverage']['endpoint']}\n")
            f.write(f"- **Cloud Coverage**: {metrics['coverage']['cloud']}\n\n")
            
            f.write("## INFRASTRUCTURE DISTRIBUTION\n\n")
            for infra_type, count in metrics['distributions']['infrastructure'].items():
                percentage = (count / metrics['total_assets']) * 100
                f.write(f"- **{infra_type}**: {count:,} ({percentage:.1f}%)\n")
            f.write("\n")
            
            f.write("## REGIONAL DISTRIBUTION\n\n")
            for region, count in metrics['distributions']['region'].items():
                percentage = (count / metrics['total_assets']) * 100
                f.write(f"- **{region}**: {count:,} ({percentage:.1f}%)\n")
            f.write("\n")
            
            f.write("## SYSTEM CLASSIFICATION\n\n")
            for sys_class, count in metrics['distributions']['system_class'].items():
                percentage = (count / metrics['total_assets']) * 100
                f.write(f"- **{sys_class}**: {count:,} ({percentage:.1f}%)\n")
            f.write("\n")
            
            f.write("## SECURITY COVERAGE GAPS\n\n")
            f.write(f"- **Assets without EDR/Tanium**: {metrics['gaps']['security']:,}\n")
            f.write(f"- **Assets without Splunk/GSO Logging**: {metrics['gaps']['logging']:,}\n")
            f.write(f"- **Assets with Low Visibility (<50%)**: {metrics['gaps']['compliance']:,}\n\n")
            
            coverage = results.get('coverage_analysis', {}).get('coverage', {})
            if coverage:
                f.write("## DETAILED COVERAGE METRICS\n\n")
                f.write("| Coverage Type | Count | Percentage | Gap |\n")
                f.write("|--------------|-------|------------|-----|\n")
                for coverage_type, stats in coverage.items():
                    f.write(f"| {coverage_type.replace('_', ' ').title()} | {stats['count']:,} | {stats['percentage']:.1f}% | {stats['gap_count']:,} |\n")
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
            
            f.write("## KEY PERFORMANCE INDICATORS\n\n")
            processing_time = results['discovery_metadata']['processing_time_seconds']
            f.write(f"- **Discovery Time**: {processing_time:.1f} seconds ({processing_time/60:.1f} minutes)\n")
            f.write(f"- **Assets Processed**: {results['discovery_metadata']['total_assets']:,}\n")
            f.write(f"- **Database Records**: {results['discovery_metadata']['stored_assets']:,}\n")
            f.write(f"- **Projects Scanned**: {len(results['discovery_metadata']['projects'])}\n")
        
        logger.info(f"Executive report generated: {report_file}")