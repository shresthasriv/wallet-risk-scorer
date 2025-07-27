import os
import sys
import time
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.interfaces import WalletRiskAnalyzer
from infrastructure.data_provider import EtherscanV2DataProvider
from features.extractor import CompoundFeatureExtractor
from scoring.risk_scorer import CompoundRiskScorer
from utils.wallet_loader import WalletLoader
from utils.csv_exporter import CSVExporter

load_dotenv()


def main():
    input_file = "wallets.csv"
    output_file = "wallet_risk_scores.csv"
    
    wallet_addresses = WalletLoader.load_wallet_addresses(input_file)
    
    # Single API key for Etherscan V2 multi-chain support
    api_key = os.getenv("ETH_API_KEY")
    
    data_provider = EtherscanV2DataProvider(api_key)
    feature_extractor = CompoundFeatureExtractor()
    risk_scorer = CompoundRiskScorer()
    
    analyzer = WalletRiskAnalyzer(data_provider, feature_extractor, risk_scorer)
    
    scores = []
    total_wallets = len(wallet_addresses)
    
    for i, wallet_address in enumerate(wallet_addresses, 1):
        print(f"Processing wallet {i}/{total_wallets}: {wallet_address}")
        
        try:
            score = analyzer.analyze_wallet(wallet_address)
            scores.append(score)
            print(f"Score: {score.score}")
        except Exception as e:
            print(f"Error processing wallet {wallet_address}: {e}")
            from core.interfaces import WalletRiskScore
            scores.append(WalletRiskScore(wallet_id=wallet_address, score=500))
        
        time.sleep(0.2)
    
    CSVExporter.export_scores(scores, output_file)
    print(f"Risk scores exported to {output_file}")


if __name__ == "__main__":
    main()
