#!/usr/bin/env python3
"""
BigQuery Scanner
===============
High-performance BigQuery dataset and table scanner.
"""

from typing import Dict, List
from google.cloud.exceptions import NotFound, Forbidden, BadRequest
from bigquery_auth import get_bigquery_client
from ao1_config_and_logging import logger

class BigQueryScanner:
    """Smart BigQuery scanner with error handling."""
    
    def __init__(self):
        self.client = None
        self.stats = {
            'datasets_scanned': 0,
            'tables_scanned': 0, 
            'fields_analyzed': 0,
            'ao1_matches': 0
        }
    
    def authenticate(self) -> bool:
        """Authenticate with BigQuery."""
        try:
            self.client = get_bigquery_client()
            return True
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    def scan_project(self, analyzer, max_datasets: int = 20, 
                    max_tables: int = 50) -> Dict[str, List]:
        """Scan BigQuery project for AO1 fields."""
        if not self.client:
            logger.error("Not authenticated")
            return {}
        
        results = {}
        
        try:
            # Get datasets
            datasets = list(self.client.list_datasets())
            self.stats['datasets_scanned'] = min(len(datasets), max_datasets)
            
            logger.info(f"Scanning {self.stats['datasets_scanned']} datasets")
            
            for dataset in datasets[:max_datasets]:
                dataset_id = dataset.dataset_id
                logger.info(f"Analyzing dataset: {dataset_id}")
                
                dataset_results = self._scan_dataset(
                    dataset_id, analyzer, max_tables
                )
                
                if dataset_results:
                    # Sort by strategic priority
                    dataset_results.sort(
                        key=lambda x: (x.strategic_priority, x.row_count), 
                        reverse=True
                    )
                    results[dataset_id] = dataset_results
                    
                    logger.info(f"Dataset {dataset_id}: "
                              f"{len(dataset_results)} AO1 fields found")
        
        except Exception as e:
            logger.error(f"Project scan failed: {e}")
        
        self._log_stats()
        return results
    
    def _scan_dataset(self, dataset_id: str, analyzer, 
                     max_tables: int) -> List:
        """Scan single dataset."""
        results = []
        
        try:
            tables = list(self.client.list_tables(dataset_id))
            
            # Sort by row count for priority processing
            table_data = []
            for table in tables[:max_tables]:
                try:
                    table_ref = self.client.get_table(table.reference)
                    row_count = table_ref.num_rows or 0
                    table_data.append((table_ref, row_count))
                except Exception as e:
                    logger.debug(f"Error getting table info for {table.table_id}: {e}")
                    continue
            
            # Sort by row count (largest first)
            table_data.sort(key=lambda x: x[1], reverse=True)
            
            for table_ref, row_count in table_data:
                self.stats['tables_scanned'] += 1
                
                try:
                    table_results = self._scan_table(
                        table_ref, dataset_id, row_count, analyzer
                    )
                    results.extend(table_results)
                    
                except Exception as e:
                    logger.debug(f"Error scanning table {table_ref.table_id}: {e}")
                    continue
        
        except (Forbidden, NotFound) as e:
            logger.warning(f"Access denied for dataset {dataset_id}: {e}")
        except Exception as e:
            logger.error(f"Error scanning dataset {dataset_id}: {e}")
        
        return results
    
    def _scan_table(self, table_ref, dataset_id: str, 
                   row_count: int, analyzer) -> List:
        """Scan single table for AO1 fields."""
        results = []
        
        try:
            for field in table_ref.schema:
                self.stats['fields_analyzed'] += 1
                
                analysis = analyzer.analyze_field(
                    field_name=field.name,
                    table_name=table_ref.table_id,
                    dataset_name=dataset_id,
                    row_count=row_count
                )
                
                if analysis:
                    results.append(analysis)
                    self.stats['ao1_matches'] += 1
                    
                    logger.debug(f"AO1 match: {field.name} "
                               f"({analysis.match_type})")
        
        except Exception as e:
            logger.debug(f"Error analyzing table schema: {e}")
        
        return results
    
    def _log_stats(self):
        """Log scanning statistics."""
        logger.info("Scanning completed:")
        logger.info(f"  Datasets: {self.stats['datasets_scanned']}")
        logger.info(f"  Tables: {self.stats['tables_scanned']}")
        logger.info(f"  Fields: {self.stats['fields_analyzed']:,}")
        logger.info(f"  AO1 matches: {self.stats['ao1_matches']}")
    
    def get_stats(self) -> Dict:
        """Get scanning statistics."""
        return self.stats.copy()

def get_scanner():
    """Get configured BigQuery scanner."""
    return BigQueryScanner()