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
import multiprocessing as mp

try:
    from discovery_engine import SuperOptimizedAO1Discovery, SimpleOptimizedAO1Discovery, IntelligentAO1Discovery
    print("   ✅ All discovery engines loaded successfully")
    ENGINES_AVAILABLE = True
except ImportError as e:
    print(f"   ✗°｡⋆⸜ ♡   Discovery engines failed to load: {e}")
    ENGINES_AVAILABLE = False
    sys.exit(1)

from config_loader import ConfigLoader

logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OptimizedAO1Runner:
    def __init__(self, project_id: str, config_file: str = None, args=None):
        self.project_id = project_id
        self.args = args
        self.config = ConfigLoader.load_config(config_file)
        
        if args:
            self.config.update({
                'max_memory_mb': args.max_memory,
                'max_disk_gb': args.max_disk,
                'cache_dir': args.cache_dir,
                'database_path': args.database,
                'batch_size': args.batch_size,
                'max_workers': args.max_workers,
                'debug_mode': args.debug,
                'operation_timeout': args.timeout,
                'enable_chronicle': not args.no_chronicle,
                'fast_mode': args.fast_mode,
                'complete_fields': args.complete_fields
            })
        
        try:
            print("   🚀 Attempting SuperOptimized engine...")
            self.engine = SuperOptimizedAO1Discovery(project_id, self.config)
            self.engine_type = "SuperOptimized"
            print("   ✅ SuperOptimized engine initialized")
        except Exception as e:
            print(f"   ⚠°｡⋆⸜ ♡   SuperOptimized failed: {e}")
            
            try:
                print("   🔧 Attempting SimpleOptimized engine...")
                self.engine = SimpleOptimizedAO1Discovery(project_id, self.config)
                self.engine_type = "SimpleOptimized"
                print("   ✅ SimpleOptimized engine initialized")
            except Exception as simple_error:
                print(f"   ⚠°｡⋆⸜ ♡   SimpleOptimized failed: {simple_error}")
                
                try:
                    print("   🔄 Attempting Basic Intelligent engine...")
                    self.engine = IntelligentAO1Discovery(project_id, self.config)
                    self.engine_type = "Basic_Intelligent"
                    print("   ✅ Basic Intelligent engine initialized")
                except Exception as final_error:
                    print(f"   ✗°｡⋆⸜ ♡   All engines failed: {final_error}")
                    print("   💡 Try checking your dependencies and authentication")
                    raise
        
        self.shutdown_requested = False
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        print(f"\n   ⚠°｡⋆⸜ ♡   Received signal {signum}, initiating optimized shutdown...")
        self.shutdown_requested = True
        if hasattr(self.engine, 'signal_handler'):
            self.engine.signal_handler.shutdown_requested = True
    
    async def execute_optimized_discovery(self):
        start_time = time.time()
        
        try:
            if hasattr(self.engine, 'execute_super_optimized_discovery'):
                print(f"   ⚡ ｡⋅˚♡   Running {self.engine_type} batch discovery engine")
                stats, queries = await self.engine.execute_super_optimized_discovery()
                        
            elif hasattr(self.engine, 'execute_simple_discovery'):
                print(f"   ⚡ ｡⋅˚♡   Running {self.engine_type} discovery engine")
                stats, queries = await self.engine.execute_simple_discovery()
                
            elif hasattr(self.engine, 'execute_intelligent_discovery'):
                print(f"   ⚡ ｡⋅˚♡   Running {self.engine_type} discovery engine")
                stats, queries = await self.engine.execute_intelligent_discovery()
            else:
                raise Exception("No compatible discovery method found")
                
            processing_time = time.time() - start_time
            stats['total_processing_time'] = processing_time
            stats['engine_type'] = self.engine_type
            return stats, queries
        except Exception as e:
            print(f"   ✗°｡⋆⸜ ♡   Discovery failed: {e}")
            import traceback
            if self.config.get('debug_mode', False):
                print("   🐛 Debug traceback:")
                traceback.print_exc()
            return {'error': str(e), 'engine_type': self.engine_type}, {}
        finally:
            if hasattr(self.engine, 'close'):
                try:
                    self.engine.close()
                except Exception:
                    pass

def parse_arguments():
    parser = argparse.ArgumentParser(description="AO1 Log Visibility Measurement System")
    
    parser.add_argument('--project', '-p', required=True, help='GCP Project ID')
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--max-memory', type=int, default=2048, help='Max memory cache (MB)')
    parser.add_argument('--max-disk', type=int, default=20, help='Max disk cache (GB)')
    parser.add_argument('--batch-size', type=int, default=1000, help='Batch processing size')
    parser.add_argument('--max-workers', type=int, default=min(32, mp.cpu_count() * 4), help='Max parallel workers')
    parser.add_argument('--dry-run', action='store_true', help='Estimate scope')
    parser.add_argument('--output-dir', default='output', help='Output directory')
    parser.add_argument('--cache-dir', default='.cache', help='Cache directory')
    parser.add_argument('--database', default='ao1_optimized_cmdb.db', help='Database file')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--timeout', type=int, default=1200, help='Timeout per operation in seconds')
    parser.add_argument('--no-chronicle', action='store_true', help='Skip Chronicle project analysis')
    parser.add_argument('--fast-mode', action='store_true', help='Enable fast processing')
    parser.add_argument('--complete-fields', action='store_true', default=True, help='Ensure complete field population')
    parser.add_argument('--parallel-limit', type=int, default=50, help='Max parallel table analysis')
    parser.add_argument('--memory-optimize', action='store_true', help='Enable memory optimization')
    
    return parser.parse_args()

async def estimate_ao1_scope(project_id: str, config: dict, args):
    print("   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   AO1 scope estimation...")
    
    try:
        from gcp_client import BigQueryClientManager
        from intelligent_content_matcher import IntelligentContentMatcher
        
        client_manager = BigQueryClientManager(project_id)
        matcher = IntelligentContentMatcher()
        
        with client_manager.get_client() as client:
            datasets = list(client.list_datasets(project=project_id))
            
            ao1_analysis = {
                'total_datasets': len(datasets),
                'ao1_capable_tables': 0,
                'hostname_capable_tables': 0,
                'estimated_assets': 0,
                'estimated_processing_time': 0,
                'ao1_field_potential': {},
                'log_visibility_coverage': {},
                'optimization_recommendations': [],
                'engine_compatibility': 'SuperOptimized_AO1'
            }
            
            ao1_fields = [
                'infrastructure_type', 'system_classification', 'global_region', 'business_unit',
                'edr_coverage', 'tanium_coverage', 'dlp_coverage', 'network_log_types',
                'endpoint_log_types', 'cloud_log_types', 'application_log_types', 'identity_log_types'
            ]
            
            total_tables = 0
            total_rows = 0
            
            for dataset in datasets[:20]:
                try:
                    dataset_ref = client.dataset(dataset.dataset_id, project=project_id)
                    tables = list(client.list_tables(dataset_ref))
                    total_tables += len(tables)
                    
                    for table_ref in tables[:15]:
                        try:
                            full_table = client.get_table(table_ref)
                            
                            if not full_table.schema or full_table.num_rows == 0:
                                continue
                            
                            total_rows += full_table.num_rows or 0
                            
                            all_columns = [field.name for field in full_table.schema]
                            
                            hostname_indicators = ['host', 'endpoint', 'computer', 'device', 'server', 'machine', 'asset', 'node', 'system']
                            has_hostname = any(
                                any(indicator in col.lower() for indicator in hostname_indicators)
                                for col in all_columns
                            )
                            
                            if has_hostname:
                                ao1_analysis['hostname_capable_tables'] += 1
                                
                                ao1_field_coverage = 0
                                for ao1_field in ao1_fields:
                                    field_indicators = matcher.semantic_patterns.get(ao1_field, {}).get('keywords', [])
                                    if any(any(indicator in col.lower() for indicator in field_indicators) for col in all_columns):
                                        ao1_field_coverage += 1
                                        if ao1_field not in ao1_analysis['ao1_field_potential']:
                                            ao1_analysis['ao1_field_potential'][ao1_field] = 0
                                        ao1_analysis['ao1_field_potential'][ao1_field] += 1
                                
                                if ao1_field_coverage > 3:
                                    ao1_analysis['ao1_capable_tables'] += 1
                                    
                                    estimated_rows = min(full_table.num_rows or 0, 50000)
                                    asset_estimate = int(estimated_rows * 0.8)
                                    ao1_analysis['estimated_assets'] += asset_estimate
                            
                        except Exception:
                            continue
                            
                except Exception:
                    continue
            
            if ao1_analysis['estimated_assets'] > 0:
                batch_processing_time = (ao1_analysis['estimated_assets'] / args.batch_size) * 2
                parallel_factor = min(args.max_workers, ao1_analysis['ao1_capable_tables']) / 8
                ao1_analysis['estimated_processing_time'] = max(60, 
                    batch_processing_time / max(parallel_factor, 1))
            
            ao1_coverage_score = len(ao1_analysis['ao1_field_potential']) / len(ao1_fields) * 100
            
            if ao1_coverage_score > 80:
                ao1_analysis['optimization_recommendations'].append("Excellent AO1 field coverage - all log visibility domains discoverable")
            elif ao1_coverage_score > 60:
                ao1_analysis['optimization_recommendations'].append("Good AO1 coverage - most log visibility fields discoverable")
            else:
                ao1_analysis['optimization_recommendations'].append("Limited AO1 coverage - focus on hostname and basic visibility")
            
            if ao1_analysis['estimated_assets'] > 50000:
                ao1_analysis['optimization_recommendations'].append("Large scale AO1 deployment - use batch processing with reduced batch size")
            elif ao1_analysis['estimated_assets'] > 10000:
                ao1_analysis['optimization_recommendations'].append("Medium scale AO1 deployment - optimal for parallel processing")
            else:
                ao1_analysis['optimization_recommendations'].append("Small scale AO1 deployment - increase batch size for efficiency")
            
            try:
                chronicle_client = BigQueryClientManager("chronicle-fisv")
                with chronicle_client.get_client() as chronicle:
                    chronicle_datasets = list(chronicle.list_datasets())
                    ao1_analysis['estimated_assets'] += len(chronicle_datasets) * 3000
                    ao1_analysis['optimization_recommendations'].append("Chronicle integration available for security log enrichment")
            except:
                ao1_analysis['optimization_recommendations'].append("Chronicle unavailable - primary project only")
            
            print("   ❀°｡ ‧˚♡ ˚‧ ｡°❀   AO1 Scope Analysis:")
            print(f"   ✧･ﾟ: *✧･ﾟ:*   Total datasets: {ao1_analysis['total_datasets']:,}")
            print(f"   ✧･ﾟ: *✧･ﾟ:*   AO1-capable tables: {ao1_analysis['ao1_capable_tables']:,}")
            print(f"   ✧･ﾟ: *✧･ﾟ:*   Hostname-capable tables: {ao1_analysis['hostname_capable_tables']:,}")
            print(f"   ✧･ﾟ: *✧･ﾟ:*   Estimated assets: {ao1_analysis['estimated_assets']:,}")
            print(f"   ✧･ﾟ: *✧･ﾟ:*   Estimated processing time: {ao1_analysis['estimated_processing_time']:.1f} seconds")
            
            if ao1_analysis['ao1_field_potential']:
                print(f"\n   ｡･:*:･ﾟ★   AO1 Field Coverage Potential:")
                for field_type, table_count in ao1_analysis['ao1_field_potential'].items():
                    print(f"   ◦ ✨ ◦   {field_type}: {table_count} tables")
            
            print(f"\n   ♡˗ˏˋ ◞ ～   AO1 Optimization Recommendations:")
            for rec in ao1_analysis['optimization_recommendations']:
                print(f"   ･ﾟ✧ ◞ ♡   {rec}")
            
            return ao1_analysis
            
    except Exception as e:
        print(f"   ✗°｡⋆⸜ ♡   AO1 estimation failed: {e}")
        return {'error': str(e)}

async def main():
    args = parse_arguments()
    
    if not args.project:
        print("   ✗°｡⋆⸜ ♡   GCP Project ID is required for AO1 discovery")
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
            print(f"   ✗°｡⋆⸜ ♡   Configuration loading failed: {e}")
            sys.exit(1)
    
    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        print("   🐛 Debug mode enabled")
    
    if args.memory_optimize:
        import gc
        gc.set_threshold(100, 10, 10)
        print("   🧠 Memory optimization enabled")
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    print("\n" + "="*100)
    print("   ♡₊˚ ｡⋅˚♡ ✧ ‧₊˚ ⋅   AO1 Log Visibility Measurement System   ⋅ ˚₊‧ ✧ ♡˚⋅｡ ˚₊♡")
    print("="*100)
    print(f"   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Project: {args.project}")
    print(f"   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Batch Size: {args.batch_size:,}")
    print(f"   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Max Workers: {args.max_workers}")
    print(f"   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Database: {args.database}")
    print(f"   ⋆｡‧˚ʚ♡ɞ˚‧ ｡°❀   Memory Cache: {args.max_memory:,}MB")
    print(f"   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Disk Cache: {args.max_disk}GB")
    print(f"   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Fast Mode: {'Enabled' if args.fast_mode else 'Disabled'}")
    print(f"   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   AO1 Fields: {'Enabled' if args.complete_fields else 'Disabled'}")
    print(f"   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Chronicle: {'Disabled' if args.no_chronicle else 'Enabled'}")
    
    try:
        if args.dry_run:
            estimate = await estimate_ao1_scope(args.project, config, args)
            
            if 'error' in estimate:
                print(f"   ✗°｡⋆⸜ ♡   AO1 estimation failed: {estimate['error']}")
                sys.exit(1)
            
            estimate_file = output_dir / "ao1_scope_estimate.json"
            with open(estimate_file, 'w') as f:
                json.dump(estimate, f, indent=2, default=str)
            
            print(f"   ❀°｡ ‧˚♡ ˚‧ ｡°❀   AO1 scope estimate saved: {estimate_file}")
            
            if estimate['estimated_assets'] > 10000:
                print("   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Excellent scale for AO1 log visibility measurement")
            elif estimate['estimated_assets'] > 2000:
                print("   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Good scale for AO1 discovery with parallel processing")
            else:
                print("   ⚠°｡⋆⸜ ♡   Limited scale - consider increasing batch size")
            return
        
        runner = OptimizedAO1Runner(args.project, args.config, args)
        
        print("   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Starting AO1 log visibility measurement discovery")
        print("   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Processing for CSOC visibility analysis...")
        
        try:
            stats, queries = await asyncio.wait_for(
                runner.execute_optimized_discovery(), 
                timeout=args.timeout * 2
            )
        except asyncio.TimeoutError:
            print(f"   ⚠°｡⋆⸜ ♡   Discovery timed out after {args.timeout * 2} seconds")
            sys.exit(1)
        
        if 'error' in stats:
            print(f"   ✗°｡⋆⸜ ♡   AO1 discovery failed: {stats['error']}")
            sys.exit(1)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        stats_file = output_dir / f"ao1_discovery_results_{timestamp}.json"
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
                f.write(f"-- Engine: {stats.get('engine_type', 'Unknown')}\n")
                f.write(f"-- Generated: {datetime.now().isoformat()}\n")
                f.write(f"-- Database: {args.database}\n\n")
                f.write(query_sql)
        
        latest_stats = output_dir / "latest_ao1_results.json"
        latest_queries = output_dir / "latest_ao1_queries"
        
        if latest_stats.exists() or latest_stats.is_symlink():
            latest_stats.unlink()
        if latest_queries.exists() or latest_queries.is_symlink():
            latest_queries.unlink()
        
        latest_stats.symlink_to(stats_file.name)
        latest_queries.symlink_to(queries_dir.name)
        
        print("\n" + "="*100)
        print("   ♡₊˚ ｡⋅˚♡ ✧ ‧₊˚ ⋅   AO1 Log Visibility Discovery Complete   ⋅ ˚₊‧ ✧ ♡˚⋅｡ ˚₊♡")
        print("="*100)
        
        processing_time = stats.get('total_processing_time', 0)
        engine_type = stats.get('engine_type', 'Unknown')
        total_assets = stats.get('total_assets', 0)
        avg_coverage = stats.get('avg_coverage_score', 0)
        high_coverage_count = stats.get('high_coverage_assets', 0)
        
        print(f"   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Engine Type: {engine_type}")
        print(f"   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Total processing time: {processing_time:.2f} seconds")
        print(f"   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Total assets discovered: {total_assets:,}")
        print(f"   ❀°｡ ‧˚♡ ˚‧ ｡°❀   High coverage assets: {high_coverage_count:,}")
        print(f"   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Average coverage score: {avg_coverage:.1f}%")
        
        optimization_features = stats.get('optimization_features', {})
        if optimization_features:
            print(f"\n   ｡･:*:･ﾟ★   AO1 Features:")
            for feature, enabled in optimization_features.items():
                if enabled:
                    feature_name = feature.replace('_', ' ').title()
                    print(f"   ◦ ⚡ ◦   {feature_name}")
        
        print("\n   ｡･:*:･ﾟ★   AO1 Output Files:")
        print(f"   ◦ 🚀 ◦   AO1 results: {stats_file}")
        print(f"   ◦ 🚀 ◦   Latest results: {latest_stats}")
        print(f"   ◦ 🚀 ◦   AO1 queries: {queries_dir}")
        print(f"   ◦ 🚀 ◦   Latest queries: {latest_queries}")
        print(f"   ◦ 🚀 ◦   AO1 database: {args.database}")
        
        if total_assets > 0:
            print(f"\n   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Success! AO1 Log Visibility CMDB built with {total_assets:,} assets")
            
            if avg_coverage >= 80:
                print("   ❀°｡ ‧˚♡ ˚‧ ｡°❀   🌟 EXCELLENT log visibility coverage achieved!")
            elif avg_coverage >= 60:
                print("   ❀°｡ ‧˚♡ ˚‧ ｡°❀   ✨ GOOD log visibility with comprehensive coverage!")
            elif avg_coverage >= 40:
                print("   ❀°｡ ‧˚♡ ˚‧ ｡°❀   💫 MODERATE coverage with improvement opportunities")
            else:
                print("   ⚠°｡⋆⸜ ♡   Coverage achieved but CSOC should improve log collection")
            
            performance_rating = "EXCELLENT" if processing_time < 300 else "GOOD" if processing_time < 600 else "FAIR"
            print(f"   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Performance: {performance_rating} ({processing_time:.1f}s)")
            
            print("   ❀°｡ ‧˚♡ ˚‧ ｡°❀   CSOC can now perform log visibility analysis with complete asset coverage")
        else:
            print("   ⚠°｡⋆⸜ ♡   No assets discovered - verify permissions and data sources")
        
        print("\n   ♡₊˚ ｡⋅˚♡ ✧ ‧₊˚ ⋅   AO1 Log Visibility System Ready   ⋅ ˚₊‧ ✧ ♡˚⋅｡ ˚₊♡")
        
    except KeyboardInterrupt:
        print("\n\n   ⚠°｡⋆⸜ ♡   AO1 discovery interrupted by user")
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
                'batch_size': args.batch_size,
                'max_workers': args.max_workers,
                'config': config,
                'args': vars(args)
            }, f, indent=2)
        
        print(f"   ･ﾟ✧ ◞ ♡   Error details saved: {error_file}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n   ⚠°｡⋆⸜ ♡   Interrupted by user")
        sys.exit(130)