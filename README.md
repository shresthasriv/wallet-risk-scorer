# Wallet Risk Scoring System for Compound Protocol

This project implements a comprehensive risk scoring system for analyzing wallet behavior on the Compound DeFi protocol across multiple blockchain networks.

## 🎯 Assignment Deliverables

### 1. Risk Scores Output
- **Format**: CSV file with columns `wallet_id` and `score`
- **Range**: Risk scores from 0-1000
- **Sample Output**:
  ```
  wallet_id,score
  0x0039f22efb07a647557c7c5d17854cfd6d489ef3,231
  0x06b51c6882b27cb05e712185531c1f74996dd988,210
  ```

### 2. Technical Implementation
- Multi-chain transaction analysis (Ethereum, Polygon, Arbitrum, Base, Optimism, Scroll)
- Comprehensive feature extraction from DeFi transactions
- Advanced risk scoring with continuous mathematical functions
- Modular architecture for extensibility

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Etherscan API key

### Installation
```bash
# Clone and navigate to project
git clone https://github.com/shresthasriv/wallet-risk-scorer.git

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
echo "ETH_API_KEY=your_etherscan_api_key" > .env

# Run the analysis
python main.py
```

### Input/Output
- **Input**: `wallets.csv` - List of wallet addresses to analyze
- **Output**: `wallet_risk_scores.csv` - Risk scores for each wallet

## 📊 Data Collection Method

### Multi-Chain Data Sources
- **Primary API**: Etherscan V2 unified endpoint
- **Coverage**: 6 major EVM networks with single API key
- **Advantage**: Eliminates API fragmentation, reduces complexity

### Supported Networks & Contracts

| Network | V2 Contracts | V3 Contracts | Chain ID |
|---------|-------------|-------------|----------|
| **Ethereum** | 20 contracts (cDAI, cETH, cUSDC, etc.) | 3 contracts (cUSDCv3, cWETHv3, cUSDTv3) | 1 |
| **Polygon** | None | cUSDCv3_Polygon | 137 |
| **Arbitrum** | None | cUSDCv3_Arbitrum | 42161 |
| **Base** | None | cUSDbCv3_Base | 8453 |
| **Optimism** | None | cUSDCv3_Optimism | 10 |
| **Scroll** | None | cUSDCv3_Scroll | 534352 |

### Transaction Data Captured
```python
@dataclass
class Transaction:
    hash: str
    block_number: int
    timestamp: int
    from_address: str
    to_address: str
    value: float           # ETH value
    gas_used: int
    gas_price: int
    function_name: str     # DeFi function called
    input_data: str
    network: str          # Chain identifier
```

## Feature Selection Rationale

### Core Risk Categories (Weighted Approach)

#### 1. Liquidation Risk (35% weight) - *Highest Priority*
- **Liquidation Count**: Direct evidence of past liquidations
- **Risky Function Ratio**: Proportion of high-risk operations
- **Functions Monitored**: `liquidateBorrow`, `repayBorrow`, `borrow`, `absorb`, `buyCollateral`
- **Justification**: Past liquidations are the strongest predictor of future risk

#### 2. Leverage Risk (25% weight)
- **Maximum Transaction Value**: Indicates position size exposure
- **Value Concentration**: Risk of over-exposure in single transactions  
- **Value Volatility**: Standard deviation relative to maximum value
- **Gas-based Fallback**: For zero-value transactions, use gas cost as significance proxy

#### 3. Activity Risk (20% weight)
- **Transaction Frequency**: Extreme patterns (bot-like or dormant)
- **Days Active**: Experience level assessment
- **Time Regularity**: Consistency vs reactive behavior
- **Risk Pattern**: Both very high and very low activity indicate risk

#### 4. Behavioral Risk (20% weight)
- **Function Diversity**: Breadth of protocol usage
- **Safe Function Ratio**: Proportion of conservative operations (`mint`, `redeem`, `transfer`)
- **Contract Diversity**: Multi-contract interaction experience
- **Gas Efficiency**: Operational sophistication indicator

#### Continuous Scoring Functions

```python
size_risk = self._normalize_value(max_value, 0.001, 10000) * 0.95
# Continuous logarithmic scaling
```

#### Normalization Strategy
```python
def _normalize_value(self, value: float, min_val: float = 0.001, max_val: float = 10000) -> float:
    """Logarithmic scaling for wide value ranges"""
    if value <= 0:
        return 0.0
    return min(1.0, math.log10(value + 1) / math.log10(max_val + 1))
```

#### Wallet Entropy for Tie-Breaking
```python
def _get_wallet_entropy(self, wallet_id: str) -> float:
    """Deterministic entropy from wallet address"""
    hash_val = int(wallet_id[-8:], 16)
    return (hash_val % 1000) / 10000.0  # 0-0.1 range
```

### Score Composition
```python
final_score = (
    liquidation_risk * 0.35 +
    leverage_risk * 0.25 +
    activity_risk * 0.20 +
    behavioral_risk * 0.20
) + wallet_entropy * 0.05  # ±5% variation

score = min(1000, max(0, int(final_score * 1000)))
```

## 🎯 Risk Score Interpretation

| Score Range | Risk Level | Profile Description |
|-------------|------------|-------------------|
| **0-100** | Very Low | No activity or minimal safe operations |
| **101-300** | Low | Conservative users, safe operations only |
| **301-500** | Medium | Regular users with moderate exposure |
| **501-700** | High | Active traders with significant leverage |
| **701-1000** | Very High | Multiple liquidations, extreme leverage |

### Example Risk Assessment
```
Wallet: 0x0039f22efb07a647557c7c5d17854cfd6d489ef3
Features: liquidations=0, risky_ratio=0.08, max_value=100.00, tx_freq=0.02
Risk scores: liq=0.03, lev=0.41, act=0.36, beh=0.22
Final Score: 231 (Low Risk)

Analysis: 26 transactions, 8% risky functions, $100 max exposure
Profile: Experienced but conservative user
```

## 🔍 Risk Indicators Justification

### Primary Indicators (Critical for DeFi)
1. **Liquidation History**: 
   - Most reliable predictor of future liquidation risk
   - Indicates poor collateral management or excessive leverage
   
2. **Position Size**: 
   - Large transactions indicate significant capital at risk
   - Higher potential impact from market volatility

3. **Function Usage Patterns**:
   - Borrowing vs supplying behavior analysis
   - Risk appetite assessment through operation types

### Secondary Indicators
1. **Trading Frequency**:
   - Bot-like patterns suggest algorithmic trading risks
   - Dormant patterns indicate inexperience

2. **Protocol Experience**:
   - Function diversity shows DeFi sophistication
   - Multi-contract usage indicates advanced understanding

3. **Gas Efficiency**:
   - Operational sophistication indicator
   - Cost-conscious behavior assessment

### Defensive Factors
1. **Safe Operations**: Regular `mint`/`redeem` operations
2. **Consistent Patterns**: Predictable, systematic behavior
3. **Multi-Network Activity**: Cross-chain DeFi experience

## 🏗️ Architecture & Design

### Modular Component Structure
```
core/
├── interfaces.py          # Abstract base classes
infrastructure/
├── data_provider.py       # Multi-chain data fetching
features/
├── extractor.py          # Feature engineering
scoring/
├── risk_scorer.py        # Risk calculation engine
utils/
├── wallet_loader.py      # Input processing
├── csv_exporter.py       # Output formatting
```

### Key Design Benefits
- **Modularity**: Swap components independently
- **Extensibility**: Add new protocols/chains easily
- **Testability**: Independent component validation
- **Scalability**: Efficient batch processing with rate limiting

### Multi-Chain Implementation
```python
# Single API key for all chains
class EtherscanV2DataProvider:
    def __init__(self, api_key: str):
        self.base_url = "https://api.etherscan.io/v2/api"
        self.chain_configs = {
            1: {'name': 'ethereum', 'compound_v2_addresses': {...}},
            137: {'name': 'polygon', 'compound_v3_addresses': {...}},
            # ... additional chains
        }
```
