#!/usr/bin/env python3
"""
Forzatura Dati Reali e Setup API Binance Testnet
Risolve definitivamente il problema dati mock vs reali
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Optional

from binance.client import Client


PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

logger = logging.getLogger(__name__)


class RealDataForcer:
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger('RealDataForcer')
        self.project_root = PROJECT_ROOT

    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def print_header(self, title):
        """Header professionale"""
        print(f"\n{'='*100}")
        print(f"🔧 {title}")
        print(f"{'='*100}")

    def print_section(self, title):
        """Sezione"""
        print(f"\n📋 {title}")
        print(f"{'-'*80}")

    async def force_real_data_setup(self):
        """Forza setup dati reali e risolve problemi API"""
        self.print_header("FORZATURA DATI REALI E SETUP API BINANCE TESTNET")

        try:
            # 1. Setup API Key Binance Testnet
            self.setup_binance_testnet_api()

            # 2. Eliminazione completa dati mock
            await self.eliminate_mock_data_completely()

            # 3. Forzatura dati reali in tutti i moduli
            await self.force_real_data_all_modules()

            # 4. Test connessione dati reali
            await self.test_real_data_connection()

            # 5. Configurazione fallback intelligente
            await self.setup_intelligent_fallback()

        except Exception as e:
            self.logger.error(f"❌ Errore setup dati reali: {e}")
            raise

    def _required_env(self):
        api_key = os.environ.get('BINANCE_API_KEY')
        secret_key = os.environ.get('BINANCE_SECRET_KEY')
        missing = [
            key for key, value in (
                ('BINANCE_API_KEY', api_key),
                ('BINANCE_SECRET_KEY', secret_key),
            )
            if not value
        ]
        if missing:
            raise RuntimeError(
                f"Variabili ambiente mancanti: {', '.join(missing)}. "
                "Configura le API keys prima di forzare i dati reali."
            )
        return api_key, secret_key

    def setup_binance_testnet_api(self):
        """Setup API Key Binance Testnet"""
        self.print_section("SETUP API KEY BINANCE TESTNET")

        api_key, secret_key = self._required_env()
        use_testnet = os.environ.get('USE_TESTNET', 'true')
        force_real_data = os.environ.get('FORCE_REAL_DATA', 'true')
        write_env_file = os.environ.get('WRITE_ENV_FILE', 'false').lower() == 'true'

        testnet_config = {
            'BINANCE_API_KEY': api_key,
            'BINANCE_SECRET_KEY': secret_key,
            'USE_TESTNET': use_testnet,
            'FORCE_REAL_DATA': force_real_data,
        }

        print("  🔑 Configurazione API Key Binance Testnet...")

        if write_env_file:
            env_file = self.project_root / '.env'
            with open(env_file, 'w') as f:
                for key, value in testnet_config.items():
                    f.write(f"{key}={value}\n")
            print(f"    ✅ File .env creato: {env_file}")

        for key, value in testnet_config.items():
            os.environ[key] = value

        print("    ✅ Variabili ambiente impostate")
        print("  🔍 Verifica configurazione:")
        print(f"    API Key: {os.environ.get('BINANCE_API_KEY', 'NON TROVATA')[:20]}...")
        print(f"    Testnet: {os.environ.get('USE_TESTNET', 'NON IMPOSTATO')}")
        print(f"    Force Real Data: {os.environ.get('FORCE_REAL_DATA', 'NON IMPOSTATO')}")

    async def eliminate_mock_data_completely(self):
        """Elimina completamente la logica dati mock"""
        self.print_section("ELIMINAZIONE COMPLETA DATI MOCK")

        files_to_modify = [
            self.project_root / 'utils' / 'data_loader.py',
            self.project_root / 'utils' / 'ai_trading.py',
        ]

        for file_path in files_to_modify:
            print(f"  🔧 Modifica {file_path.name}...")

            with open(file_path, 'r') as f:
                content = f.read()

            modifications = [
                ('logger.info("Generating mock data', '# logger.info("Generating mock data'),
                ('logger.info(f"Generating mock data', '# logger.info(f"Generating mock data'),
                ('if not self.client:', 'if False:  # Force real data - mock disabled'),
                ('if self.client is None:', 'if False:  # Force real data - mock disabled'),
                ('return mock_data', '# return mock_data  # DISABLED - real data only'),
                ('return self._generate_mock_data', '# return self._generate_mock_data  # DISABLED'),
                ('self.client = None', 'self.client = self._setup_binance_client()'),
            ]

            modified = False
            for old, new in modifications:
                if old in content:
                    content = content.replace(old, new)
                    modified = True

            if modified:
                with open(file_path, 'w') as f:
                    f.write(content)
                print(f"    ✅ {file_path.name} modificato")
            else:
                print(f"    ℹ️ {file_path.name} già configurato")

    async def force_real_data_all_modules(self):
        """Forza dati reali in tutti i moduli"""
        self.print_section("FORZATURA DATI REALI IN TUTTI I MODULI")

        data_loader_path = self.project_root / 'utils' / 'data_loader.py'

        with open(data_loader_path, 'r') as f:
            content = f.read()

        force_real_method = '''
    def _force_real_data_setup(self):
        """Forza setup per dati reali"""
        api_key = os.environ.get('BINANCE_API_KEY')
        secret_key = os.environ.get('BINANCE_SECRET_KEY')

        if not api_key or not secret_key:
            logger.error("❌ API Key non trovate nelle variabili ambiente")
            return False

        testnet = os.environ.get('USE_TESTNET', 'true').lower() == 'true'

        self.client = Client(
            api_key=api_key,
            api_secret=secret_key,
            testnet=testnet
        )

        logger.info(f"✅ Client Binance inizializzato (testnet={testnet})")
        return True

    async def get_real_price_forced(self, symbol: str) -> Optional[float]:
        """Ottiene prezzo reale forzato (no mock)"""
        if not self.client:
            if not self._force_real_data_setup():
                raise Exception("Impossibile inizializzare client reale")

        ticker = self.client.get_symbol_ticker(symbol=symbol)
        price = float(ticker['price'])

        if symbol == 'BTCUSDT' and price < 10000:
            raise Exception(f"Prezzo BTC non realistico: ${price}")

        logger.info(f"✅ Prezzo reale {symbol}: ${price:,.2f}")
        return price
'''

        if "_force_real_data_setup" not in content:
            lines = content.split('\n')
            lines.insert(-1, force_real_method)

            with open(data_loader_path, 'w') as f:
                f.write('\n'.join(lines))

            print("    ✅ Metodi forzatura dati reali aggiunti")
        else:
            print("    ℹ️ Metodi forzatura già presenti")

        with open(data_loader_path, 'r') as f:
            content = f.read()

        if "get_real_price_forced" in content and "async def get_latest_price" in content:
            content = content.replace(
                "async def get_latest_price(self, symbol: str) -> Optional[float]:",
                "async def get_latest_price(self, symbol: str) -> Optional[float]:\n        # FORCE REAL DATA - NO MOCK\n        return await self.get_real_price_forced(symbol)"
            )

            with open(data_loader_path, 'w') as f:
                f.write(content)

            print("    ✅ get_latest_price modificato per forzare dati reali")

    async def test_real_data_connection(self):
        """Testa connessione dati reali"""
        self.print_section("TEST CONNESSIONE DATI REALI")

        print("  🔍 Test diretto API Binance...")

        api_key = os.environ.get('BINANCE_API_KEY')
        secret_key = os.environ.get('BINANCE_SECRET_KEY')

        if not api_key or not secret_key:
            print("    ❌ API Key non configurate")
            return False

        client = Client(
            api_key=api_key,
            api_secret=secret_key,
            testnet=True
        )

        server_time = client.get_server_time()
        print(f"    ✅ Connessione Binance OK - Server time: {server_time}")

        ticker = client.get_symbol_ticker(symbol='BTCUSDT')
        btc_price = float(ticker['price'])

        if btc_price > 10000:
            print(f"    ✅ Prezzo BTC reale: ${btc_price:,.2f}")
        else:
            print(f"    ❌ Prezzo BTC non realistico: ${btc_price}")
            return False

        try:
            account = client.get_account()
            balances = {b['asset']: float(b['free']) for b in account['balances'] if float(b['free']) > 0}

            print("    💰 Saldi account testnet:")
            for asset, balance in balances.items():
                print(f"      {asset}: {balance}")

        except Exception as e:
            print(f"    ⚠️ Impossibile recuperare saldo: {e}")

        print("  🧪 Test data_loader modificato...")

        if 'utils.data_loader' in sys.modules:
            del sys.modules['utils.data_loader']

        from utils.data_loader import CryptoDataLoader

        data_loader = CryptoDataLoader(use_live_data=True, testnet=True)
        await data_loader.initialize()

        price = await data_loader.get_latest_price('BTCUSDT')

        if price and price > 10000:
            print(f"    ✅ Data loader - Prezzo BTC: ${price:,.2f}")
            return True

        print(f"    ❌ Data loader - Prezzo: ${price}")
        return False

    async def setup_intelligent_fallback(self):
        """Setup fallback intelligente per situazioni di emergenza"""
        self.print_section("SETUP FALLBACK INTELLIGENTE")

        fallback_code = '''
    async def get_public_api_price(self, symbol: str) -> Optional[float]:
        """Fallback usando API pubbliche (senza autenticazione)"""
        import aiohttp

        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    price = float(data['price'])

                    logger.info(f"✅ Prezzo pubblico {symbol}: ${price:,.2f}")
                    return price

                logger.error(f"❌ API pubblica fallita: {response.status}")
                return None

    async def get_price_with_intelligent_fallback(self, symbol: str) -> Optional[float]:
        """Ottiene prezzo con fallback intelligente"""
        if self.client:
            try:
                ticker = self.client.get_symbol_ticker(symbol=symbol)
                price = float(ticker['price'])
                if price > 10000:  # Prezzo realistico per BTC
                    return price
            except Exception as e:
                logger.warning(f"Client autenticato fallito: {e}")

        logger.info("Usando fallback API pubblica...")
        price = await self.get_public_api_price(symbol)
        if price and price > 10000:
            return price

        raise Exception("Tutti i metodi di recupero prezzo falliti")
'''

        data_loader_path = self.project_root / 'utils' / 'data_loader.py'

        with open(data_loader_path, 'r') as f:
            content = f.read()

        if "get_public_api_price" not in content:
            lines = content.split('\n')
            lines.insert(-1, fallback_code)

            with open(data_loader_path, 'w') as f:
                f.write('\n'.join(lines))

            print("    ✅ Fallback intelligente implementato")
        else:
            print("    ℹ️ Fallback intelligente già presente")


async def main():
    """Main forzatura dati reali"""
    forcer = RealDataForcer()
    await forcer.force_real_data_setup()


if __name__ == "__main__":
    asyncio.run(main())
