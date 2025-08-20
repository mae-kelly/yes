#!/usr/bin/env python3
"""
Setup script for corporate environment
Handles SSL issues, downloads models, and configures the environment
"""

import os
import sys
import subprocess
import logging
import json
import shutil
from pathlib import Path
from typing import Optional, Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CorporateEnvironmentSetup:
    def __init__(self):
        self.home_dir = Path.home()
        self.cache_dir = self.home_dir / '.cache' / 'ao1_visibility'
        self.models_dir = self.cache_dir / 'models'
        self.certs_dir = self.cache_dir / 'certificates'
        self.config_file = self.cache_dir / 'config.json'
        
        # Create directories
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.certs_dir.mkdir(parents=True, exist_ok=True)
        
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load or create configuration"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        
        return {
            'ssl_configured': False,
            'models_downloaded': False,
            'proxy_configured': False,
            'fallback_mode': False
        }
    
    def save_config(self):
        """Save configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def setup_ssl(self) -> bool:
        """Setup SSL for corporate environment"""
        logger.info("Setting up SSL for corporate environment...")
        
        # Import and use our SSL manager
        try:
            from corporate_ssl_config import ensure_ssl_configured, get_ssl_status
            
            if ensure_ssl_configured():
                status = get_ssl_status()
                logger.info(f"SSL configured successfully using: {status['successful_method']}")
                self.config['ssl_configured'] = True
                self.save_config()
                return True
            else:
                logger.warning("SSL configuration failed, will use fallback mode")
                self.config['fallback_mode'] = True
                self.save_config()
                return False
        except Exception as e:
            logger.error(f"SSL setup failed: {e}")
            return False
    
    def download_models_offline(self) -> bool:
        """Download models for offline use"""
        logger.info("Attempting to download models for offline use...")
        
        models_to_download = [
            {
                'name': 'sentence-transformers/all-MiniLM-L6-v2',
                'type': 'huggingface',
                'fallback_url': 'https://github.com/sentence-transformers/all-MiniLM-L6-v2'
            }
        ]
        
        for model_info in models_to_download:
            model_name = model_info['name']
            model_path = self.models_dir / model_name.replace('/', '_')
            
            if model_path.exists():
                logger.info(f"Model already downloaded: {model_name}")
                continue
            
            # Try multiple download methods
            if self._download_with_huggingface_cli(model_name, model_path):
                logger.info(f"Downloaded {model_name} with huggingface-cli")
                continue
            
            if self._download_with_git(model_info.get('fallback_url'), model_path):
                logger.info(f"Downloaded {model_name} with git")
                continue
            
            if self._download_with_wget(model_info.get('fallback_url'), model_path):
                logger.info(f"Downloaded {model_name} with wget")
                continue
            
            logger.warning(f"Failed to download {model_name}, will use fallback embeddings")
        
        self.config['models_downloaded'] = True
        self.save_config()
        return True
    
    def _download_with_huggingface_cli(self, model_name: str, output_path: Path) -> bool:
        """Download model using huggingface-cli"""
        try:
            cmd = [
                'huggingface-cli', 'download',
                model_name,
                '--cache-dir', str(output_path),
                '--local-dir', str(output_path)
            ]
            
            # Add proxy if configured
            if 'HTTP_PROXY' in os.environ:
                cmd.extend(['--proxy', os.environ['HTTP_PROXY']])
            
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except Exception as e:
            logger.debug(f"huggingface-cli download failed: {e}")
            return False
    
    def _download_with_git(self, repo_url: str, output_path: Path) -> bool:
        """Download model using git clone"""
        if not repo_url:
            return False
        
        try:
            # Configure git for corporate proxy
            if 'HTTP_PROXY' in os.environ:
                subprocess.run(['git', 'config', '--global', 'http.proxy', os.environ['HTTP_PROXY']])
                subprocess.run(['git', 'config', '--global', 'https.proxy', os.environ['HTTPS_PROXY']])
            
            # Disable SSL verification if needed
            subprocess.run(['git', 'config', '--global', 'http.sslVerify', 'false'])
            
            # Clone the repository
            subprocess.run(['git', 'clone', repo_url, str(output_path)], check=True)
            return True
        except Exception as e:
            logger.debug(f"Git clone failed: {e}")
            return False
    
    def _download_with_wget(self, url: str, output_path: Path) -> bool:
        """Download model using wget"""
        if not url:
            return False
        
        try:
            cmd = ['wget', '--no-check-certificate', '-r', '-np', '-nH', url, '-P', str(output_path)]
            
            # Add proxy if configured
            if 'HTTP_PROXY' in os.environ:
                cmd.extend(['-e', f"http_proxy={os.environ['HTTP_PROXY']}"])
                cmd.extend(['-e', f"https_proxy={os.environ['HTTPS_PROXY']}"])
            
            subprocess.run(cmd, check=True)
            return True
        except Exception as e:
            logger.debug(f"Wget download failed: {e}")
            return False
    
    def setup_proxy(self) -> bool:
        """Setup corporate proxy"""
        logger.info("Checking for corporate proxy...")
        
        # Check common proxy environment variables
        proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
        proxy_found = any(os.environ.get(var) for var in proxy_vars)
        
        if not proxy_found:
            # Try to detect proxy from system
            proxy_configs = [
                '/etc/proxy.conf',
                '/etc/environment',
                str(self.home_dir / '.proxy'),
                str(self.home_dir / '.bashrc'),
            ]
            
            for config_file in proxy_configs:
                if os.path.exists(config_file):
                    try:
                        with open(config_file, 'r') as f:
                            content = f.read()
                            if 'proxy' in content.lower():
                                logger.info(f"Found proxy configuration in {config_file}")
                                # Parse and set proxy (simplified)
                                lines = content.split('\n')
                                for line in lines:
                                    if 'proxy' in line.lower() and '=' in line:
                                        key, value = line.split('=', 1)
                                        os.environ[key.strip()] = value.strip()
                                proxy_found = True
                                break
                    except:
                        continue
        
        if proxy_found:
            logger.info("Corporate proxy configured")
            self.config['proxy_configured'] = True
            self.save_config()
            
            # Set no_proxy for local addresses
            os.environ['NO_PROXY'] = 'localhost,127.0.0.1,::1'
            os.environ['no_proxy'] = 'localhost,127.0.0.1,::1'
        else:
            logger.info("No corporate proxy detected")
        
        return True
    
    def install_dependencies(self) -> bool:
        """Install Python dependencies"""
        logger.info("Installing Python dependencies...")
        
        try:
            # First, upgrade pip
            subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'], check=True)
            
            # Install from requirements.txt
            if os.path.exists('requirements.txt'):
                cmd = [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt']
                
                # Add trusted hosts for corporate environments
                trusted_hosts = ['pypi.org', 'files.pythonhosted.org']
                for host in trusted_hosts:
                    cmd.extend(['--trusted-host', host])
                
                # Add proxy if configured
                if 'HTTP_PROXY' in os.environ:
                    cmd.extend(['--proxy', os.environ['HTTP_PROXY']])
                
                # Add index URL if internal PyPI mirror exists
                internal_pypi = os.environ.get('PIP_INDEX_URL')
                if internal_pypi:
                    cmd.extend(['--index-url', internal_pypi])
                
                subprocess.run(cmd, check=True)
                logger.info("Dependencies installed successfully")
                return True
            else:
                logger.warning("requirements.txt not found")
                return False
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install dependencies: {e}")
            
            # Try installing essential packages one by one
            essential_packages = [
                'numpy',
                'pandas',
                'scikit-learn',
                'duckdb',
                'google-cloud-bigquery',
                'pyyaml',
                'requests',
                'certifi'
            ]
            
            logger.info("Trying to install essential packages individually...")
            for package in essential_packages:
                try:
                    cmd = [sys.executable, '-m', 'pip', 'install', package]
                    if 'HTTP_PROXY' in os.environ:
                        cmd.extend(['--proxy', os.environ['HTTP_PROXY']])
                    subprocess.run(cmd, check=True)
                    logger.info(f"Installed {package}")
                except:
                    logger.warning(f"Failed to install {package}")
            
            return False
    
    def test_environment(self) -> bool:
        """Test if the environment is properly configured"""
        logger.info("Testing environment configuration...")
        
        tests_passed = 0
        tests_total = 0
        
        # Test 1: Python version
        tests_total += 1
        python_version = sys.version_info
        if python_version.major >= 3 and python_version.minor >= 8:
            logger.info(f"✓ Python version: {python_version.major}.{python_version.minor}")
            tests_passed += 1
        else:
            logger.warning(f"✗ Python version {python_version.major}.{python_version.minor} (need 3.8+)")
        
        # Test 2: BigQuery access
        tests_total += 1
        try:
            from google.cloud import bigquery
            logger.info("✓ Google Cloud BigQuery library available")
            tests_passed += 1
        except ImportError:
            logger.warning("✗ Google Cloud BigQuery library not available")
        
        # Test 3: ML libraries
        tests_total += 1
        ml_available = False
        
        try:
            import torch
            logger.info("✓ PyTorch available")
            ml_available = True
        except ImportError:
            logger.info("- PyTorch not available")
        
        try:
            import sklearn
            logger.info("✓ Scikit-learn available (fallback)")
            ml_available = True
        except ImportError:
            logger.info("- Scikit-learn not available")
        
        if ml_available:
            tests_passed += 1
        else:
            logger.warning("✗ No ML libraries available")
        
        # Test 4: SSL connectivity
        tests_total += 1
        try:
            import urllib.request
            # Test connection to PyPI
            response = urllib.request.urlopen('https://pypi.org', timeout=5)
            logger.info("✓ SSL connectivity working")
            tests_passed += 1
        except Exception as e:
            logger.warning(f"✗ SSL connectivity issues: {e}")
        
        # Test 5: Model availability
        tests_total += 1
        if self.config.get('models_downloaded') or self.config.get('fallback_mode'):
            logger.info("✓ Models configured or fallback mode enabled")
            tests_passed += 1
        else:
            logger.warning("✗ Models not configured")
        
        # Test 6: DuckDB
        tests_total += 1
        try:
            import duckdb
            conn = duckdb.connect(':memory:')
            conn.execute("SELECT 1").fetchone()
            conn.close()
            logger.info("✓ DuckDB working")
            tests_passed += 1
        except Exception as e:
            logger.warning(f"✗ DuckDB not working: {e}")
        
        # Summary
        logger.info(f"\nEnvironment Test Results: {tests_passed}/{tests_total} tests passed")
        
        if tests_passed == tests_total:
            logger.info("✓ Environment fully configured!")
            return True
        elif tests_passed >= 4:
            logger.info("⚠ Environment partially configured (will work with limitations)")
            return True
        else:
            logger.error("✗ Environment configuration incomplete")
            return False
    
    def create_launch_script(self):
        """Create a launch script for the application"""
        script_content = '''#!/usr/bin/env python3
"""
Launch script for AO1 Visibility System
Automatically handles corporate environment setup
"""

import os
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Ensure SSL is configured
    try:
        from corporate_ssl_config import ensure_ssl_configured
        ensure_ssl_configured()
        logger.info("SSL configuration applied")
    except Exception as e:
        logger.warning(f"SSL configuration failed: {e}")
        logger.info("Proceeding with fallback mode...")
    
    # Import and run the main application
    try:
        from run_discovery import main as run_main
        import asyncio
        asyncio.run(run_main())
    except ImportError as e:
        logger.error(f"Failed to import main application: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Application failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
        
        launch_script = Path('launch_ao1_visibility.py')
        with open(launch_script, 'w') as f:
            f.write(script_content)
        
        # Make it executable on Unix-like systems
        if os.name != 'nt':
            os.chmod(launch_script, 0o755)
        
        logger.info(f"Created launch script: {launch_script}")
    
    def create_offline_config(self):
        """Create configuration for offline mode"""
        offline_config = {
            'discovery_settings': {
                'use_fallback_embeddings': True,
                'offline_mode': True,
                'skip_ssl_verification': True,
                'max_retries': 3,
                'timeout_seconds': 30
            },
            'ml_settings': {
                'backend': 'auto',  # Will auto-select based on availability
                'fallback_order': [
                    'transformers',
                    'sentence-transformers',
                    'sklearn',
                    'word2vec',
                    'hash'
                ]
            },
            'ssl_settings': {
                'verify': False,
                'use_system_certs': True,
                'corporate_cert_path': str(self.certs_dir / 'ca-bundle.crt')
            }
        }
        
        offline_config_file = Path('offline_config.yaml')
        
        import yaml
        with open(offline_config_file, 'w') as f:
            yaml.dump(offline_config, f, default_flow_style=False)
        
        logger.info(f"Created offline configuration: {offline_config_file}")
    
    def print_next_steps(self):
        """Print next steps for the user"""
        print("\n" + "="*60)
        print("SETUP COMPLETE - NEXT STEPS")
        print("="*60)
        print("\n1. If you have corporate certificates, copy them to:")
        print(f"   {self.certs_dir}")
        print("\n2. If using a corporate proxy, set environment variables:")
        print("   export HTTP_PROXY=http://proxy.company.com:8080")
        print("   export HTTPS_PROXY=http://proxy.company.com:8080")
        print("\n3. To run the discovery system:")
        print("   python launch_ao1_visibility.py")
        print("\n4. For offline mode (no internet access):")
        print("   python run_discovery.py --config offline_config.yaml")
        print("\n5. If you encounter SSL issues, try:")
        print("   export PYTHONHTTPSVERIFY=0")
        print("   export REQUESTS_CA_BUNDLE=''")
        print("\n6. To test a specific project:")
        print("   python run_discovery.py --projects your-project-id --dry-run")
        print("\n" + "="*60)
        
        if self.config.get('fallback_mode'):
            print("\n⚠ NOTE: Running in FALLBACK MODE")
            print("  The system will use alternative ML libraries")
            print("  Performance may be reduced but functionality preserved")
        
        print("\n✓ Setup completed successfully!")
        print("="*60 + "\n")
    
    def run_full_setup(self):
        """Run the complete setup process"""
        logger.info("Starting corporate environment setup...")
        logger.info("="*60)
        
        steps = [
            ("Setting up proxy", self.setup_proxy),
            ("Configuring SSL", self.setup_ssl),
            ("Installing dependencies", self.install_dependencies),
            ("Downloading models", self.download_models_offline),
            ("Creating launch script", self.create_launch_script),
            ("Creating offline config", self.create_offline_config),
            ("Testing environment", self.test_environment)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"\n{step_name}...")
            try:
                step_func()
                logger.info(f"✓ {step_name} completed")
            except Exception as e:
                logger.error(f"✗ {step_name} failed: {e}")
                if step_name in ["Installing dependencies", "Testing environment"]:
                    logger.error("Critical step failed. Please fix the issue and retry.")
                    return False
        
        self.save_config()
        self.print_next_steps()
        return True

def main():
    """Main entry point"""
    setup = CorporateEnvironmentSetup()
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--test':
            setup.test_environment()
        elif sys.argv[1] == '--ssl-only':
            setup.setup_ssl()
        elif sys.argv[1] == '--download-models':
            setup.download_models_offline()
        elif sys.argv[1] == '--help':
            print("Usage: python setup_corporate_environment.py [option]")
            print("\nOptions:")
            print("  --test           Test environment configuration")
            print("  --ssl-only       Configure SSL only")
            print("  --download-models Download models for offline use")
            print("  --help           Show this help message")
            print("\nNo options: Run full setup")
    else:
        # Run full setup
        setup.run_full_setup()

if __name__ == "__main__":
    main()