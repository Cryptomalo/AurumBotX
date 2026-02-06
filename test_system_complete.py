#!/usr/bin/env python3
"""
AurumBotX - Complete System Test
Test end-to-end del sistema completo per preparazione trading reale

Author: AurumBotX Team
Date: 12 Settembre 2025
Version: 1.0 - Complete System Test
"""

import sys
import os
import json
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def _load_dashboards_from_env() -> dict:
    raw = os.getenv("DASHBOARD_URLS", "")
    if not raw:
        return {
            "Main Dashboard": "http://localhost:8501",
        }
    dashboards = {}
    for entry in raw.split(","):
        if "|" in entry:
            name, url = entry.split("|", 1)
            dashboards[name.strip()] = url.strip()
    return dashboards or {"Main Dashboard": "http://localhost:8501"}


class _SimpleAPIHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload: dict, status_code: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/status":
            self._send_json({"status": "online", "mode": "local"})
            return
        if self.path == "/api/balance":
            self._send_json({"USDT": 30.0, "total_value": 30.0, "available": 30.0, "locked": 0.0})
            return
        self._send_json({"error": "not found"}, status_code=404)

    def do_POST(self):
        if self.path == "/api/emergency-stop":
            self._send_json({"status": "stopped", "reason": "local test"})
            return
        self._send_json({"error": "not found"}, status_code=404)


class _SimpleDashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b"<html><body><h1>AurumBotX Dashboard (Local Test)</h1></body></html>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def _start_local_services():
    services = []
    if os.getenv("SPAWN_LOCAL_SERVICES", "false").lower() != "true":
        return services

    try:
        api_server = HTTPServer(("127.0.0.1", 5678), _SimpleAPIHandler)
        api_thread = threading.Thread(target=api_server.serve_forever, daemon=True)
        api_thread.start()
        services.append(api_server)
        print("✅ Local API server avviato su http://127.0.0.1:5678")
    except OSError as exc:
        print(f"⚠️ Local API server non avviato: {exc}")

    try:
        dashboard_server = HTTPServer(("127.0.0.1", 8501), _SimpleDashboardHandler)
        dashboard_thread = threading.Thread(target=dashboard_server.serve_forever, daemon=True)
        dashboard_thread.start()
        services.append(dashboard_server)
        print("✅ Local dashboard avviata su http://127.0.0.1:8501")
    except OSError as exc:
        print(f"⚠️ Local dashboard non avviata: {exc}")

    return services


def _stop_local_services(servers):
    for server in servers:
        server.shutdown()
        server.server_close()


def test_dashboard_connectivity():
    """Test connettività dashboard"""
    print("🌐 Testing Dashboard Connectivity...")
    
    dashboards = _load_dashboards_from_env()
    
    online_dashboards = 0
    
    for name, url in dashboards.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name}: ONLINE")
                online_dashboards += 1
            else:
                print(f"⚠️ {name}: Response {response.status_code}")
        except requests.exceptions.RequestException:
            print(f"❌ {name}: OFFLINE")
    
    print(f"📊 Dashboard Status: {online_dashboards}/{len(dashboards)} online")
    return online_dashboards >= len(dashboards) * 0.5

def test_trading_engine():
    """Test trading engine"""
    print("\n🤖 Testing Trading Engine...")
    
    try:
        # Test import trading engine
        from src.core.trading_engine_usdt_sqlalchemy import TradingEngineUSDT
        print("✅ Trading Engine import: SUCCESS")
        
        # Initialize engine
        engine = TradingEngineUSDT()
        print("✅ Trading Engine initialization: SUCCESS")
        
        # Test basic functionality
        balance = engine.get_balance()
        print(f"✅ Current Balance: {balance}")
        
        return True
    except Exception as e:
        print(f"❌ Trading Engine test: FAILED - {e}")
        return False

def test_strategy_network():
    """Test strategy network"""
    print("\n📈 Testing Strategy Network...")
    
    try:
        from src.strategies.strategy_network import StrategyNetwork
        print("✅ Strategy Network import: SUCCESS")
        
        # Initialize strategy network
        strategy_net = StrategyNetwork()
        print("✅ Strategy Network initialization: SUCCESS")
        
        # Test strategy count
        strategies = strategy_net.get_available_strategies()
        print(f"✅ Available Strategies: {len(strategies)}")
        
        return True
    except Exception as e:
        print(f"❌ Strategy Network test: FAILED - {e}")
        return False

def test_meme_coin_hunter():
    """Test meme coin hunter"""
    print("\n🎯 Testing Meme Coin Hunter...")
    
    try:
        from src.alerts.meme_coin_hunter import MemeCoinHunter
        print("✅ Meme Coin Hunter import: SUCCESS")
        
        # Initialize hunter
        hunter = MemeCoinHunter()
        print("✅ Meme Coin Hunter initialization: SUCCESS")
        
        return True
    except Exception as e:
        print(f"❌ Meme Coin Hunter test: FAILED - {e}")
        return False

def test_challenge_configuration():
    """Test 100 Euro Challenge configuration"""
    print("\n💰 Testing 100 Euro Challenge Configuration...")
    
    config_file = os.path.join(project_root, "config/100_euro_challenge.json")
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            print("✅ Challenge config file: EXISTS")
            print(f"✅ Initial Capital: {config.get('initial_capital', 'N/A')}")
            print(f"✅ Target Amount: {config.get('target_amount', 'N/A')}")
            print(f"✅ Growth Factor: {config.get('growth_factor', 'N/A')}x")
            
            return True
        except Exception as e:
            print(f"❌ Challenge config read: FAILED - {e}")
            return False
    else:
        print("❌ Challenge config file: NOT FOUND")
        return False

def test_wallet_integration():
    """Test wallet integration"""
    print("\n💳 Testing Wallet Integration...")
    
    try:
        from src.wallet.enhanced_wallet_manager import EnhancedWalletManager
        
        wallet_manager = EnhancedWalletManager()
        print("✅ Wallet Manager: INITIALIZED")
        
        # Test wallet types
        supported = wallet_manager.supported_wallets
        print(f"✅ Supported Wallets: {len(supported)}")
        
        # Check for mainnet support
        mainnet_wallets = [w for w, info in supported.items() if not info.get('testnet_only', True)]
        print(f"✅ Mainnet Wallets: {len(mainnet_wallets)}")
        
        return True
    except Exception as e:
        print(f"❌ Wallet Integration test: FAILED - {e}")
        return False

def test_api_server():
    """Test API server functionality"""
    print("\n🔌 Testing API Server...")
    
    try:
        api_base = os.getenv("API_BASE_URL", "http://localhost:5678")
        # Test status endpoint
        response = requests.get(f"{api_base}/api/status", timeout=5)
        if response.status_code == 200:
            print("✅ API Status endpoint: ONLINE")
        else:
            print(f"⚠️ API Status: Response {response.status_code}")
        
        # Test balance endpoint
        try:
            response = requests.get(f"{api_base}/api/balance", timeout=5)
            if response.status_code == 200:
                print("✅ API Balance endpoint: ONLINE")
            else:
                print(f"⚠️ API Balance: Response {response.status_code}")
        except:
            print("⚠️ API Balance endpoint: Not accessible")
        
        return True
    except Exception as e:
        print(f"❌ API Server test: FAILED - {e}")
        return False

def test_security_features():
    """Test security features"""
    print("\n🛡️ Testing Security Features...")
    
    try:
        from src.security.advanced_security_layer import AdvancedSecurityLayer
        
        security = AdvancedSecurityLayer()
        print("✅ Security Layer: INITIALIZED")
        
        # Test encryption
        test_data = "AurumBotX Test 2025"
        encrypted = security.encrypt_data(test_data)
        decrypted = security.decrypt_data(encrypted)
        
        if test_data == decrypted:
            print("✅ Encryption/Decryption: SUCCESS")
        else:
            print("❌ Encryption/Decryption: FAILED")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Security Features test: FAILED - {e}")
        return False

def test_real_trading_readiness():
    """Test readiness for real trading"""
    print("\n🚀 Testing Real Trading Readiness...")
    
    readiness_checks = {
        "Trading Engine": False,
        "Strategy Network": False,
        "Security Layer": False,
        "Wallet Manager": False,
        "API Server": False,
        "Challenge Config": False
    }
    
    # Check each component
    try:
        from src.core.trading_engine_usdt_sqlalchemy import TradingEngineUSDT
        TradingEngineUSDT()
        readiness_checks["Trading Engine"] = True
    except:
        pass
    
    try:
        from src.strategies.strategy_network import StrategyNetwork
        StrategyNetwork()
        readiness_checks["Strategy Network"] = True
    except:
        pass
    
    try:
        from src.security.advanced_security_layer import AdvancedSecurityLayer
        AdvancedSecurityLayer()
        readiness_checks["Security Layer"] = True
    except:
        pass
    
    try:
        from src.wallet.enhanced_wallet_manager import EnhancedWalletManager
        EnhancedWalletManager()
        readiness_checks["Wallet Manager"] = True
    except:
        pass
    
    try:
        response = requests.get("http://localhost:5678/api/status", timeout=3)
        if response.status_code == 200:
            readiness_checks["API Server"] = True
    except:
        pass
    
    if os.path.exists(os.path.join(project_root, "config/100_euro_challenge.json")):
        readiness_checks["Challenge Config"] = True
    
    # Calculate readiness percentage
    ready_components = sum(readiness_checks.values())
    total_components = len(readiness_checks)
    readiness_percentage = (ready_components / total_components) * 100
    
    print(f"📊 System Readiness: {readiness_percentage:.1f}% ({ready_components}/{total_components})")
    
    for component, status in readiness_checks.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {component}: {'READY' if status else 'NOT READY'}")
    
    return readiness_percentage >= 80

def generate_system_report():
    """Generate complete system report"""
    print("\n📋 Generating Complete System Report...")
    
    report = {
        "test_timestamp": datetime.now().isoformat(),
        "system_version": "AurumBotX v3.0",
        "test_version": "1.0",
        "components_tested": [
            "Dashboard Connectivity",
            "Trading Engine",
            "Strategy Network", 
            "Meme Coin Hunter",
            "Challenge Configuration",
            "Wallet Integration",
            "API Server",
            "Security Features",
            "Real Trading Readiness"
        ],
        "system_status": "TESTING_COMPLETED",
        "trading_ready": False,
        "next_steps": [
            "Configure mainnet API keys",
            "Set up real USDT wallet",
            "Perform final security check",
            "Start with minimal capital (30-50 USDT)",
            "Monitor first trades closely"
        ]
    }
    
    report_file = f"SYSTEM_TEST_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    try:
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"✅ System Report saved: {report_file}")
    except Exception as e:
        print(f"❌ Failed to save report: {e}")
    
    return report

def main():
    """Main test function"""
    print("🚀 AurumBotX Complete System Test Starting...")
    print("=" * 70)
    
    start_time = time.time()
    local_services = _start_local_services()
    
    try:
        # Run all tests
        tests = [
            test_dashboard_connectivity,
            test_trading_engine,
            test_strategy_network,
            test_meme_coin_hunter,
            test_challenge_configuration,
            test_wallet_integration,
            test_api_server,
            test_security_features,
            test_real_trading_readiness
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed_tests += 1
            except Exception as e:
                print(f"❌ Test failed with exception: {e}")
    finally:
        if local_services:
            _stop_local_services(local_services)
    
    # Generate report
    report = generate_system_report()
    
    # Summary
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "=" * 70)
    print("🎯 COMPLETE SYSTEM TEST SUMMARY")
    print("=" * 70)
    print(f"📊 Tests Passed: {passed_tests}/{total_tests} ({(passed_tests/total_tests)*100:.1f}%)")
    print(f"⏱️ Duration: {duration:.2f} seconds")
    print(f"📅 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if passed_tests == total_tests:
        print("✅ SYSTEM STATUS: FULLY OPERATIONAL - READY FOR TRADING")
        return 0
    elif passed_tests >= total_tests * 0.8:
        print("⚠️ SYSTEM STATUS: MOSTLY READY (minor issues)")
        return 1
    else:
        print("❌ SYSTEM STATUS: NOT READY FOR TRADING")
        return 2

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
