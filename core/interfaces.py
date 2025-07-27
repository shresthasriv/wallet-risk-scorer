from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class Transaction:
    hash: str
    block_number: int
    timestamp: int
    from_address: str
    to_address: str
    value: float
    gas_used: int
    gas_price: int
    function_name: str
    input_data: str
    network: str = "ethereum" 


@dataclass
class WalletRiskScore:
    wallet_id: str
    score: int


class DataProvider(ABC):
    @abstractmethod
    def get_wallet_transactions(self, wallet_address: str) -> List[Transaction]:
        pass


class FeatureExtractor(ABC):
    @abstractmethod
    def extract_features(self, transactions: List[Transaction]) -> Dict[str, Any]:
        pass


class RiskScorer(ABC):
    @abstractmethod
    def calculate_score(self, features: Dict[str, Any]) -> int:
        pass


class WalletRiskAnalyzer:
    def __init__(self, data_provider: DataProvider, feature_extractor: FeatureExtractor, risk_scorer: RiskScorer):
        self.data_provider = data_provider
        self.feature_extractor = feature_extractor
        self.risk_scorer = risk_scorer

    def analyze_wallet(self, wallet_address: str) -> WalletRiskScore:
        transactions = self.data_provider.get_wallet_transactions(wallet_address)
        features = self.feature_extractor.extract_features(transactions)
        # Add wallet_id to features for entropy calculation
        features["wallet_id"] = wallet_address
        score = self.risk_scorer.calculate_score(features)
        return WalletRiskScore(wallet_id=wallet_address, score=score)

    def analyze_wallets(self, wallet_addresses: List[str]) -> List[WalletRiskScore]:
        return [self.analyze_wallet(address) for address in wallet_addresses]
