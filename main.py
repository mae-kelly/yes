#!/usr/bin/env python3

import os
import sys
import time
import json
import logging
import asyncio
import argparse
from pathlib import Path
from datetime import datetime

from comprehensive_discovery_engine import UltimateCMDBBuilder
from cache_manager import IntelligentCacheManager
from content_matcher import IntelligentContentMatcher
from gcp_client import BigQueryClientManager
from config_loader import ConfigLoader

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UltimateAO1DiscoverySystem:
    def __init__(self, projects: List[str], config: dict, args=None):
        self.projects = projects
        self.config = config
        self.args = args
        
        self.cache_manager = IntelligentCacheManager(
            cache_dir=config.get('cache_dir', '.cache'),
            max_memory_mb=config.get('max_memory_mb', 2048),
            max_disk_gb=config.get('max_disk_gb', 50)
        )
        
        self.content_matcher = IntelligentContentMatcher()
        
        self.client_managers = {}
        for project_id in projects:
            try:
                self.client_managers[project_id] = BigQueryClientManager(project_id)
                logger.info(f"Connected to project {project_id}")
            except Exception as e:
                logger.error(f"Failed to connect to project {project_id}: {e}")
        
        self.ultimate_builder = UltimateCMDBBuilder(
            config=config,
            content_matcher=self.content_matcher,
            cache_manager=self.cache_manager
        )
    
    async def execute_ultimate_discovery(self):
        logger.info("Starting ultimate CMDB discovery across all projects and tables")
        
        start_time = time.time()
        
        results = await self.ultimate_builder.build_ultimate_cmdb(
            projects=self.projects,
            client_managers=self.client_managers
        )
        
        processing_time = time.time() - start_time
        results['total_processing_time'] = processing_time
        
        return results
    
    def generate_visibility_report(self) -> Dict[str, Any]:
        queries = self.ultimate_builder.get_visibility_queries()
        report = {}
        
        for query_name, query_sql in queries.items():
            try:
                result = self.ultimate_builder.conn.execute(query_sql).fetchall()
                if query_name == 'visibility_summary':
                    columns = ['total_assets', 'in_cmdb', 'in_splunk', 'in_chronicle', 'in_crowdstrike', 'multi_source']
                    report[query_name] = dict(zip(columns, result[0])) if result else {}
                elif query_name == 'coverage_percentages':
                    columns = ['cmdb_percentage', 'splunk_percentage', 'chronicle_percentage', 'crowdstrike_percentage']
                    report[query_name] = dict(zip(columns, result[0])) if result else {}
                elif query_name in ['missing_from_cmdb', 'visibility_gaps', 'best_visibility']:
                    report[query_name] = result
                else:
                    report[query_name] = result[0][0] if result and result[0] else 0
            except Exception as e:
                logger.error(f"Failed to execute query {query_name}: {e}")
                report[query_name] = f"Error: {e}"
        
        return report
    
    def close(self):
        if hasattr(self.ultimate_builder, 'close'):
            self.ultimate_builder.close()

def parse_arguments():
    parser = argparse.ArgumentParser(description="Ultimate AO1 CMDB Discovery System")
    
    parser.add_argument('--projects', '-p', nargs='+', required=True, 
                       help='List of GCP Project IDs (e.g., prj-fisv chronicle-fisv)')
    parser.add_argument('--max-memory', type=int, default=4096, 
                       help='Max memory cache (MB)')
    parser.add_argument('--max-disk', type=int, default=100, 
                       help='Max disk cache (GB)')
    parser.add_argument('--config', '-c', default='config.yaml', 
                       help='Configuration file path')
    parser.add_argument('--output-dir', default='ultimate_output', 
                       help='Output directory')
    parser.add_argument('--database', default='ultimate_cmdb.db', 
                       help='Ultimate CMDB database file')
    parser.add_argument('--debug', action='store_true', 
                       help='Enable debug mode')
    parser.add_argument('--report-only', action='store_true',
                       help='Generate report from existing database only')
    
    return parser.parse_args()

async def main():
    args = parse_arguments()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled for ultimate discovery")
    
    config = ConfigLoader.load_config(args.config) if Path(args.config).exists() else {}
    
    config.update({
        'max_memory_mb': args.max_memory,
        'max_disk_gb': args.max_disk,
        'database_path': args.database,
        'output_dir': args.output_dir
    })
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    logger.info("Ultimate AO1 CMDB Discovery System")
    logger.info(f"Projects: {', '.join(args.projects)}")
    logger.info(f"Memory: {args.max_memory:,}MB, Disk: {args.max_disk}GB")
    logger.info(f"Database: {args.database}")
    
    try:
        system = UltimateAO1DiscoverySystem(args.projects, config, args)
        
        if args.report_only:
            logger.info("Generating visibility report from existing database")
            if not Path(args.database).exists():
                logger.error(f"Database {args.database} does not exist")
                sys.exit(1)
            
            report = system.generate_visibility_report()
        else:
            logger.info("Starting full discovery process")
            results = await system.execute_ultimate_discovery()
            
            logger.info("Generating comprehensive visibility report")
            report = system.generate_visibility_report()
            results['visibility_report'] = report
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = output_dir / f"ultimate_discovery_{timestamp}.json"
            
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"Results saved: {results_file}")
        
        logger.info("Ultimate CMDB Discovery Complete!")
        
        if 'visibility_report' in locals() and 'visibility_summary' in report:
            summary = report['visibility_summary']
            logger.info(f"Total assets discovered: {summary.get('total_assets', 0):,}")
            logger.info(f"In original CMDB: {summary.get('in_cmdb', 0):,}")
            logger.info(f"In Splunk: {summary.get('in_splunk', 0):,}")
            logger.info(f"In Chronicle: {summary.get('in_chronicle', 0):,}")
            logger.info(f"In CrowdStrike: {summary.get('in_crowdstrike', 0):,}")
            logger.info(f"Multi-source assets: {summary.get('multi_source', 0):,}")
        
        if 'coverage_percentages' in report:
            percentages = report['coverage_percentages']
            logger.info("Coverage Percentages:")
            logger.info(f"  CMDB: {percentages.get('cmdb_percentage', 0):.1f}%")
            logger.info(f"  Splunk: {percentages.get('splunk_percentage', 0):.1f}%")
            logger.info(f"  Chronicle: {percentages.get('chronicle_percentage', 0):.1f}%")
            logger.info(f"  CrowdStrike: {percentages.get('crowdstrike_percentage', 0):.1f}%")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = output_dir / f"visibility_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Visibility report saved: {report_file}")
        logger.info(f"Ultimate CMDB database: {args.database}")
        
        system.close()
        
    except KeyboardInterrupt:
        logger.warning("Discovery interrupted by user")
        sys.exit(130)
        
    except Exception as e:
        logger.error(f"Ultimate discovery failed: {e}")
        
        if args.debug:
            import traceback
            traceback.print_exc()
        
        error_file = output_dir / f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(error_file, 'w') as f:
            json.dump({
                'error': str(e),
                'type': type(e).__name__,
                'timestamp': datetime.now().isoformat(),
                'projects': args.projects,
                'config': config
            }, f, indent=2)
        
        logger.error(f"Error details saved: {error_file}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        sys.exit(130)