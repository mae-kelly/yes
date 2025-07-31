import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime, timezone
from math import log10
from models import TableMetrics

logger = logging.getLogger(__name__)

class EnhancedTablePrioritizer:
    def __init__(self):
        self.requirement_indicators = self._build_requirement_indicators()
        self.scoring_weights = self._initialize_scoring_weights()
    
    def _build_requirement_indicators(self) -> Dict[str, List[str]]:
        return {
            'GLOBAL_ASSET_IDENTITY': [
                'asset', 'device', 'host', 'machine', 'computer', 'inventory', 'serial', 'uuid', 'cmdb',
                'endpoint', 'workstation', 'server', 'laptop', 'desktop', 'tablet', 'mobile'
            ],
            'INFRASTRUCTURE_TYPE': [
                'infrastructure', 'platform', 'deployment', 'cloud', 'aws', 'azure', 'gcp', 'onprem',
                'physical', 'virtual', 'container', 'kubernetes', 'vmware', 'hypervisor'
            ],
            'REGIONAL_COUNTRY': [
                'country', 'region', 'location', 'site', 'datacenter', 'geo', 'zone', 'facility',
                'area', 'geography', 'locale', 'territory', 'jurisdiction'
            ],
            'BUSINESS_CONTEXT': [
                'business', 'organization', 'department', 'application', 'service', 'owner', 'team',
                'cost', 'budget', 'function', 'purpose', 'mission', 'objective'
            ],
            'SYSTEM_CLASSIFICATION': [
                'os', 'operating', 'system', 'platform', 'windows', 'linux', 'server', 'version',
                'architecture', 'build', 'kernel', 'distribution'
            ],
            'SECURITY_COVERAGE': [
                'security', 'agent', 'edr', 'crowdstrike', 'tanium', 'protection', 'antivirus',
                'firewall', 'dlp', 'threat', 'vulnerability', 'compliance'
            ],
            'LOGGING_COMPLIANCE': [
                'log', 'logging', 'audit', 'splunk', 'chronicle', 'siem', 'forwarder', 'ingestion',
                'collection', 'monitoring', 'telemetry', 'observability'
            ],
            'DOMAIN_VISIBILITY': [
                'domain', 'dns', 'hostname', 'fqdn', 'network', 'subdomain', 'namespace',
                'directory', 'active_directory', 'ldap'
            ]
        }
    
    def _initialize_scoring_weights(self) -> Dict[str, float]:
        return {
            'row_count': 0.25,
            'requirement_coverage': 0.30,
            'field_relevance_density': 0.20,
            'schema_complexity': 0.10,
            'table_freshness': 0.10,
            'production_indicator': 0.05
        }
    
    def prioritize_tables_mcda(self, tables: List[Any], dataset_id: str, client: Any) -> List[Tuple[Any, float, Dict[str, Any]]]:
        scored_tables = []
        
        for table in tables:
            try:
                table_ref = client.get_table(table.reference)
                metrics = self._extract_table_metrics(table_ref)
                scores = self._calculate_mcda_scores(table_ref, metrics, dataset_id)
                
                composite_score = self._calculate_topsis_score(scores)
                
                scored_tables.append((table, composite_score, scores))
                
            except Exception as e:
                logger.warning(f"Failed to score table {table.table_id}: {e}")
                scored_tables.append((table, 0.0, {}))
        
        scored_tables.sort(key=lambda x: x[1], reverse=True)
        return scored_tables
    
    def _extract_table_metrics(self, table_ref: Any) -> TableMetrics:
        return TableMetrics(
            row_count=table_ref.num_rows or 0,
            column_count=len(table_ref.schema),
            size_bytes=table_ref.num_bytes or 0,
            last_modified=table_ref.modified or datetime.now(timezone.utc),
            creation_time=table_ref.created or datetime.now(timezone.utc),
            table_type=table_ref.table_type or "TABLE",
            clustering_fields=table_ref.clustering_fields or [],
            partitioning_field=table_ref.time_partitioning.field if table_ref.time_partitioning else None,
            labels=table_ref.labels or {}
        )
    
    def _calculate_mcda_scores(self, table_ref: Any, metrics: TableMetrics, dataset_id: str) -> Dict[str, float]:
        scores = {}
        
        if metrics.row_count > 0:
            scores['row_count'] = min(log10(metrics.row_count) / 8, 1.0)
        else:
            scores['row_count'] = 0.0
        
        scores['requirement_coverage'] = self._calculate_requirement_coverage(table_ref)
        
        scores['field_relevance_density'] = self._calculate_relevance_density(table_ref)
        
        scores['schema_complexity'] = min(metrics.column_count / 200, 1.0)
        
        scores['table_freshness'] = self._calculate_freshness_score(metrics)
        
        scores['production_indicator'] = self._calculate_production_score(table_ref, dataset_id)
        
        return scores
    
    def _calculate_requirement_coverage(self, table_ref: Any) -> float:
        table_name = table_ref.table_id.lower()
        field_names = [field.name.lower() for field in table_ref.schema]
        combined_text = f"{table_name} {' '.join(field_names)}"
        
        coverage_count = 0
        total_requirements = len(self.requirement_indicators)
        
        for req_name, indicators in self.requirement_indicators.items():
            requirement_strength = 0
            for indicator in indicators:
                occurrences = combined_text.count(indicator)
                if occurrences > 0:
                    requirement_strength += occurrences
            
            if requirement_strength >= 2 or (requirement_strength >= 1 and indicator in table_name):
                coverage_count += 1
        
        return coverage_count / total_requirements
    
    def _calculate_relevance_density(self, table_ref: Any) -> float:
        if not table_ref.schema:
            return 0.0
        
        field_names = [field.name.lower() for field in table_ref.schema]
        all_indicators = [indicator for indicators in self.requirement_indicators.values() for indicator in indicators]
        
        relevant_fields = 0
        for field_name in field_names:
            for indicator in all_indicators:
                if indicator in field_name:
                    relevant_fields += 1
                    break
        
        return relevant_fields / len(field_names)
    
    def _calculate_freshness_score(self, metrics: TableMetrics) -> float:
        now = datetime.now(timezone.utc)
        
        last_modified = metrics.last_modified
        if last_modified.tzinfo is None:
            last_modified = last_modified.replace(tzinfo=timezone.utc)
        
        days_old = (now - last_modified).days
        
        if days_old < 30:
            return 1.0
        elif days_old < 90:
            return 0.8
        elif days_old < 365:
            return 0.6
        elif days_old < 1095:
            return 0.4
        else:
            return 0.2
    
    def _calculate_production_score(self, table_ref: Any, dataset_id: str) -> float:
        table_name = table_ref.table_id.lower()
        dataset_name = dataset_id.lower()
        
        production_indicators = ['prod', 'production', 'live', 'main', 'master']
        test_indicators = ['test', 'temp', 'tmp', 'dev', 'sandbox', 'backup', 'staging']
        
        score = 0.5
        
        for indicator in production_indicators:
            if indicator in table_name or indicator in dataset_name:
                score += 0.3
        
        for indicator in test_indicators:
            if indicator in table_name or indicator in dataset_name:
                score -= 0.4
        
        return max(0.0, min(1.0, score))
    
    def _calculate_topsis_score(self, scores: Dict[str, float]) -> float:
        if not scores:
            return 0.0
        
        weighted_scores = []
        for criterion, score in scores.items():
            weight = self.scoring_weights.get(criterion, 0.1)
            weighted_scores.append(score * weight)
        
        composite = sum(weighted_scores)
        
        return 1 - (1 - composite) ** 1.5