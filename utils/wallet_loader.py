import csv
from typing import List


class WalletLoader:
    @staticmethod
    def load_wallet_addresses(file_path: str) -> List[str]:
        addresses = []
        with open(file_path, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                addresses.append(row['wallet_id'])
        return addresses
