import statistics
from collections import Counter
from typing import List, Dict, Any

class ReportGenerator:
    def __init__(self, recommendation_stats: Dict[str, int]):
        self.stats = recommendation_stats

    def generate_quick_start(self, prioritized: List[Dict[str, Any]]) -> str:
        quick_start = []
        quick_start.append("🚀 ULTRA-INTELLIGENT AO1 VISIBILITY QUICK START")
        quick_start.append("=" * 100)
        quick_start.append("")
        
        trivial_wins = [r for r in prioritized if r['implementation_difficulty'] == 'AO1_Trivial'][:3]
        easy_wins = [r for r in prioritized if r['implementation_difficulty'] == 'AO1_Easy'][:5]
        
        if trivial_wins:
            quick_start.append("⚡ INSTANT IMPLEMENTATION - ZERO COMPLEXITY:")
            quick_start.append("-" * 70)
            
            for i, rec in enumerate(trivial_wins, 1):
                quick_start.append(f"{i}. 🚀 DEPLOY NOW: {rec['ao1_visibility_factor']}")
                quick_start.append(f"   📊 Data Source: {rec['dataset']}.{rec['table_name']}")
                quick_start.append(f"   📈 Scale: {rec['row_count']:,} rows ({rec['size_category']})")
                quick_start.append(f"   🎯 Measures: {rec['description']}")
                quick_start.append(f"   💡 Key Question: {rec['visibility_query']}")
                quick_start.append(f"   💼 Business Value: {rec['business_impact']}")
                quick_start.append(f"   ⚠️  Security Context: {rec['threat_context']}")
                quick_start.append(f"   🤖 AI Confidence: {rec['feasibility_score']:.3f} | Intelligence: {rec.get('intelligence_score', 0):.3f}")
                
                if rec['matched_columns']:
                    top_matches = sorted(rec['matched_columns'], key=lambda x: x['confidence'], reverse=True)[:3]
                    quick_start.append("   🔑 Key Columns:")
                    for match in top_matches:
                        conf_pct = int(match['confidence'] * 100)
                        match_type = match['match_type'].replace('_', ' ').title()
                        quick_start.append(f"     • '{match['matched_column']}' ({match_type}, {conf_pct}% confidence)")
                
                quick_start.append("")
        
        if easy_wins:
            quick_start.append("⚡ EASY WINS - HIGH IMPACT, LOW EFFORT:")
            quick_start.append("-" * 70)
            
            for i, rec in enumerate(easy_wins, 1):
                quick_start.append(f"{i}. ⚡ IMPLEMENT: {rec['ao1_visibility_factor']}")
                quick_start.append(f"   📊 Source: {rec['dataset']}.{rec['table_name']} ({rec['row_count']:,} rows)")
                quick_start.append(f"   🎯 Capability: {rec['description']}")
                quick_start.append(f"   💼 Impact: {rec['business_impact']}")
                quick_start.append(f"   🏆 Priority: {rec.get('priority', 'MEDIUM')} | Rank: {rec.get('recommendation_rank', 0):.3f}")
                
                ultra_matches = [m for m in rec['matched_columns'] if m['match_type'] == 'ultra_semantic']
                if ultra_matches:
                    quick_start.append(f"   🧠🚀 Ultra-AI Matches: {len(ultra_matches)} detected")
                
                quick_start.append("")
        
        if not trivial_wins and not easy_wins:
            quick_start.append("⚠️  NO TRIVIAL OR EASY IMPLEMENTATIONS FOUND")
            quick_start.append("🔧 RECOMMENDED ACTIONS:")
            quick_start.append("   • Review data source integration and column naming conventions")
            quick_start.append("   • Consider data enrichment or additional log source integration")
            quick_start.append("   • Focus on medium-complexity options with highest business impact")
            quick_start.append("")
            
            medium_recs = [r for r in prioritized if r['implementation_difficulty'] == 'AO1_Medium'][:3]
            if medium_recs:
                quick_start.append("🔧 BEST MEDIUM-COMPLEXITY OPTIONS:")
                for i, rec in enumerate(medium_recs, 1):
                    quick_start.append(f"   {i}. {rec['ao1_visibility_factor']} (Feasibility: {rec['feasibility_score']:.3f})")
        
        quick_start.append("📊 ADVANCED ANALYTICS SUMMARY:")
        quick_start.append("-" * 70)
        quick_start.append(f"🎯 Total Metrics Analyzed: {len(prioritized)}")
        quick_start.append(f"🧠 Ultra-Semantic Matches: {self.stats['ultra_semantic']}")
        quick_start.append(f"🤖 ML-Enhanced Matches: {self.stats['ml_enhanced']}")
        quick_start.append(f"🏆 High-Confidence Matches: {self.stats['high_confidence']}")
        
        if prioritized:
            avg_feasibility = statistics.mean(r['feasibility_score'] for r in prioritized)
            avg_intelligence = statistics.mean(r.get('intelligence_score', 0) for r in prioritized)
            quick_start.append(f"📈 Average Feasibility Score: {avg_feasibility:.3f}")
            quick_start.append(f"🧠 Average Intelligence Score: {avg_intelligence:.3f}")
        
        return "\n".join(quick_start)

    def generate_implementation_guide(self, recommendations: List[Dict[str, Any]]) -> str:
        guide = []
        guide.append("=" * 100)
        guide.append("🎯 ULTRA-INTELLIGENT AO1 VISIBILITY METRICS IMPLEMENTATION GUIDE")
        guide.append("=" * 100)
        guide.append("")
        
        guide.append("🧠 ADVANCED AI ANALYSIS SUMMARY:")
        guide.append("-" * 70)
        
        difficulty_counts = Counter(r['implementation_difficulty'] for r in recommendations)
        priority_counts = Counter(r.get('priority', 'UNKNOWN') for r in recommendations)
        
        guide.append(f"📊 Total AO1 Visibility Metrics Discovered: {len(recommendations)}")
        guide.append(f"🚀 Ultra-Semantic AI Matches: {self.stats['ultra_semantic']}")
        guide.append(f"🤖 ML-Enhanced Matches: {self.stats['ml_enhanced']}")
        guide.append(f"🎯 High-Confidence Matches: {self.stats['high_confidence']}")
        guide.append("")
        
        guide.append("📈 IMPLEMENTATION DIFFICULTY DISTRIBUTION:")
        for difficulty, count in difficulty_counts.most_common():
            percentage = (count / len(recommendations)) * 100
            display_name = difficulty.replace('AO1_', '')
            guide.append(f"   • {display_name}: {count} metrics ({percentage:.1f}%)")
        guide.append("")
        
        guide.append("⚡ PRIORITY DISTRIBUTION:")
        for priority, count in priority_counts.most_common():
            percentage = (count / len(recommendations)) * 100
            guide.append(f"   • {priority}: {count} metrics ({percentage:.1f}%)")
        guide.append("")
        
        if recommendations:
            avg_feasibility = statistics.mean(r['feasibility_score'] for r in recommendations)
            avg_intelligence = statistics.mean(r.get('intelligence_score', 0) for r in recommendations)
            avg_confidence = statistics.mean(r.get('confidence_score', 0) for r in recommendations)
            
            guide.append("🎯 ADVANCED SCORING STATISTICS:")
            guide.append(f"   • Average Feasibility Score: {avg_feasibility:.3f}")
            guide.append(f"   • Average Intelligence Score: {avg_intelligence:.3f}")
            guide.append(f"   • Average Confidence Score: {avg_confidence:.3f}")
            guide.append("")
        
        for difficulty in ['AO1_Trivial', 'AO1_Easy', 'AO1_Medium', 'AO1_Hard']:
            difficulty_recs = [r for r in recommendations if r['implementation_difficulty'] == difficulty]
            if difficulty_recs:
                display_name = difficulty.replace('AO1_', '').upper()
                guide.append(f"🎯 {display_name} IMPLEMENTATION METRICS:")
                guide.append("-" * 80)
                
                for i, rec in enumerate(difficulty_recs[:10], 1):
                    guide.append(f"{i}. 🎯 {rec['ao1_visibility_factor']} ({rec['role']} - {rec['log_type']})")
                    guide.append(f"   📊 Data Source: {rec['dataset']}.{rec['table_name']}")
                    guide.append(f"   📈 Table Statistics: {rec['row_count']:,} rows ({rec['size_category']})")
                    guide.append(f"   🎯 AO1 Description: {rec['description']}")
                    guide.append(f"   💡 Visibility Query: {rec['visibility_query']}")
                    guide.append(f"   💼 Business Impact: {rec['business_impact']}")
                    guide.append(f"   ⚠️  Threat Context: {rec['threat_context']}")
                    guide.append(f"   🏆 Priority Level: {rec.get('priority', 'MEDIUM')}")
                    
                    guide.append(f"   🤖 AI Scores: Feasibility={rec['feasibility_score']:.3f}, Intelligence={rec.get('intelligence_score', 0):.3f}, Confidence={rec.get('confidence_score', 0):.3f}")
                    guide.append(f"   🏅 Recommendation Rank: {rec.get('recommendation_rank', 0):.3f}")
                    
                    if rec['matched_columns']:
                        guide.append("   🔑 Ultra-Intelligent Column Matches:")
                        for col_match in rec['matched_columns'][:5]:
                            match_indicator = {
                                'ultra_semantic': '🧠🚀',
                                'semantic': '🧠',
                                'partial': '📝',
                                'synonym': '🎯'
                            }.get(col_match['match_type'], '❓')
                            
                            confidence_pct = int(col_match['confidence'] * 100)
                            ml_conf = col_match.get('ml_confidence', 0)
                            evidence_str = ', '.join(col_match['evidence'][:2]) if col_match['evidence'] else 'direct_match'
                            
                            guide.append(f"     {match_indicator} '{col_match['matched_column']}' ← {col_match['match_term']}")
                            guide.append(f"       📊 Match: {confidence_pct}% confidence, ML: {ml_conf:.2f}, Evidence: {evidence_str}")
                    
                    guide.append("")
                
                if len(difficulty_recs) > 10:
                    guide.append(f"   ... and {len(difficulty_recs) - 10} more {display_name.lower()} metrics available")
                    guide.append("")
        
        return "\n".join(guide)