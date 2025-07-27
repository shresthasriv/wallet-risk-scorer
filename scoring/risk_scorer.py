import math
from typing import Dict, Any
from core.interfaces import RiskScorer


class CompoundRiskScorer(RiskScorer):
    def __init__(self):
        self.weights = {
            "liquidation_risk": 0.35,
            "leverage_risk": 0.25,
            "activity_risk": 0.20,
            "behavioral_risk": 0.20
        }

    def calculate_score(self, features: Dict[str, Any]) -> int:
        if features["total_transactions"] == 0:
            return 'NA'

        liquidation_score = self._calculate_liquidation_risk(features)
        leverage_score = self._calculate_leverage_risk(features)
        activity_score = self._calculate_activity_risk(features)
        behavioral_score = self._calculate_behavioral_risk(features)
        
        weighted_score = (
            liquidation_score * self.weights["liquidation_risk"] +
            leverage_score * self.weights["leverage_risk"] +
            activity_score * self.weights["activity_risk"] +
            behavioral_score * self.weights["behavioral_risk"]
        )
        
        # Add wallet-specific entropy to distinguish similar profiles
        wallet_entropy = self._get_wallet_entropy(features.get("wallet_id", ""))
        adjusted_score = weighted_score + (wallet_entropy * 0.05)  # ±5% variation
        
        return min(1000, max(0, int(adjusted_score * 1000)))

    def _get_wallet_entropy(self, wallet_id: str) -> float:
        """Generate deterministic entropy from wallet address to break ties"""
        if not wallet_id or len(wallet_id) < 8:
            return 0.0
        try:
            # Use last 8 characters for entropy
            hash_val = int(wallet_id[-8:], 16)
            return (hash_val % 1000) / 10000.0  # 0-0.1 range
        except ValueError:
            return 0.0

    def _normalize_value(self, value: float, min_val: float = 0.001, max_val: float = 10000) -> float:
        """Normalize values using log scaling to handle wide ranges"""
        if value <= 0:
            return 0.0
        return min(1.0, math.log10(value + 1) / math.log10(max_val + 1))

    def _calculate_liquidation_risk(self, features: Dict[str, Any]) -> float:
        liquidation_count = features["liquidation_count"]

        liquidation_risk = min(1.0, liquidation_count / 3.0)
        
        risky_functions = features["risky_function_ratio"]
        function_risk = min(0.9, risky_functions * 1.2)
        
        return liquidation_risk * 0.7 + function_risk * 0.3

    def _calculate_leverage_risk(self, features: Dict[str, Any]) -> float:
        max_value = features["max_value"]
        value_concentration = features["value_concentration"]
        if max_value <= 0:
            gas_value = features.get("total_gas_cost", 0) / 10**18 
            size_risk = min(0.4, gas_value / 0.05) 
        else:
            size_risk = self._normalize_value(max_value, 0.001, 10000) * 0.95

        concentration_risk = min(0.9, value_concentration * 1.1)

        value_volatility = min(1.0, features["value_std"] / max(max_value, 0.001))
        
        return size_risk * 0.4 + concentration_risk * 0.4 + value_volatility * 0.2

    def _calculate_activity_risk(self, features: Dict[str, Any]) -> float:
        frequency = features["transaction_frequency"]
        days_active = features["days_active"]

        if frequency < 0.1:
            frequency_risk = 0.3 + (0.1 - frequency) * 2  # Penalty for very low activity
        elif frequency > 3:
            frequency_risk = min(0.9, 0.4 + (frequency - 3) * 0.1)  # Penalty for high frequency
        else:
            frequency_risk = 0.1 + frequency * 0.1  # Moderate risk for normal activity
        
        # Continuous time risk - inexperience penalty
        time_risk = max(0.1, min(0.8, 1.0 / math.sqrt(days_active + 1)))
        
        # Enhanced irregularity calculation
        irregularity = 1.0 - features["time_regularity"]
        irregularity_risk = min(0.7, irregularity * 0.8)
        
        return frequency_risk * 0.4 + time_risk * 0.4 + irregularity_risk * 0.2

    def _calculate_behavioral_risk(self, features: Dict[str, Any]) -> float:
        function_diversity = features["function_diversity"]
        safe_ratio = features["safe_function_ratio"]
        unique_contracts = features["unique_contracts"]
        
        # Continuous diversity risk - penalize low diversity more gradually
        diversity_risk = max(0.1, min(0.8, 1.0 / (function_diversity + 0.5)))
        
        # Enhanced safety risk - non-linear penalty for risky behavior
        safety_risk = (1.0 - safe_ratio) ** 1.5  # Exponential penalty for low safety
        
        # Continuous contract risk with diminishing returns
        contract_risk = max(0.1, min(0.7, 0.8 / math.sqrt(unique_contracts + 0.5)))
        
        # Add gas efficiency as behavioral indicator
        avg_gas = features.get("avg_gas_used", 0)
        gas_efficiency_risk = min(0.3, avg_gas / 500000) if avg_gas > 0 else 0.1
        
        return (diversity_risk * 0.3 + safety_risk * 0.3 + 
                contract_risk * 0.3 + gas_efficiency_risk * 0.1)
