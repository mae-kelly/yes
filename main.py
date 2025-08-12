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

# Simplified imports - only use what's actually working
try:
    from discovery_engine import SimpleOptimizedAO1Discovery
    print("   ✅ SimpleOptimized discovery engine loaded successfully")
    BASIC_ENGINE_AVAILABLE = True
except ImportError as e:
    print(f"   ✗ SimpleOptimized engine failed to load: {e}")
    BASIC_ENGINE_AVAILABLE = False

# Try to import the more advanced engines but don't fail if they're not available
try:
    from discovery_engine import SuperOptimizedAO1Discovery
    print("   ✅ SuperOptimized discovery engine loaded successfully")
    SUPER_ENGINE_AVAILABLE = True
except ImportError as e:
    print(f"   ⚠ SuperOptimized engine not available: {e}")
    SUPER_ENGINE_AVAILABLE = False

try:
    from discovery_engine import IntelligentAO1Discovery
    print("   ✅ Intelligent discovery engine loaded successfully")
    INTELLIGENT_ENGINE_AVAILABLE = True
except ImportError as e:
    print(f"   ⚠ Intelligent engine not available: {e}")
    INTELLIGENT_ENGINE_AVAILABLE = False

if not (BASIC_ENGINE_AVAILABLE or SUPER_ENGINE_AVAILABLE or INTELLIGENT_ENGINE_AVAILABLE):
    print("   ✗ No discovery engines available")
    sys.exit(1)

from config_loader import ConfigLoader

logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ReliableAO1Runner:
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
        
        self.engine = None
        self.engine_type = None
        self.shutdown_requested = False
        
        # Try engines in order of preference, but ensure we get a working one
        self._initialize_engine()
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _initialize_engine(self):
        """Initialize the best available working engine"""
        
        # First try the SuperOptimized engine if available
        if SUPER_ENGINE_AVAILABLE and not self.args.force_simple:
            try:
                print("   🚀 Attempting SuperOptimized engine...")
                self.engine = SuperOptimizedAO1Discovery(self.project_id, self.config)
                self.engine_type = "SuperOptimized"
                print("   ✅ SuperOptimized engine initialized successfully")
                return
            except Exception as e:
                print(f"   ⚠ SuperOptimized failed: {e}")
                if self.args.debug:
                    import traceback
                    traceback.print_exc()
        
        # Fall back to SimpleOptimized engine
        if BASIC_ENGINE_AVAILABLE:
            try:
                print("   🔧 Using SimpleOptimized engine...")
                self.engine = SimpleOptimizedAO1Discovery(self.project_id, self.config)
                self.engine_type = "SimpleOptimized"
                print("   ✅ SimpleOptimized engine initialized successfully")
                return
            except Exception as e:
                print(f"   ⚠ SimpleOptimized failed: {e}")
                if self.args.debug:
                    import traceback
                    traceback.print_exc()
        
        # Last resort - try Intelligent engine
        if INTELLIGENT_ENGINE_AVAILABLE:
            try:
                print("   🔄 Using Basic Intelligent engine...")
                self.engine = IntelligentAO1Discovery(self.project_id, self.config)
                self.engine_type = "Basic_Intelligent"
                print("   ✅ Basic Intelligent engine initialized successfully")
                return
            except Exception as e:
                print(f"   ⚠ Basic Intelligent failed: {e}")
                if self.args.debug:
                    import traceback
                    traceback.print_exc()
        
        # If we get here, nothing worked
        raise Exception("All discovery engines failed to initialize. Check your dependencies and authentication.")
    
    def _signal_handler(self, signum, frame):
        print(f"\n   ⚠ Received signal {signum}, initiating shutdown...")
        self.shutdown_requested = True
        if hasattr(self.engine, 'signal_handler'):
            self.engine.signal_handler.shutdown_requested = True
    
    async def execute_discovery(self):
        start_time = time.time()
        
        if not self.engine:
            raise Exception("No engine available for discovery")
        
        try:
            print(f"   ⚡ Running {self.engine_type} discovery engine")
            
            # Route to the appropriate discovery method
            if hasattr(self.engine, 'execute_super_optimized_discovery'):
                print("   ⚡ Executing super optimized discovery...")
                stats, queries = await self.engine.execute_super_optimized_discovery()
                        
            elif hasattr(self.engine, 'execute_simple_discovery'):
                print("   ⚡ Executing simple discovery...")
                stats, queries = await self.engine.execute_simple_discovery()
                
            elif hasattr(self.engine, 'execute_intelligent_discovery'):
                print("   ⚡ Executing intelligent discovery...")
                stats, queries = await self.engine.execute_intelligent_discovery()
            else:
                raise Exception(f"Engine {self.engine_type} has no compatible discovery method")
            
            # Verify we actually got results
            total_assets = stats.get('total_assets', 0)
            if total_assets == 0:
                print("   ⚠ Warning: No assets were discovered. This might indicate:")
                print("     - Authentication issues")
                print("     - No data in the project")
                print("     - Insufficient permissions")
                print("     - Engine configuration problems")
                
                # Add debugging info
                if self.args.debug:
                    print(f"   🐛 Debug - Full stats: {json.dumps(stats, indent=2, default=str)}")
            
            processing_time = time.time() - start_time
            stats['total_processing_time'] = processing_time
            stats['engine_type'] = self.engine_type
            
            return stats, queries
            
        except Exception as e:
            print(f"   ✗ Discovery failed: {e}")
            if self.args.debug:
                import traceback
                print("   🐛 Debug traceback:")
                traceback.print_exc()
            return {'error': str(e), 'engine_type': self.engine_type}, {}
        finally:
            if hasattr(self.engine, 'close'):
                try:
                    self.engine.close()
                except Exception as close_error:
                    print(f"   ⚠ Engine cleanup warning: {close_error}")

def parse_arguments():
    parser = argparse.ArgumentParser(description="AO1 Log Visibility Measurement System")
    
    parser.add_argument('--project', '-p', required=True, help='GCP Project ID')
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--max-memory', type=int, default=1024, help='Max memory cache (MB)')
    parser.add_argument('--max-disk', type=int, default=10, help='Max disk cache (GB)')
    parser.add_argument('--batch-size', type=int, default=500, help='Batch processing size')
    parser.add_argument('--max-workers', type=int, default=min(16, mp.cpu_count() * 2), help='Max parallel workers')
    parser.add_argument('--dry-run', action='store_true', help='Estimate scope')
    parser.add_argument('--output-dir', default='output', help='Output directory')
    parser.add_argument('--cache-dir', default='.cache', help='Cache directory')
    parser.add_argument('--database', default='ao1_discovery_cmdb.db', help='Database file')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--timeout', type=int, default=600, help='Timeout per operation in seconds')
    parser.add_argument('--no-chronicle', action='store_true', help='Skip Chronicle project analysis')
    parser.add_argument('--fast-mode', action='store_true', help='Enable fast processing')
    parser.add_argument('--complete-fields', action='store_true', default=True, help='Ensure complete field population')
    parser.add_argument('--force-simple', action='store_true', help='Force use of simple engine')
    parser.add_argument('--verify-db', action='store_true', help='Verify database contents after discovery')
    
    return parser.parse_args()

async def verify_database_content(database_path: str) -> dict:
    """Verify that the database actually contains data"""
    try:
        import duckdb
        
        if not os.path.exists(database_path):
            return {'error': 'Database file does not exist', 'path': database_path}
        
        conn = duckdb.connect(database_path, read_only=True)
        
        verification = {
            'database_exists': True,
            'database_path': database_path,
            'file_size_mb': os.path.getsize(database_path) / (1024 * 1024),
            'tables': {},
            'total_records': 0
        }
        
        # Get all tables
        tables_result = conn.execute("SHOW TABLES").fetchall()
        
        for (table_name,) in tables_result:
            try:
                count_result = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
                record_count = count_result[0] if count_result else 0
                verification['tables'][table_name] = record_count
                verification['total_records'] += record_count
                
                if record_count > 0:
                    # Get a sample record to verify structure
                    sample = conn.execute(f"SELECT * FROM {table_name} LIMIT 1").fetchone()
                    if sample:
                        verification['tables'][f'{table_name}_sample'] = len(sample)
                        
            except Exception as table_error:
                verification['tables'][table_name] = f'Error: {table_error}'
        
        conn.close()
        return verification
        
    except Exception as e:
        return {'error': f'Database verification failed: {e}'}

async def estimate_scope(project_id: str, config: dict, args):
    """Estimate discovery scope"""
    print("   ⋆ AO1 scope estimation...")
    
    try:
        from gcp_client import BigQueryClientManager
        
        client_manager = BigQueryClientManager(project_id)
        
        with client_manager.get_client() as client:
            datasets = list(client.list_datasets(project=project_id))
            
            estimate = {
                'total_datasets': len(datasets),
                'hostname_capable_tables': 0,
                'estimated_assets': 0,
                'estimated_processing_time': 0,
                'recommendations': []
            }
            
            total_tables = 0
            
            # Sample first 10 datasets for estimation
            for dataset in datasets[:10]:
                try:
                    dataset_ref = client.dataset(dataset.dataset_id, project=project_id)
                    tables = list(client.list_tables(dataset_ref))
                    total_tables += len(tables)
                    
                    for table_ref in tables[:5]:  # Sample 5 tables per dataset
                        try:
                            full_table = client.get_table(table_ref)
                            
                            if not full_table.schema or full_table.num_rows == 0:
                                continue
                            
                            columns = [field.name for field in full_table.schema]
                            
                            # Check for hostname indicators
                            hostname_indicators = ['host', 'endpoint', 'computer', 'device', 'server', 'machine', 'asset', 'node', 'system']
                            has_hostname = any(
                                any(indicator in col.lower() for indicator in hostname_indicators)
                                for col in columns
                            )
                            
                            if has_hostname:
                                estimate['hostname_capable_tables'] += 1
                                estimated_rows = min(full_table.num_rows or 0, 10000)
                                estimate['estimated_assets'] += int(estimated_rows * 0.6)
                                
                        except Exception:
                            continue
                            
                except Exception:
                    continue
            
            # Extrapolate for all datasets
            if len(datasets) > 10:
                extrapolation_factor = len(datasets) / 10
                estimate['hostname_capable_tables'] = int(estimate['hostname_capable_tables'] * extrapolation_factor)
                estimate['estimated_assets'] = int(estimate['estimated_assets'] * extrapolation_factor)
            
            # Estimate processing time
            if estimate['estimated_assets'] > 0:
                base_time = 60  # 1 minute baseline
                asset_time = estimate['estimated_assets'] / 100  # 1 second per 100 assets
                table_time = estimate['hostname_capable_tables'] * 2  # 2 seconds per table
                estimate['estimated_processing_time'] = base_time + asset_time + table_time
            
            # Generate recommendations
            if estimate['estimated_assets'] > 10000:
                estimate['recommendations'].append("Large scale deployment - use batch processing")
            elif estimate['estimated_assets'] > 1000:
                estimate['recommendations'].append("Medium scale deployment - optimal for parallel processing")
            else:
                estimate['recommendations'].append("Small scale deployment - consider increasing batch size")
            
            if estimate['hostname_capable_tables'] < 5:
                estimate['recommendations'].append("Limited hostname data detected - verify data sources")
            
            print(f"   ✧ Estimated datasets: {estimate['total_datasets']:,}")
            print(f"   ✧ Hostname-capable tables: {estimate['hostname_capable_tables']:,}")
            print(f"   ✧ Estimated assets: {estimate['estimated_assets']:,}")
            print(f"   ✧ Estimated time: {estimate['estimated_processing_time']:.1f} seconds")
            
            return estimate
            
    except Exception as e:
        print(f"   ✗ Scope estimation failed: {e}")
        return {'error': str(e)}

async def main():
    args = parse_arguments()
    
    if not args.project:
        print("   ✗ GCP Project ID is required")
        sys.exit(1)
    
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
        except Exception as e:
            print(f"   ✗ Configuration loading failed: {e}")
            sys.exit(1)
    
    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        print("   🐛 Debug mode enabled")
    
    # Ensure output directory exists
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    print("\n" + "="*80)
    print("   ♡ AO1 Log Visibility Measurement System ♡")
    print("="*80)
    print(f"   Project: {args.project}")
    print(f"   Database: {args.database}")
    print(f"   Batch Size: {args.batch_size:,}")
    print(f"   Max Workers: {args.max_workers}")
    print(f"   Memory Cache: {args.max_memory:,}MB")
    print(f"   Disk Cache: {args.max_disk}GB")
    
    try:
        # Handle dry run
        if args.dry_run:
            estimate = await estimate_scope(args.project, config, args)
            
            if 'error' in estimate:
                print(f"   ✗ Estimation failed: {estimate['error']}")
                sys.exit(1)
            
            estimate_file = output_dir / "scope_estimate.json"
            with open(estimate_file, 'w') as f:
                json.dump(estimate, f, indent=2, default=str)
            
            print(f"   ✅ Scope estimate saved: {estimate_file}")
            return
        
        # Initialize and run discovery
        runner = ReliableAO1Runner(args.project, args.config, args)
        
        print("   ⚡ Starting AO1 discovery...")
        
        try:
            stats, queries = await asyncio.wait_for(
                runner.execute_discovery(), 
                timeout=args.timeout * 3  # Give extra time for full discovery
            )
        except asyncio.TimeoutError:
            print(f"   ⚠ Discovery timed out after {args.timeout * 3} seconds")
            sys.exit(1)
        
        if 'error' in stats:
            print(f"   ✗ Discovery failed: {stats['error']}")
            sys.exit(1)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        stats_file = output_dir / f"discovery_results_{timestamp}.json"
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2, default=str)
        
        # Save queries
        if queries:
            queries_dir = output_dir / f"queries_{timestamp}"
            queries_dir.mkdir(exist_ok=True)
            
            for query_name, query_sql in queries.items():
                query_file = queries_dir / f"{query_name}.sql"
                with open(query_file, 'w') as f:
                    f.write(f"-- {query_name.replace('_', ' ').title()}\n")
                    f.write(f"-- Generated: {datetime.now().isoformat()}\n")
                    f.write(f"-- Database: {args.database}\n\n")
                    f.write(query_sql)
        
        # Verify database if requested
        if args.verify_db:
            print("   🔍 Verifying database contents...")
            verification = await verify_database_content(args.database)
            
            verification_file = output_dir / f"database_verification_{timestamp}.json"
            with open(verification_file, 'w') as f:
                json.dump(verification, f, indent=2, default=str)
            
            if 'error' in verification:
                print(f"   ⚠ Database verification failed: {verification['error']}")
            else:
                print(f"   ✅ Database verified: {verification['total_records']:,} total records")
                for table_name, count in verification['tables'].items():
                    if isinstance(count, int) and count > 0:
                        print(f"     - {table_name}: {count:,} records")
        
        # Print results
        print("\n" + "="*80)
        print("   ♡ AO1 Discovery Complete ♡")
        print("="*80)
        
        processing_time = stats.get('total_processing_time', 0)
        engine_type = stats.get('engine_type', 'Unknown')
        total_assets = stats.get('total_assets', 0)
        
        print(f"   Engine: {engine_type}")
        print(f"   Processing time: {processing_time:.2f} seconds")
        print(f"   Total assets: {total_assets:,}")
        
        if 'high_coverage_assets' in stats:
            print(f"   High coverage assets: {stats['high_coverage_assets']:,}")
        
        print(f"\n   Output Files:")
        print(f"   📊 Results: {stats_file}")
        if queries:
            print(f"   📝 Queries: {queries_dir}")
        print(f"   🗄️ Database: {args.database}")
        
        if args.verify_db and 'verification' in locals():
            print(f"   🔍 Verification: {verification_file}")
        
        if total_assets == 0:
            print("\n   ⚠ WARNING: No assets discovered!")
            print("   This could indicate:")
            print("     - Authentication issues")
            print("     - No suitable data in the project")
            print("     - Insufficient permissions")
            print("   Try running with --debug for more information")
        else:
            print(f"\n   ✅ Success! {total_assets:,} assets discovered")
            if processing_time > 0:
                rate = total_assets / processing_time
                print(f"   ⚡ Processing rate: {rate:.1f} assets/second")
        
    except KeyboardInterrupt:
        print("\n\n   ⚠ Discovery interrupted by user")
        sys.exit(130)
        
    except Exception as e:
        print(f"\n   ✗ Discovery failed: {e}")
        
        error_file = output_dir / f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(error_file, 'w') as f:
            json.dump({
                'error': str(e),
                'type': type(e).__name__,
                'timestamp': datetime.now().isoformat(),
                'project': args.project,
                'config': config,
                'args': vars(args)
            }, f, indent=2)
        
        print(f"   Error details saved: {error_file}")
        
        if args.debug:
            import traceback
            print("\n   🐛 Full traceback:")
            traceback.print_exc()
        
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n   ⚠ Interrupted by user")
        sys.exit(130)