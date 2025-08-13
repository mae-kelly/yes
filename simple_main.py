#!/usr/bin/env python3

import os
import sys
import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleDiscoverySystem:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.config = self._load_default_config()
    
    def _load_default_config(self):
        return {
            'intelligence_level': 'standard',
            'max_memory_mb': 1024,
            'max_disk_gb': 5,
            'database_path': 'simple_cmdb.db',
            'cache_dir': '.cache'
        }
    
    async def run_discovery(self):
        logger.info(f"Starting discovery for project: {self.project_id}")
        
        results = {
            'project_id': self.project_id,
            'start_time': datetime.now().isoformat(),
            'discovery_method': 'simplified',
            'status': 'completed'
        }
        
        try:
            from gcp_client import BigQueryClientManager
            client_manager = BigQueryClientManager(self.project_id)
            
            with client_manager.get_client() as client:
                datasets = list(client.list_datasets(max_results=10))
                results['datasets_found'] = len(datasets)
                
                tables_found = 0
                for dataset in datasets:
                    tables = list(client.list_tables(dataset, max_results=50))
                    tables_found += len(tables)
                
                results['tables_found'] = tables_found
                results['estimated_assets'] = tables_found * 100
            
        except Exception as e:
            logger.error(f"Discovery failed: {e}")
            results['error'] = str(e)
            results['status'] = 'failed'
        
        results['end_time'] = datetime.now().isoformat()
        return results

def main():
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
    if not project_id:
        logger.error("GOOGLE_CLOUD_PROJECT environment variable not set")
        return 1
    
    system = SimpleDiscoverySystem(project_id)
    
    try:
        results = asyncio.run(system.run_discovery())
        
        output_file = f"discovery_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Discovery completed. Results saved to {output_file}")
        
        if results['status'] == 'completed':
            logger.info(f"Found {results['datasets_found']} datasets, {results['tables_found']} tables")
            logger.info(f"Estimated {results['estimated_assets']} assets")
        
        return 0
        
    except Exception as e:
        logger.error(f"Discovery system failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())