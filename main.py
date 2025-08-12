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

from intelligent_discovery_engine import IntelligentUniversalCMDBBuilder
from cache_manager import IntelligentCacheManager
from content_matcher import IntelligentContentMatcher
from intelligence_engine import IntelligenceEngine
from config_loader import ConfigLoader

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IntelligentAO1System:
    def __init__(self, project_id: str, config: dict, args=None):
        self.project_id = project_id
        self.config = config
        self.args = args
        self.shutdown_requested = False
        
        self.cache_manager = IntelligentCacheManager(
            cache_dir=config.get('cache_dir', '.cache'),
            max_memory_mb=config.get('max_memory_mb', 1024),
            max_disk_gb=config.get('max_disk_gb', 10)
        )
        
        self.content_matcher = IntelligentContentMatcher()
        self.intelligence_engine = IntelligenceEngine(config)
        
        self.discovery_engine = IntelligentUniversalCMDBBuilder(
            project_id=project_id,
            config=config,
            cache_manager=self.cache_manager,
            content_matcher=self.content_matcher,
            intelligence_engine=self.intelligence_engine
        )
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        logger.warning(f"Received signal {signum}, initiating intelligent shutdown...")
        self.shutdown_requested = True
        self.discovery_engine.shutdown_requested = True
    
    async def execute_intelligent_discovery(self):
        logger.info("Starting intelligent universal CMDB discovery...")
        
        discovery_context = {
            'project_id': self.project_id,
            'max_memory_mb': self.config.get('max_memory_mb', 1024),
            'max_disk_gb': self.config.get('max_disk_gb', 10),
            'parallel_workers': self.config.get('max_workers', 16),
            'intelligence_level': self.config.get('intelligence_level', 'expert'),
            'enable_deep_analysis': self.config.get('enable_deep_analysis', True),
            'enable_semantic_matching': self.config.get('enable_semantic_matching', True),
            'enable_predictive_enrichment': self.config.get('enable_predictive_enrichment', True)
        }
        
        intelligence_result = await self.intelligence_engine.enhance_discovery_intelligence(discovery_context)
        
        logger.info(f"Intelligence analysis complete. Strategy: {intelligence_result['strategy_recommendation']['strategy_name']}")
        
        discovery_stats = await self.discovery_engine.execute_intelligent_discovery(intelligence_result)
        
        learning_result = await self.intelligence_engine.learn_from_discovery_results(
            discovery_stats, intelligence_result.get('predictions', {})
        )
        
        final_results = {
            'discovery_stats': discovery_stats,
            'intelligence_insights': intelligence_result,
            'learning_results': learning_result,
            'cache_performance': self.cache_manager.get_stats(),
            'content_matching_insights': self.content_matcher.generate_discovery_insights({}),
            'intelligence_summary': self.intelligence_engine.get_intelligence_summary()
        }
        
        return final_results
    
    def close(self):
        if hasattr(self.discovery_engine, 'close'):
            self.discovery_engine.close()
        self.cache_manager.clear()

def parse_arguments():
    parser = argparse.ArgumentParser(description="Intelligent AO1 Universal CMDB Discovery System")
    
    parser.add_argument('--project', '-p', required=True, help='GCP Project ID')
    parser.add_argument('--intelligence-level', choices=['basic', 'advanced', 'expert'], default='expert', help='Intelligence level')
    parser.add_argument('--max-memory', type=int, default=2048, help='Max memory cache (MB)')
    parser.add_argument('--max-disk', type=int, default=20, help='Max disk cache (GB)')
    parser.add_argument('--config', '-c', default='intelligent_config.yaml', help='Configuration file path')
    parser.add_argument('--output-dir', default='output', help='Output directory')
    parser.add_argument('--cache-dir', default='.cache', help='Cache directory')
    parser.add_argument('--database', default='ao1_intelligent_cmdb.db', help='Database file')
    parser.add_argument('--dry-run', action='store_true', help='Estimate scope with intelligence')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--timeout', type=int, default=14400, help='Timeout in seconds (4 hours default)')
    
    return parser.parse_args()

async def estimate_intelligent_scope(project_id: str, config: dict):
    logger.info("Performing intelligent scope estimation...")
    
    try:
        from gcp_client import BigQueryClientManager
        client_manager = BigQueryClientManager(project_id)
        
        with client_manager.get_client() as client:
            datasets = list(client.list_datasets(project=project_id))
            
            intelligence_engine = IntelligenceEngine(config)
            content_matcher = IntelligentContentMatcher()
            
            discovery_context = {
                'project_id': project_id,
                'dataset_count': len(datasets),
                'estimated_tables': len(datasets) * 50,
                'intelligence_level': config.get('intelligence_level', 'expert')
            }
            
            for dataset in datasets[:5]:
                try:
                    dataset_ref = client.dataset(dataset.dataset_id, project=project_id)
                    tables = list(client.list_tables(dataset_ref))
                    discovery_context['table_count'] = len(tables)
                    break
                except:
                    continue
            
            intelligence_result = await intelligence_engine.enhance_discovery_intelligence(discovery_context)
            
            estimate = {
                'intelligent_analysis': intelligence_result,
                'total_datasets': len(datasets),
                'predicted_outcomes': intelligence_result.get('predictions', {}),
                'recommended_strategy': intelligence_result.get('strategy_recommendation', {}),
                'confidence_summary': intelligence_result.get('confidence_summary', {}),
                'optimization_insights': intelligence_result.get('insights', [])
            }
            
            logger.info(f"Intelligent estimation complete:")
            logger.info(f"  Datasets: {estimate['total_datasets']:,}")
            
            predictions = intelligence_result.get('predictions', {})
            if 'asset_count' in predictions and predictions['asset_count'].get('value'):
                estimated_assets = predictions['asset_count']['value']
                logger.info(f"  Predicted assets: {estimated_assets:,}")
            
            if 'processing_time' in predictions and predictions['processing_time'].get('value'):
                estimated_time = predictions['processing_time']['value']
                logger.info(f"  Predicted time: {estimated_time:.1f} seconds")
            
            strategy = intelligence_result.get('strategy_recommendation', {})
            if strategy.get('strategy_name'):
                logger.info(f"  Recommended strategy: {strategy['strategy_name']}")
            
            return estimate
            
    except Exception as e:
        logger.error(f"Intelligent scope estimation failed: {e}")
        return {'error': str(e)}

async def main():
    args = parse_arguments()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled for intelligent discovery")
    
    config = ConfigLoader.load_config(args.config) if Path(args.config).exists() else {}
    
    config.update({
        'max_memory_mb': args.max_memory,
        'max_disk_gb': args.max_disk,
        'cache_dir': args.cache_dir,
        'database_path': args.database,
        'intelligence_level': args.intelligence_level,
        'output_dir': args.output_dir,
        'enable_deep_analysis': True,
        'enable_semantic_matching': True,
        'enable_predictive_enrichment': True,
        'enable_quality_scoring': True,
        'enable_intelligent_caching': True,
        'enable_multi_source_fusion': True,
        'enable_conflict_resolution': True,
        'enable_pattern_recognition': True,
        'enable_anomaly_detection': True
    })
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    logger.info("Intelligent AO1 Universal CMDB Discovery System")
    logger.info(f"Project: {args.project}")
    logger.info(f"Intelligence Level: {args.intelligence_level}")
    logger.info(f"Memory: {args.max_memory:,}MB, Disk: {args.max_disk}GB")
    logger.info(f"Database: {args.database}")
    
    try:
        if args.dry_run:
            estimate = await estimate_intelligent_scope(args.project, config)
            
            if 'error' in estimate:
                logger.error(f"Estimation failed: {estimate['error']}")
                sys.exit(1)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            estimate_file = output_dir / f"intelligent_estimate_{timestamp}.json"
            
            with open(estimate_file, 'w') as f:
                json.dump(estimate, f, indent=2, default=str)
            
            logger.info(f"Intelligent scope estimate saved: {estimate_file}")
            return
        
        system = IntelligentAO1System(args.project, config, args)
        
        start_time = time.time()
        
        try:
            results = await asyncio.wait_for(
                system.execute_intelligent_discovery(),
                timeout=args.timeout
            )
        except asyncio.TimeoutError:
            logger.error(f"Discovery timed out after {args.timeout} seconds")
            sys.exit(1)
        
        processing_time = time.time() - start_time
        results['total_processing_time'] = processing_time
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        results_file = output_dir / f"intelligent_discovery_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        discovery_stats = results.get('discovery_stats', {})
        total_assets = discovery_stats.get('total_assets', 0)
        high_quality_assets = discovery_stats.get('high_quality_assets', 0)
        
        logger.info("Intelligent Discovery Complete!")
        logger.info(f"Processing time: {processing_time:.2f} seconds")
        logger.info(f"Total assets discovered: {total_assets:,}")
        logger.info(f"High quality assets: {high_quality_assets:,}")
        
        cache_stats = results.get('cache_performance', {})
        if cache_stats.get('hit_rate'):
            logger.info(f"Cache hit rate: {cache_stats['hit_rate']:.1f}%")
        
        intelligence_summary = results.get('intelligence_summary', {})
        if intelligence_summary.get('learning_iterations'):
            logger.info(f"Learning iterations: {intelligence_summary['learning_iterations']}")
        
        logger.info(f"Results saved: {results_file}")
        logger.info(f"Database: {args.database}")
        
        if processing_time > 0 and total_assets > 0:
            rate = total_assets / processing_time
            logger.info(f"Processing rate: {rate:.1f} assets/second")
        
        if total_assets == 0:
            logger.warning("No assets discovered - check authentication and data availability")
        
        system.close()
        
    except KeyboardInterrupt:
        logger.warning("Discovery interrupted by user")
        sys.exit(130)
        
    except Exception as e:
        logger.error(f"Discovery failed: {e}")
        
        if args.debug:
            import traceback
            traceback.print_exc()
        
        error_file = output_dir / f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(error_file, 'w') as f:
            json.dump({
                'error': str(e),
                'type': type(e).__name__,
                'timestamp': datetime.now().isoformat(),
                'project': args.project,
                'config': config
            }, f, indent=2)
        
        logger.error(f"Error details saved: {error_file}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        sys.exit(130)