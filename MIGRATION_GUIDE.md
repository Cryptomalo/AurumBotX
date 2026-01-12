# 🔄 Guida Migrazione Database: SQLite → PostgreSQL

## 📋 Panoramica

Questa guida spiega come migrare AurumBotX da SQLite (database locale) a PostgreSQL (database enterprise) per migliorare performance, scalabilità e affidabilità.

## 🎯 Vantaggi PostgreSQL

### ✅ **Performance**
- **Concurrent Access**: Gestione simultanea di più connessioni
- **Advanced Indexing**: Indici B-tree, Hash, GiST, GIN
- **Query Optimization**: Planner avanzato per query complesse
- **Parallel Processing**: Esecuzione parallela query

### ✅ **Scalabilità**
- **Large Datasets**: Gestione database multi-TB
- **Connection Pooling**: Gestione efficiente connessioni
- **Partitioning**: Partizionamento tabelle per performance
- **Replication**: Master-slave per alta disponibilità

### ✅ **Affidabilità**
- **ACID Compliance**: Transazioni atomiche e consistenti
- **Point-in-time Recovery**: Backup e recovery avanzati
- **Data Integrity**: Vincoli e validazioni robuste
- **Crash Recovery**: Recupero automatico da crash

### ✅ **Funzionalità Avanzate**
- **JSON Support**: Campi JSONB per dati strutturati
- **Full-text Search**: Ricerca testuale avanzata
- **Stored Procedures**: Logica business nel database
- **Extensions**: PostGIS, pg_stat_statements, etc.

## 🛠️ Prerequisiti

### 📦 **Software Richiesto**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib python3-psycopg2

# macOS
brew install postgresql
pip3 install psycopg2-binary

# Windows
# Scarica da https://www.postgresql.org/download/
pip install psycopg2-binary
```

### 🔧 **Configurazione PostgreSQL**

#### **1. Avvio Servizio**
```bash
# Ubuntu/Debian
sudo systemctl start postgresql
sudo systemctl enable postgresql

# macOS
brew services start postgresql

# Windows
# Avvia da Services o pgAdmin
```

#### **2. Creazione Database e Utente**
```sql
-- Accedi come superuser
sudo -u postgres psql

-- Crea database
CREATE DATABASE aurumbotx_db;

-- Crea utente
CREATE USER aurumbotx_user WITH PASSWORD 'your_secure_password';

-- Assegna privilegi
GRANT ALL PRIVILEGES ON DATABASE aurumbotx_db TO aurumbotx_user;

-- Esci
\q
```

#### **3. Test Connessione**
```bash
psql -h localhost -U aurumbotx_user -d aurumbotx_db
```

## 🚀 Processo Migrazione

### **Step 1: Backup Dati Esistenti**
```bash
# Il script crea automaticamente backup
# Backup manuale (opzionale)
cp *.db backup/
```

### **Step 2: Configurazione Credenziali**
Modifica `migrate_sqlite_to_postgresql.py`:
```python
self.pg_config = {
    'host': 'localhost',          # IP server PostgreSQL
    'port': 5432,                 # Porta (standard 5432)
    'database': 'aurumbotx_db',   # Nome database
    'user': 'aurumbotx_user',     # Username
    'password': 'your_password'   # Password sicura
}
```

### **Step 3: Esecuzione Migrazione**
```bash
cd AurumBotX
python3 migrate_sqlite_to_postgresql.py
```

### **Step 4: Verifica Migrazione**
```sql
-- Connetti a PostgreSQL
psql -h localhost -U aurumbotx_user -d aurumbotx_db

-- Verifica tabelle
\dt

-- Conta record
SELECT 'mega_trades' as table_name, COUNT(*) as records FROM mega_trades
UNION ALL
SELECT 'ultra_trades', COUNT(*) FROM ultra_trades
UNION ALL
SELECT 'mega_mainnet_trades', COUNT(*) FROM mega_mainnet_trades
UNION ALL
SELECT 'system_health', COUNT(*) FROM system_health;
```

## 📊 Schema Database PostgreSQL

### **Tabella: mega_trades**
```sql
CREATE TABLE mega_trades (
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
```

### **Tabella: ultra_trades**
```sql
CREATE TABLE ultra_trades (
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
```

### **Indici per Performance**
```sql
CREATE INDEX idx_mega_trades_timestamp ON mega_trades(timestamp);
CREATE INDEX idx_mega_trades_action ON mega_trades(action);
CREATE INDEX idx_ultra_trades_timestamp ON ultra_trades(timestamp);
CREATE INDEX idx_system_health_timestamp ON system_health(timestamp);
```

## ⚙️ Configurazione AurumBotX

### **File: config.json**
```json
{
  "database": {
    "type": "postgresql",
    "url": "postgresql://aurumbotx_user:password@localhost:5432/aurumbotx_db",
    "host": "localhost",
    "port": 5432,
    "database": "aurumbotx_db",
    "user": "aurumbotx_user",
    "password": "your_secure_password"
  }
}
```

### **File: .env**
```bash
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://aurumbotx_user:password@localhost:5432/aurumbotx_db

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=aurumbotx_db
POSTGRES_USER=aurumbotx_user
POSTGRES_PASSWORD=your_secure_password
```

## 🔧 Troubleshooting

### **Problema: Connessione Rifiutata**
```bash
# Verifica servizio attivo
sudo systemctl status postgresql

# Verifica porta
sudo netstat -tlnp | grep 5432

# Controlla configurazione
sudo nano /etc/postgresql/*/main/postgresql.conf
# listen_addresses = 'localhost'

sudo nano /etc/postgresql/*/main/pg_hba.conf
# local   all   aurumbotx_user   md5
```

### **Problema: Autenticazione Fallita**
```sql
-- Reset password utente
sudo -u postgres psql
ALTER USER aurumbotx_user PASSWORD 'new_password';
```

### **Problema: Database Non Trovato**
```sql
-- Lista database
\l

-- Crea se mancante
CREATE DATABASE aurumbotx_db OWNER aurumbotx_user;
```

### **Problema: Permessi Insufficienti**
```sql
-- Assegna tutti i privilegi
GRANT ALL PRIVILEGES ON DATABASE aurumbotx_db TO aurumbotx_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO aurumbotx_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO aurumbotx_user;
```

## 📈 Ottimizzazioni Performance

### **Configurazione PostgreSQL**
```sql
-- postgresql.conf ottimizzazioni
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
```

### **Indici Avanzati**
```sql
-- Indice composito per query frequenti
CREATE INDEX idx_mega_trades_timestamp_action ON mega_trades(timestamp, action);

-- Indice parziale per trade profittevoli
CREATE INDEX idx_mega_trades_profitable ON mega_trades(timestamp) 
WHERE profit_loss > 0;

-- Indice GIN per ricerca JSON
CREATE INDEX idx_mega_trades_ai_signals ON mega_trades 
USING GIN (ai_signals);
```

### **Vacuum e Analyze**
```sql
-- Manutenzione automatica
ALTER TABLE mega_trades SET (autovacuum_vacuum_scale_factor = 0.1);
ALTER TABLE mega_trades SET (autovacuum_analyze_scale_factor = 0.05);

-- Manutenzione manuale
VACUUM ANALYZE mega_trades;
```

## 🔄 Rollback (Se Necessario)

### **Ripristino SQLite**
```bash
# Ferma AurumBotX
./stop_aurumbotx.sh

# Ripristina backup SQLite
cp backup_sqlite_*/mega_aggressive_trading.db .
cp backup_sqlite_*/ultra_aggressive_trading.db .

# Ripristina configurazione SQLite
git checkout config.json .env

# Riavvia
./start_aurumbotx.sh
```

## 📊 Monitoraggio PostgreSQL

### **Query Performance**
```sql
-- Query più lente
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Dimensioni tabelle
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### **Connessioni Attive**
```sql
SELECT 
    datname,
    usename,
    application_name,
    client_addr,
    state,
    query_start
FROM pg_stat_activity
WHERE state = 'active';
```

## 🎯 Vantaggi Post-Migrazione

### **Performance Migliorata**
- ✅ Query complesse 5-10x più veloci
- ✅ Gestione concorrente di più dashboard
- ✅ Backup incrementali automatici
- ✅ Indici ottimizzati per trading data

### **Scalabilità Enterprise**
- ✅ Supporto per milioni di trade
- ✅ Partitioning per dati storici
- ✅ Connection pooling per alta concorrenza
- ✅ Replication per alta disponibilità

### **Funzionalità Avanzate**
- ✅ Ricerca full-text sui trade
- ✅ Analisi JSON avanzate
- ✅ Stored procedures per logica business
- ✅ Trigger per automazioni

---

## 🎉 Conclusione

La migrazione a PostgreSQL trasforma AurumBotX da sistema locale a piattaforma enterprise-ready, con performance superiori, scalabilità illimitata e affidabilità production-grade.

**Database URL Finale:**
```
postgresql://aurumbotx_user:your_password@localhost:5432/aurumbotx_db
```

**🚀 AurumBotX è ora pronto per deployment enterprise!**

