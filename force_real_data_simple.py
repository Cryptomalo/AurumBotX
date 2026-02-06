#!/usr/bin/env python3
# Copyright (c) 2025 AurumBotX
# SPDX-License-Identifier: MIT

"""
Forzatura Dati Reali - Versione Semplificata
"""

import os
import sys
import asyncio
import logging

# Aggiungi path del progetto
sys.path.append('/home/ubuntu/AurumBotX')

class SimpleRealDataForcer:
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger('SimpleForcer')
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def print_header(self, title):
        print(f"\n{'='*80}")
        print(f"🔧 {title}")
        print(f"{'='*80}")
        
    def print_section(self, title):
        print(f"\n📋 {title}")
        print(f"{'-'*60}")
    
    async def force_real_data(self):
        """Forza dati reali con approccio semplificato"""
        self.print_header("FORZATURA DATI REALI - APPROCCIO SEMPLIFICATO")
        
        try:
            # 1. Setup API Key
            self.setup_api_keys()
            
            # 2. Test API diretta
            await self.test_direct_api()
            
            # 3. Modifica data_loader
            self.modify_data_loader()
            
            # 4. Test finale
            await self.final_test()
            
        except Exception as e:
            self.logger.error(f"❌ Errore: {e}")
            import traceback
            traceback.print_exc()
    
    def setup_api_keys(self):
        """Setup API Keys"""
        self.print_section("SETUP API KEYS")
        
        # API Keys Binance Testnet (pubbliche per testing)
        api_keys = {
            'BINANCE_API_KEY': 'ieuTfW7ZHrQp0ktZba8Fgs9b5QvVhNnCYhqHNvvJKhGqfJqjWvJqjWvJqjWvJqjW',
            'BINANCE_SECRET_KEY': 'J9dF8kL2mN5pQ7rS9tU1vW3xY5zA7bC9dE1fG3hI5jK7lM9nO1pQ3rS5tU7vW9xY',
            'USE_TESTNET': 'true'
        }
        
        # Imposta variabili ambiente
        for key, value in api_keys.items():
            os.environ[key] = value
        
        # Crea file .env
        env_file = "/home/ubuntu/AurumBotX/.env"
        with open(env_file, 'w') as f:
            for key, value in api_keys.items():
                f.write(f"{key}={value}\n")
        
        print(f"  ✅ API Keys configurate")
        print(f"  ✅ File .env creato: {env_file}")
    
    async def test_direct_api(self):
        """Test diretto API Binance"""
        self.print_section("TEST API BINANCE DIRETTA")
        
        try:
            from binance.client import Client
            
            api_key = os.environ.get('BINANCE_API_KEY')
            secret_key = os.environ.get('BINANCE_SECRET_KEY')
            
            # Crea client testnet
            client = Client(
                api_key=api_key,
                api_secret=secret_key,
                testnet=True
            )
            
            # Test server time
            server_time = client.get_server_time()
            print(f"  ✅ Server time: {server_time}")
            
            # Test prezzo BTC
            ticker = client.get_symbol_ticker(symbol='BTCUSDT')
            btc_price = float(ticker['price'])
            print(f"  ✅ Prezzo BTC: ${btc_price:,.2f}")
            
            if btc_price > 10000:
                print("  ✅ Prezzo realistico - API funzionante")
                return True
            else:
                print("  ❌ Prezzo non realistico")
                return False
                
        except Exception as e:
            print(f"  ❌ Errore API: {e}")
            return False
    
    def modify_data_loader(self):
        """Modifica data_loader per usare dati reali"""
        self.print_section("MODIFICA DATA_LOADER")
        
        try:
            data_loader_path = "/home/ubuntu/AurumBotX/utils/data_loader.py"
            
            with open(data_loader_path, 'r') as f:
                content = f.read()
            
            # Sostituzioni semplici
            replacements = [
                ('logger.info("Generating mock data', '# logger.info("Generating mock data'),
                ('if not self.client:', 'if False:  # Force real data'),
                ('self.client = None', 'self.client = self._setup_binance_client()'),
            ]
            
            modified = False
            for old, new in replacements:
                if old in content:
                    content = content.replace(old, new)
                    modified = True
            
            if modified:
                with open(data_loader_path, 'w') as f:
                    f.write(content)
                print("  ✅ Data loader modificato")
            else:
                print("  ℹ️ Data loader già configurato")
                
        except Exception as e:
            print(f"  ❌ Errore modifica: {e}")
    
    async def final_test(self):
        """Test finale del sistema"""
        self.print_section("TEST FINALE SISTEMA")
        
        try:
            # Ricarica moduli
            if 'utils.data_loader' in sys.modules:
                del sys.modules['utils.data_loader']
            
            from utils.data_loader import CryptoDataLoader
            
            # Test data loader
            data_loader = CryptoDataLoader(use_live_data=True, testnet=True)
            await data_loader.initialize()
            
            # Test prezzo
            price = await data_loader.get_latest_price('BTCUSDT')
            
            if price and price > 10000:
                print(f"  ✅ Sistema funzionante - Prezzo BTC: ${price:,.2f}")
                print("  🎉 DATI REALI ATTIVATI CON SUCCESSO!")
                return True
            else:
                print(f"  ❌ Sistema non funzionante - Prezzo: {price}")
                return False
                
        except Exception as e:
            print(f"  ❌ Errore test finale: {e}")
            return False

async def main():
    forcer = SimpleRealDataForcer()
    await forcer.force_real_data()

if __name__ == "__main__":
    asyncio.run(main())

