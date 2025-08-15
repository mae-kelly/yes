import asyncio
import logging
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from core.types import QuantumDiscovery, HyperAsset
from gcp.client import BigQueryClientManager
from cache.system import IntelligentCache
from ai.intelligence import QuantumIntelligenceEngine
from ai.content import QuantumContentAnalyzer
from ai.training_orchestrator import IntensiveTrainingOrchestrator
from discovery.ao1 import AO1SuperEngine
from storage.database import DatabaseManager, ContentDatabase, EnhancedDatabaseManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MLEnhancedQuantumDiscoverySystem:
    def __init__(self, project_id: str, config: Dict[str, Any]):
        self.project_id = project_id
        self.config = config
        
        self.quantum_cache = IntelligentCache(
            cache_dir=config.get('cache_dir', '.cache'),
            max_memory_mb=config.get('max_memory_mb', 4096),
            max_disk_gb=config.get('max_disk_gb', 50)
        )
        
        self.quantum_intelligence = QuantumIntelligenceEngine(config)
        
        self.content_analyzer = QuantumContentAnalyzer()
        
        self.ml_training_orchestrator = IntensiveTrainingOrchestrator(
            cache_dir=config.get('cache_dir', '.cache')
        )
        
        self.client_managers = {}
        self._init_quantum_clients()
        
        self.quantum_ao1_engine = AO1SuperEngine(config)
        
        self.quantum_db = EnhancedDatabaseManager(config.get('database_path', 'smart_cmdb.db'))
        self.quantum_content_db = ContentDatabase(config.get('content_db_path', 'content_cmdb.db'))
        
        self.ml_stats = {
            'ml_training_completed': False,
            'ml_accuracy': 0.0,
            'total_predictions_made': 0,
            'high_confidence_predictions': 0
        }
        
        self.quantum_stats = {
            'start_time': datetime.now(),
            'engines_used': [],
            'total_hyper_assets': 0,
            'total_cells_analyzed': 0,
            'processing_errors': 0,
            'quantum_hyperintelligent_mode': True,
            'ml_enhanced': True
        }
        
    def _init_quantum_clients(self):
        try:
            self.client_managers[self.project_id] = BigQueryClientManager(self.project_id)
            logger.info(f"Connected to quantum main project: {self.project_id}")
        except Exception as e:
            logger.error(f"Failed to connect to quantum {self.project_id}: {e}")
            raise
        
        quantum_additional_projects = self.config.get('additional_projects', ['chronicle-fisv'])
        for project in quantum_additional_projects:
            try:
                self.client_managers[project] = BigQueryClientManager(project)
                logger.info(f"Connected to quantum additional project: {project}")
            except Exception as e:
                logger.warning(f"Quantum additional project {project} not available: {e}")
    
    async def initialize_ml_training(self):
        logger.info("Initializing ML-enhanced content analysis")
        
        try:
            training_success = await self.ml_training_orchestrator.perform_intensive_initial_training()
            
            if training_success:
                self.ml_training_orchestrator.start_continuous_learning()
                
                training_stats = self.ml_training_orchestrator.get_training_statistics()
                self.ml_stats.update({
                    'ml_training_completed': True,
                    'ml_accuracy': training_stats['performance_metrics'].get('overall_accuracy', 0.0),
                    'training_samples': training_stats['training_stats'].get('samples_processed', 0)
                })
                
                logger.info(f"ML training completed with accuracy: {self.ml_stats['ml_accuracy']:.4f}")
                
                await self.content_analyzer.start_intensive_training()
                
                return True
            else:
                logger.warning("ML training failed, proceeding with pattern-based analysis only")
                return False
                
        except Exception as e:
            logger.error(f"ML initialization failed: {e}")
            return False
    
    async def run_ml_enhanced_discovery(self) -> Dict[str, Any]:
        logger.info("STARTING ML-ENHANCED QUANTUM DISCOVERY")
        
        if self.config.get('enable_ml_training', True):
            ml_success = await self.initialize_ml_training()
            if ml_success:
                logger.info("ML training successful - enhanced accuracy mode activated")
            else:
                logger.info("Proceeding with traditional pattern matching")
        
        quantum_results = {
            'quantum_metadata': {
                'start_time': self.quantum_stats['start_time'].isoformat(),
                'project_id': self.project_id,
                'quantum_hyperintelligent_mode': True,
                'ml_enhanced': self.ml_stats['ml_training_completed'],
                'ml_accuracy': self.ml_stats['ml_accuracy'],
                'quantum_config': {k: v for k, v in self.config.items() if not k.startswith('_')}
            }
        }
        
        try:
            quantum_discovery = await self._run_ml_enhanced_ao1_discovery()
            
            if quantum_discovery and 'assets' in quantum_discovery:
                logger.info(f"Converting {len(quantum_discovery['assets']):,} assets to hyper assets")
                
                quantum_assets = {}
                for asset_id, asset_data in quantum_discovery['assets'].items():
                    hyper_asset = self._convert_dict_to_hyper_asset(asset_id, asset_data)
                    if hyper_asset:
                        quantum_assets[asset_id] = hyper_asset
                
                logger.info(f"Converted {len(quantum_assets):,} hyper assets")
                
                quantum_discovery_obj = QuantumDiscovery()
                quantum_discovery_obj.hyper_assets = quantum_assets
                quantum_discovery_obj.intelligence_metrics = quantum_discovery.get('discovery_stats', {})
                quantum_discovery_obj.intelligence_metrics.update(self.ml_stats)
                
                logger.info(f"Storing {len(quantum_assets):,} assets to database")
                quantum_stored_count = self.quantum_db.store_comprehensive_discovery(quantum_discovery_obj)
                logger.info(f"Successfully stored {quantum_stored_count:,} assets")
                
                content_stored = self.quantum_content_db.store_content_assets(quantum_discovery['assets'])
                logger.info(f"Stored {content_stored:,} raw content assets")
                
                self.quantum_stats['total_hyper_assets'] = len(quantum_assets)
            else:
                logger.error("No assets returned from discovery")
                quantum_assets = {}
                quantum_discovery_obj = QuantumDiscovery()
            
            self.quantum_stats['engines_used'].append('ml_enhanced_quantum_ao1')
            
            quantum_hyperintelligent_results = {
                'ml_enhanced_discovery': {
                    'hyper_assets': {k: self._hyper_asset_to_dict(v) for k, v in quantum_assets.items()} if 'quantum_assets' in locals() else {},
                    'intelligence_metrics': quantum_discovery.get('discovery_stats', {}),
                    'ml_statistics': self.ml_stats,
                    'quantum_discovery_mode': 'ml_enhanced_quantum_ao1'
                }
            }
            
            quantum_results.update(quantum_hyperintelligent_results)
            
        except Exception as e:
            logger.error(f"ML-enhanced discovery failed: {e}")
            quantum_results['error'] = str(e)
            self.quantum_stats['processing_errors'] += 1
        
        finally:
            quantum_results['quantum_final_stats'] = self._calculate_quantum_stats()
        
        return quantum_results
    
    async def _run_ml_enhanced_ao1_discovery(self) -> Dict[str, Any]:
        logger.info("Running ML-enhanced AO1 discovery")
        
        try:
            quantum_results = await self.quantum_ao1_engine.enhanced_discovery(self.client_managers)
            return quantum_results
        except Exception as e:
            logger.error(f"ML-enhanced AO1 discovery failed: {e}")
            return {'error': str(e)}
    
    def _convert_dict_to_hyper_asset(self, asset_id: str, asset_data: Dict[str, Any]) -> HyperAsset:
        try:
            hyper_asset = HyperAsset(id=asset_id)
            
            hyper_asset.hostname = asset_data.get('hostname', '')
            hyper_asset.primary_identity = hyper_asset.hostname
            
            all_data = asset_data.get('all_data', {})
            
            if 'ip_address' in all_data and all_data['ip_address']:
                hyper_asset.ip = all_data['ip_address'][0] if isinstance(all_data['ip_address'], list) else str(all_data['ip_address'])
            if 'fqdn' in all_data and all_data['fqdn']:
                hyper_asset.fqdn = all_data['fqdn'][0] if isinstance(all_data['fqdn'], list) else str(all_data['fqdn'])
            if 'mac_address' in all_data and all_data['mac_address']:
                hyper_asset.mac = all_data['mac_address'][0] if isinstance(all_data['mac_address'], list) else str(all_data['mac_address'])
            if 'infrastructure_type' in all_data and all_data['infrastructure_type']:
                hyper_asset.infrastructure_type = all_data['infrastructure_type'][0] if isinstance(all_data['infrastructure_type'], list) else str(all_data['infrastructure_type'])
            if 'system_classification' in all_data and all_data['system_classification']:
                hyper_asset.system_classification = all_data['system_classification'][0] if isinstance(all_data['system_classification'], list) else str(all_data['system_classification'])
            if 'business_unit' in all_data and all_data['business_unit']:
                hyper_asset.business_unit = all_data['business_unit'][0] if isinstance(all_data['business_unit'], list) else str(all_data['business_unit'])
            if 'region' in all_data and all_data['region']:
                hyper_asset.region = all_data['region'][0] if isinstance(all_data['region'], list) else str(all_data['region'])
            if 'country' in all_data and all_data['country']:
                hyper_asset.country = all_data['country'][0] if isinstance(all_data['country'], list) else str(all_data['country'])
            if 'datacenter' in all_data and all_data['datacenter']:
                hyper_asset.datacenter = all_data['datacenter'][0] if isinstance(all_data['datacenter'], list) else str(all_data['datacenter'])
            if 'cio' in all_data and all_data['cio']:
                hyper_asset.cio = all_data['cio'][0] if isinstance(all_data['cio'], list) else str(all_data['cio'])
            if 'application_class' in all_data and all_data['application_class']:
                hyper_asset.application_class = all_data['application_class'][0] if isinstance(all_data['application_class'], list) else str(all_data['application_class'])
            
            hyper_asset.edr_coverage = asset_data.get('edr_coverage', False)
            hyper_asset.dlp_coverage = asset_data.get('dlp_coverage', False)
            hyper_asset.tanium_coverage = asset_data.get('tanium_coverage', False)
            hyper_asset.splunk_coverage = asset_data.get('splunk_coverage', False)
            hyper_asset.chronicle_coverage = asset_data.get('chronicle_coverage', False)
            hyper_asset.crowdstrike_coverage = asset_data.get('crowdstrike_coverage', False)
            hyper_asset.cmdb_visibility = asset_data.get('cmdb_visibility', False)
            
            hyper_asset.source_provenance = asset_data.get('sources', [])
            hyper_asset.tables_found_in = asset_data.get('tables_found_in', [])
            
            hyper_asset.visibility_score = self._calculate_visibility_score(hyper_asset)
            hyper_asset.intelligence_quotient = min(1.0, len(asset_data.get('sources', [])) / 4.0)
            hyper_asset.quality_coefficient = len([f for f in [hyper_asset.ip, hyper_asset.fqdn, hyper_asset.infrastructure_type] if f]) / 3.0
            hyper_asset.confidence_index = min(1.0, len(hyper_asset.tables_found_in) / 3.0)
            hyper_asset.entropy_measure = 0.5
            
            hyper_asset.quantum_state = {
                'all_data': all_data,
                'ml_enhanced': self.ml_stats['ml_training_completed'],
                'ml_accuracy': self.ml_stats['ml_accuracy']
            }
            
            return hyper_asset
            
        except Exception as e:
            logger.error(f"Failed to convert asset {asset_id}: {e}")
            return None
    
    def _calculate_visibility_score(self, hyper_asset: HyperAsset) -> float:
        score = 0.0
        
        if hyper_asset.cmdb_visibility:
            score += 0.3
        if hyper_asset.splunk_coverage:
            score += 0.25
        if hyper_asset.chronicle_coverage:
            score += 0.25
        if hyper_asset.edr_coverage:
            score += 0.1
        if hyper_asset.dlp_coverage:
            score += 0.1
        
        return min(1.0, score)
    
    def _hyper_asset_to_dict(self, hyper_asset: HyperAsset) -> Dict[str, Any]:
        return {
            'id': hyper_asset.id,
            'primary_identity': hyper_asset.primary_identity,
            'hostname': hyper_asset.hostname,
            'ip': hyper_asset.ip,
            'fqdn': hyper_asset.fqdn,
            'mac': getattr(hyper_asset, 'mac', ''),
            'infrastructure_type': hyper_asset.infrastructure_type,
            'system_classification': hyper_asset.system_classification,
            'region': hyper_asset.region,
            'country': getattr(hyper_asset, 'country', ''),
            'business_unit': hyper_asset.business_unit,
            'datacenter': hyper_asset.datacenter,
            'cio': hyper_asset.cio,
            'application_class': hyper_asset.application_class,
            'visibility_score': hyper_asset.visibility_score,
            'intelligence_quotient': hyper_asset.intelligence_quotient,
            'quality_coefficient': hyper_asset.quality_coefficient,
            'confidence_index': hyper_asset.confidence_index,
            'cmdb_visibility': hyper_asset.cmdb_visibility,
            'splunk_coverage': hyper_asset.splunk_coverage,
            'chronicle_coverage': hyper_asset.chronicle_coverage,
            'crowdstrike_coverage': hyper_asset.crowdstrike_coverage,
            'edr_coverage': hyper_asset.edr_coverage,
            'dlp_coverage': hyper_asset.dlp_coverage,
            'tanium_coverage': hyper_asset.tanium_coverage,
            'sources': hyper_asset.source_provenance,
            'tables_found_in': getattr(hyper_asset, 'tables_found_in', []),
            'tables_count': len(getattr(hyper_asset, 'tables_found_in', [])),
            'ml_enhanced': self.ml_stats['ml_training_completed'],
            'quantum_hyperintelligent_classified': True,
            'comprehensive_discovery': True
        }
    
    def _calculate_quantum_stats(self) -> Dict[str, Any]:
        processing_time = (datetime.now() - self.quantum_stats['start_time']).total_seconds()
        
        ml_stats = {}
        if hasattr(self, 'ml_training_orchestrator'):
            ml_stats = self.ml_training_orchestrator.get_training_statistics()
        
        return {
            'total_processing_time_seconds': processing_time,
            'total_hyper_assets_discovered': self.quantum_stats['total_hyper_assets'],
            'engines_used': self.quantum_stats['engines_used'],
            'processing_errors': self.quantum_stats['processing_errors'],
            'quantum_hyperintelligent_mode': self.quantum_stats['quantum_hyperintelligent_mode'],
            'ml_enhanced': self.quantum_stats['ml_enhanced'],
            'ml_statistics': self.ml_stats,
            'detailed_ml_stats': ml_stats,
            'quantum_cache_stats': self.quantum_cache.get_stats()
        }
    
    def generate_ml_enhanced_report(self, quantum_results: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'quantum_executive_summary': {
                'discovery_timestamp': datetime.now().isoformat(),
                'project_id': self.project_id,
                'total_hyper_assets': self.quantum_stats['total_hyper_assets'],
                'discovery_method': 'ml-enhanced quantum ao1 analysis',
                'ml_training_completed': self.ml_stats['ml_training_completed'],
                'ml_accuracy': self.ml_stats['ml_accuracy'],
                'processing_time_minutes': quantum_results.get('quantum_final_stats', {}).get('total_processing_time_seconds', 0) / 60
            },
            'ml_performance_metrics': {
                'predictions_made': self.ml_stats['total_predictions_made'],
                'high_confidence_predictions': self.ml_stats['high_confidence_predictions'],
                'training_samples_processed': self.ml_stats.get('training_samples', 0)
            },
            'quantum_database_files': [self.quantum_db.db_path, self.quantum_content_db.db_path]
        }
    
    def close(self):
        try:
            if hasattr(self, 'ml_training_orchestrator'):
                self.ml_training_orchestrator.stop_continuous_learning()
            
            self.quantum_cache.clear()
            self.quantum_db.close()
            self.quantum_content_db.close()
            logger.info("ML-enhanced quantum system shutdown complete")
        except Exception as e:
            logger.error(f"Shutdown error: {e}")

def load_ml_enhanced_config(config_file: str = None) -> Dict[str, Any]:
    quantum_default_config = {
        'max_memory_mb': 4096,
        'max_disk_gb': 50,
        'cache_dir': '.cache',
        'database_path': 'smart_cmdb.db',
        'content_db_path': 'content_cmdb.db',
        'max_workers': 32,
        'enable_machine_learning': True,
        'enable_ml_training': True,
        'ml_training_epochs': 10,
        'ml_batch_size': 32,
        'additional_projects': ['chronicle-fisv']
    }
    
    if config_file and Path(config_file).exists():
        try:
            import yaml
            with open(config_file, 'r') as f:
                user_config = yaml.safe_load(f)
                quantum_default_config.update(user_config)
        except Exception as e:
            logger.warning(f"Config load failed: {e}")
    
    return quantum_default_config

def parse_args():
    parser = argparse.ArgumentParser(description="ML-Enhanced Quantum Discovery System")
    parser.add_argument('--project', '-p', required=True, help='GCP Project ID')
    parser.add_argument('--config', '-c', help='Config file path')
    parser.add_argument('--output', '-o', default='output', help='Output directory')
    parser.add_argument('--memory', type=int, default=4096, help='Max memory MB')
    parser.add_argument('--disk', type=int, default=50, help='Max disk GB')
    parser.add_argument('--workers', type=int, default=32, help='Parallel workers')
    parser.add_argument('--debug', action='store_true', help='Debug mode')
    parser.add_argument('--dry-run', action='store_true', help='Estimation only')
    parser.add_argument('--skip-ml-training', action='store_true', help='Skip ML training')
    return parser.parse_args()

async def main():
    args = parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    config = load_ml_enhanced_config(args.config)
    config.update({
        'max_memory_mb': args.memory,
        'max_disk_gb': args.disk,
        'max_workers': args.workers,
        'output_dir': args.output,
        'enable_ml_training': not args.skip_ml_training
    })
    
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)
    
    logger.info("ML-ENHANCED QUANTUM DISCOVERY SYSTEM")
    logger.info(f"Project: {args.project}")
    logger.info(f"Memory: {args.memory}MB, Disk: {args.disk}GB")
    logger.info(f"ML Training: {'Enabled' if config['enable_ml_training'] else 'Disabled'}")
    
    system = None
    try:
        system = MLEnhancedQuantumDiscoverySystem(args.project, config)
        
        if args.dry_run:
            logger.info("DRY RUN MODE - Estimating scope")
            
            total_tables = 0
            for project_id, client_manager in system.client_managers.items():
                with client_manager.get_client() as client:
                    datasets = list(client.list_datasets(project=project_id))
                    for dataset in datasets:
                        tables = list(client.list_tables(dataset))
                        total_tables += len(tables)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dry_run_file = output_dir / f"ml_enhanced_dry_run_{timestamp}.json"
            
            dry_run_results = {
                'estimated_tables': total_tables,
                'ml_training_enabled': config['enable_ml_training'],
                'timestamp': datetime.now().isoformat()
            }
            
            with open(dry_run_file, 'w') as f:
                json.dump(dry_run_results, f, indent=2)
            
            logger.info(f"Estimated {total_tables} tables for ML-enhanced processing")
            return 0
        
        logger.info("INITIATING ML-ENHANCED MAXIMUM INTENSITY DISCOVERY")
        
        results = await system.run_ml_enhanced_discovery()
        report = system.generate_ml_enhanced_report(results)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        results_file = output_dir / f"ml_enhanced_results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        report_file = output_dir / f"ml_enhanced_report_{timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info("ML-ENHANCED DISCOVERY COMPLETED")
        logger.info(f"Results: {results_file}")
        logger.info(f"Report: {report_file}")
        logger.info(f"Hosts Discovered: {system.quantum_stats['total_hyper_assets']:,}")
        logger.info(f"ML Training: {'Completed' if system.ml_stats['ml_training_completed'] else 'Skipped'}")
        if system.ml_stats['ml_training_completed']:
            logger.info(f"ML Accuracy: {system.ml_stats['ml_accuracy']:.4f}")
        
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