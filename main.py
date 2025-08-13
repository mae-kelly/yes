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
from typing import Dict, List, Any

# Import all the discovery engines and components
from intelligent_discovery_engine import IntelligentUniversalCMDBBuilder
from content_based_discovery import ContentBasedCMDBBuilder
from ao1_ai_integration import AO1EnhancedDiscoveryEngine
from intelligent_cache_manager import IntelligentCacheManager
from intelligent_content_matcher import IntelligentContentMatcher
from intelligence_engine import IntelligenceEngine
from enhanced_ai_intelligence import AO1SuperIntelligentEngine
from gcp_client import BigQueryClientManager
from signal_handler import SignalHandler
from progress_tracker import ProgressTracker
from checkpoint_manager import CheckpointManager
import yaml

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IntelligentAO1DiscoverySystem:
    def __init__(self, project_id: str, config: Dict[str, Any], args=None):
        self.project_id = project_id
        self.config = config
        self.args = args
        
        # Initialize signal handling
        self.signal_handler = SignalHandler()
        
        # Initialize progress tracking
        self.progress_tracker = ProgressTracker()
        
        # Initialize checkpoint manager
        self.checkpoint_manager = CheckpointManager()
        
        # Initialize intelligent cache
        self.cache_manager = IntelligentCacheManager(
            cache_dir=config.get('cache_dir', '.cache'),
            max_memory_mb=config.get('max_memory_mb', 2048),
            max_disk_gb=config.get('max_disk_gb', 20)
        )
        
        # Initialize intelligent content matcher
        self.content_matcher = IntelligentContentMatcher()
        
        # Initialize intelligence engine
        self.intelligence_engine = IntelligenceEngine(config)
        
        # Initialize AI super engine
        self.ai_super_engine = AO1SuperIntelligentEngine(config)
        
        # Initialize BigQuery clients
        self.client_managers = {}
        try:
            self.client_managers[project_id] = BigQueryClientManager(project_id)
            logger.info(f"Connected to main project: {project_id}")
        except Exception as e:
            logger.error(f"Failed to connect to project {project_id}: {e}")
            raise
        
        # Try to connect to Chronicle if available
        try:
            self.client_managers["chronicle-fisv"] = BigQueryClientManager("chronicle-fisv")
            logger.info("Connected to Chronicle project")
        except Exception as e:
            logger.warning(f"Chronicle connection not available: {e}")
        
        # Initialize discovery engines
        self.intelligent_engine = IntelligentUniversalCMDBBuilder(
            project_id=project_id,
            config=config,
            cache_manager=self.cache_manager,
            content_matcher=self.content_matcher,
            intelligence_engine=self.intelligence_engine
        )
        
        self.content_based_engine = ContentBasedCMDBBuilder(
            project_id=project_id,
            config=config,
            cache_manager=self.cache_manager,
            content_matcher=self.content_matcher,
            intelligence_engine=self.intelligence_engine
        )
        
        self.ao1_ai_engine = AO1EnhancedDiscoveryEngine(
            project_id=project_id,
            config=config,
            cache_manager=self.cache_manager,
            original_content_matcher=self.content_matcher,
            intelligence_engine=self.intelligence_engine
        )
        
        logger.info("Intelligent AO1 Discovery System initialized")
    
    async def execute_comprehensive_discovery(self) -> Dict[str, Any]:
        """Execute all discovery methods and combine results"""
        logger.info("🚀 Starting comprehensive AO1 discovery with all engines")
        
        start_time = time.time()
        results = {
            'discovery_metadata': {
                'start_time': datetime.now().isoformat(),
                'project_id': self.project_id,
                'config_intelligence_level': self.config.get('intelligence_level', 'standard'),
                'engines_used': []
            }
        }
        
        try:
            # Phase 1: Intelligence Analysis
            logger.info("Phase 1: Performing intelligence analysis and strategy selection")
            
            discovery_context = {
                'project_id': self.project_id,
                'dataset_count': await self._estimate_dataset_count(),
                'table_count': await self._estimate_table_count(),
                'intelligence_level': self.config.get('intelligence_level', 'expert'),
                'max_memory_mb': self.config.get('max_memory_mb', 2048),
                'max_disk_gb': self.config.get('max_disk_gb', 20)
            }
            
            intelligence_result = await self.intelligence_engine.enhance_discovery_intelligence(discovery_context)
            results['intelligence_analysis'] = intelligence_result
            
            # Phase 2: Intelligent Universal CMDB Discovery
            if not self.signal_handler.shutdown_requested:
                logger.info("Phase 2: Running Intelligent Universal CMDB Discovery")
                
                intelligent_results = await self.intelligent_engine.execute_intelligent_discovery(intelligence_result)
                results['intelligent_discovery'] = intelligent_results
                results['discovery_metadata']['engines_used'].append('intelligent_universal')
                
                self.progress_tracker.update_stats(
                    endpoints_discovered=intelligent_results.get('total_assets', 0)
                )
            
            # Phase 3: Content-Based Discovery
            if not self.signal_handler.shutdown_requested:
                logger.info("Phase 3: Running Content-Based Discovery (analyzing all table content)")
                
                content_results = await self.content_based_engine.execute_content_based_discovery(intelligence_result)
                results['content_based_discovery'] = content_results
                results['discovery_metadata']['engines_used'].append('content_based')
                
                self.progress_tracker.update_stats(
                    tables_processed=content_results.get('tables_analyzed', 0),
                    endpoints_discovered=content_results.get('total_unique_assets', 0)
                )
            
            # Phase 4: AO1 AI-Enhanced Discovery
            if not self.signal_handler.shutdown_requested:
                logger.info("Phase 4: Running AO1 AI-Enhanced Discovery")
                
                ao1_results = await self.ao1_ai_engine.execute_ao1_enhanced_discovery(intelligence_result)
                results['ao1_ai_discovery'] = ao1_results
                results['discovery_metadata']['engines_used'].append('ao1_ai_enhanced')
            
            # Phase 5: Learning and Optimization
            if not self.signal_handler.shutdown_requested:
                logger.info("Phase 5: Learning from results and optimizing")
                
                learning_results = await self.intelligence_engine.learn_from_discovery_results(
                    results, intelligence_result.get('predictions', {})
                )
                results['learning_analysis'] = learning_results
            
            # Calculate final metrics
            processing_time = time.time() - start_time
            results['discovery_metadata'].update({
                'end_time': datetime.now().isoformat(),
                'total_processing_time_seconds': processing_time,
                'processing_time_formatted': f"{processing_time/60:.1f} minutes",
                'final_stats': self.progress_tracker.get_stats(),
                'cache_stats': self.cache_manager.get_stats()
            })
            
            logger.info(f"✅ Comprehensive discovery completed in {processing_time/60:.1f} minutes")
            return results
            
        except Exception as e:
            logger.error(f"Discovery failed: {e}")
            results['error'] = {
                'message': str(e),
                'type': type(e).__name__,
                'processing_time': time.time() - start_time
            }
            return results
    
    async def _estimate_dataset_count(self) -> int:
        """Estimate number of datasets for intelligence planning"""
        try:
            with self.client_managers[self.project_id].get_client() as client:
                datasets = list(client.list_datasets(project=self.project_id, max_results=1000))
                return len(datasets)
        except Exception as e:
            logger.warning(f"Could not estimate dataset count: {e}")
            return 10  # Conservative estimate
    
    async def _estimate_table_count(self) -> int:
        """Estimate number of tables for intelligence planning"""
        try:
            total_tables = 0
            with self.client_managers[self.project_id].get_client() as client:
                datasets = list(client.list_datasets(project=self.project_id, max_results=100))
                for dataset in datasets[:10]:  # Sample first 10 datasets
                    tables = list(client.list_tables(dataset, max_results=1000))
                    total_tables += len(tables)
            
            # Extrapolate from sample
            if len(datasets) > 10:
                total_tables = int(total_tables * (len(datasets) / 10))
            
            return total_tables
        except Exception as e:
            logger.warning(f"Could not estimate table count: {e}")
            return 100  # Conservative estimate
    
    def generate_unified_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a unified report from all discovery results"""
        report = {
            'executive_summary': {
                'discovery_timestamp': datetime.now().isoformat(),
                'project_id': self.project_id,
                'total_processing_time': results.get('discovery_metadata', {}).get('total_processing_time_seconds', 0),
                'engines_used': results.get('discovery_metadata', {}).get('engines_used', []),
                'intelligence_level': self.config.get('intelligence_level', 'standard')
            },
            'asset_discovery_summary': {},
            'visibility_analysis': {},
            'intelligence_insights': [],
            'recommendations': [],
            'database_files': []
        }
        
        # Aggregate asset counts from all engines
        total_assets = 0
        high_quality_assets = 0
        
        if 'intelligent_discovery' in results:
            intelligent_data = results['intelligent_discovery']
            total_assets += intelligent_data.get('total_assets', 0)
            high_quality_assets += intelligent_data.get('high_quality_assets', 0)
            report['database_files'].append(intelligent_data.get('database_path'))
        
        if 'content_based_discovery' in results:
            content_data = results['content_based_discovery']
            total_assets += content_data.get('total_unique_assets', 0)
        
        if 'ao1_ai_discovery' in results:
            ao1_data = results['ao1_ai_discovery']
            if isinstance(ao1_data, dict) and 'discovery_stats' in ao1_data:
                total_assets += ao1_data['discovery_stats'].get('total_assets', 0)
        
        report['asset_discovery_summary'] = {
            'total_assets_discovered': total_assets,
            'high_quality_assets': high_quality_assets,
            'quality_rate': (high_quality_assets / max(total_assets, 1)) * 100
        }
        
        # Extract visibility analysis
        if 'ao1_ai_discovery' in results and isinstance(results['ao1_ai_discovery'], dict):
            ao1_data = results['ao1_ai_discovery']
            if 'visibility_analysis' in ao1_data:
                report['visibility_analysis'] = ao1_data['visibility_analysis']
        
        # Extract intelligence insights
        if 'intelligence_analysis' in results:
            intelligence_data = results['intelligence_analysis']
            insights = intelligence_data.get('insights', [])
            report['intelligence_insights'] = insights
        
        # Extract recommendations
        all_recommendations = []
        
        if 'ao1_ai_discovery' in results and isinstance(results['ao1_ai_discovery'], dict):
            ao1_recommendations = results['ao1_ai_discovery'].get('recommendations', [])
            all_recommendations.extend(ao1_recommendations)
        
        if 'learning_analysis' in results:
            learning_recommendations = results['learning_analysis'].optimization_recommendations
            all_recommendations.extend(learning_recommendations)
        
        report['recommendations'] = list(set(all_recommendations))  # Remove duplicates
        
        return report
    
    def close(self):
        """Clean up all resources"""
        try:
            if hasattr(self.intelligent_engine, 'close'):
                self.intelligent_engine.close()
            if hasattr(self.content_based_engine, 'close'):
                self.content_based_engine.close()
            logger.info("All discovery engines closed successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

def load_config(config_file: str) -> Dict[str, Any]:
    """Load configuration from YAML file"""
    default_config = {
        'intelligence_level': 'expert',
        'max_memory_mb': 2048,
        'max_disk_gb': 20,
        'cache_dir': '.cache',
        'database_path': 'ao1_intelligent_cmdb.db',
        'enable_ai_classification': True,
        'enable_deep_analysis': True,
        'enable_semantic_matching': True,
        'enable_predictive_enrichment': True
    }
    
    if Path(config_file).exists():
        try:
            with open(config_file, 'r') as f:
                user_config = yaml.safe_load(f)
                default_config.update(user_config)
        except Exception as e:
            logger.warning(f"Could not load config file {config_file}: {e}")
    
    return default_config

def parse_arguments():
    parser = argparse.ArgumentParser(description="Intelligent AO1 CMDB Discovery System")
    
    parser.add_argument('--project', '-p', required=True,
                       help='GCP Project ID (e.g., prj-fisv)')
    parser.add_argument('--intelligence-level', choices=['basic', 'standard', 'advanced', 'expert'],
                       default='expert', help='Intelligence level for discovery')
    parser.add_argument('--max-memory', type=int, default=2048,
                       help='Maximum memory cache in MB')
    parser.add_argument('--max-disk', type=int, default=20,
                       help='Maximum disk cache in GB')
    parser.add_argument('--config', '-c', default='intelligent_config.yaml',
                       help='Configuration file path')
    parser.add_argument('--output-dir', default='output',
                       help='Output directory for results')
    parser.add_argument('--database', default='ao1_intelligent_cmdb.db',
                       help='Database file name')
    parser.add_argument('--cache-dir', default='.cache',
                       help='Cache directory')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    parser.add_argument('--dry-run', action='store_true',
                       help='Perform estimation only, no actual discovery')
    parser.add_argument('--timeout', type=int, default=0,
                       help='Discovery timeout in seconds (0 = no timeout)')
    
    return parser.parse_args()

async def main():
    args = parse_arguments()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")
    
    # Load configuration
    config = load_config(args.config)
    
    # Override config with command line arguments
    config.update({
        'intelligence_level': args.intelligence_level,
        'max_memory_mb': args.max_memory,
        'max_disk_gb': args.max_disk,
        'database_path': args.database,
        'cache_dir': args.cache_dir,
        'output_dir': args.output_dir,
        'debug_mode': args.debug,
        'dry_run': args.dry_run,
        'timeout_seconds': args.timeout
    })
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    logger.info("♡₊˚ ｡⋅˚♡ ✧ ‧₊˚ ⋅  Intelligent AO1 Discovery System  ⋅ ˚₊‧ ✧ ♡˚⋅｡ ˚₊♡")
    logger.info(f"Project: {args.project}")
    logger.info(f"Intelligence Level: {args.intelligence_level}")
    logger.info(f"Memory: {args.max_memory:,}MB, Disk: {args.max_disk}GB")
    logger.info(f"Database: {args.database}")
    logger.info(f"Output: {args.output_dir}")
    
    system = None
    try:
        # Initialize the discovery system
        system = IntelligentAO1DiscoverySystem(args.project, config, args)
        
        if args.dry_run:
            logger.info("🔍 Performing dry run - estimation only")
            discovery_context = {
                'project_id': args.project,
                'dataset_count': await system._estimate_dataset_count(),
                'table_count': await system._estimate_table_count(),
                'intelligence_level': args.intelligence_level
            }
            
            intelligence_result = await system.intelligence_engine.enhance_discovery_intelligence(discovery_context)
            
            predictions = intelligence_result.get('predictions', {})
            logger.info("📊 Discovery Estimates:")
            logger.info(f"  Datasets: {discovery_context['dataset_count']:,}")
            logger.info(f"  Tables: {discovery_context['table_count']:,}")
            logger.info(f"  Estimated Assets: {predictions.get('asset_count', {}).get('value', 'Unknown'):,}")
            logger.info(f"  Estimated Duration: {predictions.get('processing_time', {}).get('value', 'Unknown')} seconds")
            
            # Save dry run results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dry_run_file = output_dir / f"dry_run_estimate_{timestamp}.json"
            
            with open(dry_run_file, 'w') as f:
                json.dump({
                    'dry_run': True,
                    'discovery_context': discovery_context,
                    'intelligence_result': intelligence_result,
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2, default=str)
            
            logger.info(f"📄 Dry run results saved: {dry_run_file}")
        
        else:
            # Execute full discovery
            logger.info("🚀 Starting full intelligent discovery process")
            
            # Set timeout if specified
            if args.timeout > 0:
                results = await asyncio.wait_for(
                    system.execute_comprehensive_discovery(),
                    timeout=args.timeout
                )
            else:
                results = await system.execute_comprehensive_discovery()
            
            # Generate unified report
            logger.info("📊 Generating unified discovery report")
            report = system.generate_unified_report(results)
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            results_file = output_dir / f"intelligent_discovery_results_{timestamp}.json"
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            report_file = output_dir / f"intelligent_discovery_report_{timestamp}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"✅ Discovery completed successfully!")
            logger.info(f"📄 Results saved: {results_file}")
            logger.info(f"📊 Report saved: {report_file}")
            
            # Print summary
            summary = report['asset_discovery_summary']
            logger.info(f"📈 Assets discovered: {summary.get('total_assets_discovered', 0):,}")
            logger.info(f"⭐ High quality assets: {summary.get('high_quality_assets', 0):,}")
            logger.info(f"📊 Quality rate: {summary.get('quality_rate', 0):.1f}%")
            
            # Print recommendations
            recommendations = report.get('recommendations', [])
            if recommendations:
                logger.info("💡 Key recommendations:")
                for i, rec in enumerate(recommendations[:3], 1):
                    logger.info(f"   {i}. {rec}")
    
    except KeyboardInterrupt:
        logger.warning("⚠️ Discovery interrupted by user")
        return 130
    
    except asyncio.TimeoutError:
        logger.error(f"⏰ Discovery timed out after {args.timeout} seconds")
        return 124
    
    except Exception as e:
        logger.error(f"❌ Discovery failed: {e}")
        
        if args.debug:
            import traceback
            traceback.print_exc()
        
        # Save error details
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        error_file = output_dir / f"error_{timestamp}.json"
        
        with open(error_file, 'w') as f:
            json.dump({
                'error': str(e),
                'error_type': type(e).__name__,
                'timestamp': datetime.now().isoformat(),
                'project': args.project,
                'config': config
            }, f, indent=2, default=str)
        
        logger.error(f"💾 Error details saved: {error_file}")
        return 1
    
    finally:
        if system:
            system.close()

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code or 0)
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        sys.exit(130)