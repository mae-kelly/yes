#!/usr/bin/env python3

import sys
import asyncio
import logging
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from demos.production_demo import complete_production_demo, example_usage

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--example":
        asyncio.run(example_usage())
    elif len(sys.argv) > 1 and sys.argv[1] == "--test":
        asyncio.run(complete_production_demo())
    else:
        print("🚀 Enhanced BigQuery Field Discovery System")
        print("=" * 50)
        print("Usage:")
        print("  python main.py --test     # Run complete demo")
        print("  python main.py --example  # Run usage example")
        print()
        print("Features:")
        print("✅ Advanced semantic analysis with 10,000+ patterns")
        print("✅ Multi-tier caching with Redis support")
        print("✅ Enterprise catalog integrations")
        print("✅ Production-grade monitoring & optimization")
        print("✅ Active learning for continuous improvement")
        print("✅ Comprehensive testing framework")
        print("✅ Cost tracking and optimization")
        print("✅ Circuit breaker protection")
        print("✅ Confidence calibration")
        print("✅ Real-time data pattern analysis")
        print()
        print("Ready for enterprise deployment! 🏆")

if __name__ == "__main__":
    main()