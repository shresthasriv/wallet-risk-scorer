import math
from typing import Dict, Any
from core.interfaces import RiskScorer


class CompoundRiskScorer(RiskScorer):
    def __init__(self):
        self.weights = {
            "liquidation_risk": 0.20,
            "leverage_risk": 0.20,
            "activity_risk": 0.15,
            "behavioral_risk": 0.15,
            "trading_pattern_risk": 0.15,
            "technical_risk": 0.15
        }

    def calculate_score(self, features: Dict[str, Any]) -> int:
        if features["total_transactions"] == 0:
            return 'NA'

        liquidation_score = self._calculate_liquidation_risk(features)
        leverage_score = self._calculate_leverage_risk(features)
        activity_score = self._calculate_activity_risk(features)
        behavioral_score = self._calculate_behavioral_risk(features)
        trading_pattern_score = self._calculate_trading_pattern_risk(features)
        technical_score = self._calculate_technical_risk(features)
        
        weighted_score = (
            liquidation_score * self.weights["liquidation_risk"] +
            leverage_score * self.weights["leverage_risk"] +
            activity_score * self.weights["activity_risk"] +
            behavioral_score * self.weights["behavioral_risk"] +
            trading_pattern_score * self.weights["trading_pattern_risk"] +
            technical_score * self.weights["technical_risk"]
        )
        
        # Add wallet-specific entropy to distinguish similar profiles
        wallet_entropy = self._get_wallet_entropy(features.get("wallet_id", ""))
        adjusted_score = weighted_score + (wallet_entropy * 0.05)  # ±5% variation
        
        final_score = min(1000, max(0, int(adjusted_score * 1000)))
        
        return final_score

    def _get_wallet_entropy(self, wallet_id: str) -> float:
        if not wallet_id or len(wallet_id) < 8:
            return 0.0
        try:
            hash_val = int(wallet_id[-8:], 16)
            return (hash_val % 1000) / 10000.0
        except ValueError:
            return 0.0

    def _normalize_value(self, value: float, min_val: float = 0.001, max_val: float = 10000) -> float:
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
            size_risk = min(0.6, gas_value / 0.02)
        else:
            size_risk = self._normalize_value(max_value, 0.001, 1000) * 1.2
            size_risk = min(0.95, size_risk)

        concentration_risk = min(0.95, value_concentration * 1.5)

        value_volatility = min(1.0, features["value_std"] / max(max_value, 0.001))
        
        return size_risk * 0.4 + concentration_risk * 0.4 + value_volatility * 0.2

    def _calculate_activity_risk(self, features: Dict[str, Any]) -> float:
        frequency = features["transaction_frequency"]
        days_active = features["days_active"]

        if frequency < 0.1:
            frequency_risk = 0.3 + (0.1 - frequency) * 2
        elif frequency > 3:
            frequency_risk = min(0.9, 0.4 + (frequency - 3) * 0.1)
        else:
            frequency_risk = 0.1 + frequency * 0.1
        
        time_risk = max(0.1, min(0.8, 1.0 / math.sqrt(days_active + 1)))
        
        irregularity = 1.0 - features["time_regularity"]
        irregularity_risk = min(0.7, irregularity * 0.8)
        
        return frequency_risk * 0.4 + time_risk * 0.4 + irregularity_risk * 0.2

    def _calculate_behavioral_risk(self, features: Dict[str, Any]) -> float:
        function_diversity = features["function_diversity"]
        safe_ratio = features["safe_function_ratio"]
        unique_contracts = features["unique_contracts"]
        
        diversity_risk = max(0.1, min(0.8, 1.0 / (function_diversity + 0.5)))
        
        safety_risk = (1.0 - safe_ratio) ** 1.5
        
        contract_risk = max(0.1, min(0.7, 0.8 / math.sqrt(unique_contracts + 0.5)))
        
        avg_gas = features.get("avg_gas_used", 0)
        gas_efficiency_risk = min(0.3, avg_gas / 500000) if avg_gas > 0 else 0.1
        
        return (diversity_risk * 0.3 + safety_risk * 0.3 + 
                contract_risk * 0.3 + gas_efficiency_risk * 0.1)

    def _calculate_trading_pattern_risk(self, features: Dict[str, Any]) -> float:
        function_names = features.get("function_names", [])
        flash_loan_indicators = ["flashloan", "flash", "borrow", "liquidate"]
        flash_loan_usage = sum(1 for func in function_names if any(indicator in func.lower() for indicator in flash_loan_indicators))
        flash_loan_risk = min(0.9, flash_loan_usage / max(len(function_names), 1) * 3.0)
        
        max_value = features.get("max_value", 0)
        avg_value = features.get("avg_value", 0.001)
        if max_value > 0 and avg_value > 0:
            position_sizing_risk = min(0.8, max_value / max(avg_value, 0.001) / 15.0)
        else:
            position_sizing_risk = 0.1
        
        time_std = features.get("time_std", 0)
        avg_interval = features.get("avg_time_between_tx", 86400)
        if avg_interval > 0:
            panic_trading_risk = min(0.7, time_std / avg_interval / 5.0)
        else:
            panic_trading_risk = 0.2
        
        value_std = features.get("value_std", 0)
        avg_value = features.get("avg_value", 0.001)
        if avg_value > 0:
            volatility_risk = min(0.8, (value_std / avg_value) * 0.5)
        else:
            volatility_risk = 0.1
        
        final_risk = max(0.0, flash_loan_risk * 0.3 + position_sizing_risk * 0.3 + 
                        panic_trading_risk * 0.2 + volatility_risk * 0.2)
        
        return min(1.0, final_risk)

    def _calculate_technical_risk(self, features: Dict[str, Any]) -> float:
        avg_gas_price = features.get("avg_gas_price", 0)
        
        gas_efficiency_risk = 0.2
        if avg_gas_price > 0:
            normalized_gas = min(1.0, avg_gas_price / 1e9 / 100)
            gas_efficiency_risk = min(0.9, 0.2 + normalized_gas * 0.7)
        
        function_diversity = features.get("function_diversity", 1)
        failure_risk = min(0.8, function_diversity / 10.0)
        
        unique_contracts = features.get("unique_contracts", 1)
        contract_interaction_risk = min(0.9, unique_contracts / 5.0)
        
        frequency = features.get("transaction_frequency", 0)
        overtrading_risk = 0.1
        if frequency > 0.5:
            overtrading_risk = min(0.9, 0.1 + (frequency - 0.5) * 0.3)
        
        return (gas_efficiency_risk * 0.3 + failure_risk * 0.2 + 
                contract_interaction_risk * 0.3 + overtrading_risk * 0.2)
