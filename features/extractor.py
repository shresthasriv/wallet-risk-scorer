import numpy as np
from typing import List, Dict, Any
from collections import Counter
from core.interfaces import FeatureExtractor, Transaction


class CompoundFeatureExtractor(FeatureExtractor):
    def extract_features(self, transactions: List[Transaction]) -> Dict[str, Any]:
        if not transactions:
            return self._get_default_features()
        
        
        features = {}
        
        features.update(self._extract_basic_features(transactions))
        features.update(self._extract_frequency_features(transactions))
        features.update(self._extract_value_features(transactions))
        features.update(self._extract_gas_features(transactions))
        features.update(self._extract_temporal_features(transactions))
        features.update(self._extract_function_features(transactions))
        
        # Debug: Show extracted features
        print("Extracted features:")
        for key, value in features.items():
            if key != "function_names":  # Skip the long list
                if isinstance(value, float):
                    print(f"  {key}: {value:.6f}")
                else:
                    print(f"  {key}: {value}")
        print("=" * 50)
        
        return features

    def _extract_basic_features(self, transactions: List[Transaction]) -> Dict[str, Any]:
        return {
            "total_transactions": len(transactions),
            "unique_contracts": len(set(tx.to_address for tx in transactions)),
            "total_value": sum(tx.value for tx in transactions),
            "avg_value": np.mean([tx.value for tx in transactions]) if transactions else 0
        }

    def _extract_frequency_features(self, transactions: List[Transaction]) -> Dict[str, Any]:
        if not transactions:
            return {"transaction_frequency": 0, "days_active": 0}
        
        timestamps = [tx.timestamp for tx in transactions]
        time_span = max(timestamps) - min(timestamps)
        days_active = time_span / 86400 if time_span > 0 else 1
        
        return {
            "transaction_frequency": len(transactions) / max(days_active, 1),
            "days_active": days_active
        }

    def _extract_value_features(self, transactions: List[Transaction]) -> Dict[str, Any]:
        values = [tx.value for tx in transactions if tx.value > 0]
        if not values:
            return {"value_std": 0, "max_value": 0, "value_concentration": 0}
        
        return {
            "value_std": np.std(values),
            "max_value": max(values),
            "value_concentration": max(values) / sum(values) if sum(values) > 0 else 0
        }

    def _extract_gas_features(self, transactions: List[Transaction]) -> Dict[str, Any]:
        gas_used = [tx.gas_used for tx in transactions]
        gas_prices = [tx.gas_price for tx in transactions]
        
        return {
            "avg_gas_used": np.mean(gas_used) if gas_used else 0,
            "avg_gas_price": np.mean(gas_prices) if gas_prices else 0,
            "total_gas_cost": sum(tx.gas_used * tx.gas_price for tx in transactions)
        }

    def _extract_temporal_features(self, transactions: List[Transaction]) -> Dict[str, Any]:
        if len(transactions) < 2:
            return {
                "avg_time_between_tx": 0, 
                "time_regularity": 0,
                "time_std": 0
            }
        
        timestamps = sorted([tx.timestamp for tx in transactions])
        intervals = [timestamps[i] - timestamps[i-1] for i in range(1, len(timestamps))]
        
        return {
            "avg_time_between_tx": np.mean(intervals),
            "time_regularity": 1 / (1 + np.std(intervals)) if intervals else 0,
            "time_std": np.std(intervals) if intervals else 0
        }

    def _extract_function_features(self, transactions: List[Transaction]) -> Dict[str, Any]:
        functions = [tx.function_name for tx in transactions if tx.function_name]
        function_counts = Counter(functions)
        
        # V2 and V3 function patterns
        risky_functions = ["liquidateBorrow", "repayBorrow", "borrow", "absorb", "buyCollateral"]
        safe_functions = ["mint", "redeem", "transfer", "supply", "withdraw"]
        
        risky_count = 0
        safe_count = 0
        liquidation_count = 0
        
        for func_name in functions:
            func_lower = func_name.lower()
            
            if any(risky_func.lower() in func_lower for risky_func in risky_functions):
                risky_count += 1
                
            if "liquidateborrow" in func_lower:
                liquidation_count += 1
                
            if any(safe_func.lower() in func_lower for safe_func in safe_functions):
                safe_count += 1
        
        return {
            "function_diversity": len(function_counts),
            "risky_function_ratio": risky_count / len(transactions) if transactions else 0,
            "safe_function_ratio": safe_count / len(transactions) if transactions else 0,
            "liquidation_count": liquidation_count,
            "function_names": functions  # Add raw function names for pattern analysis
        }

    def _get_default_features(self) -> Dict[str, Any]:
        return {
            "total_transactions": 0,
            "unique_contracts": 0,
            "total_value": 0,
            "avg_value": 0,
            "transaction_frequency": 0,
            "days_active": 0,
            "value_std": 0,
            "max_value": 0,
            "value_concentration": 0,
            "avg_gas_used": 0,
            "avg_gas_price": 0,
            "total_gas_cost": 0,
            "avg_time_between_tx": 0,
            "time_regularity": 0,
            "time_std": 0,
            "function_diversity": 0,
            "risky_function_ratio": 0,
            "safe_function_ratio": 0,
            "liquidation_count": 0,
            "function_names": []
        }
