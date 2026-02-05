from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class WalletProfile:
    name: str
    wallet_type: str
    supports_testnet: bool
    supports_mainnet: bool
    description: str


class EnhancedWalletManager:
    def __init__(self):
        self.supported_wallets: Dict[str, Dict] = {
            "binance": {
                "name": "Binance Spot Wallet",
                "wallet_type": "exchange",
                "testnet_only": False,
                "description": "Primary exchange wallet for spot trading.",
            },
            "bybit": {
                "name": "Bybit Unified Wallet",
                "wallet_type": "exchange",
                "testnet_only": False,
                "description": "Unified account wallet for derivatives and spot.",
            },
            "okx": {
                "name": "OKX Trading Wallet",
                "wallet_type": "exchange",
                "testnet_only": False,
                "description": "OKX wallet supporting spot and derivatives.",
            },
            "metamask": {
                "name": "MetaMask",
                "wallet_type": "self_custody",
                "testnet_only": False,
                "description": "Self-custody wallet for EVM networks.",
            },
            "trust_wallet": {
                "name": "Trust Wallet",
                "wallet_type": "self_custody",
                "testnet_only": False,
                "description": "Mobile self-custody wallet for multi-chain assets.",
            },
            "demo_testnet": {
                "name": "Demo Testnet Wallet",
                "wallet_type": "testnet",
                "testnet_only": True,
                "description": "Simulated wallet for dry-run/testing.",
            },
        }

    def list_supported_wallets(self) -> List[WalletProfile]:
        return [
            WalletProfile(
                name=wallet["name"],
                wallet_type=wallet["wallet_type"],
                supports_testnet=wallet.get("testnet_only", False),
                supports_mainnet=not wallet.get("testnet_only", False),
                description=wallet["description"],
            )
            for wallet in self.supported_wallets.values()
        ]

    def get_wallet(self, key: str) -> Optional[Dict]:
        return self.supported_wallets.get(key)

    def is_supported(self, key: str) -> bool:
        return key in self.supported_wallets

    def add_wallet(
        self,
        key: str,
        name: str,
        wallet_type: str,
        description: str,
        testnet_only: bool = False,
    ) -> None:
        self.supported_wallets[key] = {
            "name": name,
            "wallet_type": wallet_type,
            "testnet_only": testnet_only,
            "description": description,
        }

    def remove_wallet(self, key: str) -> None:
        if key in self.supported_wallets:
            del self.supported_wallets[key]
