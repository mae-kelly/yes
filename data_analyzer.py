import json
import pandas as pd
import statistics
from collections import Counter
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class DataAnalyzer:
    def __init__(self, mapping_results_file: str = "security_mapping_results.json", original_data_file: str = "new.json"):
        self.mapping_results_file = mapping_results_file
        self.original_data_file = original_data_file
        self.mapping_data = None
        self.original_data = None
        self.load_results()

    def load_results(self):
        try:
            with open(self.mapping_results_file, 'r') as f:
                self.mapping_data = json.load(f)
            
            with open(self.original_data_file, 'r') as f:
                self.original_data = json.load(f)
                
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise

    def get_table_size_info(self, dataset_id: str, table_id: str) -> Dict[str, Any]:
        if ('datasets' in self.original_data and 
            dataset_id in self.original_data['datasets'] and
            'tables' in self.original_data['datasets'][dataset_id] and
            table_id in self.original_data['datasets'][dataset_id]['tables']):
            
            table_info = self.original_data['datasets'][dataset_id]['tables'][table_id]
            
            size_info = {
                'row_count': 0,
                'size_bytes': 0,
                'size_category': 'unknown',
                'data_quality_score': 0.0,
                'freshness_score': 0.0
            }
            
            if 'table_info' in table_info:
                table_metadata = table_info['table_info']
                
                for field in ['num_rows', 'row_count', 'rows', 'numRows', 'rowCount', 'record_count']:
                    if field in table_metadata and table_metadata[field] is not None:
                        try:
                            size_info['row_count'] = int(table_metadata[field])
                            break
                        except (ValueError, TypeError):
                            continue
                
                for field in ['num_bytes', 'size_bytes', 'bytes', 'numBytes', 'sizeBytes', 'table_size']:
                    if field in table_metadata and table_metadata[field] is not None:
                        try:
                            size_info['size_bytes'] = int(table_metadata[field])
                            break
                        except (ValueError, TypeError):
                            continue
            
            if size_info['row_count'] == 0 and 'sample_data' in table_info:
                sample_count = len(table_info['sample_data']) if table_info['sample_data'] else 0
                if sample_count > 0:
                    estimation_factor = min(max(sample_count * 100, 1000), 1000000)
                    size_info['row_count'] = estimation_factor
            
            if size_info['row_count'] > 100000000:
                size_info['size_category'] = 'ultra_massive'
                size_info['priority_score'] = 10
            elif size_info['row_count'] > 10000000:
                size_info['size_category'] = 'very_large'
                size_info['priority_score'] = 8
            elif size_info['row_count'] > 1000000:
                size_info['size_category'] = 'large'
                size_info['priority_score'] = 6
            elif size_info['row_count'] > 100000:
                size_info['size_category'] = 'medium'
                size_info['priority_score'] = 4
            elif size_info['row_count'] > 10000:
                size_info['size_category'] = 'small'
                size_info['priority_score'] = 2
            elif size_info['row_count'] > 0:
                size_info['size_category'] = 'very_small'
                size_info['priority_score'] = 1
            else:
                size_info['size_category'] = 'empty'
                size_info['priority_score'] = 0
            
            size_info['data_quality_score'] = self._calculate_data_quality_score(table_info)
            size_info['freshness_score'] = self._calculate_freshness_score(table_info)
            
            return size_info
        
        return {
            'row_count': 0, 'size_bytes': 0, 'size_category': 'unknown', 
            'priority_score': 0, 'data_quality_score': 0.0, 'freshness_score': 0.0
        }

    def _calculate_data_quality_score(self, table_info):
        quality_score = 0.0
        
        if 'schema' in table_info or 'columns' in table_info:
            quality_score += 0.3
        
        if 'sample_data' in table_info and table_info['sample_data']:
            quality_score += 0.2
            sample_size = len(table_info['sample_data'])
            if sample_size > 10:
                quality_score += 0.1
            if sample_size > 100:
                quality_score += 0.1
        
        if 'table_info' in table_info:
            metadata_fields = len(table_info['table_info'])
            quality_score += min(metadata_fields / 20, 0.3)
        
        return min(quality_score, 1.0)

    def _calculate_freshness_score(self, table_info):
        freshness_score = 0.5
        
        timestamp_fields = [
            'last_modified', 'lastModified', 'modified_time', 'modifiedTime',
            'created_time', 'createdTime', 'creation_time', 'updated_at'
        ]
        
        if 'table_info' in table_info:
            for field in timestamp_fields:
                if field in table_info['table_info']:
                    try:
                        timestamp_value = table_info['table_info'][field]
                        if timestamp_value:
                            freshness_score = 0.8
                            break
                    except:
                        continue
        
        return freshness_score

    def get_available_data_sources(self) -> Dict[str, Dict[str, Any]]:
        available_sources = {}
        
        for role, requirements in self.mapping_data['matches']['log_types'].items():
            available_sources[role] = {}
            
            for log_type, matches in requirements.items():
                if matches['table_names']:
                    tables_info = []
                    
                    for table_match in matches['table_names']:
                        table_columns = []
                        for column_match in matches['column_names']:
                            if (column_match['dataset_id'] == table_match['dataset_id'] and 
                                column_match['table_id'] == table_match['table_id']):
                                table_columns.append(column_match['name'])
                        
                        size_info = self.get_table_size_info(table_match['dataset_id'], table_match['table_id'])
                        
                        tables_info.append({
                            'table_name': table_match['name'],
                            'dataset': table_match['dataset_id'],
                            'table_id': table_match['table_id'],
                            'columns': table_columns,
                            'column_count': len(table_columns),
                            'row_count': size_info['row_count'],
                            'size_bytes': size_info['size_bytes'],
                            'size_category': size_info['size_category'],
                            'size_priority_score': size_info['priority_score'],
                            'data_quality_score': size_info['data_quality_score'],
                            'freshness_score': size_info['freshness_score']
                        })
                    
                    tables_info.sort(key=lambda x: (
                        x['size_priority_score'], 
                        x['data_quality_score'], 
                        x['freshness_score'],
                        x['column_count']
                    ), reverse=True)
                    
                    available_sources[role][log_type] = {
                        'tables': tables_info,
                        'total_columns': len(matches['column_names']),
                        'total_tables': len(tables_info),
                        'max_rows': max((t['row_count'] for t in tables_info), default=0),
                        'avg_quality': statistics.mean([t['data_quality_score'] for t in tables_info]) if tables_info else 0
                    }
        
        return available_sources

    def assess_data_quality(self, recommendations):
        all_tables = {}
        
        for role_recs in recommendations.values():
            for rec in role_recs:
                table_key = f"{rec['dataset']}.{rec['table_name']}"
                if table_key not in all_tables:
                    all_tables[table_key] = {
                        'row_count': rec['row_count'],
                        'size_category': rec['size_category'],
                        'data_quality_score': rec.get('data_quality_score', 0.0),
                        'freshness_score': rec.get('freshness_score', 0.0),
                        'column_count': rec.get('column_count', 0),
                        'metrics_supported': 0
                    }
                all_tables[table_key]['metrics_supported'] += 1
        
        quality_scores = [t['data_quality_score'] for t in all_tables.values()]
        freshness_scores = [t['freshness_score'] for t in all_tables.values()]
        
        return {
            'total_tables_analyzed': len(all_tables),
            'average_data_quality': statistics.mean(quality_scores) if quality_scores else 0,
            'average_freshness': statistics.mean(freshness_scores) if freshness_scores else 0,
            'high_quality_tables': len([t for t in all_tables.values() if t['data_quality_score'] > 0.7]),
            'large_tables': len([t for t in all_tables.values() if t['size_category'] in ['large', 'very_large', 'ultra_massive']]),
            'multi_metric_tables': len([t for t in all_tables.values() if t['metrics_supported'] > 1])
        }

    def generate_comprehensive_analytics(self, prioritized):
        analytics = {}
        
        if not prioritized:
            return analytics
        
        analytics['distributions'] = {
            'by_difficulty': dict(Counter(r['implementation_difficulty'] for r in prioritized)),
            'by_priority': dict(Counter(r.get('priority', 'UNKNOWN') for r in prioritized)),
            'by_role': dict(Counter(r['role'] for r in prioritized)),
            'by_size_category': dict(Counter(r['size_category'] for r in prioritized))
        }
        
        feasibility_scores = [r['feasibility_score'] for r in prioritized]
        intelligence_scores = [r.get('intelligence_score', 0) for r in prioritized]
        
        analytics['score_statistics'] = {
            'feasibility': {
                'mean': statistics.mean(feasibility_scores),
                'median': statistics.median(feasibility_scores),
                'std_dev': statistics.stdev(feasibility_scores) if len(feasibility_scores) > 1 else 0,
                'min': min(feasibility_scores),
                'max': max(feasibility_scores)
            },
            'intelligence': {
                'mean': statistics.mean(intelligence_scores),
                'median': statistics.median(intelligence_scores),
                'std_dev': statistics.stdev(intelligence_scores) if len(intelligence_scores) > 1 else 0,
                'min': min(intelligence_scores),
                'max': max(intelligence_scores)
            }
        }
        
        return analytics