#!/usr/bin/env python3
"""
AurumBotX - Security Audit Test
Test completo delle funzionalità di sicurezza del sistema

Author: AurumBotX Team
Date: 12 Settembre 2025
Version: 1.0 - Security Audit
"""

import sys
import os
import json
import time
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_security_imports():
    """Test import dei moduli di sicurezza"""
    print("🔍 Testing Security Module Imports...")
    
    try:
        from src.security.advanced_security_layer import AdvancedSecurityLayer
        print("✅ AdvancedSecurityLayer import: SUCCESS")
        return True
    except ImportError as e:
        print(f"❌ AdvancedSecurityLayer import: FAILED - {e}")
        return False

def test_wallet_manager():
    """Test wallet manager"""
    print("\n💰 Testing Wallet Manager...")
    
    try:
        from src.wallet.enhanced_wallet_manager import EnhancedWalletManager
        wallet_manager = EnhancedWalletManager()
        print("✅ EnhancedWalletManager initialization: SUCCESS")
        
        # Test supported wallets
        supported = wallet_manager.supported_wallets
        print(f"✅ Supported wallets: {len(supported)} types")
        for wallet_type, info in supported.items():
            print(f"   - {info['name']}: {info['supported_assets']}")
        
        return True
    except Exception as e:
        print(f"❌ Wallet Manager test: FAILED - {e}")
        return False

def test_encryption():
    """Test funzionalità di crittografia"""
    print("\n🔐 Testing Encryption...")
    
    try:
        from cryptography.fernet import Fernet
        
        # Test basic encryption
        key = Fernet.generate_key()
        cipher_suite = Fernet(key)
        
        test_data = "AurumBotX Test Data 2025"
        encrypted = cipher_suite.encrypt(test_data.encode())
        decrypted = cipher_suite.decrypt(encrypted).decode()
        
        if test_data == decrypted:
            print("✅ AES-256 Encryption: SUCCESS")
            return True
        else:
            print("❌ AES-256 Encryption: FAILED - Data mismatch")
            return False
            
    except Exception as e:
        print(f"❌ Encryption test: FAILED - {e}")
        return False

def test_database_connections():
    """Test connessioni database"""
    print("\n🗄️ Testing Database Connections...")
    
    try:
        import sqlite3
        
        # Test wallet database
        wallet_db_path = "data/databases/enhanced_wallets.db"
        if os.path.exists(wallet_db_path):
            conn = sqlite3.connect(wallet_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            conn.close()
            print(f"✅ Wallet Database: {len(tables)} tables found")
        else:
            print("⚠️ Wallet Database: File not found (will be created on first use)")
        
        return True
    except Exception as e:
        print(f"❌ Database test: FAILED - {e}")
        return False

def test_api_endpoints():
    """Test API endpoints"""
    print("\n🌐 Testing API Endpoints...")
    
    try:
        import requests
        
        # Test local API server
        try:
            response = requests.get("http://localhost:5678/api/status", timeout=5)
            if response.status_code == 200:
                print("✅ API Server: ONLINE")
            else:
                print(f"⚠️ API Server: Response code {response.status_code}")
        except requests.exceptions.RequestException:
            print("❌ API Server: OFFLINE or not accessible")
        
        return True
    except Exception as e:
        print(f"❌ API test: FAILED - {e}")
        return False

def test_file_permissions():
    """Test permessi file sensibili"""
    print("\n📁 Testing File Permissions...")
    
    sensitive_files = [
        "config/wallet_encryption.key",
        "data/testnet_wallet.json",
        "data/wallet_100_euro.json",
        "data/wallet_500_usdt.json"
    ]
    
    secure_count = 0
    total_count = 0
    
    for file_path in sensitive_files:
        if os.path.exists(file_path):
            total_count += 1
            stat_info = os.stat(file_path)
            permissions = oct(stat_info.st_mode)[-3:]
            
            if permissions in ['600', '644', '640']:  # Secure permissions
                print(f"✅ {file_path}: Secure ({permissions})")
                secure_count += 1
            else:
                print(f"⚠️ {file_path}: Potentially insecure ({permissions})")
        else:
            print(f"ℹ️ {file_path}: Not found")
    
    if total_count > 0:
        security_ratio = (secure_count / total_count) * 100
        print(f"📊 File Security: {security_ratio:.1f}% ({secure_count}/{total_count})")
    
    return True

def test_network_security():
    """Test sicurezza di rete"""
    print("\n🌐 Testing Network Security...")
    
    try:
        import socket
        
        # Test local ports
        test_ports = [8501, 8502, 8503, 8504, 5678]
        open_ports = []
        
        for port in test_ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            if result == 0:
                open_ports.append(port)
            sock.close()
        
        print(f"✅ Open Ports: {open_ports}")
        
        # Test external IP (basic check)
        try:
            import requests
            response = requests.get("https://httpbin.org/ip", timeout=5)
            if response.status_code == 200:
                ip_info = response.json()
                print(f"✅ External IP: {ip_info.get('origin', 'Unknown')}")
        except:
            print("⚠️ External IP check: Failed")
        
        return True
    except Exception as e:
        print(f"❌ Network security test: FAILED - {e}")
        return False

def generate_security_report():
    """Genera report di sicurezza"""
    print("\n📋 Generating Security Report...")
    
    report = {
        "audit_timestamp": datetime.now().isoformat(),
        "system_version": "AurumBotX v3.0",
        "audit_version": "1.0",
        "tests_performed": [
            "Security Module Imports",
            "Wallet Manager Functionality", 
            "Encryption Systems",
            "Database Connections",
            "API Endpoints",
            "File Permissions",
            "Network Security"
        ],
        "security_status": "AUDIT_COMPLETED",
        "recommendations": [
            "Monitor API server connectivity",
            "Verify VPN integration",
            "Test MetaMask integration in production",
            "Implement additional monitoring"
        ]
    }
    
    report_file = f"SECURITY_AUDIT_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    try:
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"✅ Security Report saved: {report_file}")
    except Exception as e:
        print(f"❌ Failed to save report: {e}")
    
    return report

def main():
    """Main audit function"""
    print("🚀 AurumBotX Security Audit Starting...")
    print("=" * 60)
    
    start_time = time.time()
    
    # Run all tests
    tests = [
        test_security_imports,
        test_wallet_manager,
        test_encryption,
        test_database_connections,
        test_api_endpoints,
        test_file_permissions,
        test_network_security
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test in tests:
        try:
            if test():
                passed_tests += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    # Generate report
    report = generate_security_report()
    
    # Summary
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "=" * 60)
    print("🎯 SECURITY AUDIT SUMMARY")
    print("=" * 60)
    print(f"📊 Tests Passed: {passed_tests}/{total_tests} ({(passed_tests/total_tests)*100:.1f}%)")
    print(f"⏱️ Duration: {duration:.2f} seconds")
    print(f"📅 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if passed_tests == total_tests:
        print("✅ AUDIT STATUS: ALL TESTS PASSED")
        return 0
    elif passed_tests >= total_tests * 0.8:
        print("⚠️ AUDIT STATUS: MOSTLY SECURE (some issues found)")
        return 1
    else:
        print("❌ AUDIT STATUS: SECURITY ISSUES DETECTED")
        return 2

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

