#!/usr/bin/env python3

import logging
import sys
from metrics_recommender import MetricsRecommender
from report_generator import ReportGenerator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("🚀 Initializing Ultra-Intelligent AO1 Visibility Analytics System...")
        
        recommender = MetricsRecommender()
        
        logger.info("🔍 Performing ultra-intelligent analysis...")
        
        recommendations = recommender.map_metrics_to_data()
        prioritized = recommender.prioritize_recommendations(recommendations)
        
        report_gen = ReportGenerator(recommender.recommendation_stats)
        
        quick_start = report_gen.generate_quick_start(prioritized)
        print(quick_start)
        print("\n" + "="*100 + "\n")
        
        full_guide = report_gen.generate_implementation_guide(prioritized)
        print(full_guide)
        
        output_data = recommender.save_recommendations(recommendations)
        
        logger.info("✅ Ultra-intelligent AO1 visibility analysis complete!")
        logger.info("📊 Check generated files for detailed analysis")
        
        return output_data
        
    except KeyboardInterrupt:
        logger.info("⏹️ Analysis interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Critical error in ultra-intelligent analysis: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()