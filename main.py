# main.py - enhanced version

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
from discovery.core import EnhancedDiscoveryEngine, ComprehensiveAssetBuilder
from discovery.content import ContentBasedEngine, UniversalTableScanner
from discovery.ao1 import AO1SuperEngine
from storage.database import DatabaseManager, ContentDatabase, EnhancedDatabaseManager

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
        
        self.discovery_engine = EnhancedDiscoveryEngine(project_id, config, self.cache, self.intelligence)
        self.content_engine = ContentBasedEngine(project_id, config, self.cache, self.intelligence)
        self.ao1_engine = AO1SuperEngine(config)
        self.scanner = UniversalTableScanner(self.content_engine.analyzer)
        
        self.db = EnhancedDatabaseManager(config.get('database_path', 'smart_cmdb.db'))
        self.content_db = ContentDatabase(config.get('content_db_path', 'content_cmdb.db'))
        
        self.stats = {
            'start_time': datetime.now(),
            'engines_used': [],
            'total_assets': 0,
            'processing_errors': 0,
            'comprehensive_mode': config.get('comprehensive_discovery', True)
        }
    
    def _init_clients(self):
        try:
            self.client_managers[self.project_id] = BigQueryClientManager(self.project_id)
            logger.info(f"Connected to main project: {self.project_id}")
        except Exception as e:
            logger.error(f"Failed to connect to {self.project_id}: {e}")
            raise
        
        additional_projects = self.config.get('additional_projects', ['chronicle-fisv'])
        for project in additional_projects:
            try:
                self.client_managers[project] = BigQueryClientManager(project)
                logger.info(f"Connected to additional project: {project}")
            except Exception as e:
                logger.warning(f"Additional project {project} not available: {e}")
    
    async def run_comprehensive_discovery(self) -> Dict[str, Any]:
        logger.info("Starting comprehensive smart discovery with entity resolution")
        
        results = {
            'metadata': {
                'start_time': self.stats['start_time'].isoformat(),
                'project_id': self.project_id,
                'comprehensive_mode': self.stats['comprehensive_mode'],
                'config': {k: v for k, v in self.config.items() if not k.startswith('_')}
            }
        }
        
        try:
            if self.stats['comprehensive_mode']:
                results.update(await self._run_comprehensive_mode())
            else:
                results.update(await self._run_legacy_mode())
            
        except Exception as e:
            logger.error(f"Discovery failed: {e}")
            results['error'] = str(e)
            self.stats['processing_errors'] += 1
        
        finally:
            results['final_stats'] = self._calculate_final_stats()
        
        return results
    
    async def _run_comprehensive_mode(self) -> Dict[str, Any]:
        logger.info("Running comprehensive entity-resolved discovery")
        
        try:
            discovery = await self.discovery_engine.discover_assets_comprehensively(self.client_managers)
            
            if discovery.assets:
                stored_count = self.db.store_comprehensive_discovery(discovery)
                discovery.stats['stored_assets'] = stored_count
                self.stats['total_assets'] += len(discovery.assets)
            
            self.stats['engines_used'].append('comprehensive')
            
            comprehensive_results = {
                'comprehensive_discovery': {
                    'assets': {k: self._asset_to_dict(v) for k, v in discovery.assets.items()},
                    'stats': discovery.stats,
                    'insights': discovery.insights,
                    'recommendations': discovery.recommendations
                },
                'discovery_mode': 'comprehensive_entity_resolution'
            }
            
            if self.config.get('enable_parallel_validation', False):
                validation_results = await self._run_validation_discovery()
                comprehensive_results['validation_discovery'] = validation_results
            
            return comprehensive_results
            
        except Exception as e:
            logger.error(f"Comprehensive discovery failed: {e}")
            return {'error': str(e)}
    
    async def _run_legacy_mode(self) -> Dict[str, Any]:
        logger.info("Running legacy discovery mode")
        
        context = await self._build_context()
        strategy = await self.intelligence.recommend_strategy(context)
        
        if strategy['strategy'] == 'enterprise_parallel':
            return await self._run_enterprise_discovery()
        elif strategy['strategy'] == 'large_scale':
            return await self._run_large_scale_discovery()
        else:
            return await self._run_standard_discovery()
    
    async def _run_validation_discovery(self) -> Dict[str, Any]:
        logger.info("Running validation discovery for comparison")
        
        tasks = [
            self._run_ao1_discovery(),
            self._run_content_discovery()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            'ao1_validation': results[0] if not isinstance(results[0], Exception) else {'error': str(results[0])},
            'content_validation': results[1] if not isinstance(results[1], Exception) else {'error': str(results[1])}
        }
    
    async def _build_context(self) -> Dict[str, Any]:
        dataset_count = 0
        table_count = 0
        total_rows = 0
        
        for project_id, client_manager in self.client_managers.items():
            try:
                with client_manager.get_client() as client:
                    datasets = list(client.list_datasets(project=project_id, max_results=200))
                    dataset_count += len(datasets)
                    
                    for dataset in datasets[:10]:
                        tables = list(client.list_tables(dataset, max_results=500))
                        table_count += len(tables)
                        
                        for table_ref in tables[:20]:
                            try:
                                table = client.get_table(table_ref)
                                if table.num_rows:
                                    total_rows += table.num_rows
                            except:
                                continue
                                
            except Exception as e:
                logger.warning(f"Context building failed for {project_id}: {e}")
        
        return {
            'project_id': self.project_id,
            'dataset_count': dataset_count,
            'table_count': table_count,
            'estimated_total_rows': total_rows,
            'has_chronicle': any('chronicle' in p for p in self.client_managers.keys()),
            'parallel_workers': self.config.get('max_workers', 16),
            'memory_limit_mb': self.config.get('max_memory_mb', 2048),
            'comprehensive_mode': self.stats['comprehensive_mode']
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
            from discovery.core import AdvancedSchemaAnalyzer, IntelligentAssetExtractor
            
            schema_analyzer = AdvancedSchemaAnalyzer(self.intelligence)
            asset_extractor = IntelligentAssetExtractor(self.intelligence)
            
            discovery = Discovery()
            all_assets = {}
            
            source_tables = {
                'cmdb': 'prj-fisv.SAS_BI.V_DIM_ENDPOINT',
                'splunk': 'prj-fisv.SAS_BI.V_SPL_ENDPOINT_LOG',
                'crowdstrike': 'prj-fisv.SAS_BI.V_DIM_ENDPOINTAGENT'
            }
            
            if 'chronicle-fisv' in self.client_managers:
                source_tables['chronicle'] = 'chronicle-fisv.datalake.events'
            
            for source_name, table_path in source_tables.items():
                try:
                    client_manager = self.client_managers.get('prj-fisv')
                    if source_name == 'chronicle' and 'chronicle-fisv' in self.client_managers:
                        client_manager = self.client_managers['chronicle-fisv']
                    
                    if not client_manager:
                        continue
                    
                    with client_manager.get_client() as client:
                        schema = await schema_analyzer.analyze_table_deeply(client, table_path)
                        
                        if schema:
                            discovery.schemas[table_path] = schema
                            
                            table_insights = schema_analyzer.table_insights.get(table_path, {})
                            
                            assets = await asset_extractor.extract_assets_intelligently(
                                client, schema, source_name, table_insights
                            )
                            
                            for asset_id, asset in assets.items():
                                if asset_id in all_assets:
                                    all_assets[asset_id] = self._merge_assets_intelligently(
                                        all_assets[asset_id], asset
                                    )
                                else:
                                    all_assets[asset_id] = asset
                
                except Exception as e:
                    logger.error(f"Intelligent processing failed for {source_name}: {e}")
            
            discovery.assets = all_assets
            
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
    
    def _merge_assets_intelligently(self, primary, secondary):
        from core.types import Asset
        
        merged = Asset(id=primary.id)
        
        text_fields = ['hostname', 'ip', 'fqdn', 'mac', 'infra_type', 'system_class',
                      'region', 'country', 'datacenter', 'cloud_region', 'business_unit',
                      'cio', 'app_class']
        
        for field in text_fields:
            primary_val = getattr(primary, field, "")
            secondary_val = getattr(secondary, field, "")
            
            if secondary_val and not primary_val:
                setattr(merged, field, secondary_val)
            elif primary_val:
                setattr(merged, field, primary_val)
            elif secondary_val and primary_val and len(secondary_val) > len(primary_val):
                setattr(merged, field, secondary_val)
            else:
                setattr(merged, field, primary_val)
        
        bool_fields = ['edr', 'dlp', 'tanium', 'splunk', 'chronicle', 'gso', 'cmdb', 'crowdstrike']
        for field in bool_fields:
            primary_val = getattr(primary, field, False)
            secondary_val = getattr(secondary, field, False)
            setattr(merged, field, primary_val or secondary_val)
        
        merged.sources = primary.sources + secondary.sources
        merged.intelligence = max(primary.intelligence, secondary.intelligence)
        merged.quality = max(primary.quality, secondary.quality)
        merged.confidence = (primary.confidence + secondary.confidence) / 2
        
        return merged
    
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
    
    def _calculate_final_stats(self) -> Dict[str, Any]:
        processing_time = (datetime.now() - self.stats['start_time']).total_seconds()
        
        return {
            'total_processing_time_seconds': processing_time,
            'total_assets_discovered': self.stats['total_assets'],
            'engines_used': self.stats['engines_used'],
            'processing_errors': self.stats['processing_errors'],
            'comprehensive_mode': self.stats['comprehensive_mode'],
            'cache_stats': self.cache.get_stats(),
            'assets_per_second': self.stats['total_assets'] / max(processing_time, 1)
        }
    
    def generate_comprehensive_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'executive_summary': {
                'discovery_timestamp': datetime.now().isoformat(),
                'project_id': self.project_id,
                'total_assets': self.stats['total_assets'],
                'discovery_mode': results.get('discovery_mode', 'unknown'),
                'engines_used': self.stats['engines_used'],
                'processing_time_minutes': results.get('final_stats', {}).get('total_processing_time_seconds', 0) / 60,
                'comprehensive_entity_resolution': self.stats['comprehensive_mode']
            },
            'asset_summary': self._generate_comprehensive_asset_summary(results),
            'visibility_analysis': self._extract_comprehensive_visibility_analysis(results),
            'coverage_metrics': self._calculate_coverage_metrics(results),
            'recommendations': self._aggregate_comprehensive_recommendations(results),
            'data_quality_assessment': self._assess_data_quality(results),
            'database_files': [self.db.db_path, self.content_db.db_path]
        }
    
    def _generate_comprehensive_asset_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        summary = {'total_discovered': self.stats['total_assets']}
        
        if 'comprehensive_discovery' in results:
            comp = results['comprehensive_discovery']
            stats = comp.get('stats', {})
            summary.update({
                'comprehensive_assets': stats.get('total_assets', 0),
                'high_quality_assets': stats.get('high_quality_assets', 0),
                'multi_source_assets': stats.get('multi_source_assets', 0),
                'cmdb_assets': stats.get('cmdb_assets', 0),
                'security_covered_assets': stats.get('security_covered_assets', 0),
                'entity_resolution_applied': stats.get('entity_resolution_applied', False)
            })
        
        return summary
    
    def _extract_comprehensive_visibility_analysis(self, results: Dict[str, Any]) -> Dict[str, Any]:
        visibility = {}
        
        if 'comprehensive_discovery' in results:
            assets = results['comprehensive_discovery'].get('assets', {})
            if assets:
                visibility.update(self._analyze_asset_visibility(assets))
        
        if 'ao1_discovery' in results:
            ao1 = results['ao1_discovery']
            visibility.update(ao1.get('visibility_analysis', {}))
        
        return visibility
    
    def _analyze_asset_visibility(self, assets: Dict[str, Any]) -> Dict[str, Any]:
        total = len(assets)
        if total == 0:
            return {}
        
        cmdb_count = sum(1 for a in assets.values() if a.get('cmdb', False))
        splunk_count = sum(1 for a in assets.values() if a.get('splunk', False))
        chronicle_count = sum(1 for a in assets.values() if a.get('chronicle', False))
        edr_count = sum(1 for a in assets.values() if a.get('edr', False))
        
        return {
            'total_assets': total,
            'cmdb_coverage_pct': round(100 * cmdb_count / total, 2),
            'splunk_coverage_pct': round(100 * splunk_count / total, 2),
            'chronicle_coverage_pct': round(100 * chronicle_count / total, 2),
            'edr_coverage_pct': round(100 * edr_count / total, 2),
            'multi_source_pct': round(100 * sum(1 for a in assets.values() if a.get('sources', 0) > 1) / total, 2)
        }
    
    def _calculate_coverage_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        metrics = {}
        
        if 'comprehensive_discovery' in results:
            assets = results['comprehensive_discovery'].get('assets', {})
            metrics['comprehensive_metrics'] = self._compute_coverage_metrics(assets)
        
        return metrics
    
    def _compute_coverage_metrics(self, assets: Dict[str, Any]) -> Dict[str, Any]:
        if not assets:
            return {}
        
        total = len(assets)
        infrastructure_types = defaultdict(int)
        regions = defaultdict(int)
        business_units = defaultdict(int)
        
        for asset in assets.values():
            if asset.get('infra_type'):
                infrastructure_types[asset['infra_type']] += 1
            if asset.get('region'):
                regions[asset['region']] += 1
            if asset.get('business_unit'):
                business_units[asset['business_unit']] += 1
        
        return {
            'infrastructure_distribution': dict(infrastructure_types),
            'regional_distribution': dict(regions),
            'business_unit_distribution': dict(business_units),
            'coverage_completeness': {
                'has_infrastructure_type': len(infrastructure_types) / total,
                'has_region': len(regions) / total,
                'has_business_unit': len(business_units) / total
            }
        }
    
    def _aggregate_comprehensive_recommendations(self, results: Dict[str, Any]) -> List[str]:
        all_recommendations = []
        
        for engine_name in ['comprehensive_discovery', 'intelligent_discovery', 'ao1_discovery', 'content_discovery']:
            if engine_name in results:
                engine_results = results[engine_name]
                recommendations = engine_results.get('recommendations', [])
                all_recommendations.extend(recommendations)
        
        all_recommendations.extend(self._generate_coverage_recommendations(results))
        
        return list(set(all_recommendations))
    
    def _generate_coverage_recommendations(self, results: Dict[str, Any]) -> List[str]:
        recommendations = []
        
        if 'comprehensive_discovery' in results:
            assets = results['comprehensive_discovery'].get('assets', {})
            
            if assets:
                total = len(assets)
                cmdb_count = sum(1 for a in assets.values() if a.get('cmdb', False))
                
                if cmdb_count / total < 0.8:
                    recommendations.append("CMDB coverage below 80% - consider CMDB data quality improvement")
                
                security_count = sum(1 for a in assets.values() if a.get('edr', False) or a.get('dlp', False))
                if security_count / total < 0.7:
                    recommendations.append("Security control coverage below 70% - review endpoint protection deployment")
        
        return recommendations
    
    def _assess_data_quality(self, results: Dict[str, Any]) -> Dict[str, Any]:
        quality_assessment = {}
        
        if 'comprehensive_discovery' in results:
            assets = results['comprehensive_discovery'].get('assets', {})
            quality_assessment['comprehensive_quality'] = self._compute_data_quality(assets)
        
        return quality_assessment
    
    def _compute_data_quality(self, assets: Dict[str, Any]) -> Dict[str, Any]:
        if not assets:
            return {}
        
        total = len(assets)
        quality_scores = [a.get('quality', 0) for a in assets.values()]
        confidence_scores = [a.get('confidence', 0) for a in assets.values()]
        
        return {
            'average_quality': sum(quality_scores) / len(quality_scores),
            'average_confidence': sum(confidence_scores) / len(confidence_scores),
            'high_quality_percentage': sum(1 for q in quality_scores if q > 0.8) / total,
            'high_confidence_percentage': sum(1 for c in confidence_scores if c > 0.8) / total
        }
    
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
        'max_memory_mb': 4096,
        'max_disk_gb': 50,
        'cache_dir': '.cache',
        'database_path': 'smart_cmdb.db',
        'content_db_path': 'content_cmdb.db',
        'max_workers': 32,
        'enable_machine_learning': True,
        'use_universal_scanner': False,
        'comprehensive_discovery': True,
        'enable_parallel_validation': False,
        'additional_projects': ['chronicle-fisv']
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
    parser = argparse.ArgumentParser(description="Smart Discovery System with Entity Resolution")
    parser.add_argument('--project', '-p', required=True, help='GCP Project ID')
    parser.add_argument('--config', '-c', help='Config file path')
    parser.add_argument('--output', '-o', default='output', help='Output directory')
    parser.add_argument('--memory', type=int, default=4096, help='Max memory MB')
    parser.add_argument('--disk', type=int, default=50, help='Max disk GB')
    parser.add_argument('--workers', type=int, default=32, help='Parallel workers')
    parser.add_argument('--debug', action='store_true', help='Debug mode')
    parser.add_argument('--dry-run', action='store_true', help='Estimation only')
    parser.add_argument('--comprehensive', action='store_true', default=True, help='Use comprehensive discovery')
    parser.add_argument('--legacy', action='store_true', help='Use legacy discovery mode')
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
        'output_dir': args.output,
        'comprehensive_discovery': not args.legacy
    })
    
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)
    
    logger.info(f"Smart Discovery System - Project: {args.project}")
    logger.info(f"Mode: {'Comprehensive Entity Resolution' if config['comprehensive_discovery'] else 'Legacy'}")
    logger.info(f"Memory: {args.memory}MB, Disk: {args.disk}GB, Workers: {args.workers}")
    
    system = None
    try:
        system = SmartDiscoverySystem(args.project, config)
        
        if args.dry_run:
            context = await system._build_context()
            
            logger.info("Dry run estimates:")
            logger.info(f"  Datasets: {context['dataset_count']}")
            logger.info(f"  Tables: {context['table_count']}")
            logger.info(f"  Estimated rows: {context.get('estimated_total_rows', 0):,}")
            logger.info(f"  Comprehensive mode: {context['comprehensive_mode']}")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dry_run_file = output_dir / f"dry_run_{timestamp}.json"
            
            with open(dry_run_file, 'w') as f:
                json.dump({
                    'context': context,
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2)
            
            logger.info(f"Dry run saved: {dry_run_file}")
            return 0
        
        results = await system.run_comprehensive_discovery()
        report = system.generate_comprehensive_report(results)
        
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
        logger.info(f"Mode: {'Comprehensive' if system.stats['comprehensive_mode'] else 'Legacy'}")
        
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