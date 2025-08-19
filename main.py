# main.py

import asyncio
import logging
import json
import argparse
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

from core.types import HyperAsset, QuantumDiscovery
from gcp.client import BigQueryClientManager
from cache.system import IntelligentCache
from ai.intelligence import QuantumIntelligenceEngine
from ai.content import QuantumContentAnalyzer
from ai.training_orchestrator import IntensiveTrainingOrchestrator
from discovery.ao1 import AO1SuperEngine
from discovery.content import QuantumContentBasedEngine
from discovery.core import QuantumHyperDiscoveryEngine
from storage.database import QuantumEnhancedDatabaseManager

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('discovery.log')
    ]
)
logger = logging.getLogger(__name__)

class UltimateQuantumDiscoverySystem:
    def __init__(self, project_id: str, config: Dict[str, Any]):
        self.project_id = project_id
        self.config = config
        self.start_time = datetime.now()
        
        self.cache = IntelligentCache(
            cache_dir=config.get('cache_dir', '.cache'),
            max_memory_mb=config.get('max_memory_mb', 8192),
            max_disk_gb=config.get('max_disk_gb', 100)
        )
        
        self.intelligence = QuantumIntelligenceEngine(config)
        self.content_analyzer = QuantumContentAnalyzer()
        self.training_orchestrator = IntensiveTrainingOrchestrator()
        
        self.client_managers = {}
        self._initialize_clients()
        
        self.discovery_engines = {
            'ao1': AO1SuperEngine(config),
            'content': QuantumContentBasedEngine(project_id, config, self.cache, self.intelligence),
            'core': QuantumHyperDiscoveryEngine(project_id, config, self.cache, self.intelligence)
        }
        
        self.database = QuantumEnhancedDatabaseManager(
            config.get('database_path', 'quantum_discovery.db')
        )
        
        self.stats = {
            'total_assets_discovered': 0,
            'total_tables_processed': 0,
            'total_rows_processed': 0,
            'ml_predictions_made': 0,
            'high_confidence_predictions': 0,
            'coverage_flags_set': 0,
            'processing_errors': 0
        }
    
    def _initialize_clients(self):
        primary_projects = [self.project_id]
        additional_projects = self.config.get('additional_projects', [
            'chronicle-fisv', 'fisv-security', 'fisv-logs', 'fisv-data'
        ])
        
        all_projects = primary_projects + additional_projects
        
        for project in all_projects:
            try:
                self.client_managers[project] = BigQueryClientManager(project)
                logger.info(f"Connected to project: {project}")
            except Exception as e:
                logger.warning(f"Failed to connect to {project}: {e}")
    
    async def initialize_ml_training(self) -> bool:
        if not self.config.get('enable_machine_learning', True):
            return False
        
        logger.info("Initializing ML training systems")
        
        try:
            training_success = await self.training_orchestrator.perform_intensive_initial_training()
            if training_success:
                self.training_orchestrator.start_continuous_learning()
                await self.content_analyzer.start_intensive_training()
                logger.info("ML training completed successfully")
                return True
        except Exception as e:
            logger.error(f"ML training failed: {e}")
        
        return False
    
    async def run_comprehensive_discovery(self) -> Dict[str, Any]:
        logger.info("Starting comprehensive quantum discovery")
        
        ml_enabled = await self.initialize_ml_training()
        
        all_assets = {}
        discovery_results = {}
        
        for engine_name, engine in self.discovery_engines.items():
            try:
                logger.info(f"Running {engine_name} discovery engine")
                
                if engine_name == 'ao1':
                    result = await engine.enhanced_discovery(self.client_managers)
                elif engine_name == 'content':
                    result = await engine.discover_all_quantum_content(self.client_managers)
                elif engine_name == 'core':
                    result = await engine.discover_assets_quantum_intensively(self.client_managers)
                
                discovery_results[engine_name] = result
                
                if engine_name == 'ao1' and 'assets' in result:
                    assets = result['assets']
                elif engine_name == 'content' and 'quantum_assets' in result:
                    assets = result['quantum_assets']
                elif engine_name == 'core' and hasattr(result, 'hyper_assets'):
                    assets = {k: self._hyper_asset_to_dict(v) for k, v in result.hyper_assets.items()}
                else:
                    assets = {}
                
                for asset_id, asset_data in assets.items():
                    if asset_id in all_assets:
                        all_assets[asset_id] = self._merge_asset_data(all_assets[asset_id], asset_data)
                    else:
                        all_assets[asset_id] = asset_data
                
                self.stats['total_assets_discovered'] = len(all_assets)
                logger.info(f"{engine_name} completed: {len(assets)} assets, total: {len(all_assets)}")
                
            except Exception as e:
                logger.error(f"{engine_name} engine failed: {e}")
                self.stats['processing_errors'] += 1
        
        enhanced_assets = await self._enhance_all_assets(all_assets)
        
        stored_count = self.database.store_comprehensive_discovery_results(enhanced_assets, self.stats)
        
        self.stats['database_storage_count'] = stored_count
        processing_time = (datetime.now() - self.start_time).total_seconds()
        
        final_results = {
            'discovery_metadata': {
                'timestamp': datetime.now().isoformat(),
                'project_id': self.project_id,
                'processing_time_seconds': processing_time,
                'ml_enabled': ml_enabled,
                'engines_used': list(self.discovery_engines.keys()),
                'projects_scanned': list(self.client_managers.keys())
            },
            'statistics': self.stats,
            'assets': enhanced_assets,
            'discovery_results': discovery_results,
            'database_stats': self.database.get_comprehensive_stats()
        }
        
        return final_results
    
    async def _enhance_all_assets(self, assets: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Enhancing {len(assets)} assets with ML and intelligence")
        
        enhanced = {}
        
        for asset_id, asset_data in assets.items():
            try:
                enhanced_asset = await self._enhance_single_asset(asset_id, asset_data)
                enhanced[asset_id] = enhanced_asset
            except Exception as e:
                logger.error(f"Failed to enhance asset {asset_id}: {e}")
                enhanced[asset_id] = asset_data
        
        return enhanced
    
    async def _enhance_single_asset(self, asset_id: str, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        enhanced = asset_data.copy()
        
        hostname = enhanced.get('hostname', '')
        all_data = enhanced.get('all_data', {})
        
        if hostname and self.content_analyzer:
            try:
                field_analysis = self.content_analyzer.analyze_column('hostname', [hostname])
                if field_analysis:
                    enhanced['ml_confidence'] = field_analysis[1]
                    enhanced['ml_metadata'] = field_analysis[2]
                    self.stats['ml_predictions_made'] += 1
                    if field_analysis[1] > 0.8:
                        self.stats['high_confidence_predictions'] += 1
            except Exception as e:
                logger.debug(f"ML analysis failed for {hostname}: {e}")
        
        enhanced['visibility_score'] = self._calculate_visibility_score(enhanced)
        enhanced['quality_score'] = self._calculate_quality_score(enhanced)
        enhanced['confidence_score'] = self._calculate_confidence_score(enhanced)
        enhanced['intelligence_quotient'] = self._calculate_intelligence_quotient(enhanced)
        
        enhanced['coverage_analysis'] = self._analyze_coverage(enhanced)
        enhanced['risk_assessment'] = self._assess_risk(enhanced)
        enhanced['compliance_status'] = self._check_compliance(enhanced)
        
        return enhanced
    
    def _calculate_visibility_score(self, asset: Dict[str, Any]) -> float:
        score = 0.0
        coverage_flags = asset.get('coverage_flags', {})
        
        if coverage_flags.get('in_original_cmdb'):
            score += 0.3
        if coverage_flags.get('in_chronicle'):
            score += 0.25
        if coverage_flags.get('in_splunk'):
            score += 0.2
        if coverage_flags.get('in_crowdstrike'):
            score += 0.15
        if coverage_flags.get('in_tanium'):
            score += 0.1
        
        return min(1.0, score)
    
    def _calculate_quality_score(self, asset: Dict[str, Any]) -> float:
        all_data = asset.get('all_data', {})
        filled_fields = sum(1 for v in all_data.values() if v)
        total_possible = 25
        return min(1.0, filled_fields / total_possible)
    
    def _calculate_confidence_score(self, asset: Dict[str, Any]) -> float:
        source_count = asset.get('source_count', 0)
        ml_confidence = asset.get('ml_confidence', 0.0)
        return min(1.0, (source_count / 5.0) * 0.6 + ml_confidence * 0.4)
    
    def _calculate_intelligence_quotient(self, asset: Dict[str, Any]) -> float:
        all_data = asset.get('all_data', {})
        data_richness = len([v for v in all_data.values() if v and len(str(v)) > 3])
        return min(1.0, data_richness / 15.0)
    
    def _analyze_coverage(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        coverage_flags = asset.get('coverage_flags', {})
        total_tools = len(coverage_flags)
        covered_tools = sum(1 for v in coverage_flags.values() if v)
        
        return {
            'total_security_tools': total_tools,
            'covered_by_tools': covered_tools,
            'coverage_percentage': (covered_tools / total_tools * 100) if total_tools > 0 else 0,
            'missing_coverage': [k for k, v in coverage_flags.items() if not v],
            'coverage_level': 'high' if covered_tools >= 4 else 'medium' if covered_tools >= 2 else 'low'
        }
    
    def _assess_risk(self, asset: Dict[str, Any]) -> Dict[str, str]:
        coverage = self._analyze_coverage(asset)
        all_data = asset.get('all_data', {})
        
        risk_level = 'low'
        if coverage['coverage_level'] == 'low':
            risk_level = 'high'
        elif coverage['coverage_level'] == 'medium':
            risk_level = 'medium'
        
        criticality = str(all_data.get('criticality', ['unknown'])[0]).lower()
        if 'critical' in criticality or 'high' in criticality:
            risk_level = 'high' if risk_level != 'high' else 'critical'
        
        return {
            'risk_level': risk_level,
            'risk_factors': coverage['missing_coverage'],
            'mitigation_priority': 'immediate' if risk_level in ['high', 'critical'] else 'standard'
        }
    
    def _check_compliance(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        coverage_flags = asset.get('coverage_flags', {})
        all_data = asset.get('all_data', {})
        
        compliance_score = 0.0
        requirements_met = []
        requirements_failed = []
        
        if coverage_flags.get('in_chronicle'):
            compliance_score += 0.25
            requirements_met.append('security_logging')
        else:
            requirements_failed.append('security_logging')
        
        if coverage_flags.get('in_crowdstrike') or coverage_flags.get('in_tanium'):
            compliance_score += 0.25
            requirements_met.append('endpoint_protection')
        else:
            requirements_failed.append('endpoint_protection')
        
        if all_data.get('owner') or all_data.get('business_unit'):
            compliance_score += 0.25
            requirements_met.append('asset_ownership')
        else:
            requirements_failed.append('asset_ownership')
        
        if all_data.get('classification') or all_data.get('criticality'):
            compliance_score += 0.25
            requirements_met.append('asset_classification')
        else:
            requirements_failed.append('asset_classification')
        
        return {
            'compliance_score': compliance_score,
            'compliance_percentage': compliance_score * 100,
            'requirements_met': requirements_met,
            'requirements_failed': requirements_failed,
            'compliance_status': 'compliant' if compliance_score >= 0.8 else 'partial' if compliance_score >= 0.5 else 'non_compliant'
        }
    
    def _merge_asset_data(self, primary: Dict[str, Any], secondary: Dict[str, Any]) -> Dict[str, Any]:
        merged = primary.copy()
        
        primary_all_data = merged.get('all_data', {})
        secondary_all_data = secondary.get('all_data', {})
        
        for key, value in secondary_all_data.items():
            if key not in primary_all_data:
                primary_all_data[key] = value
            else:
                if isinstance(primary_all_data[key], list) and isinstance(value, list):
                    combined = list(set(primary_all_data[key] + value))
                    primary_all_data[key] = combined
                elif value and value not in str(primary_all_data[key]):
                    if isinstance(primary_all_data[key], list):
                        primary_all_data[key].append(value)
                    else:
                        primary_all_data[key] = [primary_all_data[key], value]
        
        merged['all_data'] = primary_all_data
        
        primary_coverage = merged.get('coverage_flags', {})
        secondary_coverage = secondary.get('coverage_flags', {})
        for flag, value in secondary_coverage.items():
            primary_coverage[flag] = primary_coverage.get(flag, False) or value
        merged['coverage_flags'] = primary_coverage
        
        merged['source_count'] = max(
            merged.get('source_count', 0),
            secondary.get('source_count', 0)
        )
        
        primary_sources = set(merged.get('source_tables', []))
        secondary_sources = set(secondary.get('source_tables', []))
        merged['source_tables'] = list(primary_sources.union(secondary_sources))
        
        return merged
    
    def _hyper_asset_to_dict(self, hyper_asset: HyperAsset) -> Dict[str, Any]:
        return {
            'hostname': hyper_asset.hostname,
            'primary_identity': hyper_asset.primary_identity,
            'all_data': {
                'ip_address': [hyper_asset.ip] if hyper_asset.ip else [],
                'fqdn': [hyper_asset.fqdn] if hyper_asset.fqdn else [],
                'mac_address': [hyper_asset.mac] if hyper_asset.mac else [],
                'infrastructure_type': [hyper_asset.infrastructure_type] if hyper_asset.infrastructure_type else [],
                'system_classification': [hyper_asset.system_classification] if hyper_asset.system_classification else [],
                'business_unit': [hyper_asset.business_unit] if hyper_asset.business_unit else [],
                'region': [hyper_asset.region] if hyper_asset.region else [],
                'country': [hyper_asset.country] if hyper_asset.country else [],
                'datacenter': [hyper_asset.datacenter] if hyper_asset.datacenter else [],
                'cio': [hyper_asset.cio] if hyper_asset.cio else [],
                'application_class': [hyper_asset.application_class] if hyper_asset.application_class else []
            },
            'coverage_flags': {
                'in_original_cmdb': hyper_asset.cmdb_visibility,
                'in_chronicle': hyper_asset.chronicle_coverage,
                'in_splunk': hyper_asset.splunk_coverage,
                'in_crowdstrike': hyper_asset.crowdstrike_coverage,
                'in_tanium': hyper_asset.tanium_coverage,
                'in_dlp': hyper_asset.dlp_coverage
            },
            'source_tables': hyper_asset.tables_found_in,
            'source_count': len(hyper_asset.tables_found_in),
            'visibility_score': hyper_asset.visibility_score,
            'intelligence_quotient': hyper_asset.intelligence_quotient,
            'quality_coefficient': hyper_asset.quality_coefficient,
            'confidence_index': hyper_asset.confidence_index
        }
    
    def generate_comprehensive_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        assets = results.get('assets', {})
        stats = results.get('statistics', {})
        
        coverage_analysis = {}
        risk_analysis = {}
        compliance_analysis = {}
        
        for asset_id, asset in assets.items():
            coverage = asset.get('coverage_analysis', {})
            risk = asset.get('risk_assessment', {})
            compliance = asset.get('compliance_status', {})
            
            coverage_level = coverage.get('coverage_level', 'unknown')
            coverage_analysis[coverage_level] = coverage_analysis.get(coverage_level, 0) + 1
            
            risk_level = risk.get('risk_level', 'unknown')
            risk_analysis[risk_level] = risk_analysis.get(risk_level, 0) + 1
            
            comp_status = compliance.get('compliance_status', 'unknown')
            compliance_analysis[comp_status] = compliance_analysis.get(comp_status, 0) + 1
        
        return {
            'executive_summary': {
                'total_assets': len(assets),
                'discovery_success_rate': (len(assets) / max(stats.get('total_tables_processed', 1), 1)) * 100,
                'ml_prediction_accuracy': (stats.get('high_confidence_predictions', 0) / max(stats.get('ml_predictions_made', 1), 1)) * 100,
                'average_visibility_score': sum(a.get('visibility_score', 0) for a in assets.values()) / len(assets) if assets else 0,
                'processing_time_minutes': results.get('discovery_metadata', {}).get('processing_time_seconds', 0) / 60
            },
            'coverage_breakdown': coverage_analysis,
            'risk_breakdown': risk_analysis,
            'compliance_breakdown': compliance_analysis,
            'recommendations': self._generate_recommendations(assets),
            'database_location': self.database.db_path,
            'assets_requiring_attention': self._identify_priority_assets(assets)
        }
    
    def _generate_recommendations(self, assets: Dict[str, Any]) -> List[str]:
        recommendations = []
        
        low_coverage_count = sum(1 for a in assets.values() 
                               if a.get('coverage_analysis', {}).get('coverage_level') == 'low')
        if low_coverage_count > 0:
            recommendations.append(f"Improve security tool coverage for {low_coverage_count} assets")
        
        high_risk_count = sum(1 for a in assets.values() 
                            if a.get('risk_assessment', {}).get('risk_level') in ['high', 'critical'])
        if high_risk_count > 0:
            recommendations.append(f"Address high-risk issues for {high_risk_count} critical assets")
        
        non_compliant_count = sum(1 for a in assets.values() 
                                if a.get('compliance_status', {}).get('compliance_status') == 'non_compliant')
        if non_compliant_count > 0:
            recommendations.append(f"Remediate compliance issues for {non_compliant_count} assets")
        
        return recommendations
    
    def _identify_priority_assets(self, assets: Dict[str, Any]) -> List[Dict[str, Any]]:
        priority_assets = []
        
        for asset_id, asset in assets.items():
            risk_level = asset.get('risk_assessment', {}).get('risk_level', 'low')
            compliance_status = asset.get('compliance_status', {}).get('compliance_status', 'compliant')
            
            if risk_level in ['high', 'critical'] or compliance_status == 'non_compliant':
                priority_assets.append({
                    'asset_id': asset_id,
                    'hostname': asset.get('hostname', ''),
                    'risk_level': risk_level,
                    'compliance_status': compliance_status,
                    'missing_coverage': asset.get('coverage_analysis', {}).get('missing_coverage', [])
                })
        
        return sorted(priority_assets, 
                     key=lambda x: (x['risk_level'] == 'critical', x['risk_level'] == 'high'))
    
    def close(self):
        try:
            if hasattr(self.training_orchestrator, 'stop_continuous_learning'):
                self.training_orchestrator.stop_continuous_learning()
            self.cache.clear()
            self.database.close()
            logger.info("System shutdown completed successfully")
        except Exception as e:
            logger.error(f"Shutdown error: {e}")

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    default_config = {
        'max_memory_mb': 8192,
        'max_disk_gb': 100,
        'cache_dir': '.cache',
        'database_path': 'quantum_discovery.db',
        'max_workers': 64,
        'enable_machine_learning': True,
        'enable_deep_analysis': True,
        'enable_semantic_matching': True,
        'enable_predictive_enrichment': True,
        'intelligence_level': 'expert',
        'semantic_confidence_threshold': 0.7,
        'validation_confidence_threshold': 0.8,
        'data_quality_threshold': 0.75,
        'additional_projects': [
            'chronicle-fisv', 'fisv-security', 'fisv-logs', 'fisv-data',
            'fisv-compliance', 'fisv-risk', 'fisv-audit'
        ],
        'field_type_priorities': {
            'hostname': 100, 'fqdn': 95, 'ip_address': 90, 'mac_address': 85,
            'infrastructure_type': 80, 'system_classification': 75,
            'global_region': 70, 'business_unit': 65
        },
        'source_priorities': {
            'cmdb': 100, 'crowdstrike': 95, 'chronicle': 90, 'splunk': 85,
            'tanium': 80, 'dlp': 75, 'security': 70
        }
    }
    
    if config_path and Path(config_path).exists():
        try:
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                default_config.update(user_config)
        except Exception as e:
            logger.warning(f"Failed to load config from {config_path}: {e}")
    
    return default_config

def parse_arguments():
    parser = argparse.ArgumentParser(description="Ultimate Quantum Discovery System")
    parser.add_argument('--project', '-p', required=True, help='Primary GCP Project ID')
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--output', '-o', default='output', help='Output directory')
    parser.add_argument('--memory', type=int, default=8192, help='Max memory in MB')
    parser.add_argument('--disk', type=int, default=100, help='Max disk in GB')
    parser.add_argument('--workers', type=int, default=64, help='Number of parallel workers')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--dry-run', action='store_true', help='Estimation mode only')
    parser.add_argument('--skip-ml', action='store_true', help='Skip ML training')
    parser.add_argument('--engines', nargs='+', default=['ao1', 'content', 'core'], 
                       choices=['ao1', 'content', 'core'], help='Discovery engines to use')
    return parser.parse_args()

async def main():
    args = parse_arguments()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    config = load_config(args.config)
    config.update({
        'max_memory_mb': args.memory,
        'max_disk_gb': args.disk,
        'max_workers': args.workers,
        'enable_machine_learning': not args.skip_ml,
        'enabled_engines': args.engines
    })
    
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)
    
    logger.info("ULTIMATE QUANTUM DISCOVERY SYSTEM INITIATED")
    logger.info(f"Project: {args.project}")
    logger.info(f"Memory: {args.memory}MB, Disk: {args.disk}GB, Workers: {args.workers}")
    logger.info(f"ML Enabled: {not args.skip_ml}")
    logger.info(f"Engines: {', '.join(args.engines)}")
    
    system = None
    try:
        system = UltimateQuantumDiscoverySystem(args.project, config)
        
        if args.dry_run:
            logger.info("DRY RUN MODE - Estimating discovery scope")
            
            total_tables = 0
            total_datasets = 0
            
            for project_id, client_manager in system.client_managers.items():
                try:
                    with client_manager.get_client() as client:
                        datasets = list(client.list_datasets(project=project_id))
                        total_datasets += len(datasets)
                        
                        for dataset in datasets:
                            tables = list(client.list_tables(dataset))
                            total_tables += len(tables)
                except Exception as e:
                    logger.warning(f"Failed to estimate {project_id}: {e}")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dry_run_file = output_dir / f"dry_run_estimate_{timestamp}.json"
            
            estimate = {
                'timestamp': datetime.now().isoformat(),
                'estimated_datasets': total_datasets,
                'estimated_tables': total_tables,
                'estimated_processing_time_hours': total_tables / 1000,
                'projects_available': list(system.client_managers.keys()),
                'configuration': config
            }
            
            with open(dry_run_file, 'w') as f:
                json.dump(estimate, f, indent=2, default=str)
            
            logger.info(f"Estimation complete: {total_tables} tables across {total_datasets} datasets")
            logger.info(f"Estimated processing time: {total_tables / 1000:.1f} hours")
            return 0
        
        logger.info("STARTING COMPREHENSIVE QUANTUM DISCOVERY")
        
        results = await system.run_comprehensive_discovery()
        report = system.generate_comprehensive_report(results)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        results_file = output_dir / f"discovery_results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        report_file = output_dir / f"discovery_report_{timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info("QUANTUM DISCOVERY COMPLETED SUCCESSFULLY")
        logger.info(f"Results: {results_file}")
        logger.info(f"Report: {report_file}")
        logger.info(f"Database: {system.database.db_path}")
        logger.info(f"Assets Discovered: {system.stats['total_assets_discovered']:,}")
        logger.info(f"Tables Processed: {system.stats['total_tables_processed']:,}")
        logger.info(f"Processing Time: {(datetime.now() - system.start_time).total_seconds() / 60:.1f} minutes")
        
        return 0
        
    except KeyboardInterrupt:
        logger.warning("Discovery interrupted by user")
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
    sys.exit(asyncio.run(main()))