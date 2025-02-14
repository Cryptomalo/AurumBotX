import os
from typing import Dict, Any

# Social Media OAuth Configuration
OAUTH_CONFIG = {
    "telegram": {
        "api_id": os.getenv("TELEGRAM_API_ID"),
        "api_hash": os.getenv("TELEGRAM_API_HASH"),
        "bot_token": os.getenv("TELEGRAM_BOT_TOKEN")
    },
    "reddit": {
        "client_id": os.getenv("REDDIT_CLIENT_ID"),
        "client_secret": os.getenv("REDDIT_CLIENT_SECRET"),
        "redirect_uri": os.getenv("REDDIT_REDIRECT_URI"),
        "user_agent": "AurumBot/1.0"
    },
    "github": {
        "client_id": os.getenv("GITHUB_CLIENT_ID"),
        "client_secret": os.getenv("GITHUB_CLIENT_SECRET"),
        "redirect_uri": os.getenv("GITHUB_REDIRECT_URI")
    }
}

# Supported wallet types and their configurations
WALLET_CONFIG = {
    "ETH": {
        "chain_id": 1,
        "rpc_url": os.getenv("ETH_RPC_URL", "https://mainnet.infura.io/v3/your-project-id")
    },
    "BSC": {
        "chain_id": 56,
        "rpc_url": os.getenv("BSC_RPC_URL", "https://bsc-dataseed.binance.org/")
    },
    "SOLANA": {
        "network": "mainnet-beta",
        "rpc_url": os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
    }
}

def get_provider_config(provider: str) -> Dict[str, Any]:
    """Get configuration for a specific provider"""
    return OAUTH_CONFIG.get(provider, {})

def get_wallet_config(chain_type: str) -> Dict[str, Any]:
    """Get configuration for a specific blockchain"""
    return WALLET_CONFIG.get(chain_type, {})
