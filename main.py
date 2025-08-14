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
from discovery.ao1 import AO1SuperEngine
from storage.database import DatabaseManager, ContentDatabase, EnhancedDatabaseManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QuantumHyperIntelligentDiscoverySystem:
    def __init__(self, project_id: str, config: Dict[str, Any]):
        self.project_id = project_id
        self.config = config
        
        self.quantum_cache = IntelligentCache(
            cache_dir=config.get('cache_dir', '.cache'),
            max_memory_mb=config.get('max_memory_mb', 4096),
            max_disk_gb=config.get('max_disk_gb', 50)
        )
        
        self.quantum_intelligence = QuantumIntelligenceEngine(config)
        
        self.client_managers = {}
        self._init_quantum_clients()
        
        self.quantum_ao1_engine = AO1SuperEngine(config)
        
        self.quantum_db = EnhancedDatabaseManager(config.get('database_path', 'smart_cmdb.db'))
        self.quantum_content_db = ContentDatabase(config.get('content_db_path', 'content_cmdb.db'))
        
        self.quantum_stats = {
            'start_time': datetime.now(),
            'engines_used': [],
            'total_hyper_assets': 0,
            'total_cells_analyzed': 0,
            'processing_errors': 0,
            'quantum_hyperintelligent_mode': True
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
    
    async def run_quantum_hyperintelligent_discovery(self) -> Dict[str, Any]:
        logger.info("STARTING QUANTUM HYPER-INTELLIGENT DISCOVERY")
        
        quantum_results = {
            'quantum_metadata': {
                'start_time': self.quantum_stats['start_time'].isoformat(),
                'project_id': self.project_id,
                'quantum_hyperintelligent_mode': True,
                'quantum_config': {k: v for k, v in self.config.items() if not k.startswith('_')}
            }
        }
        
        try:
            quantum_discovery = await self._run_quantum_ao1_discovery()
            
            if quantum_discovery and 'assets' in quantum_discovery:
                quantum_assets = {}
                for asset_id, asset_data in quantum_discovery['assets'].items():
                    hyper_asset = self._convert_dict_to_hyper_asset(asset_id, asset_data)
                    if hyper_asset:
                        quantum_assets[asset_id] = hyper_asset
                
                quantum_discovery_obj = QuantumDiscovery()
                quantum_discovery_obj.hyper_assets = quantum_assets
                quantum_discovery_obj.intelligence_metrics = quantum_discovery.get('discovery_stats', {})
                
                quantum_stored_count = self.quantum_db.store_comprehensive_discovery(quantum_discovery_obj)
                quantum_discovery_obj.intelligence_metrics['stored_hyper_assets'] = quantum_stored_count
                self.quantum_stats['total_hyper_assets'] = len(quantum_assets)
            
            self.quantum_stats['engines_used'].append('quantum_ao1')
            
            quantum_hyperintelligent_results = {
                'quantum_hyperintelligent_discovery': {
                    'hyper_assets': {k: self._hyper_asset_to_dict(v) for k, v in quantum_assets.items()} if 'quantum_assets' in locals() else {},
                    'intelligence_metrics': quantum_discovery.get('discovery_stats', {}),
                    'quantum_discovery_mode': 'quantum_ao1_enhanced'
                }
            }
            
            quantum_results.update(quantum_hyperintelligent_results)
            
        except Exception as e:
            logger.error(f"Quantum hyper-intelligent discovery failed: {e}")
            quantum_results['error'] = str(e)
            self.quantum_stats['processing_errors'] += 1
        
        finally:
            quantum_results['quantum_final_stats'] = self._calculate_quantum_hyperintelligent_stats()
        
        return quantum_results
    
    async def _run_quantum_ao1_discovery(self) -> Dict[str, Any]:
        logger.info("Running quantum AO1 discovery")
        
        try:
            quantum_results = await self.quantum_ao1_engine.enhanced_discovery(self.client_managers)
            return quantum_results
        except Exception as e:
            logger.error(f"Quantum AO1 discovery failed: {e}")
            return {'error': str(e)}
    
    def _convert_dict_to_hyper_asset(self, asset_id: str, asset_data: Dict[str, Any]) -> HyperAsset:
        try:
            hyper_asset = HyperAsset(id=asset_id)
            
            hyper_asset.hostname = asset_data.get('hostname', '')
            hyper_asset.ip = asset_data.get('ip', '')
            hyper_asset.fqdn = asset_data.get('fqdn', '')
            hyper_asset.infrastructure_type = asset_data.get('infrastructure_type', '')
            hyper_asset.system_classification = asset_data.get('system_classification', '')
            hyper_asset.business_unit = asset_data.get('business_unit', '')
            hyper_asset.region = asset_data.get('region', '')
            hyper_asset.application_class = asset_data.get('application_class', '')
            
            hyper_asset.edr_coverage = asset_data.get('edr', False)
            hyper_asset.dlp_coverage = asset_data.get('dlp', False)
            hyper_asset.tanium_coverage = asset_data.get('tanium', False)
            hyper_asset.splunk_coverage = asset_data.get('splunk', False)
            hyper_asset.chronicle_coverage = asset_data.get('chronicle', False)
            hyper_asset.crowdstrike_coverage = asset_data.get('crowdstrike', False)
            hyper_asset.cmdb_visibility = asset_data.get('cmdb', False)
            
            hyper_asset.visibility_score = asset_data.get('visibility_score', 0.0)
            hyper_asset.intelligence_quotient = asset_data.get('intelligence_quotient', 0.5)
            hyper_asset.quality_coefficient = asset_data.get('quality_coefficient', 0.5)
            hyper_asset.confidence_index = asset_data.get('confidence_index', 0.5)
            
            return hyper_asset
            
        except Exception as e:
            logger.error(f"Failed to convert dict to hyper asset {asset_id}: {e}")
            return None
    
    def _hyper_asset_to_dict(self, hyper_asset: HyperAsset) -> Dict[str, Any]:
        return {
            'id': hyper_asset.id,
            'primary_identity': hyper_asset.primary_identity,
            'hostname': hyper_asset.hostname,
            'ip': hyper_asset.ip,
            'fqdn': hyper_asset.fqdn,
            'infrastructure_type': hyper_asset.infrastructure_type,
            'system_classification': hyper_asset.system_classification,
            'region': hyper_asset.region,
            'business_unit': hyper_asset.business_unit,
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
            'quantum_hyperintelligent_classified': True
        }
    
    def _calculate_quantum_hyperintelligent_stats(self) -> Dict[str, Any]:
        processing_time = (datetime.now() - self.quantum_stats['start_time']).total_seconds()
        
        return {
            'total_processing_time_seconds': processing_time,
            'total_hyper_assets_discovered': self.quantum_stats['total_hyper_assets'],
            'engines_used': self.quantum_stats['engines_used'],
            'processing_errors': self.quantum_stats['processing_errors'],
            'quantum_hyperintelligent_mode': self.quantum_stats['quantum_hyperintelligent_mode'],
            'quantum_cache_stats': self.quantum_cache.get_stats()
        }
    
    def generate_quantum_hyperintelligent_report(self, quantum_results: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'quantum_executive_summary': {
                'discovery_timestamp': datetime.now().isoformat(),
                'project_id': self.project_id,
                'total_hyper_assets': self.quantum_stats['total_hyper_assets'],
                'discovery_method': 'quantum ao1 visibility analysis',
                'processing_time_minutes': quantum_results.get('quantum_final_stats', {}).get('total_processing_time_seconds', 0) / 60
            },
            'quantum_database_files': [self.quantum_db.db_path, self.quantum_content_db.db_path]
        }
    
    def close(self):
        try:
            self.quantum_cache.clear()
            self.quantum_db.close()
            self.quantum_content_db.close()
            logger.info("Quantum hyper-intelligent system shutdown complete")
        except Exception as e:
            logger.error(f"Quantum shutdown error: {e}")

def load_quantum_hyperintelligent_config(config_file: str = None) -> Dict[str, Any]:
    quantum_default_config = {
        'max_memory_mb': 4096,
        'max_disk_gb': 50,
        'cache_dir': '.cache',
        'database_path': 'smart_cmdb.db',
        'content_db_path': 'content_cmdb.db',
        'max_workers': 32,
        'enable_machine_learning': True,
        'additional_projects': ['chronicle-fisv']
    }
    
    if config_file and Path(config_file).exists():
        try:
            import yaml
            with open(config_file, 'r') as f:
                user_config = yaml.safe_load(f)
                quantum_default_config.update(user_config)
        except Exception as e:
            logger.warning(f"Quantum config load failed: {e}")
    
    return quantum_default_config

def parse_quantum_args():
    parser = argparse.ArgumentParser(description="Quantum Hyper-Intelligent Discovery System")
    parser.add_argument('--project', '-p', required=True, help='GCP Project ID')
    parser.add_argument('--config', '-c', help='Config file path')
    parser.add_argument('--output', '-o', default='output', help='Output directory')
    parser.add_argument('--memory', type=int, default=4096, help='Max memory MB')
    parser.add_argument('--disk', type=int, default=50, help='Max disk GB')
    parser.add_argument('--workers', type=int, default=32, help='Parallel workers')
    parser.add_argument('--debug', action='store_true', help='Debug mode')
    parser.add_argument('--dry-run', action='store_true', help='Estimation only')
    return parser.parse_args()

async def quantum_main():
    args = parse_quantum_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    quantum_config = load_quantum_hyperintelligent_config(args.config)
    quantum_config.update({
        'max_memory_mb': args.memory,
        'max_disk_gb': args.disk,
        'max_workers': args.workers,
        'output_dir': args.output
    })
    
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)
    
    logger.info("QUANTUM HYPER-INTELLIGENT DISCOVERY SYSTEM")
    logger.info(f"Project: {args.project}")
    logger.info(f"Memory: {args.memory}MB, Disk: {args.disk}GB")
    logger.info(f"Workers: {args.workers}")
    
    quantum_system = None
    try:
        quantum_system = QuantumHyperIntelligentDiscoverySystem(args.project, quantum_config)
        
        if args.dry_run:
            logger.info("QUANTUM DRY RUN MODE - Estimating discovery scope")
            
            total_tables = 0
            
            for project_id, client_manager in quantum_system.client_managers.items():
                with client_manager.get_client() as client:
                    datasets = list(client.list_datasets(project=project_id))
                    for dataset in datasets:
                        tables = list(client.list_tables(dataset))
                        total_tables += len(tables)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            quantum_dry_run_file = output_dir / f"quantum_dry_run_{timestamp}.json"
            
            quantum_dry_run_results = {
                'estimated_tables': total_tables,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(quantum_dry_run_file, 'w') as f:
                json.dump(quantum_dry_run_results, f, indent=2)
            
            logger.info(f"Quantum estimated {total_tables} tables")
            logger.info(f"Quantum dry run saved: {quantum_dry_run_file}")
            return 0
        
        logger.info("INITIATING QUANTUM HYPERINTELLIGENT DISCOVERY")
        
        quantum_results = await quantum_system.run_quantum_hyperintelligent_discovery()
        quantum_report = quantum_system.generate_quantum_hyperintelligent_report(quantum_results)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        quantum_results_file = output_dir / f"discovery_results_{timestamp}.json"
        with open(quantum_results_file, 'w') as f:
            json.dump(quantum_results, f, indent=2, default=str)
        
        quantum_report_file = output_dir / f"discovery_report_{timestamp}.json"
        with open(quantum_report_file, 'w') as f:
            json.dump(quantum_report, f, indent=2, default=str)
        
        logger.info("QUANTUM HYPERINTELLIGENT DISCOVERY COMPLETED SUCCESSFULLY")
        logger.info(f"Results: {quantum_results_file}")
        logger.info(f"Report: {quantum_report_file}")
        logger.info(f"Assets discovered: {quantum_system.quantum_stats['total_hyper_assets']:,}")
        
        return 0
        
    except KeyboardInterrupt:
        logger.warning("Quantum discovery interrupted by user")
        return 130
    
    except Exception as e:
        logger.error(f"Quantum hyperintelligent discovery failed: {e}")
        
        if args.debug:
            import traceback
            traceback.print_exc()
        
        return 1
    
    finally:
        if quantum_system:
            quantum_system.close()

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(quantum_main())
    sys.exit(exit_code)