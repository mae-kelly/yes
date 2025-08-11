#!/usr/bin/env python3

class CostEstimator:
    BIGQUERY_COST_PER_TB = 5.0
    BIGQUERY_FREE_TIER_TB = 1.0
    
    def __init__(self):
        self.monthly_usage_tb = 0.0
    
    def estimate_query_cost(self, bytes_processed: int) -> float:
        tb_processed = bytes_processed / (1024 ** 4)
        
        if self.monthly_usage_tb + tb_processed <= self.BIGQUERY_FREE_TIER_TB:
            return 0.0
        
        billable_tb = max(0, tb_processed - max(0, self.BIGQUERY_FREE_TIER_TB - self.monthly_usage_tb))
        return billable_tb * self.BIGQUERY_COST_PER_TB
    
    def add_usage(self, bytes_processed: int):
        self.monthly_usage_tb += bytes_processed / (1024 ** 4)