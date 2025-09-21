#!/usr/bin/env python3
"""
AurumBotX - Test Binance Connection
Script per testare la connessione API Binance prima del trading reale

Author: AurumBotX Team
Date: 12 Settembre 2025
Version: 1.0
"""

import os
import sys
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def load_env_file():
    """Load environment variables from .env file"""
    env_file = os.path.join(project_root, '.env')
    
    if not os.path.exists(env_file):
        print("❌ File .env non trovato!")
        print("💡 Crea il file .env con le tue API key Binance")
        return None, None
    
    api_key = None
    secret_key = None
    
    try:
        with open(env_file, 'r') as f:
            for line in f:
                if line.startswith('BINANCE_API_KEY='):
                    api_key = line.split('=', 1)[1].strip()
                elif line.startswith('BINANCE_SECRET_KEY='):
                    secret_key = line.split('=', 1)[1].strip()
        
        return api_key, secret_key
    except Exception as e:
        print(f"❌ Errore lettura .env: {e}")
        return None, None

def test_binance_connection():
    """Test Binance API connection"""
    print("🔍 Testing Binance API Connection...")
    print("=" * 50)
    
    # Load credentials
    api_key, secret_key = load_env_file()
    
    if not api_key or not secret_key:
        print("❌ API credentials non trovate nel file .env")
        print("\n📋 Esempio file .env:")
        print("BINANCE_API_KEY=your_api_key_here")
        print("BINANCE_SECRET_KEY=your_secret_key_here")
        print("BINANCE_TESTNET=false")
        return False
    
    print(f"✅ API Key trovata: {api_key[:8]}...")
    print(f"✅ Secret Key trovata: {secret_key[:8]}...")
    
    try:
        # Import Binance adapter
        from src.exchanges.binance_adapter import BinanceAdapter
        
        # Initialize adapter
        adapter = BinanceAdapter(api_key, secret_key)
        print("✅ BinanceAdapter inizializzato")
        
        # Test connection
        print("\n🌐 Testing API Connection...")
        
        # Test account info
        try:
            account_info = adapter.get_account_info()
            if account_info:
                print("✅ Connessione API: SUCCESS")
                print(f"✅ Account Type: {account_info.get('accountType', 'Unknown')}")
                print(f"✅ Can Trade: {account_info.get('canTrade', False)}")
            else:
                print("❌ Connessione API: FAILED")
                return False
        except Exception as e:
            print(f"❌ Errore connessione API: {e}")
            return False
        
        # Test balance
        print("\n💰 Testing Balance Retrieval...")
        try:
            balance = adapter.get_balance()
            if balance:
                print("✅ Balance retrieval: SUCCESS")
                usdt_balance = balance.get('USDT', 0)
                print(f"✅ USDT Balance: {usdt_balance}")
                
                if usdt_balance >= 30:
                    print("✅ Capitale sufficiente per trading (≥30 USDT)")
                else:
                    print("⚠️ Capitale insufficiente per trading (<30 USDT)")
                    print("💡 Deposita almeno 30 USDT per iniziare")
            else:
                print("❌ Balance retrieval: FAILED")
                return False
        except Exception as e:
            print(f"❌ Errore balance: {e}")
            return False
        
        # Test market data
        print("\n📊 Testing Market Data...")
        try:
            btc_price = adapter.get_current_price('BTCUSDT')
            if btc_price:
                print("✅ Market data: SUCCESS")
                print(f"✅ BTC/USDT Price: ${btc_price}")
            else:
                print("❌ Market data: FAILED")
                return False
        except Exception as e:
            print(f"❌ Errore market data: {e}")
            return False
        
        print("\n" + "=" * 50)
        print("🎉 BINANCE CONNECTION TEST: SUCCESS")
        print("✅ Sistema pronto per trading reale!")
        return True
        
    except ImportError as e:
        print(f"❌ Errore import BinanceAdapter: {e}")
        return False
    except Exception as e:
        print(f"❌ Errore generale: {e}")
        return False

def main():
    """Main function"""
    print("🚀 AurumBotX - Binance Connection Test")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    success = test_binance_connection()
    
    if success:
        print("\n🎯 NEXT STEPS:")
        print("1. Avvia il trading: python scripts/start_100_euro_challenge.py")
        print("2. Monitora dashboard: http://localhost:8501")
        print("3. Controlla primi trades")
        return 0
    else:
        print("\n🔧 TROUBLESHOOTING:")
        print("1. Verifica API key nel file .env")
        print("2. Controlla permessi API su Binance")
        print("3. Assicurati di avere USDT nel wallet")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

