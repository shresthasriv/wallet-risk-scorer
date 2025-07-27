import requests
import time
from typing import List
from core.interfaces import DataProvider, Transaction


class EtherscanV2DataProvider(DataProvider):
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.base_url = "https://api.etherscan.io/v2/api"
        
        # Chain ID mapping - using standard EVM chain IDs
        self.chain_configs = {
            1: {  # Ethereum Mainnet
                'name': 'ethereum',
                'compound_v2_addresses': {
                    "0x3d9819210a31b4961b30ef54be2aed79b9c9cd3b": "Comptroller",
                    "0x4ddc2d193948926d02f9b1fe9e1daa0718270ed5": "cETH",
                    "0x5d3a536e4d6dbd6114cc1ead35777bab948e3643": "cDAI",
                    "0x39aa39c021dfbae8fac545936693ac917d5e7563": "cUSDC",
                    "0xf650c3d88d12db855b8bf7d11be6c55a4e07dcc9": "cUSDT",
                    "0xc11b1268c1a384e55c48c2391d8d480264a3a7f4": "cWBTC",
                    "0x35a18000230da775cac24873d00ff85bccded550": "cUNI",
                    "0x70e36f6bf80a52b3b46b3af8e106cc0ed743e8e4": "cCOMP",
                    "0xe65cdb6479bac1e22340e4e755fae7e509ecd06c": "cAAVE",
                    "0x95b4ef2869ebd94beb4eee400a99824bf5dc325b": "cMKR",
                    "0x4b0181102a0112a2ef11abee5563bb4a3176c9d7": "cSUSHI",
                    "0x6c8c6b02e7b2be14d4fa6022dfd6d75921d90e4e": "cBAT",
                    "0x7713dd9ca933848f6819f38b8352d9a15ea73f67": "cFEI",
                    "0xface851a4921ce59e912d19329929ce6da6eb0c7": "cLINK",
                    "0x12392f67bdf24fae0af363c24ac620a2f67dad86": "cTUSD",
                    "0x041171993284df560249b57358f931d9eb7b925d": "cUSDP",
                    "0x80a2ae356fc9ef4305676f7a3e2ed04e12c33946": "cYFI",
                    "0xb3319f5d18bc0d84dd1b4825dcde5d5f7266d407": "cZRX",
                    "0x158079ee67fce2f58472a96584a73c7ab9ac95c1": "cREP",
                    "0xf5dce57282a584d2746faf1593d3121fcac444dc": "cSAI"  # Legacy SAI market
                },
                'compound_v3_addresses': {
                    "0xc3d688b66703497daa19211eedff47f25384cdc3": "cUSDCv3",
                    "0xa17581a9e3356d9a858b789d68b4d866e593ae94": "cWETHv3",
                    "0xd98be00b5d27fc98112bde293e487f8d4ca57d07": "cUSDTv3"
                }
            },
            137: {  # Polygon
                'name': 'polygon',
                'compound_v2_addresses': {},  # No V2 on Polygon
                'compound_v3_addresses': {
                    "0xf25212e676d1f7f89cd72ffee66158f541246445": "cUSDCv3_Polygon"
                }
            },
            42161: {  # Arbitrum One
                'name': 'arbitrum',
                'compound_v2_addresses': {},  # No V2 on Arbitrum
                'compound_v3_addresses': {
                    "0x9c4ec768c28520b50860ea7a15bd7213a9ff58bf": "cUSDCv3_Arbitrum"
                }
            },
            8453: {  # Base
                'name': 'base',
                'compound_v2_addresses': {},  # No V2 on Base
                'compound_v3_addresses': {
                    "0x9c4ec768c28520b50860ea7a15bd7213a9ff58bf": "cUSDbCv3_Base"
                }
            },
            10: {  # Optimism
                'name': 'optimism',
                'compound_v2_addresses': {},  # No V2 on Optimism
                'compound_v3_addresses': {
                    "0x2e44e174f7d53f0212823acc11c01a11d58c5bcb": "cUSDCv3_Optimism"
                }
            },
            534352: {  # Scroll
                'name': 'scroll',
                'compound_v2_addresses': {},  # No V2 on Scroll
                'compound_v3_addresses': {
                    "0xB2f97c1Bd3bf02f5e74d13f02E3e26F93D77CE44": "cUSDCv3_Scroll"
                }
            }
        }

    def get_wallet_transactions(self, wallet_address: str) -> List[Transaction]:
        all_transactions = []
        
        # Fetch from all supported chains
        for chain_id, config in self.chain_configs.items():
            print(f"Fetching {config['name']} (chain {chain_id}) transactions for {wallet_address}")
            
            try:
                transactions = self._fetch_chain_transactions(wallet_address, chain_id)
                
                # Filter for Compound addresses on this chain
                compound_addresses = set(
                    list(config['compound_v2_addresses'].keys()) + 
                    list(config['compound_v3_addresses'].keys())
                )
                
                chain_compound_txs = []
                for tx in transactions:
                    if tx.to_address and tx.to_address.lower() in [addr.lower() for addr in compound_addresses]:
                        # Add network info to transaction
                        tx.network = config['name']
                        chain_compound_txs.append(tx)
                
                all_transactions.extend(chain_compound_txs)
                print(f"Found {len(chain_compound_txs)} Compound transactions on {config['name']}")
                
                # Rate limiting between chains
                time.sleep(0.2)  # Reduced since it's the same API endpoint
                
            except Exception as e:
                print(f"Error fetching {config['name']} transactions: {e}")
                continue
        
        print(f"Total Compound transactions across all chains: {len(all_transactions)}")
        return all_transactions

    def _fetch_chain_transactions(self, wallet_address: str, chain_id: int) -> List[Transaction]:
        params = {
            "chainid": chain_id,
            "module": "account",
            "action": "txlist",
            "address": wallet_address,
            "startblock": 0,
            "endblock": 99999999,
            "page": 1,
            "offset": 10000,
            "sort": "desc",
            "apikey": self.api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            data = response.json()
            
            if data.get("status") != "1":
                if "No transactions found" in data.get("message", ""):
                    return []  # No transactions is normal
                else:
                    print(f"Chain {chain_id} API response: {data.get('message', 'Unknown error')}")
                    return []
            
            transactions = []
            for tx in data["result"]:
                transaction = Transaction(
                    hash=tx["hash"],
                    block_number=int(tx["blockNumber"]),
                    timestamp=int(tx["timeStamp"]),
                    from_address=tx["from"],
                    to_address=tx["to"],
                    value=float(tx["value"]) / 10**18,
                    gas_used=int(tx["gasUsed"]),
                    gas_price=int(tx["gasPrice"]),
                    function_name=tx.get("functionName", ""),
                    input_data=tx["input"]
                )
                transactions.append(transaction)
            
            return transactions
        except Exception as e:
            print(f"Error fetching chain {chain_id} transactions: {e}")
            return []
