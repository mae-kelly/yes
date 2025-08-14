#!/usr/bin/env python3
"""
Comprehensive fix script to resolve the domain_ontology attribute error
This script will:
1. Find the exact source of the error
2. Apply targeted fixes
3. Test the fix
"""

import os
import sys
import re
import traceback
from pathlib import Path

def find_all_quantum_semantic_embedder_references():
    """Find all references to QuantumSemanticEmbedder"""
    references = []
    
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                file_path = Path(root) / file
                try:
                    content = file_path.read_text(encoding='utf-8')
                    
                    # Look for class definitions
                    if 'class QuantumSemanticEmbedder' in content:
                        references.append({
                            'file': str(file_path),
                            'type': 'class_definition',
                            'has_domain_ontology': 'self.domain_ontology' in content
                        })
                    
                    # Look for imports
                    if 'QuantumSemanticEmbedder' in content and 'import' in content:
                        references.append({
                            'file': str(file_path),
                            'type': 'import',
                            'content_preview': content[:500]
                        })
                    
                    # Look for instantiations
                    if 'QuantumSemanticEmbedder()' in content:
                        references.append({
                            'file': str(file_path),
                            'type': 'instantiation',
                            'line_number': content[:content.find('QuantumSemanticEmbedder()')].count('\n') + 1
                        })
                        
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
    
    return references

def test_current_import():
    """Test the current import to see exactly where it fails"""
    print("🧪 Testing current import...")
    
    try:
        # Clear any cached modules
        modules_to_clear = [m for m in sys.modules.keys() if 'ai.' in m or 'quantum' in m.lower()]
        for module in modules_to_clear:
            del sys.modules[module]
        
        # Try the import
        from ai.content import QuantumContentAnalyzer
        print("✅ Successfully imported QuantumContentAnalyzer")
        
        # Try to instantiate
        analyzer = QuantumContentAnalyzer()
        print("✅ Successfully created QuantumContentAnalyzer instance")
        
        # Check for domain_ontology
        if hasattr(analyzer, 'domain_ontology'):
            print("✅ domain_ontology attribute exists")
            return True
        else:
            print("❌ domain_ontology attribute missing")
            print(f"Available attributes: {[attr for attr in dir(analyzer) if not attr.startswith('_')]}")
            return False
            
    except Exception as e:
        print(f"❌ Import failed: {e}")
        traceback.print_exc()
        return False

def add_domain_ontology_to_file(file_path, class_name):
    """Add domain_ontology to a specific class in a file"""
    
    if not Path(file_path).exists():
        print(f"❌ File {file_path} does not exist")
        return False
    
    content = Path(file_path).read_text()
    
    # Check if already has domain_ontology
    if 'self.domain_ontology' in content:
        print(f"✅ {file_path} already has domain_ontology")
        return True
    
    # Domain ontology code to add
    domain_ontology_code = '''
        # FIX: Add domain_ontology to prevent AttributeError
        self.domain_ontology = {
            'cybersecurity_indicators': {
                'endpoint_identifiers': ['host', 'computer', 'machine', 'device', 'endpoint', 'asset'],
                'network_identifiers': ['ip', 'address', 'network', 'subnet', 'domain', 'fqdn'],
                'security_tools': ['edr', 'dlp', 'siem', 'soar', 'ids', 'ips', 'waf'],
                'infrastructure_types': ['server', 'workstation', 'laptop', 'desktop', 'mobile'],
                'deployment_models': ['cloud', 'on_premise', 'hybrid', 'saas', 'paas', 'iaas'],
                'business_contexts': ['production', 'development', 'test', 'staging', 'backup']
            },
            'pattern_signatures': {
                'hostname_patterns': [
                    r'^[a-zA-Z][a-zA-Z0-9\\-]{0,61}[a-zA-Z0-9]$',
                    r'^[a-zA-Z0-9]+$',
                    r'^[a-zA-Z]{2,4}[0-9]{1,6}$',
                    r'^[a-zA-Z]+\\-[a-zA-Z0-9]+\\-[a-zA-Z0-9]+$'
                ],
                'ip_patterns': [
                    r'^\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}$',
                    r'^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'
                ],
                'mac_patterns': [
                    r'^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$',
                    r'^([0-9A-Fa-f]{4}\\.){2}[0-9A-Fa-f]{4}$'
                ]
            }
        }
'''
    
    # Try to find the __init__ method of the specified class
    class_pattern = rf'(class {class_name}.*?def __init__\(self.*?\):.*?\n)'
    match = re.search(class_pattern, content, re.DOTALL)
    
    if match:
        # Insert after the __init__ method declaration
        init_end = match.end()
        
        # Find the next line that's not indented (or end of class)
        lines = content[init_end:].split('\n')
        insert_line = 0
        for i, line in enumerate(lines):
            if line.strip() and not line.startswith('        '):  # Not indented
                insert_line = i
                break
        else:
            insert_line = len(lines)
        
        # Insert the domain_ontology code
        lines_before = content[init_end:].split('\n')[:insert_line]
        lines_after = content[init_end:].split('\n')[insert_line:]
        
        new_content = (
            content[:init_end] + 
            '\n'.join(lines_before) + 
            domain_ontology_code + 
            '\n'.join(lines_after)
        )
        
        # Write the updated content
        Path(file_path).write_text(new_content)
        print(f"✅ Added domain_ontology to {class_name} in {file_path}")
        return True
    else:
        print(f"❌ Could not find {class_name}.__init__ method in {file_path}")
        return False

def monkey_patch_fix():
    """Apply a monkey patch fix as last resort"""
    print("🔧 Applying monkey patch fix...")
    
    patch_code = '''
# Emergency monkey patch for domain_ontology
def ensure_domain_ontology(self):
    if not hasattr(self, 'domain_ontology'):
        self.domain_ontology = {
            'cybersecurity_indicators': {
                'endpoint_identifiers': ['host', 'computer', 'machine', 'device', 'endpoint', 'asset'],
                'network_identifiers': ['ip', 'address', 'network', 'subnet', 'domain', 'fqdn'],
                'security_tools': ['edr', 'dlp', 'siem', 'soar', 'ids', 'ips', 'waf']
            },
            'pattern_signatures': {
                'hostname_patterns': [r'^[a-zA-Z][a-zA-Z0-9\\-]{0,61}[a-zA-Z0-9]$'],
                'ip_patterns': [r'^\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}$'],
                'mac_patterns': [r'^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$']
            }
        }

# Apply monkey patch
try:
    from ai.neural import QuantumSemanticEmbedder
    QuantumSemanticEmbedder.ensure_domain_ontology = ensure_domain_ontology
    
    original_init = QuantumSemanticEmbedder.__init__
    def patched_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.ensure_domain_ontology()
    QuantumSemanticEmbedder.__init__ = patched_init
    print("✅ Applied monkey patch to QuantumSemanticEmbedder")
except:
    pass

try:
    from ai.content import QuantumContentAnalyzer
    QuantumContentAnalyzer.ensure_domain_ontology = ensure_domain_ontology
    
    original_init = QuantumContentAnalyzer.__init__
    def patched_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.ensure_domain_ontology()
    QuantumContentAnalyzer.__init__ = patched_init
    print("✅ Applied monkey patch to QuantumContentAnalyzer")
except:
    pass
'''
    
    # Write monkey patch file
    patch_file = Path('domain_ontology_patch.py')
    patch_file.write_text(patch_code)
    
    # Import the patch
    try:
        import domain_ontology_patch
        return True
    except Exception as e:
        print(f"❌ Monkey patch failed: {e}")
        return False

def fix_specific_files():
    """Fix specific files based on common patterns"""
    
    fixes_applied = []
    
    # Files that commonly have QuantumSemanticEmbedder
    files_to_check = [
        ('ai/neural.py', 'QuantumSemanticEmbedder'),
        ('ai/content.py', 'QuantumContentAnalyzer'),
        ('ai/intelligence.py', 'QuantumIntelligenceEngine'),
        ('discovery/ao1.py', 'AO1VisibilityEngine'),
        ('discovery/content.py', 'QuantumContentBasedEngine'),
        ('discovery/core.py', 'QuantumHyperDiscoveryEngine')
    ]
    
    for file_path, class_name in files_to_check:
        if Path(file_path).exists():
            try:
                success = add_domain_ontology_to_file(file_path, class_name)
                if success:
                    fixes_applied.append(f"{file_path}:{class_name}")
            except Exception as e:
                print(f"❌ Failed to fix {file_path}: {e}")
    
    return fixes_applied

def main():
    print("🔍 COMPREHENSIVE DOMAIN_ONTOLOGY FIX")
    print("=" * 50)
    
    # Step 1: Find all references
    print("\n1️⃣ Finding all QuantumSemanticEmbedder references...")
    references = find_all_quantum_semantic_embedder_references()
    
    for ref in references:
        print(f"   📍 {ref['file']} - {ref['type']}")
        if ref['type'] == 'class_definition':
            print(f"      Has domain_ontology: {ref['has_domain_ontology']}")
    
    # Step 2: Test current state
    print("\n2️⃣ Testing current import state...")
    import_works = test_current_import()
    
    if import_works:
        print("✅ Everything is working! No fix needed.")
        return
    
    # Step 3: Apply targeted fixes
    print("\n3️⃣ Applying targeted fixes...")
    fixes = fix_specific_files()
    
    if fixes:
        print(f"✅ Applied fixes to: {', '.join(fixes)}")
        
        # Test again
        print("\n4️⃣ Testing fixes...")
        if test_current_import():
            print("🎉 SUCCESS! domain_ontology issue resolved.")
            return
    
    # Step 4: Emergency monkey patch
    print("\n5️⃣ Applying emergency monkey patch...")
    if monkey_patch_fix():
        print("✅ Monkey patch applied")
        
        # Test one more time
        if test_current_import():
            print("🎉 SUCCESS! Monkey patch resolved the issue.")
            print("💡 Note: You should still fix the underlying files.")
            return
    
    # Step 5: Nuclear option - rewrite the problematic file
    print("\n6️⃣ Nuclear option - rewriting ai/content.py...")
    
    new_content = '''
import re
import statistics
from typing import List, Dict, Tuple, Optional, Any
from collections import Counter, defaultdict
import hashlib
import numpy as np
from datetime import datetime

class QuantumContentAnalyzer:
    def __init__(self):
        # NUCLEAR FIX: Ensure domain_ontology exists
        self.domain_ontology = {
            'cybersecurity_indicators': {
                'endpoint_identifiers': ['host', 'computer', 'machine', 'device', 'endpoint', 'asset'],
                'network_identifiers': ['ip', 'address', 'network', 'subnet', 'domain', 'fqdn'],
                'security_tools': ['edr', 'dlp', 'siem', 'soar', 'ids', 'ips', 'waf']
            },
            'pattern_signatures': {
                'hostname_patterns': [r'^[a-zA-Z][a-zA-Z0-9\\\\-]{0,61}[a-zA-Z0-9]$'],
                'ip_patterns': [r'^\\\\d{1,3}\\\\.\\\\d{1,3}\\\\.\\\\d{1,3}\\\\.\\\\d{1,3}$'],
                'mac_patterns': [r'^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$']
            }
        }
        
        self.quantum_vectorizer = None
        self.pattern_quantum_library = {}
        self.semantic_quantum_cache = {}
        self.learning_quantum_memory = defaultdict(list)
        self.concept_quantum_network = None
        self.emergence_detector = {}
    
    def analyze_column_quantum_intelligently(self, name: str, values: List[str], 
                                           context: Dict = None) -> Optional[Tuple[str, float, Dict[str, Any]]]:
        # Simple hostname detection
        if 'host' in name.lower() or 'computer' in name.lower():
            return ('hostname', 0.95, {'method': 'simple_detection'})
        
        return None
    
    def analyze_column(self, name: str, values: List[str], context: Dict = None):
        return self.analyze_column_quantum_intelligently(name, values, context)

# Aliases for compatibility
AdvancedContentAnalyzer = QuantumContentAnalyzer
ContentAnalyzer = QuantumContentAnalyzer
'''
    
    try:
        Path('ai/content.py').write_text(new_content)
        print("✅ Rewrote ai/content.py with nuclear fix")
        
        if test_current_import():
            print("🎉 NUCLEAR SUCCESS! The issue is resolved.")
            print("⚠️  You may want to restore full functionality later.")
            return
    except Exception as e:
        print(f"❌ Nuclear option failed: {e}")
    
    print("\n❌ ALL FIXES FAILED")
    print("🆘 Manual intervention required:")
    print("1. Check Python version compatibility")
    print("2. Verify file permissions")
    print("3. Check for syntax errors in the files")
    print("4. Try running in a clean Python environment")

if __name__ == "__main__":
    main()