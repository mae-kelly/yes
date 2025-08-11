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

logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AO1DiscoveryRunner:
    def __init__(self, project_id: str, config_file: str = None):
        self.project_id = project_id
        self.config = ConfigLoader.load_config(config_file)
        self.engine = DiscoveryEngine(project_id, self.config)
        self.shutdown_requested = False
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        print(f"\n   ⚠°｡⋆⸜ ♡   Received signal {signum}, graceful shutdown...")
        self.shutdown_requested = True
        if hasattr(self.engine, 'signal_handler'):
            self.engine.signal_handler.shutdown_requested = True
    
    async def run_discovery(self) -> tuple[Dict[str, Any], Dict[str, str]]:
        start_time = time.time()
        
        try:
            stats, queries = await self.engine.discover_all_endpoints()
            processing_time = time.time() - start_time
            stats['total_processing_time'] = processing_time
            return stats, queries
        except Exception as e:
            print(f"   ✗°｡⋆⸜ ♡   Discovery failed: {e}")
            return {'error': str(e)}, {}
        finally:
            self.engine.close()

def parse_arguments():
    parser = argparse.ArgumentParser(description="AO1 Log Visibility Discovery System")
    
    parser.add_argument('--project', '-p', required=True, help='GCP Project ID')
    parser.add_argument('--config', '-c', help='Configuration file')
    parser.add_argument('--workers', '-w', type=int, help='Maximum parallel workers')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    parser.add_argument('--dry-run', action='store_true', help='Estimate scope')
    parser.add_argument('--output-dir', default='output', help='Output directory')
    parser.add_argument('--cache-dir', default='.cache', help='Cache directory')
    parser.add_argument('--database', default='ao1_visibility_cmdb.db', help='Database file')
    
    return parser.parse_args()

async def estimate_discovery_scope(project_id: str, config: Dict[str, Any]):
    print("   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Estimating discovery scope...")
    
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
                print(f"   ｡･:*:･ﾟ★   Sampling dataset {i+1}/10: {dataset.dataset_id}")
                
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
            
            print("   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Discovery Scope Estimate:")
            print(f"   ✧･ﾟ: *✧･ﾟ:*   Total datasets: {estimate['total_datasets']:,}")
            print(f"   ✧･ﾟ: *✧･ﾟ:*   Estimated tables: {estimate['estimated_tables']:,}")
            print(f"   ✧･ﾟ: *✧･ﾟ:*   Estimated data size: {estimate['estimated_size_gb']:,.1f} GB")
            print(f"   ✧･ﾟ: *✧･ﾟ:*   Recommendation: {estimate['recommendation']}")
            
            return estimate
            
    except Exception as e:
        print(f"   ✗°｡⋆⸜ ♡   Failed to estimate scope: {e}")
        return {'error': str(e)}

async def main():
    args = parse_arguments()
    
    if not args.project:
        print("   ✗°｡⋆⸜ ♡   GCP Project ID is required")
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
            print(f"   ✗°｡⋆⸜ ♡   Failed to load config: {e}")
            sys.exit(1)
    
    if args.workers:
        config['max_workers'] = args.workers
    if args.cache_dir:
        config['cache_dir'] = args.cache_dir
    if args.database:
        config['database_path'] = args.database
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    print("   ♡₊˚ ✧ ‧₊˚ ⋅   AO1 Log Visibility Discovery   ⋅ ˚₊‧ ✧ ˚₊♡")
    print(f"   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Project: {args.project}")
    print(f"   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Output directory: {output_dir}")
    print(f"   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Database: {config.get('database_path', 'ao1_visibility_cmdb.db')}")
    print(f"   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Max workers: {config.get('max_workers', 12)}")
    
    try:
        if args.dry_run:
            estimate = await estimate_discovery_scope(args.project, config)
            
            if 'error' in estimate:
                print(f"   ✗°｡⋆⸜ ♡   Estimation failed: {estimate['error']}")
                sys.exit(1)
            
            estimate_file = output_dir / "scope_estimate.json"
            with open(estimate_file, 'w') as f:
                json.dump(estimate, f, indent=2)
            
            print(f"   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Scope estimate saved: {estimate_file}")
            print("   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Scope estimation complete. Run without --dry-run to proceed.")
            return
        
        runner = AO1DiscoveryRunner(args.project, args.config)
        
        if not args.resume:
            print("   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Starting fresh discovery")
        else:
            print("   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Attempting to resume from checkpoint")
        
        stats, queries = await runner.run_discovery()
        
        if 'error' in stats:
            print(f"   ✗°｡⋆⸜ ♡   Discovery failed: {stats['error']}")
            sys.exit(1)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        stats_file = output_dir / f"ao1_visibility_stats_{timestamp}.json"
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2, default=str)
        
        queries_dir = output_dir / f"ao1_queries_{timestamp}"
        queries_dir.mkdir(exist_ok=True)
        
        for query_name, query_sql in queries.items():
            query_file = queries_dir / f"{query_name}.sql"
            with open(query_file, 'w') as f:
                f.write(f"-- {query_name.replace('_', ' ').title()}\n")
                f.write(f"-- AO1 Log Visibility Discovery\n")
                f.write(f"-- Project: {args.project}\n")
                f.write(f"-- Generated: {datetime.now().isoformat()}\n")
                f.write(f"-- Database: {config.get('database_path', 'ao1_visibility_cmdb.db')}\n\n")
                f.write(query_sql)
        
        latest_stats = output_dir / "latest_ao1_stats.json"
        latest_queries = output_dir / "latest_ao1_queries"
        
        if latest_stats.exists() or latest_stats.is_symlink():
            latest_stats.unlink()
        if latest_queries.exists() or latest_queries.is_symlink():
            latest_queries.unlink()
        
        latest_stats.symlink_to(stats_file.name)
        latest_queries.symlink_to(queries_dir.name)
        
        print("\n" + "="*80)
        print("   ♡₊˚ ✧ ‧₊˚ ⋅   AO1 Discovery Complete   ⋅ ˚₊‧ ✧ ˚₊♡")
        print("="*80)
        
        performance_stats = stats.get('performance_stats', {})
        visibility_coverage = stats.get('visibility_coverage', {})
        
        print(f"   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Total processing time: {stats.get('total_processing_time', 0):.2f} seconds")
        print(f"   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Total assets discovered: {stats.get('total_endpoints', 0):,}")
        print(f"   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Datasets processed: {performance_stats.get('datasets_processed', 0)}")
        print(f"   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Tables processed: {performance_stats.get('tables_processed', 0)}")
        
        if visibility_coverage:
            print("\n   ♡˗ˏˋ ◞ ～   AO1 Visibility Coverage:")
            print(f"   ✧･ﾟ: *✧･ﾟ:*   CMDB Coverage: {visibility_coverage.get('cmdb_coverage_pct', 0):.1f}%")
            print(f"   ✧･ﾟ: *✧･ﾟ:*   Splunk Coverage: {visibility_coverage.get('splunk_coverage_pct', 0):.1f}%")
            print(f"   ✧･ﾟ: *✧･ﾟ:*   Chronicle Coverage: {visibility_coverage.get('chronicle_coverage_pct', 0):.1f}%")
            print(f"   ✧･ﾟ: *✧･ﾟ:*   CrowdStrike Coverage: {visibility_coverage.get('crowdstrike_coverage_pct', 0):.1f}%")
        
        print("\n   ｡･:*:･ﾟ★   Output Files:")
        print(f"   ◦ ❀ ◦   Statistics: {stats_file}")
        print(f"   ◦ ❀ ◦   Latest stats: {latest_stats}")
        print(f"   ◦ ❀ ◦   AO1 queries: {queries_dir}")
        print(f"   ◦ ❀ ◦   Latest queries: {latest_queries}")
        print(f"   ◦ ❀ ◦   Database: {config.get('database_path', 'ao1_visibility_cmdb.db')}")
        
        discovery_summary = stats.get('discovery_summary', {})
        if discovery_summary:
            total_endpoints = discovery_summary.get('total_endpoints', 0)
            
            if total_endpoints > 0:
                print(f"\n   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Success! Discovered {total_endpoints:,} assets for AO1 visibility measurement")
                print("   ❀°｡ ‧˚♡ ˚‧ ｡°❀   CSOC can now measure log visibility across critical domains")
            else:
                print("   ⚠°｡⋆⸜ ♡   No assets discovered - check permissions and data sources")
        
        print("\n   ♡₊˚ ✧ ‧₊˚ ⋅   Ready for AO1 Visibility Analysis   ⋅ ˚₊‧ ✧ ˚₊♡")
        
    except KeyboardInterrupt:
        print("\n\n   ⚠°｡⋆⸜ ♡   Discovery interrupted by user")
        print("   ･ﾟ✧ ◞ ♡   Check for checkpoint files to resume later")
        sys.exit(130)
        
    except Exception as e:
        print(f"\n   ✗°｡⋆⸜ ♡   Discovery failed: {e}")
        
        error_file = output_dir / f"ao1_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(error_file, 'w') as f:
            json.dump({
                'error': str(e),
                'type': type(e).__name__,
                'timestamp': datetime.now().isoformat(),
                'project': args.project,
                'config': config
            }, f, indent=2)
        
        print(f"   ･ﾟ✧ ◞ ♡   Error details saved: {error_file}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n   ⚠°｡⋆⸜ ♡   Interrupted by user")
        sys.exit(130)