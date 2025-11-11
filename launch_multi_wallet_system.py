#!/usr/bin/env python3
"""
AurumBotX - Multi-Wallet System Launcher
Avvia e gestisce multiple sessioni di trading parallele
"""

import subprocess
import time
import json
import os
from datetime import datetime

WALLETS = [
    {
        "id": "wallet_100",
        "config": "config/demo_mainnet_100usd.json",
        "capital": 100,
        "script": "ai_autonomous_always_on.py",
        "status": "already_running"  # Già attivo
    },
    {
        "id": "wallet_500",
        "config": "config/wallet_500usd.json",
        "capital": 500,
        "script": "ai_autonomous_always_on.py",
        "status": "to_launch"
    },
    {
        "id": "wallet_1000",
        "config": "config/wallet_1000usd.json",
        "capital": 1000,
        "script": "ai_autonomous_always_on.py",
        "status": "to_launch"
    },
    {
        "id": "wallet_5000",
        "config": "config/wallet_5000usd.json",
        "capital": 5000,
        "script": "ai_autonomous_always_on.py",
        "status": "to_launch"
    }
]

def check_wallet_running(wallet_id):
    """Verifica se un wallet è già in esecuzione"""
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
    return wallet_id in result.stdout

def launch_wallet(wallet):
    """Avvia una sessione wallet"""
    print(f"\n{'='*80}")
    print(f"Avvio Wallet: {wallet['id']}")
    print(f"Capitale: ${wallet['capital']}")
    print(f"Config: {wallet['config']}")
    print(f"{'='*80}")
    
    # Crea script specifico per questo wallet
    script_content = f"""#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/ubuntu/AurumBotX')

# Importa il sistema always-on originale
import ai_autonomous_always_on as base_system

# Override configurazione
base_system.CONFIG_FILE = '{wallet['config']}'
base_system.WALLET_ID = '{wallet['id']}'

# Avvia
if __name__ == '__main__':
    base_system.main()
"""
    
    script_path = f"/home/ubuntu/AurumBotX/wallet_{wallet['id']}_runner.py"
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    os.chmod(script_path, 0o755)
    
    # Avvia in background
    log_file = f"logs/{wallet['id']}_nohup.log"
    subprocess.Popen(
        ['nohup', 'python3', script_path],
        stdout=open(log_file, 'w'),
        stderr=subprocess.STDOUT,
        cwd='/home/ubuntu/AurumBotX'
    )
    
    print(f"✅ Wallet {wallet['id']} avviato!")
    print(f"   Log: {log_file}")
    
    time.sleep(2)

def main():
    print("\n" + "="*80)
    print("AURUMBOTX - MULTI-WALLET SYSTEM LAUNCHER")
    print("="*80)
    print(f"\nData/Ora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    total_capital = sum(w['capital'] for w in WALLETS)
    print(f"\nCapitale Totale: ${total_capital:,.2f}")
    print(f"Wallet da gestire: {len(WALLETS)}")
    
    print("\n" + "-"*80)
    print("STATO WALLET")
    print("-"*80)
    
    for wallet in WALLETS:
        status_icon = "✅" if wallet['status'] == "already_running" else "🔄"
        print(f"{status_icon} {wallet['id']:<15} ${wallet['capital']:>7,.0f}   {wallet['status']}")
    
    print("\n" + "-"*80)
    input("Premi INVIO per avviare i nuovi wallet...")
    
    launched = 0
    for wallet in WALLETS:
        if wallet['status'] == "to_launch":
            if not check_wallet_running(wallet['id']):
                launch_wallet(wallet)
                launched += 1
                time.sleep(3)  # Pausa tra avvii
            else:
                print(f"⚠️  {wallet['id']} già in esecuzione, skip...")
        else:
            print(f"ℹ️  {wallet['id']} già attivo, skip...")
    
    print("\n" + "="*80)
    print(f"✅ SISTEMA MULTI-WALLET AVVIATO")
    print("="*80)
    print(f"\nWallet attivi: {len(WALLETS)}")
    print(f"Wallet appena lanciati: {launched}")
    print(f"Capitale totale: ${total_capital:,.2f}")
    
    print("\nVerifica processi attivi:")
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
    for wallet in WALLETS:
        if wallet['id'] in result.stdout:
            print(f"  ✅ {wallet['id']}")
        else:
            print(f"  ❌ {wallet['id']} - NON TROVATO!")
    
    print("\n" + "="*80)
    print("Per monitorare i wallet usa:")
    print("  python3 monitor_multi_wallet.py")
    print("="*80 + "\n")

if __name__ == '__main__':
    main()

