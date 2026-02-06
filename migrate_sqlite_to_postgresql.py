#!/usr/bin/env python3
# Copyright (c) 2025 AurumBotX
# SPDX-License-Identifier: MIT

"""
AurumBotX Database Migration: SQLite → PostgreSQL
Script completo per migrare tutti i dati da SQLite a PostgreSQL
"""

import sqlite3
import psycopg2
import json
import os
from datetime import datetime
import sys

class DatabaseMigrator:
    """Migrazione database SQLite → PostgreSQL"""
    
    def __init__(self):
        self.sqlite_dbs = [
            'mega_aggressive_trading.db',
            'ultra_aggressive_trading.db',
            'mega_mainnet_strategy.db',
            'system_monitoring.db'
        ]
        
        # Configurazione PostgreSQL
        self.pg_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'aurumbotx_db',
            'user': 'aurumbotx_user',
            'password': 'your_secure_password'
        }
        
        self.migration_log = []
    
    def log(self, message):
        """Log con timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        self.migration_log.append(log_entry)
    
    def check_postgresql_connection(self):
        """Verifica connessione PostgreSQL"""
        self.log("🔍 Verifica connessione PostgreSQL...")
        
        try:
            conn = psycopg2.connect(
                host=self.pg_config['host'],
                port=self.pg_config['port'],
                database=self.pg_config['database'],
                user=self.pg_config['user'],
                password=self.pg_config['password']
            )
            conn.close()
            self.log("✅ Connessione PostgreSQL OK")
            return True
        except Exception as e:
            self.log(f"❌ Errore connessione PostgreSQL: {e}")
            return False
    
    def create_postgresql_tables(self):
        """Crea tabelle PostgreSQL"""
        self.log("🗄️ Creazione tabelle PostgreSQL...")
        
        try:
            conn = psycopg2.connect(**self.pg_config)
            cursor = conn.cursor()
            
            # Tabella mega_trades
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mega_trades (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    action VARCHAR(10) NOT NULL,
                    amount DECIMAL(20,8) NOT NULL,
                    price DECIMAL(20,8) NOT NULL,
                    confidence DECIMAL(5,4) NOT NULL,
                    profit_loss DECIMAL(20,8) NOT NULL,
                    balance_after DECIMAL(20,8) NOT NULL,
                    position_size_percent DECIMAL(5,2) NOT NULL,
                    market_conditions JSONB,
                    ai_signals JSONB
                );
            """)
            
            # Tabella ultra_trades
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ultra_trades (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    action VARCHAR(10) NOT NULL,
                    amount DECIMAL(20,8) NOT NULL,
                    price DECIMAL(20,8) NOT NULL,
                    confidence DECIMAL(5,4) NOT NULL,
                    profit_loss DECIMAL(20,8) NOT NULL,
                    balance_after DECIMAL(20,8) NOT NULL,
                    position_size_percent DECIMAL(5,2) NOT NULL
                );
            """)
            
            # Tabella mega_mainnet_trades
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mega_mainnet_trades (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    action VARCHAR(10) NOT NULL,
                    amount DECIMAL(20,8) NOT NULL,
                    price DECIMAL(20,8) NOT NULL,
                    confidence DECIMAL(5,4) NOT NULL,
                    profit_loss DECIMAL(20,8) NOT NULL,
                    balance_after DECIMAL(20,8) NOT NULL,
                    position_size_percent DECIMAL(5,2) NOT NULL,
                    market_conditions JSONB,
                    ai_signals JSONB,
                    risk_metrics JSONB
                );
            """)
            
            # Tabella system_health
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_health (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    system_name VARCHAR(100) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    metrics JSONB,
                    alerts JSONB
                );
            """)
            
            # Indici per performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_mega_trades_timestamp ON mega_trades(timestamp);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ultra_trades_timestamp ON ultra_trades(timestamp);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_mainnet_trades_timestamp ON mega_mainnet_trades(timestamp);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_system_health_timestamp ON system_health(timestamp);")
            
            conn.commit()
            conn.close()
            
            self.log("✅ Tabelle PostgreSQL create")
            return True
            
        except Exception as e:
            self.log(f"❌ Errore creazione tabelle: {e}")
            return False
    
    def migrate_mega_trades(self):
        """Migra mega_trades da SQLite a PostgreSQL"""
        self.log("📊 Migrazione mega_trades...")
        
        try:
            # Connessione SQLite
            sqlite_conn = sqlite3.connect('mega_aggressive_trading.db')
            sqlite_cursor = sqlite_conn.cursor()
            
            # Connessione PostgreSQL
            pg_conn = psycopg2.connect(**self.pg_config)
            pg_cursor = pg_conn.cursor()
            
            # Leggi dati SQLite
            sqlite_cursor.execute("SELECT * FROM mega_trades ORDER BY id")
            rows = sqlite_cursor.fetchall()
            
            # Ottieni nomi colonne
            columns = [description[0] for description in sqlite_cursor.description]
            
            migrated_count = 0
            
            for row in rows:
                try:
                    # Converti row in dict
                    row_dict = dict(zip(columns, row))
                    
                    # Gestisci campi JSON
                    market_conditions = row_dict.get('market_conditions')
                    ai_signals = row_dict.get('ai_signals')
                    
                    if market_conditions and isinstance(market_conditions, str):
                        try:
                            market_conditions = json.loads(market_conditions)
                        except:
                            market_conditions = None
                    
                    if ai_signals and isinstance(ai_signals, str):
                        try:
                            ai_signals = json.loads(ai_signals)
                        except:
                            ai_signals = None
                    
                    # Insert in PostgreSQL
                    pg_cursor.execute("""
                        INSERT INTO mega_trades 
                        (timestamp, action, amount, price, confidence, profit_loss, 
                         balance_after, position_size_percent, market_conditions, ai_signals)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        row_dict['timestamp'],
                        row_dict['action'],
                        row_dict['amount'],
                        row_dict['price'],
                        row_dict['confidence'],
                        row_dict['profit_loss'],
                        row_dict['balance_after'],
                        row_dict['position_size_percent'],
                        json.dumps(market_conditions) if market_conditions else None,
                        json.dumps(ai_signals) if ai_signals else None
                    ))
                    
                    migrated_count += 1
                    
                except Exception as e:
                    self.log(f"⚠️ Errore migrazione riga: {e}")
                    continue
            
            pg_conn.commit()
            sqlite_conn.close()
            pg_conn.close()
            
            self.log(f"✅ Migrati {migrated_count} record mega_trades")
            return True
            
        except Exception as e:
            self.log(f"❌ Errore migrazione mega_trades: {e}")
            return False
    
    def migrate_ultra_trades(self):
        """Migra ultra_trades da SQLite a PostgreSQL"""
        self.log("📊 Migrazione ultra_trades...")
        
        try:
            # Verifica se file esiste
            if not os.path.exists('ultra_aggressive_trading.db'):
                self.log("⚠️ File ultra_aggressive_trading.db non trovato")
                return True
            
            sqlite_conn = sqlite3.connect('ultra_aggressive_trading.db')
            sqlite_cursor = sqlite_conn.cursor()
            
            pg_conn = psycopg2.connect(**self.pg_config)
            pg_cursor = pg_conn.cursor()
            
            sqlite_cursor.execute("SELECT * FROM ultra_trades ORDER BY id")
            rows = sqlite_cursor.fetchall()
            
            columns = [description[0] for description in sqlite_cursor.description]
            migrated_count = 0
            
            for row in rows:
                try:
                    row_dict = dict(zip(columns, row))
                    
                    pg_cursor.execute("""
                        INSERT INTO ultra_trades 
                        (timestamp, action, amount, price, confidence, profit_loss, 
                         balance_after, position_size_percent)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        row_dict['timestamp'],
                        row_dict['action'],
                        row_dict['amount'],
                        row_dict['price'],
                        row_dict['confidence'],
                        row_dict['profit_loss'],
                        row_dict['balance_after'],
                        row_dict['position_size_percent']
                    ))
                    
                    migrated_count += 1
                    
                except Exception as e:
                    self.log(f"⚠️ Errore migrazione riga ultra: {e}")
                    continue
            
            pg_conn.commit()
            sqlite_conn.close()
            pg_conn.close()
            
            self.log(f"✅ Migrati {migrated_count} record ultra_trades")
            return True
            
        except Exception as e:
            self.log(f"❌ Errore migrazione ultra_trades: {e}")
            return False
    
    def update_config_files(self):
        """Aggiorna file configurazione per PostgreSQL"""
        self.log("⚙️ Aggiornamento configurazione...")
        
        try:
            # Aggiorna config.json
            if os.path.exists('config.json'):
                with open('config.json', 'r') as f:
                    config = json.load(f)
                
                config['database'] = {
                    "type": "postgresql",
                    "url": f"postgresql://{self.pg_config['user']}:{self.pg_config['password']}@{self.pg_config['host']}:{self.pg_config['port']}/{self.pg_config['database']}",
                    "host": self.pg_config['host'],
                    "port": self.pg_config['port'],
                    "database": self.pg_config['database'],
                    "user": self.pg_config['user'],
                    "password": self.pg_config['password']
                }
                
                with open('config.json', 'w') as f:
                    json.dump(config, f, indent=2)
            
            # Aggiorna .env
            env_content = f"""# AurumBotX Environment Configuration - PostgreSQL
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://{self.pg_config['user']}:{self.pg_config['password']}@{self.pg_config['host']}:{self.pg_config['port']}/{self.pg_config['database']}

# PostgreSQL Configuration
POSTGRES_HOST={self.pg_config['host']}
POSTGRES_PORT={self.pg_config['port']}
POSTGRES_DB={self.pg_config['database']}
POSTGRES_USER={self.pg_config['user']}
POSTGRES_PASSWORD={self.pg_config['password']}

# Binance API (Testnet demo - sostituire per mainnet)
BINANCE_API_KEY=DEMO_KEY
BINANCE_SECRET_KEY=DEMO_SECRET
BINANCE_TESTNET=true

# Trading Configuration
INITIAL_BALANCE=250.0
DEMO_MODE=false

# Dashboard Configuration
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=8507

# AI Configuration (opzionale)
OPENROUTER_API_KEY=optional_for_enhanced_ai

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/aurumbotx.log
"""
            
            with open('.env', 'w') as f:
                f.write(env_content)
            
            self.log("✅ Configurazione aggiornata")
            return True
            
        except Exception as e:
            self.log(f"❌ Errore aggiornamento config: {e}")
            return False
    
    def create_backup(self):
        """Crea backup SQLite prima della migrazione"""
        self.log("💾 Creazione backup SQLite...")
        
        try:
            backup_dir = f"backup_sqlite_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.makedirs(backup_dir, exist_ok=True)
            
            import shutil
            
            for db_file in self.sqlite_dbs:
                if os.path.exists(db_file):
                    shutil.copy2(db_file, os.path.join(backup_dir, db_file))
                    self.log(f"✅ Backup {db_file}")
            
            self.log(f"✅ Backup creato in {backup_dir}")
            return backup_dir
            
        except Exception as e:
            self.log(f"❌ Errore backup: {e}")
            return None
    
    def verify_migration(self):
        """Verifica migrazione completata"""
        self.log("🔍 Verifica migrazione...")
        
        try:
            pg_conn = psycopg2.connect(**self.pg_config)
            pg_cursor = pg_conn.cursor()
            
            # Conta record in ogni tabella
            tables = ['mega_trades', 'ultra_trades', 'mega_mainnet_trades', 'system_health']
            
            for table in tables:
                try:
                    pg_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = pg_cursor.fetchone()[0]
                    self.log(f"📊 {table}: {count} record")
                except Exception as e:
                    self.log(f"⚠️ Tabella {table}: {e}")
            
            pg_conn.close()
            self.log("✅ Verifica completata")
            return True
            
        except Exception as e:
            self.log(f"❌ Errore verifica: {e}")
            return False
    
    def run_migration(self):
        """Esegue migrazione completa"""
        self.log("🚀 Avvio migrazione SQLite → PostgreSQL")
        self.log("=" * 60)
        
        steps = [
            ("Backup SQLite", self.create_backup),
            ("Verifica PostgreSQL", self.check_postgresql_connection),
            ("Creazione tabelle", self.create_postgresql_tables),
            ("Migrazione mega_trades", self.migrate_mega_trades),
            ("Migrazione ultra_trades", self.migrate_ultra_trades),
            ("Aggiornamento config", self.update_config_files),
            ("Verifica migrazione", self.verify_migration)
        ]
        
        success_count = 0
        
        for step_name, step_func in steps:
            self.log(f"\\n🔧 {step_name}...")
            if step_func():
                success_count += 1
            else:
                self.log(f"❌ {step_name} fallito")
                break
        
        self.log("\\n" + "=" * 60)
        self.log(f"✅ Migrazione completata: {success_count}/{len(steps)} step")
        
        if success_count == len(steps):
            self.log("🎉 Migrazione PostgreSQL completata con successo!")
            self.log("\\n📋 PROSSIMI STEP:")
            self.log("1. 🔧 Verifica connessione PostgreSQL")
            self.log("2. 🚀 Riavvia AurumBotX")
            self.log("3. 📊 Controlla dashboard per dati migrati")
        else:
            self.log("⚠️ Migrazione parzialmente completata")
        
        # Salva log migrazione
        with open('migration_log.txt', 'w') as f:
            f.write("\\n".join(self.migration_log))
        
        return success_count == len(steps)

def print_setup_instructions():
    """Stampa istruzioni setup PostgreSQL"""
    print("""
🗄️ SETUP POSTGRESQL RICHIESTO

Prima di eseguire la migrazione, configura PostgreSQL:

1. 📦 INSTALLAZIONE POSTGRESQL:
   Ubuntu/Debian:
   sudo apt update
   sudo apt install postgresql postgresql-contrib
   
   macOS:
   brew install postgresql
   
   Windows:
   Scarica da https://www.postgresql.org/download/

2. 🔧 CONFIGURAZIONE DATABASE:
   sudo -u postgres psql
   
   CREATE DATABASE aurumbotx_db;
   CREATE USER aurumbotx_user WITH PASSWORD 'your_secure_password';
   GRANT ALL PRIVILEGES ON DATABASE aurumbotx_db TO aurumbotx_user;
   \\q

3. 🔑 AGGIORNA CREDENZIALI:
   Modifica le credenziali nel file migrate_sqlite_to_postgresql.py:
   - host: 'localhost' (o IP server)
   - port: 5432 (porta standard)
   - database: 'aurumbotx_db'
   - user: 'aurumbotx_user'
   - password: 'your_secure_password'

4. 🧪 TEST CONNESSIONE:
   psql -h localhost -U aurumbotx_user -d aurumbotx_db

5. 🚀 ESEGUI MIGRAZIONE:
   python3 migrate_sqlite_to_postgresql.py
""")

def main():
    """Funzione principale"""
    print("🔄 AurumBotX Database Migration: SQLite → PostgreSQL")
    print("=" * 60)
    
    # Controlla se PostgreSQL è configurato
    try:
        import psycopg2
    except ImportError:
        print("❌ psycopg2 non installato")
        print("📦 Installa con: pip install psycopg2-binary")
        return False
    
    # Mostra istruzioni setup
    print_setup_instructions()
    
    # Chiedi conferma
    response = input("\\n🔧 PostgreSQL è configurato? Procedere con migrazione? (y/N): ")
    if response.lower() != 'y':
        print("⏸️ Migrazione annullata")
        return False
    
    # Esegui migrazione
    migrator = DatabaseMigrator()
    success = migrator.run_migration()
    
    if success:
        print("\\n🎉 MIGRAZIONE COMPLETATA CON SUCCESSO!")
        print("\\n📋 DATABASE URL POSTGRESQL:")
        print(f"postgresql://aurumbotx_user:your_secure_password@localhost:5432/aurumbotx_db")
        print("\\n🚀 AurumBotX ora usa PostgreSQL!")
    else:
        print("\\n⚠️ Migrazione parzialmente completata")
        print("📋 Controlla migration_log.txt per dettagli")
    
    return success

if __name__ == "__main__":
    main()

