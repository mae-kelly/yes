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
import psutil

# Add the unlimited discovery engine
sys.path.insert(0, os.path.dirname(__file__))

print("🚀 UNLIMITED AO1 Discovery System")
print("⚠️  ALL LIMITS REMOVED - MAXIMUM DISCOVERY MODE")
print("="*80)

try:
    from unlimited_discovery import UnlimitedAO1Discovery
    print("   ✅ Unlimited Discovery Engine loaded")
    UNLIMITED_ENGINE_AVAILABLE = True
except ImportError as e:
    print(f"   ❌ Unlimited engine failed: {e}")
    UNLIMITED_ENGINE_AVAILABLE = False
    # Fallback to regular engines
    try:
        from discovery_engine import SuperOptimizedAO1Discovery, SimpleOptimizedAO1Discovery
        print("   ⚠️  Using fallback engines")
        ENGINES_AVAILABLE = True
    except ImportError:
        print("   ❌ No discovery engines available")
        ENGINES_AVAILABLE = False
        sys.exit(1)

from config_loader import ConfigLoader

# Configure logging for unlimited processing
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('unlimited_discovery.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UnlimitedRunner:
    def __init__(self, project_id: str, config_file: str = None, args=None):
        self.project_id = project_id
        self.args = args
        self.start_time = time.time()
        
        # Load unlimited configuration
        self.config = ConfigLoader.load_config(config_file)
        
        # Override with unlimited settings
        unlimited_overrides = {
            'max_workers': min(args.max_workers if args else 128, mp.cpu_count() * 16),
            'max_memory_mb': args.max_memory if args else 65536,  # 64GB
            'max_disk_gb': args.max_disk if args else 1000,      # 1TB
            'batch_size': args.batch_size if args else 50000,
            'query_timeout_seconds': 21600,  # 6 hours
            'total_timeout_hours': 72,       # 3 days
            'disable_sampling': True,
            'ignore_table_size_limits': True,
            'enable_full_table_scans': True,
            'unlimited_mode': True,
            'discover_all_projects': True,
            'extract_all_possible_fields': True,
            'continue_on_errors': True,
            'bypass_cost_controls': True
        }
        
        self.config.update(unlimited_overrides)
        
        if args:
            self.config.update({
                'cache_dir': args.cache_dir,
                'database_path': args.database,
                'debug_mode': args.debug,
                'fast_mode': args.fast_mode,
                'comprehensive_mode': True,  # Always comprehensive in unlimited mode
                'aggressive_discovery': True
            })
        
        # Initialize the unlimited engine
        self.engine = None
        self.engine_type = "Unknown"
        
        if UNLIMITED_ENGINE_AVAILABLE:
            try:
                print("   🚀 Initializing UNLIMITED Discovery Engine...")
                self.engine = UnlimitedAO1Discovery(project_id, self.config)
                self.engine_type = "Unlimited"
                print("   ✅ UNLIMITED Engine ready for maximum discovery")
                print(f"   ⚡ Workers: {self.config['max_workers']}")
                print(f"   🧠 Memory: {self.config['max_memory_mb']:,}MB")
                print(f"   💾 Disk: {self.config['max_disk_gb']}GB")
                print(f"   ⏱️  Timeout: {self.config['query_timeout_seconds']}s per query")
            except Exception as e:
                print(f"   ❌ Unlimited engine failed: {e}")
                self.engine = None
        
        # Fallback to optimized engines if unlimited fails
        if not self.engine and ENGINES_AVAILABLE:
            try:
                print("   🔧 Falling back to SuperOptimized engine...")
                from discovery_engine import SuperOptimizedAO1Discovery
                self.engine = SuperOptimizedAO1Discovery(project_id, self.config)
                self.engine_type = "SuperOptimized_Fallback"
                print("   ✅ SuperOptimized engine ready")
            except Exception as e:
                print(f"   ❌ SuperOptimized fallback failed: {e}")
                try:
                    print("   🔧 Final fallback to Simple engine...")
                    from discovery_engine import SimpleOptimizedAO1Discovery
                    self.engine = SimpleOptimizedAO1Discovery(project_id, self.config)
                    self.engine_type = "Simple_Fallback"
                    print("   ✅ Simple engine ready")
                except Exception as final_e:
                    print(f"   ❌ All engines failed: {final_e}")
                    raise
        
        if not self.engine:
            raise Exception("No discovery engine could be initialized")
        
        # Setup signal handling for graceful shutdown
        self.shutdown_requested = False
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # System resource monitoring
        self._log_system_resources()
    
    def _signal_handler(self, signum, frame):
        print(f"\n⚠️  Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_requested = True
        if hasattr(self.engine, 'shutdown_requested'):
            self.engine.shutdown_requested = True
    
    def _log_system_resources(self):
        """Log available system resources"""
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        cpu_count = mp.cpu_count()
        
        print(f"   💻 System Resources:")
        print(f"   📊 CPU Cores: {cpu_count}")
        print(f"   🧠 Total Memory: {memory.total / (1024**3):.1f}GB")
        print(f"   💾 Available Memory: {memory.available / (1024**3):.1f}GB")
        print(f"   💿 Disk Space: {disk.free / (1024**3):.1f}GB free")
        print(f"   ⚡ Discovery will use up to {self.config['max_workers']} workers")
    
    async def execute_unlimited_discovery(self):
        """Execute unlimited discovery with maximum capability"""
        print("\n" + "="*80)
        print("🚀 STARTING UNLIMITED AO1 DISCOVERY")
        print("⚠️  Maximum processing mode - no artificial limits")
        print("="*80)
        
        try:
            if hasattr(self.engine, 'execute_unlimited_discovery'):
                print("   🎯 Using UNLIMITED discovery method")
                stats, queries = await self.engine.execute_unlimited_discovery()
            elif hasattr(self.engine, 'execute_super_optimized_discovery'):
                print("   🎯 Using SUPER OPTIMIZED discovery method")
                stats, queries = await self.engine.execute_super_optimized_discovery()
            elif hasattr(self.engine, 'execute_simple_discovery'):
                print("   🎯 Using SIMPLE discovery method")
                stats, queries = await self.engine.execute_simple_discovery()
            else:
                raise Exception("No compatible discovery method found")
            
            total_time = time.time() - self.start_time
            stats['total_runtime'] = total_time
            stats['engine_type'] = self.engine_type
            stats['unlimited_mode'] = self.config.get('unlimited_mode', False)
            
            return stats, queries
            
        except Exception as e:
            print(f"   ❌ Unlimited discovery failed: {e}")
            import traceback
            if self.config.get('debug_mode', False):
                traceback.print_exc()
            return {'error': str(e), 'engine_type': self.engine_type}, {}
        finally:
            if hasattr(self.engine, 'close'):
                try:
                    self.engine.close()
                except Exception:
                    pass

def parse_unlimited_arguments():
    parser = argparse.ArgumentParser(description="UNLIMITED AO1 Discovery System")
    
    # Basic settings
    parser.add_argument('--project', '-p', required=True, help='GCP Project ID')
    parser.add_argument('--config', '-c', help='Configuration file path')
    
    # Unlimited resource settings
    parser.add_argument('--max-memory', type=int, default=65536, help='Max memory (MB) - default 64GB')
    parser.add_argument('--max-disk', type=int, default=1000, help='Max disk (GB) - default 1TB')
    parser.add_argument('--max-workers', type=int, default=min(128, mp.cpu_count() * 16), help='Max workers')
    parser.add_argument('--batch-size', type=int, default=50000, help='Batch size - default 50k')
    
    # Discovery scope
    parser.add_argument('--unlimited', action='store_true', default=True, help='Enable unlimited mode')
    parser.add_argument('--no-sampling', action='store_true', default=True, help='Disable all sampling')
    parser.add_argument('--all-projects', action='store_true', help='Discover all accessible projects')
    parser.add_argument('--all-fields', action='store_true', default=True, help='Extract all possible fields')
    parser.add_argument('--deep-analysis', action='store_true', default=True, help='Enable deep analysis')
    
    # Processing options
    parser.add_argument('--dry-run', action='store_true', help='Estimate scope only')
    parser.add_argument('--continue-on-errors', action='store_true', default=True, help='Continue despite errors')
    parser.add_argument('--bypass-limits', action='store_true', default=True, help='Bypass all safety limits')
    parser.add_argument('--fast-mode', action='store_true', help='Optimize for speed')
    
    # Output settings
    parser.add_argument('--output-dir', default='unlimited_output', help='Output directory')
    parser.add_argument('--cache-dir', default='unlimited_cache', help='Cache directory')
    parser.add_argument('--database', default='unlimited_ao1_cmdb.db', help='Database file')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    # Time limits (generous in unlimited mode)
    parser.add_argument('--query-timeout', type=int, default=21600, help='Query timeout (seconds)')
    parser.add_argument('--total-timeout', type=int, default=259200, help='Total timeout (seconds)')
    
    return parser.parse_args()

async def estimate_unlimited_scope(project_id: str, config: dict, args):
    """Estimate scope for unlimited discovery"""
    print("🔍 UNLIMITED SCOPE ESTIMATION")
    print("   Analyzing full discovery potential...")
    
    try:
        from gcp_client import BigQueryClientManager
        
        # Check all possible projects
        projects_to_check = [project_id]
        
        # Try to find Chronicle projects
        chronicle_variants = ['chronicle-fisv', 'chronicle-security', 'security-chronicle']
        for chronicle_project in chronicle_variants:
            try:
                chronicle_client = BigQueryClientManager(chronicle_project)
                if chronicle_client.test_connection():
                    projects_to_check.append(chronicle_project)
                    print(f"   ✅ Found accessible Chronicle project: {chronicle_project}")
            except:
                continue
        
        total_datasets = 0
        total_tables = 0
        total_estimated_rows = 0
        hostname_capable_tables = 0
        
        for project in projects_to_check:
            try:
                client_mgr = BigQueryClientManager(project)
                with client_mgr.get_client() as client:
                    datasets = list(client.list_datasets(project=project))
                    total_datasets += len(datasets)
                    print(f"   📊 Project {project}: {len(datasets)} datasets")
                    
                    # Sample first 50 datasets for estimation
                    for dataset in datasets[:50]:
                        try:
                            dataset_ref = client.dataset(dataset.dataset_id, project=project)
                            tables = list(client.list_tables(dataset_ref))
                            total_tables += len(tables)
                            
                            # Sample first 20 tables per dataset
                            for table_ref in tables[:20]:
                                try:
                                    full_table = client.get_table(table_ref)
                                    if full_table.schema and full_table.num_rows:
                                        total_estimated_rows += full_table.num_rows
                                        
                                        # Check for hostname capability
                                        columns = [field.name for field in full_table.schema]
                                        hostname_indicators = ['host', 'endpoint', 'computer', 'device', 'server', 'machine', 'asset', 'node', 'system']
                                        if any(any(indicator in col.lower() for indicator in hostname_indicators) for col in columns):
                                            hostname_capable_tables += 1
                                
                                except Exception:
                                    continue
                        except Exception:
                            continue
            except Exception as e:
                print(f"   ⚠️  Project {project} failed: {e}")
                continue
        
        # Extrapolate full estimates
        sampling_factor = 50 if total_datasets > 50 else 1
        table_sampling_factor = 20 if total_tables > 1000 else 1
        
        estimated_total_tables = total_tables * sampling_factor
        estimated_total_rows = total_estimated_rows * sampling_factor * table_sampling_factor
        estimated_hostname_tables = hostname_capable_tables * sampling_factor * table_sampling_factor
        estimated_assets = min(estimated_total_rows * 0.1, estimated_hostname_tables * 10000)
        
        # Estimate processing time (no limits)
        estimated_processing_hours = max(1, estimated_total_tables / (args.max_workers * 100))
        
        estimation = {
            'projects_analyzed': len(projects_to_check),
            'total_datasets': total_datasets * sampling_factor,
            'total_tables_estimated': estimated_total_tables,
            'hostname_capable_tables': estimated_hostname_tables,
            'estimated_total_rows': estimated_total_rows,
            'estimated_assets': int(estimated_assets),
            'estimated_processing_hours': estimated_processing_hours,
            'unlimited_features': [
                'No sampling restrictions',
                'No table size limits', 
                'No timeout restrictions',
                'Complete field extraction',
                'Multi-project discovery',
                f'{args.max_workers} parallel workers',
                f'{args.max_memory:,}MB memory cache',
                f'{args.max_disk}GB disk cache'
            ],
            'resource_requirements': {
                'recommended_memory_gb': max(16, estimated_total_tables / 1000),
                'recommended_disk_gb': max(100, estimated_assets / 10000),
                'recommended_processing_hours': estimated_processing_hours
            }
        }
        
        print("\n🎯 UNLIMITED DISCOVERY SCOPE ANALYSIS")
        print("="*60)
        print(f"   📊 Projects: {estimation['projects_analyzed']}")
        print(f"   📁 Estimated Datasets: {estimation['total_datasets']:,}")
        print(f"   🗄️  Estimated Tables: {estimation['total_tables_estimated']:,}")
        print(f"   🎯 Hostname Tables: {estimation['hostname_capable_tables']:,}")
        print(f"   📈 Estimated Assets: {estimation['estimated_assets']:,}")
        print(f"   ⏱️  Estimated Time: {estimation['estimated_processing_hours']:.1f} hours")
        
        print(f"\n💪 UNLIMITED CAPABILITIES:")
        for feature in estimation['unlimited_features']:
            print(f"   ✅ {feature}")
        
        print(f"\n📋 RESOURCE REQUIREMENTS:")
        print(f"   🧠 Memory: {estimation['resource_requirements']['recommended_memory_gb']}GB+")
        print(f"   💾 Disk: {estimation['resource_requirements']['recommended_disk_gb']}GB+")
        print(f"   ⏱️  Time: {estimation['resource_requirements']['recommended_processing_hours']:.1f} hours")
        
        if estimation['estimated_assets'] > 100000:
            print("\n🌟 MASSIVE SCALE DISCOVERY DETECTED")
            print("   This will be a comprehensive enterprise-wide discovery")
        elif estimation['estimated_assets'] > 10000:
            print("\n⚡ LARGE SCALE DISCOVERY DETECTED") 
            print("   Excellent opportunity for comprehensive asset mapping")
        else:
            print("\n📊 MEDIUM SCALE DISCOVERY")
            print("   Good coverage expected with unlimited processing")
        
        return estimation
        
    except Exception as e:
        print(f"   ❌ Unlimited estimation failed: {e}")
        return {'error': str(e)}

async def main():
    """Main unlimited discovery execution"""
    args = parse_unlimited_arguments()
    
    print(f"🚀 UNLIMITED AO1 DISCOVERY SYSTEM")
    print(f"⚠️  ALL ARTIFICIAL LIMITS REMOVED")
    print("="*80)
    print(f"   🎯 Project: {args.project}")
    print(f"   ⚡ Max Workers: {args.max_workers}")
    print(f"   🧠 Memory Cache: {args.max_memory:,}MB")
    print(f"   💾 Disk Cache: {args.max_disk}GB")
    print(f"   📦 Batch Size: {args.batch_size:,}")
    print(f"   ⏱️  Query Timeout: {args.query_timeout}s")
    print(f"   🔄 Continue on Errors: {args.continue_on_errors}")
    print(f"   🚫 Sampling Disabled: {args.no_sampling}")
    print(f"   📊 Deep Analysis: {args.deep_analysis}")
    
    # Setup output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Setup cache directory
    cache_dir = Path(args.cache_dir)
    cache_dir.mkdir(exist_ok=True)
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        print("   🐛 Debug logging enabled")
    
    try:
        # Load configuration
        config = {}
        if args.config and Path(args.config).exists():
            try:
                with open(args.config, 'r') as f:
                    if args.config.endswith(('.yaml', '.yml')):
                        import yaml
                        config = yaml.safe_load(f)
                    else:
                        config = json.load(f)
                print(f"   ✅ Configuration loaded: {args.config}")
            except Exception as e:
                print(f"   ⚠️  Configuration loading failed: {e}")
        
        # Dry run estimation
        if args.dry_run:
            print("\n🔍 PERFORMING UNLIMITED SCOPE ESTIMATION")
            estimation = await estimate_unlimited_scope(args.project, config, args)
            
            if 'error' in estimation:
                print(f"   ❌ Estimation failed: {estimation['error']}")
                return
            
            # Save estimation
            estimate_file = output_dir / f"unlimited_scope_estimate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(estimate_file, 'w') as f:
                json.dump(estimation, f, indent=2, default=str)
            
            print(f"\n💾 Estimation saved: {estimate_file}")
            
            # Recommend proceeding
            if estimation['estimated_assets'] > 1000:
                print(f"\n✅ RECOMMENDATION: Proceed with unlimited discovery")
                print(f"   Expected {estimation['estimated_assets']:,} assets in {estimation['estimated_processing_hours']:.1f} hours")
            else:
                print(f"\n⚠️  RECOMMENDATION: Consider standard discovery mode")
                print(f"   Limited asset count detected: {estimation['estimated_assets']:,}")
            
            return
        
        # Execute unlimited discovery
        print(f"\n🚀 EXECUTING UNLIMITED DISCOVERY")
        runner = UnlimitedRunner(args.project, args.config, args)
        
        try:
            stats, queries = await asyncio.wait_for(
                runner.execute_unlimited_discovery(),
                timeout=args.total_timeout
            )
        except asyncio.TimeoutError:
            print(f"\n⏰ Discovery completed maximum time limit: {args.total_timeout}s")
            print("   Results may be partial but should still be comprehensive")
            return
        
        if 'error' in stats:
            print(f"\n❌ UNLIMITED DISCOVERY FAILED")
            print(f"   Error: {stats['error']}")
            print(f"   Engine: {stats.get('engine_type', 'Unknown')}")
            
            # Save error details
            error_file = output_dir / f"unlimited_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(error_file, 'w') as f:
                json.dump({
                    'error': stats['error'],
                    'engine_type': stats.get('engine_type'),
                    'timestamp': datetime.now().isoformat(),
                    'config': config,
                    'args': vars(args)
                }, f, indent=2)
            
            print(f"   💾 Error details saved: {error_file}")
            return
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Stats file
        stats_file = output_dir / f"unlimited_discovery_results_{timestamp}.json"
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2, default=str)
        
        # Queries directory
        queries_dir = output_dir / f"unlimited_queries_{timestamp}"
        queries_dir.mkdir(exist_ok=True)
        
        for query_name, query_sql in queries.items():
            query_file = queries_dir / f"{query_name}.sql"
            with open(query_file, 'w') as f:
                f.write(f"-- {query_name.replace('_', ' ').title()}\n")
                f.write(f"-- UNLIMITED AO1 Discovery Results\n")
                f.write(f"-- Project: {args.project}\n")
                f.write(f"-- Engine: {stats.get('engine_type', 'Unknown')}\n")
                f.write(f"-- Generated: {datetime.now().isoformat()}\n")
                f.write(f"-- Database: {args.database}\n")
                f.write(f"-- Mode: UNLIMITED\n\n")
                f.write(query_sql)
        
        # Create latest symlinks
        latest_stats = output_dir / "latest_unlimited_results.json"
        latest_queries = output_dir / "latest_unlimited_queries"
        
        if latest_stats.exists() or latest_stats.is_symlink():
            latest_stats.unlink()
        if latest_queries.exists() or latest_queries.is_symlink():
            latest_queries.unlink()
        
        latest_stats.symlink_to(stats_file.name)
        latest_queries.symlink_to(queries_dir.name)
        
        # Display results
        print("\n" + "="*80)
        print("🎉 UNLIMITED AO1 DISCOVERY COMPLETED")
        print("="*80)
        
        total_time = stats.get('total_runtime', stats.get('processing_time', 0))
        engine_type = stats.get('engine_type', 'Unknown')
        total_assets = stats.get('total_assets', 0)
        
        print(f"   ⚡ Engine: {engine_type}")
        print(f"   ⏱️  Total Runtime: {total_time:.2f} seconds ({total_time/3600:.2f} hours)")
        print(f"   🎯 Total Assets: {total_assets:,}")
        
        if 'total_tables_processed' in stats:
            print(f"   🗄️  Tables Processed: {stats['total_tables_processed']:,}")
        
        if 'total_hostnames_discovered' in stats:
            print(f"   🔍 Hostnames Discovered: {stats['total_hostnames_discovered']:,}")
        
        if 'analytics' in stats:
            analytics = stats['analytics']
            if 'coverage_analysis' in analytics:
                coverage = analytics['coverage_analysis']
                print(f"   📊 Average Coverage: {coverage.get('average_coverage', 0):.1f}%")
                print(f"   🌟 High Coverage Assets: {coverage.get('high_coverage_assets', 0):,}")
        
        # Performance metrics
        if total_assets > 0 and total_time > 0:
            assets_per_second = total_assets / total_time
            print(f"   🚀 Processing Rate: {assets_per_second:.1f} assets/second")
        
        # Unlimited features used
        unlimited_features = stats.get('unlimited_features_enabled', [])
        if unlimited_features:
            print(f"\n🔥 UNLIMITED FEATURES UTILIZED:")
            for feature in unlimited_features:
                print(f"   ✅ {feature.replace('_', ' ').title()}")
        
        print(f"\n📁 OUTPUT FILES:")
        print(f"   📊 Results: {stats_file}")
        print(f"   📈 Queries: {queries_dir}")
        print(f"   🔗 Latest Results: {latest_stats}")
        print(f"   🔗 Latest Queries: {latest_queries}")
        print(f"   🗄️  Database: {args.database}")
        
        # Success assessment
        if total_assets > 50000:
            print(f"\n🌟 MASSIVE SUCCESS!")
            print(f"   Enterprise-scale discovery with {total_assets:,} assets")
            print(f"   This represents comprehensive organizational coverage")
        elif total_assets > 10000:
            print(f"\n🎉 EXCELLENT SUCCESS!")
            print(f"   Large-scale discovery with {total_assets:,} assets")
            print(f"   Strong organizational asset coverage achieved")
        elif total_assets > 1000:
            print(f"\n✅ GOOD SUCCESS!")
            print(f"   Medium-scale discovery with {total_assets:,} assets") 
            print(f"   Solid asset inventory established")
        else:
            print(f"\n📊 DISCOVERY COMPLETED")
            print(f"   {total_assets:,} assets discovered")
            print(f"   Consider expanding scope or checking permissions")
        
        # Performance assessment
        if total_time < 3600:  # < 1 hour
            print(f"   ⚡ EXCELLENT PERFORMANCE: Completed in {total_time/60:.1f} minutes")
        elif total_time < 10800:  # < 3 hours
            print(f"   🚀 GOOD PERFORMANCE: Completed in {total_time/3600:.1f} hours")
        else:
            print(f"   📊 COMPREHENSIVE ANALYSIS: {total_time/3600:.1f} hours of deep discovery")
        
        print(f"\n🎯 UNLIMITED AO1 DISCOVERY SYSTEM READY FOR ANALYSIS")
        print("   Use the generated queries to explore your comprehensive asset inventory")
        
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Unlimited discovery interrupted by user")
        return
    except Exception as e:
        print(f"\n❌ UNLIMITED DISCOVERY SYSTEM FAILED")
        print(f"   Error: {e}")
        
        # Save error details
        error_file = output_dir / f"unlimited_system_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(error_file, 'w') as f:
            json.dump({
                'error': str(e),
                'type': type(e).__name__,
                'timestamp': datetime.now().isoformat(),
                'args': vars(args)
            }, f, indent=2)
        
        print(f"   💾 Error details saved: {error_file}")
        
        if args.debug:
            import traceback
            print("\n🐛 DEBUG TRACEBACK:")
            traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ System failure: {e}")
        import traceback
        traceback.print_exc()