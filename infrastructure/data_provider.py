import requests
import time
from typing import List
from web3 import Web3
from core.interfaces import DataProvider, Transaction


class EtherscanV2DataProvider(DataProvider):
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.base_url = "https://api.etherscan.io/v2/api"
        
        # Compound V2 Comptroller address on Ethereum mainnet
        self.comptroller_address = "0x3d9819210a31b4961b30ef54be2aed79b9c9cd3b"
        
        # Chain ID mapping - using standard EVM chain IDs
        self.chain_configs = {
            1: {  # Ethereum Mainnet
                'name': 'ethereum',
                'compound_v2_addresses': {
                    # This will be populated dynamically via web3
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
                    "0xf25212e676d1f7f89cd72ffee66158f541246445": "cUSDCv3"
                }
            },
            42161: {  # Arbitrum One
                'name': 'arbitrum',
                'compound_v2_addresses': {},  # No V2 on Arbitrum
                'compound_v3_addresses': {
                    "0xa5edbdd9646f8dff606d7448e414884c7d905dca": "cUSDCv3",
                    "0x9c4ec768c28520b50860ea7a15bd7213a9ff58bf": "cUSDCev3"
                }
            },
            8453: {  # Base
                'name': 'base',
                'compound_v2_addresses': {},  # No V2 on Base
                'compound_v3_addresses': {
                    "0x46e6b214b524310239732d51387075e0e70970bf": "cUSDCv3",
                    "0x9c4ec768c28520b50860ea7a15bd7213a9ff58bf": "cUSDbCv3"
                }
            },
            10: {  # Optimism
                'name': 'optimism',
                'compound_v2_addresses': {},  # No V2 on Optimism
                'compound_v3_addresses': {
                    "0x2e44e174f7d53f0212823acc11c01a11d58c5bcb": "cUSDCv3"
                }
            },
            534352: {  # Scroll
                'name': 'scroll',
                'compound_v2_addresses': {},  # No V2 on Scroll
                'compound_v3_addresses': {
                    "0xb2f97c1bd3bf02f5e74d13f02e3e26f93d77ce44": "cUSDCv3"
                }
            }
        }
        
        # Fetch dynamic Compound V2 markets on initialization
        self._fetch_compound_v2_markets()

    def _fetch_compound_v2_markets(self):
        """
        Dynamically fetch all Compound V2 market addresses from the Comptroller contract
        using web3 and a public RPC endpoint.
        """
        print("Fetching all Compound V2 market addresses dynamically...")
        
        try:
            # Use a public Ethereum RPC endpoint
            rpc_url = "https://eth.llamarpc.com"
            w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 10}))
            
            # Comptroller ABI - we only need the getAllMarkets function
            comptroller_abi = [
                {
                    "constant": True,
                    "inputs": [],
                    "name": "getAllMarkets",
                    "outputs": [{"name": "", "type": "address[]"}],
                    "payable": False,
                    "stateMutability": "view",
                    "type": "function"
                }
            ]
            
            # Create contract instance
            comptroller = w3.eth.contract(
                address=Web3.to_checksum_address(self.comptroller_address),
                abi=comptroller_abi
            )
            
            # Call getAllMarkets function
            markets = comptroller.functions.getAllMarkets().call()
            
            # Convert to our format (address -> name mapping)
            v2_addresses = {}
            for i, market_address in enumerate(markets):
                market_address_lower = market_address.lower()
                v2_addresses[market_address_lower] = f"cToken_{i}"
            
            # Add the comptroller itself
            v2_addresses[self.comptroller_address.lower()] = "Comptroller"
            
            # Update the chain config
            self.chain_configs[1]['compound_v2_addresses'] = v2_addresses
            
            print(f"Successfully loaded {len(v2_addresses)} Compound V2 addresses")
            
        except Exception as e:
            print(f"Error fetching Compound V2 markets via web3: {e}")

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
