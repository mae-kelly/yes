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

from discovery_engine import AO1IntelligentDiscovery
from config_loader import ConfigLoader

logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AO1VisibilityRunner:
    def __init__(self, project_id: str, config_file: str = None):
        self.project_id = project_id
        self.config = ConfigLoader.load_config(config_file)
        self.engine = AO1IntelligentDiscovery(project_id, self.config)
        self.shutdown_requested = False
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        print(f"\n   ⚠°｡⋆⸜ ♡   Received signal {signum}, graceful shutdown...")
        self.shutdown_requested = True
        if hasattr(self.engine, 'signal_handler'):
            self.engine.signal_handler.shutdown_requested = True
    
    async def execute_ao1_discovery(self) -> tuple[Dict[str, Any], Dict[str, str]]:
        start_time = time.time()
        
        try:
            stats, queries = await self.engine.execute_ao1_discovery()
            processing_time = time.time() - start_time
            stats['total_processing_time'] = processing_time
            return stats, queries
        except Exception as e:
            print(f"   ✗°｡⋆⸜ ♡   AO1 Discovery failed: {e}")
            return {'error': str(e)}, {}
        finally:
            self.engine.close()

def parse_arguments():
    parser = argparse.ArgumentParser(description="AO1 Log Visibility Measurement System")
    
    parser.add_argument('--project', '-p', required=True, help='GCP Project ID')
    parser.add_argument('--config', '-c', help='Configuration file')
    parser.add_argument('--workers', '-w', type=int, help='Maximum parallel workers')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    parser.add_argument('--dry-run', action='store_true', help='Estimate scope')
    parser.add_argument('--output-dir', default='output', help='Output directory')
    parser.add_argument('--cache-dir', default='.cache', help='Cache directory')
    parser.add_argument('--database', default='ao1_visibility_cmdb.db', help='Database file')
    
    return parser.parse_args()

async def estimate_ao1_scope(project_id: str, config: Dict[str, Any]):
    print("   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Estimating AO1 discovery scope...")
    
    try:
        from gcp_client import BigQueryClientManager
        
        client_manager = BigQueryClientManager(project_id)
        
        with client_manager.get_client() as client:
            datasets = list(client.list_datasets(project=project_id))
            
            critical_tables = [
                f"{project_id}.SAS_BI.V_DIM_ENDPOINT",
                f"{project_id}.SAS_BI.V_DIM_ENDPOINTAGENT", 
                f"{project_id}.SAS_BI.V_SPL_ENDPOINT_LOG"
            ]
            
            table_estimates = {}
            total_endpoints_estimate = 0
            
            for table_path in critical_tables:
                try:
                    table_ref = client.get_table(table_path)
                    row_count = table_ref.num_rows or 0
                    
                    if 'ENDPOINT' in table_path:
                        estimated_endpoints = int(row_count * 0.8)
                    elif 'AGENT' in table_path:
                        estimated_endpoints = int(row_count * 0.7)
                    elif 'SPL' in table_path:
                        estimated_endpoints = int(row_count * 0.6)
                    else:
                        estimated_endpoints = int(row_count * 0.5)
                    
                    table_estimates[table_path] = {
                        'total_rows': row_count,
                        'estimated_endpoints': estimated_endpoints,
                        'size_gb': (table_ref.num_bytes or 0) / (1024**3)
                    }
                    total_endpoints_estimate += estimated_endpoints
                    
                except Exception as e:
                    print(f"   ⚠°｡⋆⸜ ♡   Cannot access {table_path}: {e}")
                    table_estimates[table_path] = {'error': str(e)}
            
            try:
                chronicle_client = BigQueryClientManager("chronicle-fisv")
                with chronicle_client.get_client() as chronicle:
                    chronicle_table = chronicle.get_table("chronicle-fisv.datalake.events")
                    chronicle_rows = chronicle_table.num_rows or 0
                    chronicle_endpoints = int(chronicle_rows * 0.1)
                    total_endpoints_estimate += chronicle_endpoints
                    
                    table_estimates["chronicle-fisv.datalake.events"] = {
                        'total_rows': chronicle_rows,
                        'estimated_endpoints': chronicle_endpoints,
                        'size_gb': (chronicle_table.num_bytes or 0) / (1024**3)
                    }
            except Exception as e:
                print(f"   ⚠°｡⋆⸜ ♡   Chronicle estimation failed: {e}")
            
            estimate = {
                'total_datasets': len(datasets),
                'critical_tables_analyzed': len([t for t in table_estimates.values() if 'error' not in t]),
                'estimated_total_endpoints': total_endpoints_estimate,
                'table_breakdown': table_estimates,
                'recommendation': 'PROCEED' if total_endpoints_estimate > 1000 else 'REVIEW_PERMISSIONS'
            }
            
            print("   ❀°｡ ‧˚♡ ˚‧ ｡°❀   AO1 Scope Estimate:")
            print(f"   ✧･ﾟ: *✧･ﾟ:*   Total datasets: {estimate['total_datasets']:,}")
            print(f"   ✧･ﾟ: *✧･ﾟ:*   Critical tables accessible: {estimate['critical_tables_analyzed']}/4")
            print(f"   ✧･ﾟ: *✧･ﾟ:*   Estimated endpoints: {estimate['estimated_total_endpoints']:,}")
            print(f"   ✧･ﾟ: *✧･ﾟ:*   Recommendation: {estimate['recommendation']}")
            
            for table_path, data in table_estimates.items():
                if 'error' not in data:
                    table_name = table_path.split('.')[-1]
                    print(f"   ･ﾟ✧ ◞ ♡   {table_name}: {data['estimated_endpoints']:,} endpoints")
            
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
    
    print("   ♡₊˚ ｡⋅˚♡ ✧ ‧₊˚ ⋅   AO1 Log Visibility Measurement   ⋅ ˚₊‧ ✧ ♡˚⋅｡ ˚₊♡")
    print(f"   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Project: {args.project}")
    print(f"   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Output directory: {output_dir}")
    print(f"   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Database: {config.get('database_path', 'ao1_visibility_cmdb.db')}")
    print(f"   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Max workers: {config.get('max_workers', 2)}")
    
    try:
        if args.dry_run:
            estimate = await estimate_ao1_scope(args.project, config)
            
            if 'error' in estimate:
                print(f"   ✗°｡⋆⸜ ♡   Estimation failed: {estimate['error']}")
                sys.exit(1)
            
            estimate_file = output_dir / "ao1_scope_estimate.json"
            with open(estimate_file, 'w') as f:
                json.dump(estimate, f, indent=2)
            
            print(f"   ❀°｡ ‧˚♡ ˚‧ ｡°❀   AO1 scope estimate saved: {estimate_file}")
            
            if estimate['recommendation'] == 'PROCEED':
                print("   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Ready for AO1 discovery. Run without --dry-run to proceed.")
            else:
                print("   ⚠°｡⋆⸜ ♡   Please review table permissions before proceeding.")
            return
        
        runner = AO1VisibilityRunner(args.project, args.config)
        
        if not args.resume:
            print("   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Starting fresh AO1 discovery")
        else:
            print("   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Attempting to resume from checkpoint")
        
        stats, queries = await runner.execute_ao1_discovery()
        
        if 'error' in stats:
            print(f"   ✗°｡⋆⸜ ♡   AO1 Discovery failed: {stats['error']}")
            sys.exit(1)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        stats_file = output_dir / f"ao1_visibility_results_{timestamp}.json"
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2, default=str)
        
        queries_dir = output_dir / f"ao1_queries_{timestamp}"
        queries_dir.mkdir(exist_ok=True)
        
        for query_name, query_sql in queries.items():
            query_file = queries_dir / f"{query_name}.sql"
            with open(query_file, 'w') as f:
                f.write(f"-- {query_name.replace('_', ' ').title()}\n")
                f.write(f"-- AO1 Log Visibility Measurement\n")
                f.write(f"-- Project: {args.project}\n")
                f.write(f"-- Generated: {datetime.now().isoformat()}\n")
                f.write(f"-- Database: {config.get('database_path', 'ao1_visibility_cmdb.db')}\n\n")
                f.write(query_sql)
        
        latest_stats = output_dir / "latest_ao1_results.json"
        latest_queries = output_dir / "latest_ao1_queries"
        
        if latest_stats.exists() or latest_stats.is_symlink():
            latest_stats.unlink()
        if latest_queries.exists() or latest_queries.is_symlink():
            latest_queries.unlink()
        
        latest_stats.symlink_to(stats_file.name)
        latest_queries.symlink_to(queries_dir.name)
        
        print("\n" + "="*90)
        print("   ♡₊˚ ｡⋅˚♡ ✧ ‧₊˚ ⋅   AO1 Discovery Complete   ⋅ ˚₊‧ ✧ ♡˚⋅｡ ˚₊♡")
        print("="*90)
        
        ao1_metrics = stats.get('ao1_visibility_metrics', {})
        gap_analysis = stats.get('gap_analysis', {})
        compliance_status = stats.get('compliance_status', {})
        
        print(f"   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Total processing time: {stats.get('total_processing_time', 0):.2f} seconds")
        print(f"   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Total assets discovered: {stats.get('total_assets_discovered', 0):,}")
        
        if ao1_metrics:
            print("\n   ♡˗ˏˋ ◞ ～   AO1 Visibility Metrics:")
            for metric_name, metric_data in list(ao1_metrics.items())[:5]:
                metric_display = metric_name.replace('_', ' ').title()
                print(f"   ✧･ﾟ: *✧･ﾟ:*   {metric_display}: {metric_data.get('value', 0):.1f}% (Target: {metric_data.get('target', 0):.1f}%)")
        
        if gap_analysis:
            print("\n   ♡˗ˏˋ ◞ ～   Critical Visibility Gaps:")
            for gap_category, gap_info in list(gap_analysis.items())[:3]:
                print(f"   ⚠°｡⋆⸜ ♡   {gap_category}: {gap_info.get('count', 0):,} assets ({gap_info.get('severity', 'Unknown')} priority)")
        
        if compliance_status:
            print("\n   ♡˗ˏˋ ◞ ～   Logging Compliance Status:")
            for status, count in compliance_status.items():
                print(f"   ✧･ﾟ: *✧･ﾟ:*   {status}: {count:,} assets")
        
        recommendations = stats.get('ao1_recommendations', [])
        if recommendations:
            print("\n   ♡˗ˏˋ ◞ ～   AO1 Recommendations:")
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"   {i}. {rec}")
        
        print("\n   ｡･:*:･ﾟ★   Output Files:")
        print(f"   ◦ ❀ ◦   Results: {stats_file}")
        print(f"   ◦ ❀ ◦   Latest results: {latest_stats}")
        print(f"   ◦ ❀ ◦   AO1 queries: {queries_dir}")
        print(f"   ◦ ❀ ◦   Latest queries: {latest_queries}")
        print(f"   ◦ ❀ ◦   Database: {config.get('database_path', 'ao1_visibility_cmdb.db')}")
        
        total_assets = stats.get('total_assets_discovered', 0)
        
        if total_assets > 0:
            print(f"\n   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Success! AO1 CMDB built with {total_assets:,} assets")
            print("   ❀°｡ ‧˚♡ ˚‧ ｡°❀   CSOC can now measure log visibility across all critical domains")
            
            global_visibility = next((m for m in ao1_metrics.values() if 'global' in str(m)), {})
            if global_visibility and 'value' in global_visibility:
                visibility_pct = global_visibility['value']
                if visibility_pct >= 90:
                    print("   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Excellent visibility coverage achieved!")
                elif visibility_pct >= 75:
                    print("   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Good visibility coverage with room for improvement")
                else:
                    print("   ⚠°｡⋆⸜ ♡   Visibility gaps identified - review recommendations")
        else:
            print("   ⚠°｡⋆⸜ ♡   No assets discovered - check permissions and data sources")
        
        print("\n   ♡₊˚ ｡⋅˚♡ ✧ ‧₊˚ ⋅   AO1 Log Visibility Measurement Ready   ⋅ ˚₊‧ ✧ ♡˚⋅｡ ˚₊♡")
        
    except KeyboardInterrupt:
        print("\n\n   ⚠°｡⋆⸜ ♡   AO1 discovery interrupted by user")
        print("   ･ﾟ✧ ◞ ♡   Check for checkpoint files to resume later")
        sys.exit(130)
        
    except Exception as e:
        print(f"\n   ✗°｡⋆⸜ ♡   AO1 discovery failed: {e}")
        
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