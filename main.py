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

try:
    from enhanced_discovery_engine import SuperIntelligentAO1Discovery
except ImportError:
    from discovery_engine import IntelligentAO1Discovery as SuperIntelligentAO1Discovery

from config_loader import ConfigLoader

logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IntelligentAO1Runner:
    def __init__(self, project_id: str, config_file: str = None):
        self.project_id = project_id
        self.config = ConfigLoader.load_config(config_file)
        
        try:
            self.engine = SuperIntelligentAO1Discovery(project_id, self.config)
        except Exception as e:
            print(f"   ⚠°｡⋆⸜ ♡   Falling back to basic intelligent discovery: {e}")
            from discovery_engine import IntelligentAO1Discovery
            self.engine = IntelligentAO1Discovery(project_id, self.config)
        
        self.shutdown_requested = False
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        print(f"\n   ⚠°｡⋆⸜ ♡   Received signal {signum}, initiating intelligent shutdown...")
        self.shutdown_requested = True
        if hasattr(self.engine, 'signal_handler'):
            self.engine.signal_handler.shutdown_requested = True
    
    async def execute_intelligent_discovery(self):
        start_time = time.time()
        
        try:
            if hasattr(self.engine, 'execute_super_intelligent_discovery'):
                stats, queries = await self.engine.execute_super_intelligent_discovery()
            else:
                stats, queries = await self.engine.execute_intelligent_discovery()
                
            processing_time = time.time() - start_time
            stats['total_processing_time'] = processing_time
            return stats, queries
        except Exception as e:
            print(f"   ✗°｡⋆⸜ ♡   Intelligent discovery failed: {e}")
            return {'error': str(e)}, {}
        finally:
            if hasattr(self.engine, 'close'):
                self.engine.close()

def parse_arguments():
    parser = argparse.ArgumentParser(description="Intelligent AO1 Log Visibility Measurement System")
    
    parser.add_argument('--project', '-p', required=True, help='GCP Project ID')
    parser.add_argument('--config', '-c', help='Configuration file')
    parser.add_argument('--max-memory', type=int, default=1024, help='Max memory cache (MB)')
    parser.add_argument('--max-disk', type=int, default=10, help='Max disk cache (GB)')
    parser.add_argument('--dry-run', action='store_true', help='Estimate scope with intelligence')
    parser.add_argument('--output-dir', default='output', help='Output directory')
    parser.add_argument('--cache-dir', default='.cache', help='Intelligent cache directory')
    parser.add_argument('--database', default='ao1_intelligent_cmdb.db', help='Intelligent database file')
    parser.add_argument('--intelligence-level', choices=['basic', 'advanced', 'expert', 'super'], default='expert', help='Intelligence analysis level')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode with verbose output')
    parser.add_argument('--timeout', type=int, default=600, help='Timeout per operation in seconds')
    
    return parser.parse_args()

async def estimate_intelligent_scope(project_id: str, config: dict):
    print("   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Intelligent scope estimation with deep analysis...")
    
    try:
        from gcp_client import BigQueryClientManager
        from intelligent_content_matcher import IntelligentContentMatcher
        
        client_manager = BigQueryClientManager(project_id)
        matcher = IntelligentContentMatcher()
        
        with client_manager.get_client() as client:
            datasets = list(client.list_datasets(project=project_id))
            
            intelligent_analysis = {
                'total_datasets': len(datasets),
                'intelligent_tables': 0,
                'hostname_capable_tables': 0,
                'estimated_endpoints': 0,
                'data_richness_scores': [],
                'intelligence_recommendations': [],
                'ml_feasibility': False,
                'network_analysis_potential': False
            }
            
            for dataset in datasets[:15]:
                try:
                    dataset_ref = client.dataset(dataset.dataset_id, project=project_id)
                    tables = list(client.list_tables(dataset_ref))
                    
                    for table_ref in tables[:10]:
                        try:
                            full_table = client.get_table(table_ref)
                            
                            if not full_table.schema or full_table.num_rows == 0:
                                continue
                            
                            all_columns = [field.name for field in full_table.schema]
                            
                            sample_query = f"SELECT * FROM `{project_id}.{dataset.dataset_id}.{table_ref.table_id}` LIMIT 5"
                            try:
                                sample_job = client.query(sample_query)
                                sample_results = list(sample_job.result())
                                
                                sample_data = {}
                                for row in sample_results:
                                    for i, value in enumerate(row):
                                        if i < len(all_columns) and value is not None:
                                            column_name = all_columns[i]
                                            if column_name not in sample_data:
                                                sample_data[column_name] = []
                                            sample_data[column_name].append(str(value))
                                
                            except:
                                sample_data = {}
                            
                            categorized = matcher.intelligently_categorize_all_columns(all_columns, sample_data)
                            
                            has_hostname = 'hostname' in categorized or 'fqdn' in categorized
                            data_richness = len(categorized) / max(len(all_columns), 1)
                            
                            if has_hostname:
                                intelligent_analysis['hostname_capable_tables'] += 1
                                
                                estimated_rows = min(full_table.num_rows or 0, 100000)
                                endpoint_estimate = int(estimated_rows * 0.7)
                                intelligent_analysis['estimated_endpoints'] += endpoint_estimate
                            
                            if data_richness > 0.2:
                                intelligent_analysis['intelligent_tables'] += 1
                                intelligent_analysis['data_richness_scores'].append(data_richness)
                                
                                if data_richness > 0.4 and has_hostname:
                                    intelligent_analysis['ml_feasibility'] = True
                                
                                network_indicators = sum(1 for col in all_columns 
                                                        if any(net_term in col.lower() 
                                                              for net_term in ['ip', 'mac', 'network', 'subnet']))
                                if network_indicators > 2:
                                    intelligent_analysis['network_analysis_potential'] = True
                            
                        except Exception:
                            continue
                            
                except Exception:
                    continue
            
            if intelligent_analysis['estimated_endpoints'] > 10000:
                intelligent_analysis['intelligence_recommendations'].append("Excellent endpoint coverage detected - comprehensive discovery possible")
            elif intelligent_analysis['estimated_endpoints'] > 2000:
                intelligent_analysis['intelligence_recommendations'].append("Good endpoint coverage expected - advanced analytics feasible")
            else:
                intelligent_analysis['intelligence_recommendations'].append("Limited endpoint data - basic discovery recommended")
            
            if intelligent_analysis['data_richness_scores']:
                avg_richness = sum(intelligent_analysis['data_richness_scores']) / len(intelligent_analysis['data_richness_scores'])
                if avg_richness > 0.6:
                    intelligent_analysis['intelligence_recommendations'].append("High data richness - multi-dimensional analysis enabled")
                elif avg_richness > 0.4:
                    intelligent_analysis['intelligence_recommendations'].append("Moderate data richness - selective intelligence recommended")
                else:
                    intelligent_analysis['intelligence_recommendations'].append("Low data richness - basic intelligence only")
            
            if intelligent_analysis['ml_feasibility']:
                intelligent_analysis['intelligence_recommendations'].append("ML entity matching capabilities available")
            
            if intelligent_analysis['network_analysis_potential']:
                intelligent_analysis['intelligence_recommendations'].append("Network topology analysis enabled")
            
            try:
                chronicle_client = BigQueryClientManager("chronicle-fisv")
                with chronicle_client.get_client() as chronicle:
                    chronicle_datasets = list(chronicle.list_datasets())
                    intelligent_analysis['estimated_endpoints'] += len(chronicle_datasets) * 3000
                    intelligent_analysis['intelligence_recommendations'].append("Chronicle integration available for security enrichment")
            except:
                intelligent_analysis['intelligence_recommendations'].append("Chronicle unavailable - primary project only")
            
            print("   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Intelligent Scope Analysis:")
            print(f"   ✧･ﾟ: *✧･ﾟ:*   Total datasets: {intelligent_analysis['total_datasets']:,}")
            print(f"   ✧･ﾟ: *✧･ﾟ:*   Intelligent tables: {intelligent_analysis['intelligent_tables']:,}")
            print(f"   ✧･ﾟ: *✧･ﾟ:*   Hostname-capable tables: {intelligent_analysis['hostname_capable_tables']:,}")
            print(f"   ✧･ﾟ: *✧･ﾟ:*   Estimated endpoints: {intelligent_analysis['estimated_endpoints']:,}")
            print(f"   ✧･ﾟ: *✧･ﾟ:*   ML feasibility: {'Yes' if intelligent_analysis['ml_feasibility'] else 'No'}")
            print(f"   ✧･ﾟ: *✧･ﾟ:*   Network analysis potential: {'Yes' if intelligent_analysis['network_analysis_potential'] else 'No'}")
            
            if intelligent_analysis['data_richness_scores']:
                avg_richness = sum(intelligent_analysis['data_richness_scores']) / len(intelligent_analysis['data_richness_scores'])
                print(f"   ✧･ﾟ: *✧･ﾟ:*   Average data richness: {avg_richness:.2f}")
            
            print("\n   ♡˗ˏˋ ◞ ～   Intelligence Recommendations:")
            for rec in intelligent_analysis['intelligence_recommendations']:
                print(f"   ･ﾟ✧ ◞ ♡   {rec}")
            
            return intelligent_analysis
            
    except Exception as e:
        print(f"   ✗°｡⋆⸜ ♡   Intelligent estimation failed: {e}")
        return {'error': str(e)}

async def main():
    args = parse_arguments()
    
    if not args.project:
        print("   ✗°｡⋆⸜ ♡   GCP Project ID is required for intelligent discovery")
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
    
    config.update({
        'max_memory_mb': args.max_memory,
        'max_disk_gb': args.max_disk,
        'cache_dir': args.cache_dir,
        'database_path': args.database,
        'intelligence_level': args.intelligence_level,
        'debug_mode': args.debug,
        'operation_timeout': args.timeout
    })
    
    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        print("   🐛 Debug mode enabled - verbose output activated")
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    print("   ♡₊˚ ｡⋅˚♡ ✧ ‧₊˚ ⋅   Intelligent AO1 Log Visibility Measurement   ⋅ ˚₊‧ ✧ ♡˚⋅｡ ˚₊♡")
    print(f"   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Project: {args.project}")
    print(f"   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Intelligence Level: {args.intelligence_level}")
    print(f"   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Database: {args.database}")
    print(f"   ⋆｡‧˚ʚ♡ɞ˚‧ ｡°❀   Memory Cache: {args.max_memory}MB")
    print(f"   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Disk Cache: {args.max_disk}GB")
    
    try:
        if args.dry_run:
            estimate = await estimate_intelligent_scope(args.project, config)
            
            if 'error' in estimate:
                print(f"   ✗°｡⋆⸜ ♡   Intelligent estimation failed: {estimate['error']}")
                sys.exit(1)
            
            estimate_file = output_dir / "intelligent_scope_estimate.json"
            with open(estimate_file, 'w') as f:
                json.dump(estimate, f, indent=2)
            
            print(f"   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Intelligent scope estimate saved: {estimate_file}")
            
            if estimate['estimated_endpoints'] > 5000:
                print("   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Excellent scale for intelligent discovery. Run without --dry-run to proceed.")
            elif estimate['estimated_endpoints'] > 1000:
                print("   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Good scale for intelligent discovery with advanced capabilities.")
            else:
                print("   ⚠°｡⋆⸜ ♡   Limited scale detected - basic intelligent mode recommended.")
            return
        
        runner = IntelligentAO1Runner(args.project, args.config)
        
        print("   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Starting intelligent multi-dimensional discovery")
        
        stats, queries = await runner.execute_intelligent_discovery()
        
        if 'error' in stats:
            print(f"   ✗°｡⋆⸜ ♡   Intelligent discovery failed: {stats['error']}")
            sys.exit(1)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        stats_file = output_dir / f"intelligent_discovery_results_{timestamp}.json"
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2, default=str)
        
        queries_dir = output_dir / f"intelligent_queries_{timestamp}"
        queries_dir.mkdir(exist_ok=True)
        
        for query_name, query_sql in queries.items():
            query_file = queries_dir / f"{query_name}.sql"
            with open(query_file, 'w') as f:
                f.write(f"-- {query_name.replace('_', ' ').title()}\n")
                f.write(f"-- Intelligent AO1 Log Visibility Measurement\n")
                f.write(f"-- Project: {args.project}\n")
                f.write(f"-- Intelligence Level: {args.intelligence_level}\n")
                f.write(f"-- Generated: {datetime.now().isoformat()}\n")
                f.write(f"-- Database: {args.database}\n\n")
                f.write(query_sql)
        
        latest_stats = output_dir / "latest_intelligent_results.json"
        latest_queries = output_dir / "latest_intelligent_queries"
        
        if latest_stats.exists() or latest_stats.is_symlink():
            latest_stats.unlink()
        if latest_queries.exists() or latest_queries.is_symlink():
            latest_queries.unlink()
        
        latest_stats.symlink_to(stats_file.name)
        latest_queries.symlink_to(queries_dir.name)
        
        print("\n" + "="*90)
        print("   ♡₊˚ ｡⋅˚♡ ✧ ‧₊˚ ⋅   Intelligent Discovery Complete   ⋅ ˚₊‧ ✧ ♡˚⋅｡ ˚₊♡")
        print("="*90)
        
        processing_stats = stats.get('processing_stats', {})
        intelligence_stats = stats.get('intelligence_stats', {})
        cache_stats = stats.get('cache_performance', {})
        
        print(f"   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Total processing time: {stats.get('total_processing_time', 0):.2f} seconds")
        
        if 'fingerprints_created' in processing_stats:
            print(f"   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Advanced fingerprints: {processing_stats.get('fingerprints_created', 0):,}")
            print(f"   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Entity clusters: {processing_stats.get('entity_clusters', 0):,}")
            print(f"   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Consolidated assets: {intelligence_stats.get('consolidated_assets', 0):,}")
            print(f"   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Intelligence confidence: {intelligence_stats.get('avg_intelligence_confidence', 0):.3f}")
        else:
            print(f"   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Endpoints discovered: {stats.get('total_endpoints_discovered', 0):,}")
            print(f"   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Consolidated assets: {stats.get('consolidated_assets', 0):,}")
            print(f"   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Total data points: {stats.get('total_data_points', 0):,}")
            print(f"   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Average intelligence score: {stats.get('avg_intelligence_score', 0):.2f}")
        
        if cache_stats:
            hit_rate = cache_stats.get('hit_rate', 0)
            memory_usage = cache_stats.get('memory_usage_mb', 0)
            print(f"   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Cache hit rate: {hit_rate}%")
            print(f"   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Memory usage: {memory_usage:.1f}MB")
        
        print("\n   ｡･:*:･ﾟ★   Intelligent Output Files:")
        print(f"   ◦ ❀ ◦   Intelligent results: {stats_file}")
        print(f"   ◦ ❀ ◦   Latest results: {latest_stats}")
        print(f"   ◦ ❀ ◦   Intelligent queries: {queries_dir}")
        print(f"   ◦ ❀ ◦   Latest queries: {latest_queries}")
        print(f"   ◦ ❀ ◦   Intelligent database: {args.database}")
        
        total_assets = stats.get('consolidated_assets', 0) or intelligence_stats.get('consolidated_assets', 0)
        avg_intelligence = stats.get('avg_intelligence_score', 0) or intelligence_stats.get('avg_intelligence_confidence', 0)
        
        if total_assets > 0:
            print(f"\n   ❀°｡ ‧˚♡ ˚‧ ｡°❀   Success! Intelligent CMDB built with {total_assets:,} assets")
            
            if avg_intelligence >= 0.9:
                print("   ❀°｡ ‧˚♡ ˚‧ ｡°❀   🌟 EXCEPTIONAL intelligence quality achieved!")
            elif avg_intelligence >= 0.8:
                print("   ❀°｡ ‧˚♡ ˚‧ ｡°❀   ✨ EXCELLENT intelligence quality achieved!")
            elif avg_intelligence >= 0.7:
                print("   ❀°｡ ‧˚♡ ˚‧ ｡°❀   💫 HIGH intelligence quality with comprehensive data")
            elif avg_intelligence >= 0.6:
                print("   ❀°｡ ‧˚♡ ˚‧ ｡°❀   📊 GOOD intelligence quality with room for enrichment")
            else:
                print("   ⚠°｡⋆⸜ ♡   Intelligence gaps detected - consider additional data sources")
            
            print("   ❀°｡ ‧˚♡ ˚‧ ｡°❀   CSOC can now perform intelligent log visibility analysis")
            
            system_capabilities = stats.get('system_capabilities', {})
            if system_capabilities:
                print(f"\n   ｡･:*:･ﾟ★   Advanced Capabilities:")
                for capability, enabled in system_capabilities.items():
                    if enabled:
                        capability_name = capability.replace('_', ' ').title()
                        print(f"   ◦ ✨ ◦   {capability_name}")
        else:
            print("   ⚠°｡⋆⸜ ♡   No assets discovered - verify permissions and data sources")
        
        print("\n   ♡₊˚ ｡⋅˚♡ ✧ ‧₊˚ ⋅   Intelligent AO1 System Ready   ⋅ ˚₊‧ ✧ ♡˚⋅｡ ˚₊♡")
        
    except KeyboardInterrupt:
        print("\n\n   ⚠°｡⋆⸜ ♡   Intelligent discovery interrupted by user")
        print("   ･ﾟ✧ ◞ ♡   Intelligent cache preserved for faster restart")
        sys.exit(130)
        
    except Exception as e:
        print(f"\n   ✗°｡⋆⸜ ♡   Intelligent discovery failed: {e}")
        
        error_file = output_dir / f"intelligent_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(error_file, 'w') as f:
            json.dump({
                'error': str(e),
                'type': type(e).__name__,
                'timestamp': datetime.now().isoformat(),
                'project': args.project,
                'intelligence_level': args.intelligence_level,
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