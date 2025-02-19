from utils.backup_manager import BackupManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    backup_mgr = BackupManager()
    
    # Clean up old backups keeping only the most recent one
    backup_mgr.cleanup_old_backups(max_backups=1)
    
    # Create new backup with current configuration
    config = {
        'version': '1.0',
        'timestamp': '2025-02-19',
        'trading_pair': 'SOL/USDT',
        'initial_balance': 1000,
        'risk_per_trade': 0.02,
        'testnet': True,
    }
    
    backup_mgr.save_trading_config(config, "solanabot_backup")
    logger.info("Backup process completed successfully")

if __name__ == "__main__":
    main()
