#!/usr/bin/env python3
"""
Simple startup script for the Intelligent AO1 Discovery System
This ensures all components work together properly
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Setup logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_and_fix_dependencies():
    """Check for missing dependencies and fix them"""
    logger.info("Checking system dependencies...")
    
    # Check if integration fixes are needed
    if not Path('comprehensive_discovery_engine.py').exists():
        logger.info("Creating missing comprehensive_discovery_engine.py...")
        try:
            from integration_fixes import create_comprehensive_discovery_engine
            create_comprehensive_discovery_engine()
        except ImportError:
            logger.warning("Integration fixes not available, creating minimal version...")
            # Create a minimal version
            with open('comprehensive_discovery_engine.py', 'w') as f:
                f.write('''#!/usr/bin/env python3
"""Minimal comprehensive discovery engine for compatibility"""

import logging
import duckdb
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class UltimateCMDBBuilder:
    def __init__(self, config: Dict[str, Any], content_matcher, cache_manager):
        self.config = config
        self.content_matcher = content_matcher
        self.cache_manager = cache_manager
        self.db_path = config.get('database_path', 'ultimate_cmdb.db')
        self.conn = duckdb.connect(self.db_path)
        self._setup_schema()
        
    def _setup_schema(self):
        self.conn.execute("DROP TABLE IF EXISTS ultimate_universal_endpoint")
        self.conn.execute("""
            CREATE TABLE ultimate_universal_endpoint (
                asset_id VARCHAR PRIMARY KEY,
                hostname VARCHAR,
                discovery_timestamp TIMESTAMP DEFAULT NOW()
            )
        """)
        self.conn.commit()
    
    async def build_ultimate_cmdb(self, projects: List[str], client_managers: Dict[str, Any]) -> Dict[str, Any]:
        return {'total_assets': 0, 'projects_processed': 0}
    
    def get_visibility_queries(self) -> Dict[str, str]:
        return {'visibility_summary': 'SELECT COUNT(*) FROM ultimate_universal_endpoint'}
    
    def close(self):
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
''')
    
    # Check for required config files
    if not Path('intelligent_config.yaml').exists():
        logger.info("Creating default intelligent_config.yaml...")
        with open('intelligent_config.yaml', 'w') as f:
            f.write('''# Default Intelligent AO1 Configuration
intelligence_level: "expert"
max_memory_mb: 2048
max_disk_gb: 20
database_path: "ao1_intelligent_cmdb.db"
cache_dir: ".cache"
enable_ai_classification: true
enable_deep_analysis: true
''')
    
    logger.info("✅ Dependencies checked and fixed")

def main():
    """Main entry point"""
    logger.info("🚀 Starting Intelligent AO1 Discovery System")
    
    # Fix dependencies first
    check_and_fix_dependencies()
    
    # Check if we have a project ID
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
    if not project_id:
        logger.error("❌ GOOGLE_CLOUD_PROJECT environment variable not set")
        logger.info("💡 Set it with: export GOOGLE_CLOUD_PROJECT=your-project-id")
        return 1
    
    # Check for authentication
    auth_files = [
        'gcp_prod_key.json',
        os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', ''),
        os.path.expanduser('~/.config/gcloud/application_default_credentials.json')
    ]
    
    auth_found = any(Path(f).exists() for f in auth_files if f)
    if not auth_found:
        logger.warning("⚠️  No GCP authentication found")
        logger.info("💡 Options:")
        logger.info("   1. Place service account key as 'gcp_prod_key.json'")
        logger.info("   2. Run 'gcloud auth application-default login'")
        logger.info("   3. Set GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json")
    
    # Try to import and run the main discovery system
    try:
        logger.info("📡 Importing discovery system...")
        from intelligent_main import main as intelligent_main
        
        # Set up basic command line args
        sys.argv = [
            'intelligent_main.py',
            '--project', project_id,
            '--intelligence-level', 'expert',
            '--max-memory', '2048',
            '--max-disk', '20'
        ]
        
        # Add dry-run if requested
        if '--dry-run' in sys.argv or 'DRY_RUN' in os.environ:
            sys.argv.append('--dry-run')
        
        logger.info(f"🎯 Running discovery for project: {project_id}")
        return asyncio.run(intelligent_main())
        
    except ImportError as e:
        logger.error(f"❌ Failed to import discovery system: {e}")
        logger.info("💡 Try running: pip install -r requirements.txt")
        return 1
        
    except Exception as e:
        logger.error(f"❌ Discovery failed: {e}")
        logger.info("💡 Try running with --debug for more details")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code or 0)
    except KeyboardInterrupt:
        logger.warning("⚠️  Interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        sys.exit(1)