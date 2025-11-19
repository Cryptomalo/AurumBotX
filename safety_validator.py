#!/usr/bin/env python3
"""
Safety Validator - Pre-deployment checks for live trading
Verifica tutti i parametri di sicurezza prima di avviare trading live
"""

import json
import os
import sys
from pathlib import Path

class SafetyValidator:
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = None
        self.errors = []
        self.warnings = []
        self.passed = True
        
    def load_config(self):
        """Carica configurazione"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            print(f"✅ Config loaded: {self.config_path}")
            return True
        except Exception as e:
            self.errors.append(f"Failed to load config: {e}")
            return False
    
    def validate_mode(self):
        """Verifica mode = live"""
        mode = self.config.get('mode')
        if mode != 'live':
            self.errors.append(f"Mode must be 'live', found: '{mode}'")
            return False
        print(f"✅ Mode: {mode}")
        return True
    
    def validate_capital(self):
        """Verifica capitale"""
        capital = self.config.get('capital', {})
        initial = capital.get('initial')
        
        if not initial or initial < 10:
            self.errors.append(f"Initial capital too low: ${initial}")
            return False
        
        if initial > 100:
            self.warnings.append(f"Initial capital high for test: ${initial}")
        
        print(f"✅ Capital: ${initial:.2f} USDT")
        return True
    
    def validate_safety_limits(self):
        """Verifica limiti di sicurezza"""
        limits = self.config.get('safety_limits', {})
        
        # Daily loss limit
        daily_loss_pct = limits.get('daily_loss_limit_pct')
        daily_loss_usd = limits.get('daily_loss_limit_usd')
        
        if not daily_loss_pct or daily_loss_pct > 20:
            self.errors.append(f"Daily loss limit too high: {daily_loss_pct}%")
            return False
        
        if not daily_loss_usd:
            self.errors.append("Daily loss limit USD not set")
            return False
        
        print(f"✅ Daily loss limit: {daily_loss_pct}% (${daily_loss_usd})")
        
        # Emergency stop
        emergency_pct = limits.get('emergency_stop_pct')
        emergency_usd = limits.get('emergency_stop_usd')
        
        if not emergency_pct or emergency_pct > 50:
            self.errors.append(f"Emergency stop too high: {emergency_pct}%")
            return False
        
        print(f"✅ Emergency stop: {emergency_pct}% (${emergency_usd})")
        
        # Position size
        max_position_pct = limits.get('max_position_size_pct')
        max_position_usd = limits.get('max_position_size_usd')
        
        if not max_position_pct or max_position_pct > 10:
            self.errors.append(f"Position size too high: {max_position_pct}%")
            return False
        
        print(f"✅ Max position: {max_position_pct}% (${max_position_usd})")
        
        # Consecutive losses
        max_losses = limits.get('consecutive_losses_max')
        if not max_losses or max_losses > 10:
            self.errors.append(f"Consecutive losses limit too high: {max_losses}")
            return False
        
        print(f"✅ Max consecutive losses: {max_losses}")
        
        # Daily trades
        max_daily = limits.get('max_daily_trades')
        if max_daily and max_daily > 20:
            self.warnings.append(f"Daily trades limit high: {max_daily}")
        
        print(f"✅ Max daily trades: {max_daily}")
        
        return True
    
    def validate_risk_management(self):
        """Verifica risk management"""
        risk = self.config.get('risk_management', {})
        
        # Stop loss
        stop_loss = risk.get('stop_loss_pct')
        if not stop_loss or stop_loss > 5:
            self.errors.append(f"Stop loss too wide: {stop_loss}%")
            return False
        
        print(f"✅ Stop loss: {stop_loss}%")
        
        # Take profit
        take_profit = risk.get('take_profit_pct')
        if not take_profit or take_profit < stop_loss * 2:
            self.warnings.append(f"Take profit/stop loss ratio < 2:1")
        
        print(f"✅ Take profit: {take_profit}%")
        
        # Trailing stop
        trailing = risk.get('trailing_stop_enabled')
        print(f"✅ Trailing stop: {trailing}")
        
        return True
    
    def validate_api_settings(self):
        """Verifica API settings"""
        # Check .env file
        env_path = Path(__file__).parent / '.env'
        if not env_path.exists():
            self.errors.append(".env file not found")
            return False
        
        print(f"✅ .env file found")
        
        # Check required env vars
        required_vars = ['MEXC_API_KEY', 'MEXC_API_SECRET']
        missing = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing.append(var)
        
        if missing:
            self.errors.append(f"Missing env vars: {', '.join(missing)}")
            return False
        
        print(f"✅ API keys configured")
        return True
    
    def validate_confirmation_settings(self):
        """Verifica confirmation settings"""
        confirm = self.config.get('confirmation_required', {})
        
        first_3 = confirm.get('first_3_trades')
        if not first_3:
            self.warnings.append("First 3 trades confirmation disabled")
        else:
            print(f"✅ First 3 trades require confirmation")
        
        emergency = confirm.get('emergency_actions')
        if not emergency:
            self.errors.append("Emergency actions confirmation must be enabled")
            return False
        
        print(f"✅ Emergency actions require confirmation")
        return True
    
    def validate_directories(self):
        """Verifica directories"""
        state_file = self.config.get('state_file')
        if state_file:
            state_dir = Path(state_file).parent
            if not state_dir.exists():
                try:
                    state_dir.mkdir(parents=True, exist_ok=True)
                    print(f"✅ Created directory: {state_dir}")
                except Exception as e:
                    self.errors.append(f"Failed to create directory: {e}")
                    return False
        
        log_file = self.config.get('logging', {}).get('file')
        if log_file:
            log_dir = Path(log_file).parent
            if not log_dir.exists():
                try:
                    log_dir.mkdir(parents=True, exist_ok=True)
                    print(f"✅ Created directory: {log_dir}")
                except Exception as e:
                    self.errors.append(f"Failed to create directory: {e}")
                    return False
        
        return True
    
    def calculate_risk_metrics(self):
        """Calcola metriche di rischio"""
        capital = self.config['capital']['initial']
        limits = self.config['safety_limits']
        
        max_daily_loss = limits['daily_loss_limit_usd']
        max_total_loss = limits['emergency_stop_usd']
        max_position = limits['max_position_size_usd']
        
        print(f"\n📊 Risk Metrics:")
        print(f"  Capital: ${capital:.2f}")
        print(f"  Max daily loss: ${max_daily_loss:.2f} ({max_daily_loss/capital*100:.1f}%)")
        print(f"  Max total loss: ${max_total_loss:.2f} ({max_total_loss/capital*100:.1f}%)")
        print(f"  Max position: ${max_position:.2f} ({max_position/capital*100:.1f}%)")
        print(f"  Max positions: {limits['max_open_positions']}")
        print(f"  Max capital at risk: ${max_position * limits['max_open_positions']:.2f}")
        
        # Risk warnings
        total_risk = max_position * limits['max_open_positions']
        if total_risk > capital:
            self.warnings.append(f"Total risk (${total_risk:.2f}) > capital (${capital:.2f})")
        
        return True
    
    def run_all_checks(self):
        """Esegui tutti i check"""
        print("=" * 60)
        print("🔒 SAFETY VALIDATOR - Pre-deployment Checks")
        print("=" * 60)
        print()
        
        checks = [
            ("Loading config", self.load_config),
            ("Validating mode", self.validate_mode),
            ("Validating capital", self.validate_capital),
            ("Validating safety limits", self.validate_safety_limits),
            ("Validating risk management", self.validate_risk_management),
            ("Validating API settings", self.validate_api_settings),
            ("Validating confirmation settings", self.validate_confirmation_settings),
            ("Validating directories", self.validate_directories),
            ("Calculating risk metrics", self.calculate_risk_metrics),
        ]
        
        for name, check_func in checks:
            print(f"\n{name}...")
            try:
                if not check_func():
                    self.passed = False
            except Exception as e:
                self.errors.append(f"{name} failed: {e}")
                self.passed = False
        
        # Summary
        print("\n" + "=" * 60)
        print("📋 VALIDATION SUMMARY")
        print("=" * 60)
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if self.passed and not self.errors:
            print(f"\n✅ ALL CHECKS PASSED!")
            print(f"\n🚀 System is READY for live trading")
            print(f"   Config: {self.config_path}")
            print(f"   Capital: ${self.config['capital']['initial']:.2f}")
            print(f"   Exchange: {self.config['exchange'].upper()}")
            print(f"\n⚠️  IMPORTANT:")
            print(f"   - First 3 trades require manual confirmation")
            print(f"   - Monitor closely for first 24 hours")
            print(f"   - Emergency stop at -30% (${self.config['safety_limits']['emergency_stop_usd']})")
            return 0
        else:
            print(f"\n❌ VALIDATION FAILED!")
            print(f"   Fix errors before proceeding to live trading")
            return 1

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 safety_validator.py <config_file>")
        print("Example: python3 safety_validator.py config/live_mexc_50_v3.json")
        sys.exit(1)
    
    config_path = sys.argv[1]
    
    validator = SafetyValidator(config_path)
    exit_code = validator.run_all_checks()
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
