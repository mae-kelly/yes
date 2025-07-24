#!/usr/bin/env python3
"""
Simple import test to debug issues
"""
import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_step_by_step():
    print("🔍 Step-by-step import test")
    print("=" * 30)
    
    # Step 1: Test basic dependencies
    print("Step 1: Testing basic dependencies...")
    try:
        import pandas
        import numpy
        import ccxt
        print("✅ Basic dependencies OK")
    except Exception as e:
        print(f"❌ Basic dependencies failed: {e}")
        return False
    
    # Step 2: Test src path
    print("\nStep 2: Testing src path...")
    try:
        import core
        print("✅ Core package found")
    except Exception as e:
        print(f"❌ Core package failed: {e}")
        print("Available modules in src:")
        try:
            import os
            for item in os.listdir('src'):
                print(f"  - {item}")
        except:
            pass
        return False
    
    # Step 3: Test individual modules
    print("\nStep 3: Testing individual modules...")
    
    # Test signal_engine first (simplest)
    try:
        from core.signal_engine import SchermanVIXDivergenceCore
        print("✅ signal_engine OK")
    except Exception as e:
        print(f"❌ signal_engine failed: {e}")
        return False
    
    # Test risk_manager
    try:
        from core.risk_manager import RiskManager
        print("✅ risk_manager OK")
    except Exception as e:
        print(f"❌ risk_manager failed: {e}")
        return False
    
    # Test data_manager last (most complex)
    try:
        from core.data_manager import EnterpriseDataManager
        print("✅ data_manager OK")
    except Exception as e:
        print(f"❌ data_manager failed: {e}")
        print("Error details:")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 4: Test instantiation
    print("\nStep 4: Testing instantiation...")
    try:
        config = {'test': True}
        risk_mgr = RiskManager(config)
        signal_engine = SchermanVIXDivergenceCore(config)
        print("✅ Instantiation OK")
    except Exception as e:
        print(f"❌ Instantiation failed: {e}")
        return False
    
    print("\n🎉 All import tests passed!")
    return True

if __name__ == "__main__":
    success = test_step_by_step()
    sys.exit(0 if success else 1)
