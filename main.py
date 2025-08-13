# main.py

import asyncio
import logging
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from core.types import Discovery
from gcp.client import BigQueryClientManager
from cache.system import IntelligentCache
from ai.intelligence import IntelligenceEngine
from discovery.core import DiscoveryEngine
from discovery.content import ContentBasedEngine, UniversalTableScanner
from discovery.ao1 import AO1SuperEngine
from storage.database import DatabaseManager, ContentDatabase

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SmartDiscoverySystem:
    def __init__(self, project_id: str, config: Dict[str, Any]):
        self.project_id = project_id
        self.config = config
        
        self.cache = IntelligentCache(
            cache_dir=config.get('cache_dir', '.cache'),
            max_memory_mb=config.get('max_memory_mb', 2048),
            max_disk_gb=config.get('max_disk_gb', 20)
        )
        
        self.intelligence = IntelligenceEngine(config)
        
        self.client_managers = {}
        self._init_clients()
        
        self.discovery_engine = DiscoveryEngine(project_id, config, self.cache, self.intelligence)
        self.content_engine = ContentBasedEngine(project_id, config, self.cache, self.intelligence)
        self.ao1_engine = AO1SuperEngine(config)
        self.scanner = UniversalTableScanner(self.content_engine.analyzer)
        
        self.db = DatabaseManager(config.get('database_path', 'smart_cmdb.db'))
        self.content_db = ContentDatabase(config.get('content_db_path', 'content_cmdb.db'))
        
        self.stats = {
            'start_time': datetime.now(),
            'engines_used': [],
            'total_assets': 0,
            'processing_errors': 0
        }
    
    def _init_clients(self):
        try:
            self.client_managers[self.project_id] = BigQueryClientManager(self.project_id)
            logger.info(f"Connected to main project: {self.project_id}")
        except Exception as e:
            logger.error(f"Failed to connect to {self.project_id}: {e}")
            raise
        
        try:
            self.client_managers["chronicle-fisv"] = BigQueryClientManager("chronicle-fisv")
            logger.info("Connected to Chronicle project")
        except Exception as e:
            logger.warning(f"Chronicle not available: {e}")
    
    async def run_comprehensive_discovery(self) -> Dict[str, Any]:
        logger.info("Starting comprehensive smart discovery")
        
        results = {
            'metadata': {
                'start_time': self.stats['start_time'].isoformat(),
                'project_id': self.project_id,
                'config': {k: v for k, v in self.config.items() if not k.startswith('_')}
            }
        }
        
        try:
            context = await self._build_context()
            strategy = await self.intelligence.recommend_strategy(context)
            results['strategy'] = strategy
            
            if strategy['strategy'] == 'enterprise_parallel':
                results.update(await self._run_enterprise_discovery())
            elif strategy['strategy'] == 'large_scale':
                results.update(await self._run_large_scale_discovery())
            else:
                results.update(await self._run_standard_discovery())
            
            results['learning'] = await self.intelligence.learn_from_results(
                self._create_discovery_from_results(results),
                context
            )
            
        except Exception as e:
            logger.error(f"Discovery failed: {e}")
            results['error'] = str(e)
            self.stats['processing_errors'] += 1
        
        finally:
            results['final_stats'] = self._calculate_final_stats()
        
        return results
    
    async def _build_context(self) -> Dict[str, Any]:
        dataset_count = 0
        table_count = 0
        
        for project_id, client_manager in self.client_managers.items():
            try:
                with client_manager.get_client() as client:
                    datasets = list(client.list_datasets(project=project_id, max_results=100))
                    dataset_count += len(datasets)
                    
                    for dataset in datasets[:5]:
                        tables = list(client.list_tables(dataset, max_results=100))
                        table_count += len(tables)
            except Exception as e:
                logger.warning(f"Context building failed for {project_id}: {e}")
        
        return {
            'project_id': self.project_id,
            'dataset_count': dataset_count,
            'table_count': table_count,
            'has_chronicle': 'chronicle-fisv' in self.client_managers,
            'parallel_workers': self.config.get('max_workers', 16),
            'memory_limit_mb': self.config.get('max_memory_mb', 2048)
        }
    
    async def _run_enterprise_discovery(self) -> Dict[str, Any]:
        logger.info("Running enterprise-scale discovery")
        
        tasks = [
            self._run_intelligent_discovery(),
            self._run_ao1_discovery(),
            self._run_content_discovery()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            'intelligent_discovery': results[0] if not isinstance(results[0], Exception) else {'error': str(results[0])},
            'ao1_discovery': results[1] if not isinstance(results[1], Exception) else {'error': str(results[1])},
            'content_discovery': results[2] if not isinstance(results[2], Exception) else {'error': str(results[2])},
            'discovery_mode': 'enterprise_parallel'
        }
    
    async def _run_large_scale_discovery(self) -> Dict[str, Any]:
        logger.info("Running large-scale discovery")
        
        intelligent_results = await self._run_intelligent_discovery()
        ao1_results = await self._run_ao1_discovery()
        
        return {
            'intelligent_discovery': intelligent_results,
            'ao1_discovery': ao1_results,
            'discovery_mode': 'large_scale'
        }
    
    async def _run_standard_discovery(self) -> Dict[str, Any]:
        logger.info("Running standard discovery")
        
        intelligent_results = await self._run_intelligent_discovery()
        
        if intelligent_results.get('stats', {}).get('total_assets', 0) < 5000:
            content_results = await self._run_content_discovery()
            return {
                'intelligent_discovery': intelligent_results,
                'content_discovery': content_results,
                'discovery_mode': 'standard'
            }
        
        return {
            'intelligent_discovery': intelligent_results,
            'discovery_mode': 'intelligent_only'
        }
    
    async def _run_intelligent_discovery(self) -> Dict[str, Any]:
        logger.info("Executing intelligent discovery")
        
        try:
            discovery = await self.discovery_engine.discover_assets(self.client_managers)
            
            if discovery.assets:
                stored_count = self.db.store_discovery(discovery, "intelligent")
                discovery.stats['stored_assets'] = stored_count
                self.stats['total_assets'] += len(discovery.assets)
            
            self.stats['engines_used'].append('intelligent')
            
            return {
                'assets': {k: self._asset_to_dict(v) for k, v in discovery.assets.items()},
                'schemas': {k: self._schema_to_dict(v) for k, v in discovery.schemas.items()},
                'stats': discovery.stats,
                'insights': discovery.insights,
                'recommendations': discovery.recommendations
            }
            
        except Exception as e:
            logger.error(f"Intelligent discovery failed: {e}")
            return {'error': str(e)}
    
    async def _run_ao1_discovery(self) -> Dict[str, Any]:
        logger.info("Executing AO1 enhanced discovery")
        
        try:
            results = await self.ao1_engine.enhanced_discovery(self.client_managers)
            
            if results.get('assets'):
                self.stats['total_assets'] += len(results['assets'])
            
            self.stats['engines_used'].append('ao1')
            return results
            
        except Exception as e:
            logger.error(f"AO1 discovery failed: {e}")
            return {'error': str(e)}
    
    async def _run_content_discovery(self) -> Dict[str, Any]:
        logger.info("Executing content-based discovery")
        
        try:
            if self.config.get('use_universal_scanner', False):
                results = await self.scanner.scan_all_tables(self.client_managers)
            else:
                results = await self.content_engine.discover_all_content(self.client_managers)
            
            if results.get('assets'):
                stored_count = self.content_db.store_content_assets(results['assets'])
                results['stored_assets'] = stored_count
                self.stats['total_assets'] += len(results.get('assets', {}))
            
            self.stats['engines_used'].append('content')
            return results
            
        except Exception as e:
            logger.error(f"Content discovery failed: {e}")
            return {'error': str(e)}
    
    def _asset_to_dict(self, asset) -> Dict[str, Any]:
        return {
            'id': asset.id,
            'hostname': asset.hostname,
            'ip': asset.ip,
            'fqdn': asset.fqdn,
            'infra_type': asset.infra_type,
            'system_class': asset.system_class,
            'region': asset.region,
            'business_unit': asset.business_unit,
            'sources': asset.sources,
            'intelligence': asset.intelligence,
            'quality': asset.quality,
            'confidence': asset.confidence,
            'cmdb': asset.cmdb,
            'splunk': asset.splunk,
            'chronicle': asset.chronicle,
            'crowdstrike': asset.crowdstrike,
            'edr': asset.edr,
            'dlp': asset.dlp
        }
    
    def _schema_to_dict(self, schema) -> Dict[str, Any]:
        return {
            'path': schema.path,
            'name': schema.name,
            'quality': schema.quality,
            'rows': schema.rows,
            'columns': schema.columns,
            'mappings': {k: {
                'field_type': v.field_type,
                'column': v.column,
                'confidence': v.confidence
            } for k, v in schema.mappings.items()}
        }
    
    def _create_discovery_from_results(self, results: Dict[str, Any]) -> Discovery:
        discovery = Discovery()
        
        if 'intelligent_discovery' in results:
            intelligent = results['intelligent_discovery']
            discovery.stats.update(intelligent.get('stats', {}))
        
        return discovery
    
    def _calculate_final_stats(self) -> Dict[str, Any]:
        processing_time = (datetime.now() - self.stats['start_time']).total_seconds()
        
        return {
            'total_processing_time_seconds': processing_time,
            'total_assets_discovered': self.stats['total_assets'],
            'engines_used': self.stats['engines_used'],
            'processing_errors': self.stats['processing_errors'],
            'cache_stats': self.cache.get_stats(),
            'assets_per_second': self.stats['total_assets'] / max(processing_time, 1)
        }
    
    def generate_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'executive_summary': {
                'discovery_timestamp': datetime.now().isoformat(),
                'project_id': self.project_id,
                'total_assets': self.stats['total_assets'],
                'engines_used': self.stats['engines_used'],
                'processing_time_minutes': results.get('final_stats', {}).get('total_processing_time_seconds', 0) / 60
            },
            'asset_summary': self._generate_asset_summary(results),
            'visibility_analysis': self._extract_visibility_analysis(results),
            'recommendations': self._aggregate_recommendations(results),
            'database_files': [self.db.db_path, self.content_db.db_path]
        }
    
    def _generate_asset_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        summary = {'total_discovered': self.stats['total_assets']}
        
        if 'intelligent_discovery' in results:
            intelligent = results['intelligent_discovery']
            stats = intelligent.get('stats', {})
            summary.update({
                'intelligent_assets': stats.get('total_assets', 0),
                'high_quality_assets': stats.get('high_quality_assets', 0),
                'multi_source_assets': stats.get('multi_source_assets', 0)
            })
        
        if 'content_discovery' in results:
            content = results['content_discovery']
            summary['content_assets'] = len(content.get('assets', {}))
        
        if 'ao1_discovery' in results:
            ao1 = results['ao1_discovery']
            summary['ao1_assets'] = ao1.get('discovery_stats', {}).get('total_assets', 0)
        
        return summary
    
    def _extract_visibility_analysis(self, results: Dict[str, Any]) -> Dict[str, Any]:
        visibility = {}
        
        if 'ao1_discovery' in results:
            ao1 = results['ao1_discovery']
            visibility = ao1.get('visibility_analysis', {})
        
        return visibility
    
    def _aggregate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        all_recommendations = []
        
        for engine_name in ['intelligent_discovery', 'ao1_discovery', 'content_discovery']:
            if engine_name in results:
                engine_results = results[engine_name]
                recommendations = engine_results.get('recommendations', [])
                all_recommendations.extend(recommendations)
        
        return list(set(all_recommendations))
    
    def close(self):
        try:
            self.cache.clear()
            self.db.close()
            self.content_db.close()
            logger.info("System shutdown complete")
        except Exception as e:
            logger.error(f"Shutdown error: {e}")

def load_config(config_file: str = None) -> Dict[str, Any]:
    default_config = {
        'max_memory_mb': 2048,
        'max_disk_gb': 20,
        'cache_dir': '.cache',
        'database_path': 'smart_cmdb.db',
        'content_db_path': 'content_cmdb.db',
        'max_workers': 16,
        'enable_machine_learning': True,
        'use_universal_scanner': False
    }
    
    if config_file and Path(config_file).exists():
        try:
            import yaml
            with open(config_file, 'r') as f:
                user_config = yaml.safe_load(f)
                default_config.update(user_config)
        except Exception as e:
            logger.warning(f"Config load failed: {e}")
    
    return default_config

def parse_args():
    parser = argparse.ArgumentParser(description="Smart Discovery System")
    parser.add_argument('--project', '-p', required=True, help='GCP Project ID')
    parser.add_argument('--config', '-c', help='Config file path')
    parser.add_argument('--output', '-o', default='output', help='Output directory')
    parser.add_argument('--memory', type=int, default=2048, help='Max memory MB')
    parser.add_argument('--disk', type=int, default=20, help='Max disk GB')
    parser.add_argument('--workers', type=int, default=16, help='Parallel workers')
    parser.add_argument('--debug', action='store_true', help='Debug mode')
    parser.add_argument('--dry-run', action='store_true', help='Estimation only')
    return parser.parse_args()

async def main():
    args = parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    config = load_config(args.config)
    config.update({
        'max_memory_mb': args.memory,
        'max_disk_gb': args.disk,
        'max_workers': args.workers,
        'output_dir': args.output
    })
    
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)
    
    logger.info(f"Smart Discovery System - Project: {args.project}")
    logger.info(f"Memory: {args.memory}MB, Disk: {args.disk}GB, Workers: {args.workers}")
    
    system = None
    try:
        system = SmartDiscoverySystem(args.project, config)
        
        if args.dry_run:
            context = await system._build_context()
            predictions = await system.intelligence.predict_discovery_outcomes(context)
            
            logger.info("Dry run estimates:")
            logger.info(f"  Datasets: {context['dataset_count']}")
            logger.info(f"  Tables: {context['table_count']}")
            logger.info(f"  Estimated assets: {predictions['estimated_assets']}")
            logger.info(f"  Processing time: {predictions['processing_time_seconds']/60:.1f} minutes")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dry_run_file = output_dir / f"dry_run_{timestamp}.json"
            
            with open(dry_run_file, 'w') as f:
                json.dump({
                    'context': context,
                    'predictions': predictions,
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2)
            
            logger.info(f"Dry run saved: {dry_run_file}")
            return 0
        
        results = await system.run_comprehensive_discovery()
        report = system.generate_report(results)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        results_file = output_dir / f"discovery_results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        report_file = output_dir / f"discovery_report_{timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Discovery completed successfully")
        logger.info(f"Results: {results_file}")
        logger.info(f"Report: {report_file}")
        logger.info(f"Assets discovered: {system.stats['total_assets']:,}")
        logger.info(f"Engines used: {', '.join(system.stats['engines_used'])}")
        
        return 0
        
    except KeyboardInterrupt:
        logger.warning("Discovery interrupted")
        return 130
    
    except Exception as e:
        logger.error(f"Discovery failed: {e}")
        
        if args.debug:
            import traceback
            traceback.print_exc()
        
        return 1
    
    finally:
        if system:
            system.close()

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)