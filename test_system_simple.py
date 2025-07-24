#!/usr/bin/env python3
"""
Simple system test for MacOS
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_basic_imports():
    """Test that core modules can be imported"""
    try:
        from core.signal_engine import SchermanVIXDivergenceCore
        from core.risk_manager import RiskManager
        print("✅ Core modules import successfully")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality"""
    try:
        from core.signal_engine import SchermanVIXDivergenceCore
        from core.risk_manager import RiskManager
        import pandas as pd
        import numpy as np
        
        # Test signal engine
        config = {}
        engine = SchermanVIXDivergenceCore(config)
        
        # Test risk manager
        risk_config = {'risk_per_trade': 0.01}
        risk_mgr = RiskManager(risk_config)
        
        print("✅ Basic functionality works")
        return True
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        return False

def main():
    print("🧪 SIMPLE SYSTEM TEST")
    print("====================")
    
    tests = [
        ("Import Test", test_basic_imports),
        ("Functionality Test", test_basic_functionality)
    ]
    
    passed = 0
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}...")
        if test_func():
            passed += 1
    
    print(f"\n📊 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 System test passed!")
        return True
    else:
        print("❌ System test failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
