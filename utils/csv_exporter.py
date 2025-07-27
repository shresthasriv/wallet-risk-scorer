import pandas as pd
from typing import List
from core.interfaces import WalletRiskScore


class CSVExporter:
    @staticmethod
    def export_scores(scores: List[WalletRiskScore], output_path: str) -> None:
        data = [{"wallet_id": score.wallet_id, "score": score.score} for score in scores]
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False)
