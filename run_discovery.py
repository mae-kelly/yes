# run_discovery.py
"""
main orchestration script for ao1 log visibility measurement system
coordinates ml training, bigquery discovery, and database creation
demonstrates intelligent column understanding without hardcoding
"""

import os
import sys
import logging
import asyncio
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd
import duckdb

# import our custom modules
from ml_training_engine import (
    CorporateProxyHandler,
    ITInfrastructureDatasetDownloader,
    AdvancedMLTrainer
)
from discovery_engine import (
    BigQueryIntelligentReader,
    DuckDBAssetDatabase,
    AssetRecord
)

logger = logging.getLogger(__name__)

class AO1VisibilityOrchestrator:
    """
    orchestrates the complete visibility measurement process
    manages ml training, discovery, and reporting for ao1 requirements
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        initializes with configuration for corporate environment
        sets up all components for visibility measurement
        """
        self.config = config
        self.project_id = config.get('project_id')
        self.output_dir = Path(config.get('output_dir', 'visibility_output'))
        self.output_dir.mkdir(exist_ok=True)
        
        # tracking metrics
        self.metrics = {
            'start_time': datetime.now(),
            'ml_training_completed': False,
            'datasets_downloaded': 0,
            'models_trained': 0,
            'tables_analyzed': 0,
            'assets_discovered': 0,
            'coverage_gaps_identified': 0
        }
        
        logger.info("ao1 visibility orchestrator initialized")
    
    async def run_complete_discovery(self) -> Dict[str, Any]:
        """
        runs the complete discovery process end-to-end
        demonstrates intelligent understanding of bigquery data
        """
        logger.info("=" * 80)
        logger.info("AO1 LOG VISIBILITY MEASUREMENT SYSTEM")
        logger.info("intelligent bigquery analysis without hardcoding")
        logger.info("=" * 80)
        
        results = {}
        
        # step 1: setup corporate proxy
        logger.info("\nstep 1: configuring corporate network access...")
        proxy_handler = self._setup_proxy()
        
        # step 2: download training datasets
        logger.info("\nstep 2: downloading real-world infrastructure datasets...")
        datasets = await self._download_training_data(proxy_handler)
        results['training_datasets'] = len(datasets)
        
        # step 3: train ml models
        logger.info("\nstep 3: training ml models to understand column meanings...")
        models_trained = await self._train_models(datasets)
        results['models_trained'] = models_trained
        
        # step 4: discover assets in bigquery
        logger.info("\nstep 4: discovering assets across all bigquery tables...")
        assets = await self._discover_assets()
        results['assets_discovered'] = len(assets)
        
        # step 5: create visibility database
        logger.info("\nstep 5: creating duckdb visibility database...")
        db_metrics = self._create_database(assets)
        results['database_metrics'] = db_metrics
        
        # step 6: generate visibility report
        logger.info("\nstep 6: generating visibility reports...")
        reports = self._generate_reports(db_metrics)
        results['reports_generated'] = reports
        
        # calculate total time
        self.metrics['end_time'] = datetime.now()
        self.metrics['total_duration'] = (self.metrics['end_time'] - self.metrics['start_time']).total_seconds()
        
        # display summary
        self._display_summary(results)
        
        return results
    
    def _setup_proxy(self) -> CorporateProxyHandler:
        """
        configures proxy for corporate environment
        tries multiple methods to ensure connectivity
        """
        proxy_handler = CorporateProxyHandler()
        
        if proxy_handler.working_method:
            logger.info(f"  ✓ proxy configured using: {proxy_handler.working_method}")
        else:
            logger.warning("  ! no proxy detected, using direct connection")
        
        return proxy_handler
    
    async def _download_training_data(self, proxy_handler: CorporateProxyHandler) -> Dict[str, pd.DataFrame]:
        """
        downloads datasets for understanding the 17 column requirements
        uses real data from the internet, not synthetic
        """
        downloader = ITInfrastructureDatasetDownloader(proxy_handler)
        datasets = downloader.download_all_required_datasets()
        
        # display download summary
        logger.info("\n  downloaded datasets:")
        for name, df in datasets.items():
            if not df.empty:
                logger.info(f"    • {name}: {len(df)} rows")
                self.metrics['datasets_downloaded'] += 1
        
        # save datasets for inspection
        datasets_dir = self.output_dir / "training_datasets"
        datasets_dir.mkdir(exist_ok=True)
        
        for name, df in datasets.items():
            if not df.empty:
                df.to_csv(datasets_dir / f"{name}.csv", index=False)
        
        logger.info(f"  ✓ saved {self.metrics['datasets_downloaded']} datasets to {datasets_dir}")
        
        return datasets
    
    async def _train_models(self, datasets: Dict[str, pd.DataFrame]) -> int:
        """
        trains ml models on downloaded datasets
        creates models that truly understand column content
        """
        trainer = AdvancedMLTrainer(datasets)
        trainer.train_all_models()
        
        # save trained models
        model_dir = Path("trained_models")
        model_dir.mkdir(exist_ok=True)
        
        models_saved = 0
        for name, model in trainer.models.items():
            try:
                import joblib
                model_path = model_dir / f"{name}_model.pkl"
                joblib.dump(model, model_path)
                logger.info(f"  ✓ saved model: {name}")
                models_saved += 1
                self.metrics['models_trained'] += 1
            except Exception as e:
                logger.error(f"  ✗ failed to save model {name}: {e}")
        
        logger.info(f"  ✓ trained and saved {models_saved} ml models")
        
        return models_saved
    
    async def _discover_assets(self) -> Dict[str, AssetRecord]:
        """
        discovers all assets across bigquery using ml understanding
        demonstrates intelligent column identification
        """
        reader = BigQueryIntelligentReader(self.project_id)
        
        # discover assets
        assets = await reader.discover_all_assets()
        
        self.metrics['assets_discovered'] = len(assets)
        
        # save discovered assets
        assets_file = self.output_dir / "discovered_assets.json"
        assets_data = {}
        
        for hostname, asset in assets.items():
            assets_data[hostname] = {
                'hostname': asset.hostname,
                'infrastructure_type': asset.infrastructure_type,
                'region': asset.region,
                'country': asset.country,
                'business_unit': asset.business_unit,
                'datacenter': asset.datacenter,
                'cloud_region': asset.cloud_region,
                'cio': asset.cio,
                'apm': asset.apm,
                'application_class': asset.application_class,
                'system_classification': asset.system_classification,
                'edr_coverage': asset.edr_coverage,
                'tanium_coverage': asset.tanium_coverage,
                'dlp_coverage': asset.dlp_coverage,
                'splunk_coverage': asset.splunk_coverage,
                'domain': asset.domain,
                'source_tables': list(asset.source_tables),
                'data_quality_score': asset.data_quality_score
            }
        
        with open(assets_file, 'w') as f:
            json.dump(assets_data, f, indent=2, default=str)
        
        logger.info(f"  ✓ discovered {len(assets)} unique assets")
        logger.info(f"  ✓ saved to {assets_file}")
        
        return assets
    
    def _create_database(self, assets: Dict[str, AssetRecord]) -> Dict[str, Any]:
        """
        creates duckdb database with discovered assets
        provides fast analytical queries for visibility metrics
        """
        db_path = self.output_dir / "asset_visibility.duckdb"
        db = DuckDBAssetDatabase(str(db_path))
        
        # insert assets
        db.insert_assets(assets)
        
        # get metrics
        metrics = db.get_visibility_metrics()
        
        # export to csv
        csv_path = self.output_dir / "asset_visibility.csv"
        db.export_to_csv(str(csv_path))
        
        db.close()
        
        logger.info(f"  ✓ created database: {db_path}")
        logger.info(f"  ✓ exported csv: {csv_path}")
        
        return metrics
    
    def _generate_reports(self, db_metrics: Dict[str, Any]) -> List[str]:
        """
        generates visibility reports for ao1 requirements
        shows coverage gaps and improvement opportunities
        """
        reports = []
        
        # generate coverage report
        coverage_report = self.output_dir / "coverage_report.md"
        with open(coverage_report, 'w') as f:
            f.write("# AO1 LOG VISIBILITY COVERAGE REPORT\n\n")
            f.write(f"generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## executive summary\n\n")
            f.write(f"- **total assets discovered**: {db_metrics.get('total_assets', 0):,}\n")
            f.write(f"- **edr coverage**: {db_metrics.get('edr_coverage_percentage', 0):.1f}%\n")
            f.write(f"- **tanium coverage**: {db_metrics.get('tanium_coverage_percentage', 0):.1f}%\n")
            f.write(f"- **dlp coverage**: {db_metrics.get('dlp_coverage_percentage', 0):.1f}%\n")
            f.write(f"- **splunk logging**: {db_metrics.get('splunk_coverage_percentage', 0):.1f}%\n\n")
            
            f.write("## infrastructure distribution\n\n")
            infra_dist = db_metrics.get('infrastructure_distribution', {})
            for infra_type, count in infra_dist.items():
                f.write(f"- **{infra_type or 'unknown'}**: {count:,} assets\n")
            f.write("\n")
            
            f.write("## regional distribution\n\n")
            region_dist = db_metrics.get('regional_distribution', {})
            for region, count in region_dist.items():
                f.write(f"- **{region or 'unknown'}**: {count:,} assets\n")
            f.write("\n")
            
            f.write("## coverage gaps identified\n\n")
            
            # identify gaps
            total = db_metrics.get('total_assets', 0)
            if total > 0:
                edr_gap = total - (total * db_metrics.get('edr_coverage_percentage', 0) / 100)
                tanium_gap = total - (total * db_metrics.get('tanium_coverage_percentage', 0) / 100)
                dlp_gap = total - (total * db_metrics.get('dlp_coverage_percentage', 0) / 100)
                splunk_gap = total - (total * db_metrics.get('splunk_coverage_percentage', 0) / 100)
                
                f.write(f"- **edr coverage gap**: {int(edr_gap):,} assets without edr\n")
                f.write(f"- **tanium coverage gap**: {int(tanium_gap):,} assets without tanium\n")
                f.write(f"- **dlp coverage gap**: {int(dlp_gap):,} assets without dlp\n")
                f.write(f"- **splunk coverage gap**: {int(splunk_gap):,} assets without splunk\n\n")
                
                self.metrics['coverage_gaps_identified'] = int(edr_gap + tanium_gap + dlp_gap + splunk_gap)
            
            f.write("## recommendations\n\n")
            f.write("1. prioritize edr deployment to uncovered assets\n")
            f.write("2. expand splunk logging to achieve 100% coverage\n")
            f.write("3. implement tanium on critical infrastructure\n")
            f.write("4. deploy dlp agents on sensitive data systems\n")
        
        reports.append(str(coverage_report))
        logger.info(f"  ✓ generated coverage report: {coverage_report}")
        
        # generate metrics json
        metrics_file = self.output_dir / "visibility_metrics.json"
        with open(metrics_file, 'w') as f:
            json.dump(db_metrics, f, indent=2)
        
        reports.append(str(metrics_file))
        logger.info(f"  ✓ generated metrics file: {metrics_file}")
        
        return reports
    
    def _display_summary(self, results: Dict[str, Any]):
        """
        displays final summary of discovery results
        shows the power of ml-based column understanding
        """
        logger.info("\n" + "=" * 80)
        logger.info("DISCOVERY COMPLETE - SUMMARY")
        logger.info("=" * 80)
        
        logger.info("\nml training results:")
        logger.info(f"  • datasets downloaded: {results.get('training_datasets', 0)}")
        logger.info(f"  • models trained: {results.get('models_trained', 0)}")
        
        logger.info("\ndiscovery results:")
        logger.info(f"  • assets discovered: {results.get('assets_discovered', 0):,}")
        logger.info(f"  • coverage gaps identified: {self.metrics.get('coverage_gaps_identified', 0):,}")
        
        logger.info("\nvisibility metrics:")
        db_metrics = results.get('database_metrics', {})
        logger.info(f"  • edr coverage: {db_metrics.get('edr_coverage_percentage', 0):.1f}%")
        logger.info(f"  • tanium coverage: {db_metrics.get('tanium_coverage_percentage', 0):.1f}%")
        logger.info(f"  • dlp coverage: {db_metrics.get('dlp_coverage_percentage', 0):.1f}%")
        logger.info(f"  • splunk coverage: {db_metrics.get('splunk_coverage_percentage', 0):.1f}%")
        
        logger.info("\nprocessing time:")
        duration = self.metrics.get('total_duration', 0)
        logger.info(f"  • total time: {duration:.1f} seconds ({duration/60:.1f} minutes)")
        
        logger.info("\noutput files:")
        logger.info(f"  • directory: {self.output_dir}")
        logger.info("  • asset_visibility.duckdb - queryable database")
        logger.info("  • asset_visibility.csv - spreadsheet export")
        logger.info("  • coverage_report.md - executive report")
        logger.info("  • discovered_assets.json - raw asset data")
        
        logger.info("\n" + "=" * 80)
        logger.info("system demonstrates intelligent column understanding")
        logger.info("no hardcoding required - ml models understand your data")
        logger.info("=" * 80)

def main():
    """
    main entry point for ao1 visibility measurement system
    parses arguments and runs discovery
    """
    parser = argparse.ArgumentParser(
        description="ao1 log visibility measurement - intelligent bigquery analysis"
    )
    parser.add_argument(
        "--project-id",
        required=True,
        help="gcp project id to analyze"
    )
    parser.add_argument(
        "--output-dir",
        default="visibility_output",
        help="output directory for results (default: visibility_output)"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="logging level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    # setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # configuration
    config = {
        'project_id': args.project_id,
        'output_dir': args.output_dir
    }
    
    # run orchestrator
    orchestrator = AO1VisibilityOrchestrator(config)
    
    # run async discovery
    results = asyncio.run(orchestrator.run_complete_discovery())
    
    logger.info("\n✓ ao1 visibility measurement complete")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())