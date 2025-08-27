import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.neighbors import LocalOutlierFactor
from sklearn.svm import OneClassSVM
import warnings
warnings.filterwarnings('ignore')

class MLValidationEngine:
    def __init__(self):
        self.scaler = StandardScaler()
        self.algorithms = {
            'isolation_forest': IsolationForest(contamination=0.1, random_state=42),
            'lof': LocalOutlierFactor(n_neighbors=20, contamination=0.1),
            'kmeans': KMeans(n_clusters=5, random_state=42),
            'pca': PCA(n_components=0.95),
            'one_class_svm': OneClassSVM(nu=0.1),
            'random_forest': RandomForestClassifier(n_estimators=100, random_state=42)
        }
        self.validation_results = {}
        
    def prepare_data(self, raw_data):
        """Convert raw metrics to ML-ready format"""
        features = []
        
        for metric_name, metric_data in raw_data.items():
            if isinstance(metric_data, dict):
                for key, value in metric_data.items():
                    if isinstance(value, (int, float)):
                        features.append({
                            'metric': metric_name,
                            'key': key,
                            'value': value,
                            'metric_type': self._classify_metric_type(metric_name)
                        })
        
        df = pd.DataFrame(features)
        return df
    
    def _classify_metric_type(self, metric_name):
        """Classify metrics into categories for better analysis"""
        coverage_metrics = ['tanium', 'cmdb', 'splunk', 'dlp', 'ssc']
        geographic_metrics = ['region', 'country', 'datacenter']
        infrastructure_metrics = ['infrastructure', 'system', 'class']
        organizational_metrics = ['business_unit', 'cio']
        
        metric_lower = metric_name.lower()
        
        if any(cm in metric_lower for cm in coverage_metrics):
            return 'coverage'
        elif any(gm in metric_lower for gm in geographic_metrics):
            return 'geographic'
        elif any(im in metric_lower for im in infrastructure_metrics):
            return 'infrastructure'
        elif any(om in metric_lower for om in organizational_metrics):
            return 'organizational'
        else:
            return 'other'
    
    def detect_anomalies(self, df):
        """Use multiple algorithms to detect data anomalies"""
        if df.empty or len(df) < 10:
            return {'anomalies': [], 'confidence': 0.0}
        
        numeric_features = ['value']
        X = df[numeric_features].values
        
        if len(X) < 5:
            return {'anomalies': [], 'confidence': 0.0}
        
        X_scaled = self.scaler.fit_transform(X)
        
        anomaly_scores = {}
        
        try:
            iso_forest = self.algorithms['isolation_forest']
            iso_predictions = iso_forest.fit_predict(X_scaled)
            anomaly_scores['isolation_forest'] = (iso_predictions == -1).sum()
        except:
            anomaly_scores['isolation_forest'] = 0
        
        try:
            lof = self.algorithms['lof']
            lof_predictions = lof.fit_predict(X_scaled)
            anomaly_scores['lof'] = (lof_predictions == -1).sum()
        except:
            anomaly_scores['lof'] = 0
        
        try:
            svm = self.algorithms['one_class_svm']
            svm_predictions = svm.fit_predict(X_scaled)
            anomaly_scores['svm'] = (svm_predictions == -1).sum()
        except:
            anomaly_scores['svm'] = 0
        
        total_anomalies = sum(anomaly_scores.values())
        confidence = 1.0 - (total_anomalies / (len(df) * 3))
        
        return {
            'anomalies': anomaly_scores,
            'total_anomalies': total_anomalies,
            'confidence': max(0.0, confidence),
            'sample_size': len(df)
        }
    
    def validate_distributions(self, df):
        """Validate data distributions make sense"""
        if df.empty:
            return {'distribution_health': 0.0}
        
        validation_scores = {}
        
        by_metric_type = df.groupby('metric_type')['value']
        
        for metric_type, values in by_metric_type:
            if len(values) < 3:
                validation_scores[metric_type] = 0.5
                continue
            
            values_array = values.values
            
            cv = np.std(values_array) / np.mean(values_array) if np.mean(values_array) != 0 else 0
            
            skewness = self._calculate_skewness(values_array)
            
            zero_ratio = (values_array == 0).sum() / len(values_array)
            
            health_score = 1.0
            if cv > 2.0:
                health_score -= 0.3
            if abs(skewness) > 2.0:
                health_score -= 0.2
            if zero_ratio > 0.5:
                health_score -= 0.3
            
            validation_scores[metric_type] = max(0.0, health_score)
        
        overall_health = np.mean(list(validation_scores.values())) if validation_scores else 0.0
        
        return {
            'distribution_health': overall_health,
            'by_metric_type': validation_scores,
            'overall_score': overall_health
        }
    
    def _calculate_skewness(self, data):
        """Calculate skewness of data distribution"""
        if len(data) < 3:
            return 0.0
        
        mean = np.mean(data)
        std = np.std(data)
        
        if std == 0:
            return 0.0
        
        skewness = np.mean(((data - mean) / std) ** 3)
        return skewness
    
    def cluster_analysis(self, df):
        """Perform clustering to identify data patterns"""
        if df.empty or len(df) < 10:
            return {'clusters': 0, 'silhouette_score': 0.0}
        
        X = df[['value']].values
        X_scaled = self.scaler.fit_transform(X)
        
        optimal_clusters = 2
        best_score = -1
        
        for n_clusters in range(2, min(8, len(df)//2)):
            try:
                kmeans = KMeans(n_clusters=n_clusters, random_state=42)
                cluster_labels = kmeans.fit_predict(X_scaled)
                score = silhouette_score(X_scaled, cluster_labels)
                
                if score > best_score:
                    best_score = score
                    optimal_clusters = n_clusters
            except:
                continue
        
        try:
            final_kmeans = KMeans(n_clusters=optimal_clusters, random_state=42)
            cluster_labels = final_kmeans.fit_predict(X_scaled)
            
            cluster_info = {}
            for i in range(optimal_clusters):
                cluster_mask = cluster_labels == i
                cluster_values = df[cluster_mask]['value'].values
                cluster_info[f'cluster_{i}'] = {
                    'size': int(cluster_mask.sum()),
                    'mean_value': float(np.mean(cluster_values)),
                    'std_value': float(np.std(cluster_values)),
                    'metrics': df[cluster_mask]['metric'].unique().tolist()
                }
        except:
            cluster_info = {}
        
        return {
            'optimal_clusters': optimal_clusters,
            'silhouette_score': max(0.0, best_score),
            'cluster_details': cluster_info
        }
    
    def validate_relationships(self, df):
        """Validate logical relationships between metrics"""
        relationship_scores = {}
        
        by_metric = df.groupby('metric')['value'].sum().to_dict()
        
        coverage_metrics = [k for k in by_metric.keys() if any(cm in k.lower() for cm in ['tanium', 'cmdb', 'splunk'])]
        
        if len(coverage_metrics) >= 2:
            coverage_values = [by_metric[cm] for cm in coverage_metrics]
            coverage_correlation = np.corrcoef(coverage_values)[0, 1] if len(coverage_values) == 2 else 0.0
            relationship_scores['coverage_correlation'] = abs(coverage_correlation)
        
        geographic_metrics = [k for k in by_metric.keys() if any(gm in k.lower() for gm in ['region', 'country'])]
        if len(geographic_metrics) >= 2:
            geo_values = [by_metric[gm] for gm in geographic_metrics]
            geo_correlation = np.corrcoef(geo_values)[0, 1] if len(geo_values) == 2 else 0.0
            relationship_scores['geographic_consistency'] = abs(geo_correlation)
        
        total_assets_metrics = [k for k in by_metric.keys() if 'total' in k.lower()]
        if total_assets_metrics:
            total_values = [by_metric[tam] for tam in total_assets_metrics]
            consistency = 1.0 - (np.std(total_values) / np.mean(total_values)) if np.mean(total_values) > 0 else 0.0
            relationship_scores['total_consistency'] = max(0.0, consistency)
        
        return {
            'relationship_validation': relationship_scores,
            'overall_relationship_score': np.mean(list(relationship_scores.values())) if relationship_scores else 0.5
        }
    
    def comprehensive_validation(self, raw_metrics):
        """Run all validation algorithms"""
        df = self.prepare_data(raw_metrics)
        
        if df.empty:
            return {
                'overall_confidence': 0.0,
                'validation_summary': 'Insufficient data for validation',
                'recommendations': ['Ensure data collection is working properly']
            }
        
        anomaly_results = self.detect_anomalies(df)
        distribution_results = self.validate_distributions(df)
        cluster_results = self.cluster_analysis(df)
        relationship_results = self.validate_relationships(df)
        
        confidence_factors = [
            anomaly_results.get('confidence', 0.0),
            distribution_results.get('overall_score', 0.0),
            min(1.0, cluster_results.get('silhouette_score', 0.0) + 0.5),
            relationship_results.get('overall_relationship_score', 0.5)
        ]
        
        overall_confidence = np.mean(confidence_factors)
        
        recommendations = []
        if anomaly_results.get('total_anomalies', 0) > len(df) * 0.2:
            recommendations.append("High number of anomalies detected - investigate data quality")
        
        if distribution_results.get('overall_score', 0.0) < 0.7:
            recommendations.append("Distribution patterns suggest potential data collection issues")
        
        if cluster_results.get('silhouette_score', 0.0) < 0.3:
            recommendations.append("Clustering analysis shows poor data structure - verify metric calculations")
        
        if relationship_results.get('overall_relationship_score', 0.0) < 0.4:
            recommendations.append("Logical relationships between metrics appear inconsistent")
        
        if overall_confidence >= 0.8:
            validation_summary = "High confidence - metrics appear valid and consistent"
        elif overall_confidence >= 0.6:
            validation_summary = "Moderate confidence - some irregularities detected"
        else:
            validation_summary = "Low confidence - significant data quality issues detected"
        
        return {
            'overall_confidence': round(overall_confidence, 3),
            'confidence_breakdown': {
                'anomaly_detection': round(anomaly_results.get('confidence', 0.0), 3),
                'distribution_health': round(distribution_results.get('overall_score', 0.0), 3),
                'clustering_quality': round(min(1.0, cluster_results.get('silhouette_score', 0.0) + 0.5), 3),
                'relationship_consistency': round(relationship_results.get('overall_relationship_score', 0.5), 3)
            },
            'detailed_results': {
                'anomalies': anomaly_results,
                'distributions': distribution_results,
                'clusters': cluster_results,
                'relationships': relationship_results
            },
            'validation_summary': validation_summary,
            'recommendations': recommendations if recommendations else ["Data quality appears good - continue monitoring"],
            'sample_metrics_analyzed': len(df),
            'unique_metric_types': df['metric_type'].nunique() if not df.empty else 0
        }
    
    def validate_specific_metric(self, metric_name, metric_data):
        """Validate a specific metric's values"""
        if not isinstance(metric_data, dict):
            return {'metric_confidence': 0.5, 'issues': ['Metric data format invalid']}
        
        values = [v for v in metric_data.values() if isinstance(v, (int, float))]
        
        if not values:
            return {'metric_confidence': 0.0, 'issues': ['No numeric values found']}
        
        issues = []
        confidence = 1.0
        
        if any(v < 0 for v in values):
            issues.append("Negative values detected")
            confidence -= 0.3
        
        total_value = sum(values)
        if total_value == 0:
            issues.append("All values are zero")
            confidence -= 0.5
        
        if len(set(values)) == 1 and len(values) > 1:
            issues.append("All values are identical")
            confidence -= 0.2
        
        if max(values) > 1000000:
            issues.append("Extremely large values detected")
            confidence -= 0.1
        
        cv = np.std(values) / np.mean(values) if np.mean(values) != 0 else 0
        if cv > 3.0:
            issues.append("High variability in values")
            confidence -= 0.2
        
        return {
            'metric_confidence': max(0.0, confidence),
            'issues': issues if issues else ['No issues detected'],
            'value_statistics': {
                'count': len(values),
                'sum': total_value,
                'mean': np.mean(values),
                'std': np.std(values),
                'min': min(values),
                'max': max(values)
            }
        }