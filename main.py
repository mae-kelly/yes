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
import signal

from discovery_engine import DiscoveryEngine
from config_loader import ConfigLoader

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CMDBDiscoveryRunner:
    def __init__(self, project_id: str, config_file: str = None):
        self.project_id = project_id
        self.config = ConfigLoader.load_config(config_file)
        self.engine = DiscoveryEngine(project_id, self.config)
        self.shutdown_requested = False
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_requested = True
        if hasattr(self.engine, 'signal_handler'):
            self.engine.signal_handler.shutdown_requested = True
    
    async def run_discovery(self) -> tuple[Dict[str, Any], Dict[str, str]]:
        start_time = time.time()
        
        logger.info("Starting CMDB Discovery System")
        logger.info(f"Project: {self.project_id}")
        logger.info(f"Configuration: {json.dumps(self.config, indent=2)}")
        
        try:
            stats, queries = await self.engine.discover_all_endpoints()
            processing_time = time.time() - start_time
            stats['total_processing_time'] = processing_time
            return stats, queries
        except Exception as e:
            logger.error(f"Discovery failed: {e}")
            return {'error': str(e)}, {}
        finally:
            self.engine.close()

def setup_logging(log_level: str = "INFO", log_file: str = None):
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_format = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    
    handlers = []
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(logging.Formatter(log_format))
    handlers.append(console_handler)
    
    if log_file:
        file_path = log_dir / log_file
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = log_dir / f"discovery_{timestamp}.log"
    
    file_handler = logging.FileHandler(file_path)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format))
    handlers.append(file_handler)
    
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=handlers,
        format=log_format
    )
    
    logging.getLogger('google.auth').setLevel(logging.WARNING)
    logging.getLogger('google.cloud').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    logger.info(f"Logging configured - File: {file_path}")

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="CMDB Discovery System",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--project', '-p', required=True, help='GCP Project ID')
    parser.add_argument('--config', '-c', help='Configuration file (JSON or YAML)')
    parser.add_argument('--workers', '-w', type=int, help='Maximum number of parallel workers')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO', help='Logging level')
    parser.add_argument('--log-file', help='Log file name')
    parser.add_argument('--resume', action='store_true', help='Resume from previous checkpoint')
    parser.add_argument('--dry-run', action='store_true', help='Estimate scope without processing')
    parser.add_argument('--output-dir', default='output', help='Output directory for results')
    parser.add_argument('--cache-dir', default='.cache', help='Cache directory')
    parser.add_argument('--database', default='universal_cmdb.db', help='Database file path')
    
    return parser.parse_args()

async def estimate_discovery_scope(project_id: str, config: Dict[str, Any]):
    logger.info("Estimating discovery scope...")
    
    try:
        from gcp_client import BigQueryClientManager
        
        client_manager = BigQueryClientManager(project_id)
        
        with client_manager.get_client() as client:
            datasets = list(client.list_datasets(project=project_id))
            
            total_datasets = len(datasets)
            total_tables = 0
            total_size_gb = 0
            
            sample_datasets = datasets[:10]
            
            for i, dataset in enumerate(sample_datasets):
                logger.info(f"Sampling dataset {i+1}/10: {dataset.dataset_id}")
                
                try:
                    tables = list(client.list_tables(dataset.reference))
                    total_tables += len(tables)
                    
                    for table_ref in tables[:20]:
                        try:
                            table = client.get_table(table_ref)
                            if table.num_bytes:
                                size_gb = table.num_bytes / (1024**3)
                                total_size_gb += size_gb
                        except Exception:
                            continue
                except Exception:
                    continue
            
            if sample_datasets:
                scale_factor = total_datasets / len(sample_datasets)
                estimated_total_tables = int(total_tables * scale_factor)
                estimated_total_size_gb = total_size_gb * scale_factor
            else:
                estimated_total_tables = 0
                estimated_total_size_gb = 0
            
            estimate = {
                'total_datasets': total_datasets,
                'estimated_tables': estimated_total_tables,
                'estimated_size_gb': round(estimated_total_size_gb, 2),
                'sampling_coverage': f"{len(sample_datasets)}/{total_datasets} datasets",
                'recommendation': 'PROCEED'
            }
            
            logger.info("Discovery Scope Estimate:")
            logger.info(f"  Total datasets: {estimate['total_datasets']:,}")
            logger.info(f"  Estimated tables: {estimate['estimated_tables']:,}")
            logger.info(f"  Estimated data size: {estimate['estimated_size_gb']:,.1f} GB")
            logger.info(f"  Recommendation: {estimate['recommendation']}")
            
            return estimate
            
    except Exception as e:
        logger.error(f"Failed to estimate scope: {e}")
        return {'error': str(e)}

async def main():
    args = parse_arguments()
    
    setup_logging(args.log_level, args.log_file)
    
    if not args.project:
        logger.error("GCP Project ID is required")
        sys.exit(1)
    
    config = {}
    if args.config and Path(args.config).exists():
        try:
            with open(args.config, 'r') as f:
                if args.config.endswith(('.yaml', '.yml')):
                    import yaml
                    config = yaml.safe_load(f)
                else:
                    config = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            sys.exit(1)
    
    if args.workers:
        config['max_workers'] = args.workers
    if args.cache_dir:
        config['cache_dir'] = args.cache_dir
    if args.database:
        config['database_path'] = args.database
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    logger.info("CMDB Discovery System")
    logger.info(f"Project: {args.project}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Database: {config.get('database_path', 'universal_cmdb.db')}")
    logger.info(f"Max workers: {config.get('max_workers', 32)}")
    
    try:
        if args.dry_run:
            estimate = await estimate_discovery_scope(args.project, config)
            
            if 'error' in estimate:
                logger.error(f"Estimation failed: {estimate['error']}")
                sys.exit(1)
            
            estimate_file = output_dir / "scope_estimate.json"
            with open(estimate_file, 'w') as f:
                json.dump(estimate, f, indent=2)
            
            logger.info(f"Scope estimate saved: {estimate_file}")
            logger.info("Scope estimation complete. Run without --dry-run to proceed.")
            return
        
        runner = CMDBDiscoveryRunner(args.project, args.config)
        
        if not args.resume:
            logger.info("Starting fresh discovery")
        else:
            logger.info("Attempting to resume from checkpoint")
        
        stats, queries = await runner.run_discovery()
        
        if 'error' in stats:
            logger.error(f"Discovery failed: {stats['error']}")
            sys.exit(1)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        stats_file = output_dir / f"discovery_stats_{timestamp}.json"
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2, default=str)
        
        queries_dir = output_dir / f"queries_{timestamp}"
        queries_dir.mkdir(exist_ok=True)
        
        for query_name, query_sql in queries.items():
            query_file = queries_dir / f"{query_name}.sql"
            with open(query_file, 'w') as f:
                f.write(f"-- {query_name.replace('_', ' ').title()}\n")
                f.write(f"-- CMDB Discovery\n")
                f.write(f"-- Project: {args.project}\n")
                f.write(f"-- Generated: {datetime.now().isoformat()}\n")
                f.write(f"-- Database: {config.get('database_path', 'universal_cmdb.db')}\n\n")
                f.write(query_sql)
        
        latest_stats = output_dir / "latest_stats.json"
        latest_queries = output_dir / "latest_queries"
        
        if latest_stats.exists() or latest_stats.is_symlink():
            latest_stats.unlink()
        if latest_queries.exists() or latest_queries.is_symlink():
            latest_queries.unlink()
        
        latest_stats.symlink_to(stats_file.name)
        latest_queries.symlink_to(queries_dir.name)
        
        logger.info("Discovery Complete!")
        
        performance_stats = stats.get('performance_stats', {})
        processing_analysis = stats.get('processing_analysis', {})
        
        logger.info(f"Total processing time: {stats.get('total_processing_time', 0):.2f} seconds")
        logger.info(f"Unique endpoints discovered: {stats.get('total_endpoints', 0):,}")
        logger.info(f"Datasets processed: {performance_stats.get('datasets_processed', 0)}")
        logger.info(f"Tables processed: {performance_stats.get('tables_processed', 0)}")
        logger.info(f"Cache hit ratio: {processing_analysis.get('cache_hit_ratio', 0):.2%}")
        
        core_coverage = stats.get('core_coverage', {})
        if core_coverage:
            logger.info("Core System Coverage:")
            logger.info(f"  CMDB endpoints: {core_coverage.get('cmdb', 0):,}")
            logger.info(f"  Splunk endpoints: {core_coverage.get('splunk', 0):,}")
            logger.info(f"  CrowdStrike endpoints: {core_coverage.get('crowdstrike', 0):,}")
            logger.info(f"  Other tables: {core_coverage.get('other_tables', 0):,}")
        
        logger.info("Output Files:")
        logger.info(f"  Statistics: {stats_file}")
        logger.info(f"  Latest stats: {latest_stats}")
        logger.info(f"  SQL queries: {queries_dir}")
        logger.info(f"  Latest queries: {latest_queries}")
        logger.info(f"  Database: {config.get('database_path', 'universal_cmdb.db')}")
        
        discovery_summary = stats.get('discovery_summary', {})
        if discovery_summary:
            total_endpoints = discovery_summary.get('total_endpoints', 0)
            coverage_pct = discovery_summary.get('coverage_percentage', 0)
            
            if total_endpoints > 0:
                logger.info(f"Success! Discovered {total_endpoints:,} endpoints across your infrastructure")
                logger.info(f"Core system coverage: {coverage_pct}%")
                
                if coverage_pct >= 80:
                    logger.info("Excellent coverage - your CMDB is well-maintained")
                elif coverage_pct >= 60:
                    logger.info("Good coverage - some gaps to address")
                else:
                    logger.info("Significant gaps detected - review missing endpoints")
            else:
                logger.warning("No endpoints discovered - check permissions and data sources")
        
    except KeyboardInterrupt:
        logger.info("Discovery interrupted by user (Ctrl+C)")
        logger.info("Check for checkpoint files to resume later")
        sys.exit(130)
        
    except Exception as e:
        logger.error(f"Discovery failed: {e}")
        logger.error("Check logs for detailed error information")
        
        error_file = output_dir / f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(error_file, 'w') as f:
            json.dump({
                'error': str(e),
                'type': type(e).__name__,
                'timestamp': datetime.now().isoformat(),
                'project': args.project,
                'config': config
            }, f, indent=2)
        
        logger.error(f"Error details saved: {error_file}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Interrupted by user")
        sys.exit(130)