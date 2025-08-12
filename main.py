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
    from working_discovery import WorkingAO1Discovery
    print("   ✅ Working discovery engine loaded")
    WORKING_ENGINE_AVAILABLE = True
except ImportError:
    print("   ⚠°｡⋆⸜ ♡   Working engine not found")
    WORKING_ENGINE_AVAILABLE = False

try:
    from discovery_engine import SuperOptimizedAO1Discovery, SimpleOptimizedAO1Discovery, IntelligentAO1Discovery
    print("   ✅ Advanced discovery engines loaded")
    ADVANCED_ENGINES_AVAILABLE = True
except ImportError as e:
    print(f"   ⚠°｡⋆⸜ ♡   Advanced engines failed: {e}")
    ADVANCED_ENGINES_AVAILABLE = False
    SuperOptimizedAO1Discovery = None
    SimpleOptimizedAO1Discovery = None
    IntelligentAO1Discovery = None

if not WORKING_ENGINE_AVAILABLE and not ADVANCED_ENGINES_AVAILABLE:
    print("   ✗°｡⋆⸜ ♡   No discovery engines available!")
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
            if WORKING_ENGINE_AVAILABLE:
                print("   🔧 Attempting Working engine (recommended)...")
                self.engine = WorkingAO1Discovery(project_id, self.config)
                self.engine_type = "Working"
                print("   ✅ Working engine initialized")
            else:
                raise Exception("Working engine not available")
        except Exception as e:
            print(f"   ⚠°｡⋆⸜ ♡   Working engine failed: {e}")
            
            try:
                if SuperOptimizedAO1Discovery:
                    print("   🚀 Attempting SuperOptimized engine...")
                    self.engine = SuperOptimizedAO1Discovery(project_id, self.config)
                    self.engine_type = "SuperOptimized"
                    print("   ✅ SuperOptimized engine initialized")
                else:
                    raise Exception("SuperOptimized engine not available")
            except Exception as super_error:
                print(f"   ⚠°｡⋆⸜ ♡   SuperOptimized failed: {super_error}")
                
                try:
                    if SimpleOptimizedAO1Discovery:
                        print("   🔧 Attempting SimpleOptimized engine...")
                        self.engine = SimpleOptimizedAO1Discovery(project_id, self.config)
                        self.engine_type = "SimpleOptimized"
                        print("   ✅ SimpleOptimized engine initialized")
                    else:
                        raise Exception("SimpleOptimized engine not available")
                except Exception as simple_error:
                    print(f"   ⚠°｡⋆⸜ ♡   SimpleOptimized failed: {simple_error}")
                    
                    try:
                        if IntelligentAO1Discovery:
                            print("   🔄 Attempting Basic Intelligent engine...")
                            self.engine = IntelligentAO1Discovery(project_id, self.config)
                            self.engine_type = "Basic_Intelligent"
                            print("   ✅ Basic Intelligent engine initialized")
                        else:
                            raise Exception("No discovery engines available")
                    except Exception as final_error:
                        print(f"   ✗°｡⋆⸜ ♡   All engines failed: {final_error}")
                        print("   💡 Try checking your dependencies and authentication")
                        raise
                    self.engine = SimpleOptimizedAO1Discovery(project_id, self.config)
                    self.engine_type = "SimpleOptimized"
                    print("   ✅ SimpleOptimized engine initialized")
                else:
                    raise Exception("SimpleOptimized engine not available")
            except Exception as simple_error:
                print(f"   ⚠°｡⋆⸜ ♡   SimpleOptimized failed: {simple_error}")
                
                try:
                    if IntelligentAO1Discovery:
                        print("   🔄 Attempting Basic Intelligent engine...")
                        self.engine = IntelligentAO1Discovery(project_id, self.config)
                        self.engine_type = "Basic_Intelligent"
                        print("   ✅ Basic Intelligent engine initialized")
                    else:
                        raise Exception("No discovery engines available")
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
            if hasattr(self.engine, 'execute_working_discovery'):
                print(f"   ⚡ ｡⋅˚♡   Running {self.engine_type} discovery engine")
                stats, queries = await self.engine.execute_working_discovery()
                
            elif hasattr(self.engine, 'execute_super_optimized_discovery'):
                print(f"   ⚡ ｡⋅˚♡   Running {self.engine_type} batch discovery engine")
                print("   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Initializing discovery components...")
                
                try:
                    discovery_task = asyncio.create_task(self.engine.execute_super_optimized_discovery())
                    stats, queries = await asyncio.wait_for(discovery_task, timeout=self.config.get('operation_timeout', 1200))
                except asyncio.TimeoutError:
                    print("   ⚠°｡⋆⸜ ♡   Discovery timed out, attempting graceful recovery...")
                    return {'error': 'Discovery timed out', 'engine_type': self.engine_type}, {}
                except Exception as discovery_error:
                    print(f"   ⚠°｡⋆⸜ ♡   SuperOptimized execution failed: {discovery_error}")
                    print("   ⚠°｡⋆⸜ ♡   Falling back to Working engine...")
                    
                    if WORKING_ENGINE_AVAILABLE:
                        fallback_engine = WorkingAO1Discovery(self.project_id, self.config)
                        stats, queries = await fallback_engine.execute_working_discovery()
                        stats['engine_type'] = "Fallback_Working"
                        if hasattr(fallback_engine, 'close'):
                            fallback_engine.close()
                    else:
                        return {'error': str(discovery_error), 'engine_type': self.engine_type}, {}
                        
            elif hasattr(self.engine, 'execute_simple_discovery'):
                print(f"   ⚡ ｡⋅˚♡   Running {self.engine_type} discovery engine")
                stats, queries = await self.engine.execute_simple_discovery()
                
            elif hasattr(self.engine, 'execute_intelligent_discovery'):
                print(f"   ⚡ ｡⋅˚♡   Running {self.engine_type} discovery engine")
                print("   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Starting intelligent discovery...")
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
    parser = argparse.ArgumentParser(description="Super Optimized AO1 Log Visibility Measurement System")
    
    parser.add_argument('--project', '-p', required=True, help='GCP Project ID')
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--max-memory', type=int, default=2048, help='Max memory cache (MB)')
    parser.add_argument('--max-disk', type=int, default=20, help='Max disk cache (GB)')
    parser.add_argument('--batch-size', type=int, default=1000, help='Batch processing size')
    parser.add_argument('--max-workers', type=int, default=min(32, mp.cpu_count() * 4), help='Max parallel workers')
    parser.add_argument('--dry-run', action='store_true', help='Estimate scope with intelligence')
    parser.add_argument('--output-dir', default='output', help='Output directory')
    parser.add_argument('--cache-dir', default='.cache', help='Intelligent cache directory')
    parser.add_argument('--database', default='ao1_optimized_cmdb.db', help='Optimized database file')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode with verbose output')
    parser.add_argument('--timeout', type=int, default=1200, help='Timeout per operation in seconds')
    parser.add_argument('--no-chronicle', action='store_true', help='Skip Chronicle project analysis')
    parser.add_argument('--fast-mode', action='store_true', help='Enable ultra-fast processing with reduced precision')
    parser.add_argument('--complete-fields', action='store_true', default=True, help='Ensure complete field population')
    parser.add_argument('--parallel-limit', type=int, default=50, help='Max parallel table analysis')
    parser.add_argument('--memory-optimize', action='store_true', help='Enable aggressive memory optimization')
    
    return parser.parse_args()

async def estimate_optimized_scope(project_id: str, config: dict, args):
    print("   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Optimized scope estimation with batch intelligence...")
    
    try:
        from gcp_client import BigQueryClientManager
        from intelligent_content_matcher import IntelligentContentMatcher
        
        client_manager = BigQueryClientManager(project_id)
        matcher = IntelligentContentMatcher()
        
        with client_manager.get_client() as client:
            datasets = list(client.list_datasets(project=project_id))
            
            optimized_analysis = {
                'total_datasets': len(datasets),
                'batch_capable_tables': 0,
                'hostname_capable_tables': 0,
                'estimated_endpoints': 0,
                'estimated_processing_time': 0,
                'recommended_batch_size': args.batch_size,
                'recommended_workers': args.max_workers,
                'memory_requirements_mb': 0,
                'completeness_potential': {},
                'optimization_recommendations': [],
                'engine_compatibility': 'SuperOptimized'
            }
            
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
                                optimized_analysis['hostname_capable_tables'] += 1
                                optimized_analysis['batch_capable_tables'] += 1
                                
                                estimated_rows = min(full_table.num_rows or 0, 50000)
                                endpoint_estimate = int(estimated_rows * 0.8)
                                optimized_analysis['estimated_endpoints'] += endpoint_estimate
                            
                            completeness_fields = ['os', 'operating', 'critical', 'owner', 'cost', 'region', 'environment']
                            field_coverage = sum(1 for col in all_columns 
                                               if any(field_term in col.lower() for field_term in completeness_fields))
                            
                            if field_coverage > 0:
                                for field_term in completeness_fields:
                                    if any(field_term in col.lower() for col in all_columns):
                                        if field_term not in optimized_analysis['completeness_potential']:
                                            optimized_analysis['completeness_potential'][field_term] = 0
                                        optimized_analysis['completeness_potential'][field_term] += 1
                            
                        except Exception:
                            continue
                            
                except Exception:
                    continue
            
            optimized_analysis['memory_requirements_mb'] = max(1024, 
                int(optimized_analysis['estimated_endpoints'] / 1000) * 100)
            
            if optimized_analysis['estimated_endpoints'] > 0:
                batch_processing_time = (optimized_analysis['estimated_endpoints'] / args.batch_size) * 2
                parallel_factor = min(args.max_workers, optimized_analysis['batch_capable_tables']) / 8
                optimized_analysis['estimated_processing_time'] = max(60, 
                    batch_processing_time / max(parallel_factor, 1))
            
            if optimized_analysis['estimated_endpoints'] > 50000:
                optimized_analysis['optimization_recommendations'].append("Excellent scale for batch processing - reduce batch size to 500 for optimal performance")
                optimized_analysis['recommended_batch_size'] = 500
            elif optimized_analysis['estimated_endpoints'] > 10000:
                optimized_analysis['optimization_recommendations'].append("Good scale for parallel processing - current settings optimal")
            else:
                optimized_analysis['optimization_recommendations'].append("Small scale - increase batch size to 2000 for efficiency")
                optimized_analysis['recommended_batch_size'] = 2000
            
            if optimized_analysis['memory_requirements_mb'] > args.max_memory:
                optimized_analysis['optimization_recommendations'].append(f"Increase memory to {optimized_analysis['memory_requirements_mb']}MB for optimal performance")
            
            if optimized_analysis['batch_capable_tables'] > args.max_workers * 5:
                optimized_analysis['optimization_recommendations'].append(f"Increase workers to {min(64, optimized_analysis['batch_capable_tables'] // 3)} for faster parallel processing")
                optimized_analysis['recommended_workers'] = min(64, optimized_analysis['batch_capable_tables'] // 3)
            
            completeness_score = len(optimized_analysis['completeness_potential']) / 7 * 100
            if completeness_score > 80:
                optimized_analysis['optimization_recommendations'].append("Excellent field completeness potential - all critical fields discoverable")
            elif completeness_score > 60:
                optimized_analysis['optimization_recommendations'].append("Good field completeness potential - most critical fields discoverable")
            else:
                optimized_analysis['optimization_recommendations'].append("Limited field completeness - focus on hostname discovery")
            
            try:
                chronicle_client = BigQueryClientManager("chronicle-fisv")
                with chronicle_client.get_client() as chronicle:
                    chronicle_datasets = list(chronicle.list_datasets())
                    optimized_analysis['estimated_endpoints'] += len(chronicle_datasets) * 5000
                    optimized_analysis['optimization_recommendations'].append("Chronicle integration available for security enrichment")
            except:
                optimized_analysis['optimization_recommendations'].append("Chronicle unavailable - primary project only")
            
            print("   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Optimized Scope Analysis:")
            print(f"   ✧･ﾟ: *✧･ﾟ:*   Total datasets: {optimized_analysis['total_datasets']:,}")
            print(f"   ✧･ﾟ: *✧･ﾟ:*   Total tables analyzed: {total_tables:,}")
            print(f"   ✧･ﾟ: *✧･ﾟ:*   Batch-capable tables: {optimized_analysis['batch_capable_tables']:,}")
            print(f"   ✧･ﾟ: *✧･ﾟ:*   Hostname-capable tables: {optimized_analysis['hostname_capable_tables']:,}")
            print(f"   ✧･ﾟ: *✧･ﾟ:*   Estimated endpoints: {optimized_analysis['estimated_endpoints']:,}")
            print(f"   ✧･ﾟ: *✧･ﾟ:*   Estimated processing time: {optimized_analysis['estimated_processing_time']:.1f} seconds")
            print(f"   ✧･ﾟ: *✧･ﾟ:*   Memory requirements: {optimized_analysis['memory_requirements_mb']:,}MB")
            print(f"   ✧･ﾟ: *✧･ﾟ:*   Engine compatibility: {optimized_analysis['engine_compatibility']}")
            
            if optimized_analysis['completeness_potential']:
                print(f"\n   ｡･:*:･ﾟ★   Field Completeness Potential:")
                for field_type, table_count in optimized_analysis['completeness_potential'].items():
                    print(f"   ◦ ✨ ◦   {field_type}: {table_count} tables")
            
            print(f"\n   ♡˗ˏˋ ◞ ～   Optimization Recommendations:")
            for rec in optimized_analysis['optimization_recommendations']:
                print(f"   ･ﾟ✧ ◞ ♡   {rec}")
            
            return optimized_analysis
            
    except Exception as e:
        print(f"   ✗°｡⋆⸜ ♡   Optimized estimation failed: {e}")
        return {'error': str(e)}

async def main():
    args = parse_arguments()
    
    if not args.project:
        print("   ✗°｡⋆⸜ ♡   GCP Project ID is required for optimized discovery")
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
        print("   🐛 Debug mode enabled - verbose output activated")
    
    if args.memory_optimize:
        import gc
        gc.set_threshold(100, 10, 10)
        print("   🧠 Memory optimization enabled")
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    print("\n" + "="*100)
    print("   ♡₊˚ ｡⋅˚♡ ✧ ‧₊˚ ⋅   Super Optimized AO1 Log Visibility Measurement   ⋅ ˚₊‧ ✧ ♡˚⋅｡ ˚₊♡")
    print("="*100)
    print(f"   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Project: {args.project}")
    print(f"   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Batch Size: {args.batch_size:,}")
    print(f"   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Max Workers: {args.max_workers}")
    print(f"   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Database: {args.database}")
    print(f"   ⋆｡‧˚ʚ♡ɞ˚‧ ｡°❀   Memory Cache: {args.max_memory:,}MB")
    print(f"   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Disk Cache: {args.max_disk}GB")
    print(f"   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Fast Mode: {'Enabled' if args.fast_mode else 'Disabled'}")
    print(f"   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Complete Fields: {'Enabled' if args.complete_fields else 'Disabled'}")
    print(f"   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Chronicle: {'Disabled' if args.no_chronicle else 'Enabled'}")
    
    try:
        if args.dry_run:
            estimate = await estimate_optimized_scope(args.project, config, args)
            
            if 'error' in estimate:
                print(f"   ✗°｡⋆⸜ ♡   Optimized estimation failed: {estimate['error']}")
                sys.exit(1)
            
            estimate_file = output_dir / "optimized_scope_estimate.json"
            with open(estimate_file, 'w') as f:
                json.dump(estimate, f, indent=2, default=str)
            
            print(f"   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Optimized scope estimate saved: {estimate_file}")
            
            if estimate['estimated_endpoints'] > 10000:
                print("   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Excellent scale for batch processing. Run without --dry-run to proceed.")
                print(f"   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Recommended: --batch-size {estimate['recommended_batch_size']} --max-workers {estimate['recommended_workers']}")
            elif estimate['estimated_endpoints'] > 2000:
                print("   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Good scale for optimized discovery with parallel processing.")
            else:
                print("   ⚠°｡⋆⸜ ♡   Limited scale detected - consider increasing batch size for efficiency.")
            return
        
        runner = OptimizedAO1Runner(args.project, args.config, args)
        
        print("   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Starting super optimized batch discovery with complete field population")
        print("   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   This may take several minutes depending on data size...")
        
        try:
            stats, queries = await asyncio.wait_for(
                runner.execute_optimized_discovery(), 
                timeout=args.timeout * 2
            )
        except asyncio.TimeoutError:
            print(f"   ⚠°｡⋆⸜ ♡   Discovery timed out after {args.timeout * 2} seconds")
            print("   ･ﾟ✧ ◞ ♡   Try reducing batch size or increasing timeout")
            sys.exit(1)
        
        if 'error' in stats:
            print(f"   ✗°｡⋆⸜ ♡   Optimized discovery failed: {stats['error']}")
            sys.exit(1)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        stats_file = output_dir / f"optimized_discovery_results_{timestamp}.json"
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2, default=str)
        
        queries_dir = output_dir / f"optimized_queries_{timestamp}"
        queries_dir.mkdir(exist_ok=True)
        
        for query_name, query_sql in queries.items():
            query_file = queries_dir / f"{query_name}.sql"
            with open(query_file, 'w') as f:
                f.write(f"-- {query_name.replace('_', ' ').title()}\n")
                f.write(f"-- Super Optimized AO1 Log Visibility Measurement\n")
                f.write(f"-- Project: {args.project}\n")
                f.write(f"-- Engine: {stats.get('engine_type', 'Unknown')}\n")
                f.write(f"-- Batch Size: {args.batch_size}\n")
                f.write(f"-- Max Workers: {args.max_workers}\n")
                f.write(f"-- Generated: {datetime.now().isoformat()}\n")
                f.write(f"-- Database: {args.database}\n\n")
                f.write(query_sql)
        
        latest_stats = output_dir / "latest_optimized_results.json"
        latest_queries = output_dir / "latest_optimized_queries"
        
        if latest_stats.exists() or latest_stats.is_symlink():
            latest_stats.unlink()
        if latest_queries.exists() or latest_queries.is_symlink():
            latest_queries.unlink()
        
        latest_stats.symlink_to(stats_file.name)
        latest_queries.symlink_to(queries_dir.name)
        
        print("\n" + "="*100)
        print("   ♡₊˚ ｡⋅˚♡ ✧ ‧₊˚ ⋅   Super Optimized Discovery Complete   ⋅ ˚₊‧ ✧ ♡˚⋅｡ ˚₊♡")
        print("="*100)
        
        processing_time = stats.get('total_processing_time', 0)
        engine_type = stats.get('engine_type', 'Unknown')
        total_assets = stats.get('total_assets', 0)
        avg_intelligence = stats.get('avg_intelligence_score', 0)
        avg_quality = stats.get('avg_data_quality_score', 0)
        high_quality_count = stats.get('high_quality_assets', 0)
        
        print(f"   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Engine Type: {engine_type}")
        print(f"   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Total processing time: {processing_time:.2f} seconds")
        print(f"   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Total assets discovered: {total_assets:,}")
        print(f"   ❀°｡ ‧˚♡ ˚‧ ｡°❀   High quality assets: {high_quality_count:,}")
        print(f"   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Average intelligence score: {avg_intelligence:.3f}")
        print(f"   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Average data quality: {avg_quality:.1f}%")
        
        optimization_features = stats.get('optimization_features', {})
        if optimization_features:
            print(f"\n   ｡･:*:･ﾟ★   Optimization Features:")
            for feature, enabled in optimization_features.items():
                if enabled:
                    feature_name = feature.replace('_', ' ').title()
                    print(f"   ◦ ⚡ ◦   {feature_name}")
        
        batch_stats = stats.get('inventory_build_stats', {})
        if batch_stats:
            print(f"\n   ｡･:*:･ﾟ★   Batch Processing Stats:")
            print(f"   ◦ 📊 ◦   Processed endpoints: {batch_stats.get('processed_endpoints', 0):,}")
            print(f"   ◦ 📊 ◦   Enriched assets: {batch_stats.get('enriched_assets', 0):,}")
            print(f"   ◦ 📊 ◦   Total data points: {batch_stats.get('total_data_points', 0):,}")
        
        cache_stats = stats.get('cache_performance', {})
        if cache_stats:
            hit_rate = cache_stats.get('hit_rate', 0)
            memory_usage = cache_stats.get('memory_usage_mb', 0)
            print(f"   ◦ 🧠 ◦   Cache hit rate: {hit_rate}%")
            print(f"   ◦ 🧠 ◦   Memory usage: {memory_usage:.1f}MB")
        
        print("\n   ｡･:*:･ﾟ★   Optimized Output Files:")
        print(f"   ◦ 🚀 ◦   Optimized results: {stats_file}")
        print(f"   ◦ 🚀 ◦   Latest results: {latest_stats}")
        print(f"   ◦ 🚀 ◦   Optimized queries: {queries_dir}")
        print(f"   ◦ 🚀 ◦   Latest queries: {latest_queries}")
        print(f"   ◦ 🚀 ◦   Optimized database: {args.database}")
        
        if total_assets > 0:
            print(f"\n   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Success! Optimized CMDB built with {total_assets:,} complete assets")
            
            if avg_intelligence >= 0.9:
                print("   ❀°｡ ‧˚♡ ˚‧ ｡°❀   🌟 EXCEPTIONAL intelligence and completeness achieved!")
            elif avg_intelligence >= 0.8:
                print("   ❀°｡ ‧˚♡ ˚‧ ｡°❀   ✨ EXCELLENT intelligence with comprehensive field population!")
            elif avg_intelligence >= 0.7:
                print("   ❀°｡ ‧˚♡ ˚‧ ｡°❀   💫 HIGH intelligence quality with optimized performance")
            elif avg_intelligence >= 0.6:
                print("   ❀°｡ ‧˚♡ ˚‧ ｡°❀   📊 GOOD intelligence quality with batch optimization")
            else:
                print("   ⚠°｡⋆⸜ ♡   Intelligence achieved but consider additional data enrichment")
            
            performance_rating = "EXCELLENT" if processing_time < 300 else "GOOD" if processing_time < 600 else "FAIR"
            print(f"   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Performance: {performance_rating} ({processing_time:.1f}s)")
            
            print("   ❀°｡ ‧˚♡ ˚‧ ｡°❀   CSOC can now perform advanced log visibility analysis with complete asset data")
        else:
            print("   ⚠°｡⋆⸜ ♡   No assets discovered - verify permissions and data sources")
        
        print("\n   ♡₊˚ ｡⋅˚♡ ✧ ‧₊˚ ⋅   Super Optimized AO1 System Ready   ⋅ ˚₊‧ ✧ ♡˚⋅｡ ˚₊♡")
        
    except KeyboardInterrupt:
        print("\n\n   ⚠°｡⋆⸜ ♡   Optimized discovery interrupted by user")
        print("   ･ﾟ✧ ◞ ♡   Optimized cache and partial results preserved for faster restart")
        sys.exit(130)
        
    except Exception as e:
        print(f"\n   ✗°｡⋆⸜ ♡   Optimized discovery failed: {e}")
        
        error_file = output_dir / f"optimized_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
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