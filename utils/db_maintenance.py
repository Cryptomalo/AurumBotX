"""
DatabaseMaintenance module with improved backup table handling
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import psycopg2
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

logger = logging.getLogger(__name__)

class DatabaseMaintenance:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.engine = create_engine(connection_string)
        self.Session = sessionmaker(bind=self.engine)
        self.last_maintenance = None
        self.maintenance_interval = timedelta(hours=1)
        self.vacuum_threshold = 10
        self.analyze_interval = timedelta(hours=6)
        self.partition_check_interval = timedelta(minutes=30)
        self.partition_advance_months = 6
        self.trading_pairs = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
        self.last_analyze = None
        self.last_partition_check = None
        self._initialize_maintenance()

    def _is_backup_table(self, table_name: str) -> bool:
        """Check if a table is a backup table"""
        return '_backup_' in table_name.lower()

    def _is_table_partitioned(self, table_name: str) -> bool:
        """Check if a table is partitioned"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT 1 
                        FROM pg_partitioned_table pt 
                        JOIN pg_class pc ON pt.partrelid = pc.oid 
                        WHERE pc.relname = :table_name
                    )
                """), {'table_name': table_name})
                return result.scalar()
        except Exception as e:
            logger.error(f"Error checking if table {table_name} is partitioned: {e}")
            return False

    def _get_existing_partitions(self, table_name: str) -> List[str]:
        """Get list of existing partitions for a table"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT child.relname as partition_name
                    FROM pg_inherits
                    JOIN pg_class parent ON pg_inherits.inhparent = parent.oid
                    JOIN pg_class child ON pg_inherits.inhrelid = child.oid
                    WHERE parent.relname = :table_name
                """), {'table_name': table_name})
                return [row[0] for row in result]
        except Exception as e:
            logger.error(f"Error getting partitions for {table_name}: {e}")
            return []

    def _initialize_maintenance(self) -> None:
        """Initialize maintenance with improved error handling"""
        try:
            logger.info("Starting initial database maintenance...")
            self._create_template_table()
            self._cleanup_old_data() # Added cleanup call

            # Setup partitioning for all trading pairs
            for pair in self.trading_pairs:
                table_name = f"market_data_{pair.lower()}"
                self._setup_table_partitioning(table_name)

            logger.info("Initial maintenance completed successfully")
        except Exception as e:
            logger.error(f"Error during initial maintenance: {e}")
            raise

    def _create_template_table(self) -> None:
        """Create or update the template table"""
        try:
            with self.engine.begin() as conn:
                conn.execute(text("""
                DROP TABLE IF EXISTS market_data_template CASCADE;
                CREATE TABLE market_data_template (
                    id SERIAL,
                    symbol VARCHAR(20) NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    "Open" DOUBLE PRECISION NOT NULL,
                    "High" DOUBLE PRECISION NOT NULL,
                    "Low" DOUBLE PRECISION NOT NULL,
                    "Close" DOUBLE PRECISION NOT NULL,
                    "Volume" DOUBLE PRECISION NOT NULL,
                    "Returns" DOUBLE PRECISION,
                    "Volatility" DOUBLE PRECISION,
                    "Volume_MA" DOUBLE PRECISION,
                    "Volume_Ratio" DOUBLE PRECISION,
                    "SMA_20" DOUBLE PRECISION,
                    "SMA_50" DOUBLE PRECISION,
                    "SMA_200" DOUBLE PRECISION,
                    "EMA_20" DOUBLE PRECISION,
                    "EMA_50" DOUBLE PRECISION,
                    "EMA_200" DOUBLE PRECISION,
                    "MACD" DOUBLE PRECISION,
                    "MACD_Signal" DOUBLE PRECISION,
                    "MACD_Hist" DOUBLE PRECISION,
                    "RSI" DOUBLE PRECISION,
                    "ATR" DOUBLE PRECISION,
                    "BB_Middle" DOUBLE PRECISION,
                    "BB_Upper" DOUBLE PRECISION,
                    "BB_Lower" DOUBLE PRECISION,
                    "BB_Width" DOUBLE PRECISION,
                    PRIMARY KEY (symbol, timestamp)
                );
                """))
            logger.info("Template table created/updated successfully")
        except Exception as e:
            logger.error(f"Error creating template table: {e}")
            raise

    def _setup_table_partitioning(self, table_name: str) -> None:
        """Setup partitioning for a table with improved backup handling"""
        try:
            # Skip backup tables
            if self._is_backup_table(table_name):
                logger.info(f"Skipping partitioning setup for backup table: {table_name}")
                return

            with self.engine.begin() as conn:
                # Create new partitioned table
                conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    LIKE market_data_template INCLUDING ALL
                ) PARTITION BY RANGE (timestamp);
                """))
                # Create initial partitions for current and next month
                current_date = datetime.now().replace(day=1)
                next_month = (current_date + timedelta(days=32)).replace(day=1)

                for month_date in [current_date, next_month]:
                    next_month_date = (month_date + timedelta(days=32)).replace(day=1)
                    partition_name = f"{table_name}_{month_date.strftime('%Y%m')}"

                    conn.execute(text(f"""
                    CREATE TABLE IF NOT EXISTS {partition_name}
                    PARTITION OF {table_name}
                    FOR VALUES FROM ('{month_date.strftime('%Y-%m-%d')}')
                    TO ('{next_month_date.strftime('%Y-%m-%d')}');

                    CREATE INDEX IF NOT EXISTS idx_{partition_name}_timestamp 
                    ON {partition_name} USING btree (timestamp);

                    CREATE INDEX IF NOT EXISTS idx_{partition_name}_symbol_timestamp 
                    ON {partition_name} USING btree (symbol, timestamp);
                    """))

                logger.info(f"Table {table_name} partitioned successfully")
        except Exception as e:
            logger.error(f"Error setting up partitioning for {table_name}: {e}")
            raise

    def _create_advance_partitions(self) -> None:
        """Create partitions for future months with improved error handling"""
        try:
            current_date = datetime.now()

            # Create partitions for each trading pair
            for pair in self.trading_pairs:
                table_name = f"market_data_{pair.lower()}"

                # Skip if table is not partitioned
                if not self._is_table_partitioned(table_name):
                    logger.warning(f"Table {table_name} is not partitioned, skipping")
                    continue

                # Get existing partitions
                existing_partitions = self._get_existing_partitions(table_name)

                # Create partitions for next N months
                for month_offset in range(self.partition_advance_months):
                    partition_date = (current_date + timedelta(days=32 * month_offset)).replace(day=1)
                    next_month = (partition_date + timedelta(days=32)).replace(day=1)

                    partition_name = f"{table_name}_{partition_date.strftime('%Y%m')}"

                    # Skip if partition already exists
                    if partition_name in existing_partitions:
                        logger.debug(f"Partition {partition_name} already exists")
                        continue

                    try:
                        with self.engine.begin() as conn:
                            conn.execute(text(f"""
                            CREATE TABLE IF NOT EXISTS {partition_name}
                            PARTITION OF {table_name}
                            FOR VALUES FROM ('{partition_date.strftime('%Y-%m-%d')}')
                            TO ('{next_month.strftime('%Y-%m-%d')}');

                            CREATE INDEX IF NOT EXISTS idx_{partition_name}_timestamp 
                            ON {partition_name} USING btree (timestamp);

                            CREATE INDEX IF NOT EXISTS idx_{partition_name}_symbol_timestamp 
                            ON {partition_name} USING btree (symbol, timestamp);
                            """))
                            logger.info(f"Created partition {partition_name}")
                    except Exception as e:
                        logger.error(f"Error creating partition {partition_name}: {e}")

            logger.info("Advance partitions created successfully")
        except Exception as e:
            logger.error(f"Error in _create_advance_partitions: {e}")
            raise

    def perform_maintenance(self) -> None:
        """Perform scheduled maintenance tasks"""
        try:
            current_time = datetime.now()

            if (self.last_maintenance and 
                current_time - self.last_maintenance < self.maintenance_interval):
                return

            logger.info("Starting scheduled database maintenance")

            # Manage partitions if needed
            if (not self.last_partition_check or 
                current_time - self.last_partition_check >= self.partition_check_interval):
                self._create_advance_partitions()
                self.last_partition_check = current_time

            # Run VACUUM ANALYZE on tables with high dead tuples
            self._vacuum_analyze_needed_tables()

            self.last_maintenance = current_time
            logger.info("Database maintenance completed successfully")

        except Exception as e:
            logger.error(f"Error during maintenance: {e}")


    def _vacuum_analyze_needed_tables(self) -> None:
        """Run VACUUM ANALYZE on tables that need it"""
        try:
            with self.engine.connect() as conn:
                stats = self._get_table_stats(conn)
                for table_name, table_stats in stats.items():
                    if (table_stats['dead_tuple_pct'] > self.vacuum_threshold or 
                        table_stats.get('modifications', 0) > 1000):
                        self._vacuum_analyze_table(table_name)
        except Exception as e:
            logger.error(f"Error during vacuum analyze: {e}")

    def _vacuum_analyze_table(self, table_name: str) -> None:
        """Run VACUUM ANALYZE on a specific table"""
        try:
            conn = psycopg2.connect(self.connection_string)
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()

            logger.info(f"Running VACUUM ANALYZE on {table_name}")
            cur.execute(f"VACUUM ANALYZE {table_name};")
            logger.info(f"VACUUM ANALYZE completed for {table_name}")

            cur.close()
            conn.close()
        except Exception as e:
            logger.error(f"Error running VACUUM on {table_name}: {e}")

    def _get_table_stats(self, conn) -> Dict[str, Dict]:
        """Get statistics for market data tables"""
        try:
            result = conn.execute(text("""
                SELECT 
                    relname as table_name,
                    n_live_tup as live_rows,
                    n_dead_tup as dead_rows,
                    last_vacuum,
                    last_analyze,
                    n_mod_since_analyze as modifications
                FROM pg_stat_user_tables 
                WHERE schemaname = 'public'
                AND relname LIKE 'market_data_%'
            """))

            stats = {}
            for row in result:
                dead_tuple_pct = (row.dead_rows / (row.live_rows + row.dead_rows) * 100) if (row.live_rows + row.dead_rows) > 0 else 0
                stats[row.table_name] = {
                    'live_rows': row.live_rows,
                    'dead_rows': row.dead_rows,
                    'dead_tuple_pct': dead_tuple_pct,
                    'last_vacuum': row.last_vacuum,
                    'last_analyze': row.last_analyze,
                    'modifications': row.modifications
                }
            return stats
        except Exception as e:
            logger.error(f"Error getting table stats: {e}")
            return {}

    def manage_partitions(self) -> None:
        """Manage table partitions with improved error handling"""
        try:
            tables = self._get_market_data_tables()
            for table_name in tables:
                # Skip template and backup tables
                if table_name == 'market_data_template' or self._is_backup_table(table_name):
                    continue

                # Create next month's partition
                next_month = datetime.now() + timedelta(days=32)
                partition_name = f"{table_name}_y{next_month.year}m{next_month.month:02d}"

                try:
                    with self.engine.connect() as conn:
                        # Check if partition exists
                        exists_query = text(f"""
                        SELECT EXISTS (
                            SELECT FROM pg_tables 
                            WHERE schemaname = 'public' 
                            AND tablename = '{partition_name}'
                        )
                        """)
                        partition_exists = conn.execute(exists_query).scalar()

                        if not partition_exists:
                            # Create the partition directly under the main table
                            conn.execute(text(f"""
                            CREATE TABLE IF NOT EXISTS {partition_name}
                            PARTITION OF {table_name}
                            FOR VALUES FROM 
                            ('{next_month.replace(day=1).strftime('%Y-%m-%d')}')
                            TO 
                            ('{(next_month.replace(day=1) + timedelta(days=32)).replace(day=1).strftime('%Y-%m-%d')}');
                            """))

                            # Create indexes on new partition
                            conn.execute(text(f"""
                            CREATE INDEX IF NOT EXISTS idx_{partition_name}_timestamp 
                            ON {partition_name} (timestamp);

                            CREATE INDEX IF NOT EXISTS idx_{partition_name}_close_timestamp 
                            ON {partition_name} ("Close", timestamp);
                            """))

                            logger.info(f"Created partition {partition_name} with indexes")
                        else:
                            logger.debug(f"Partition {partition_name} already exists")

                except Exception as e:
                    logger.error(f"Error creating partition {partition_name}: {e}")
                    # Continue with next table even if one fails

        except Exception as e:
            logger.error(f"Error managing partitions: {e}")

    def _get_market_data_tables(self) -> List[str]:
        """Get list of market data tables"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public' 
                AND tablename LIKE 'market_data_%'
            """))
            return [row.tablename for row in result]

    def _vacuum_analyze_all_tables(self) -> None:
        """Run VACUUM ANALYZE on all market data tables"""
        try:
            # Use psycopg2 for VACUUM as it must run outside transaction
            conn = psycopg2.connect(self.connection_string)
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()

            tables = self._get_market_data_tables()
            for table in tables:
                if table != 'market_data_template':
                    logger.info(f"Running VACUUM ANALYZE on {table}")
                    cur.execute(f"VACUUM ANALYZE {table};")
                    logger.info(f"VACUUM ANALYZE completed for {table}")

            cur.close()
            conn.close()
        except Exception as e:
            logger.error(f"Error during VACUUM ANALYZE: {e}")

    def run_analyze(self, table_name: str) -> bool:
        """Run ANALYZE on a specific table"""
        try:
            with self.engine.connect() as conn:
                logger.info(f"Running ANALYZE on {table_name}")
                conn.execute(text(f"ANALYZE {table_name};"))
                logger.info(f"ANALYZE completed for {table_name}")
                return True
        except Exception as e:
            logger.error(f"Error running ANALYZE on {table_name}: {e}")
            return False

    def check_index_health(self) -> List[Dict]:
        """Check index usage and health"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT 
                        schemaname,
                        relname as table_name,
                        indexrelname as index_name,
                        idx_scan,
                        pg_size_pretty(pg_relation_size(indexrelname::regclass)) as index_size,
                        idx_tup_read,
                        idx_tup_fetch
                    FROM pg_stat_user_indexes
                    WHERE schemaname = 'public'
                    ORDER BY idx_scan DESC
                """))

                return [dict(row) for row in result]
        except Exception as e:
            logger.error(f"Error checking index health: {e}")
            return []

    def suggest_indexes(self) -> List[str]:
        """Suggest new indexes based on query patterns"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT 
                        relname as table_name,
                        seq_scan,
                        seq_tup_read,
                        idx_scan,
                        idx_tup_fetch
                    FROM pg_stat_user_tables
                    WHERE schemaname = 'public'
                    AND seq_scan > 0
                    ORDER BY seq_scan DESC
                """))

                suggestions = []
                for row in result:
                    if row.seq_scan > row.idx_scan * 10:  # High number of sequential scans
                        suggestions.append(f"Consider adding indexes to {row.table_name} "
                                            f"(sequential scans: {row.seq_scan}, "
                                            f"index scans: {row.idx_scan})")
                return suggestions
        except Exception as e:
            logger.error(f"Error generating index suggestions: {e}")
            return []

    def check_table_stats(self) -> Dict[str, Dict]:
        """Get statistics for all tables"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT 
                        relname as table_name,
                        n_live_tup as live_rows,
                        n_dead_tup as dead_rows,
                        last_vacuum,
                        last_analyze,
                        n_mod_since_analyze as modifications
                    FROM pg_stat_user_tables 
                    WHERE schemaname = 'public'
                """))

                stats = {}
                for row in result:
                    dead_tuple_pct = (row.dead_rows / (row.live_rows + row.dead_rows) * 100) if (row.live_rows + row.dead_rows) > 0 else 0
                    stats[row.table_name] = {
                        'live_rows': row.live_rows,
                        'dead_rows': row.dead_rows,
                        'dead_tuple_pct': dead_tuple_pct,
                        'last_vacuum': row.last_vacuum,
                        'last_analyze': row.last_analyze,
                        'modifications': row.modifications
                    }
                return stats
        except Exception as e:
            logger.error(f"Error checking table stats: {e}")
            return {}

    def run_vacuum(self, table_name: str) -> bool:
        """Run VACUUM ANALYZE on a specific table"""
        try:
            # Use psycopg2 for VACUUM as SQLAlchemy doesn't support it directly
            conn = psycopg2.connect(self.connection_string)
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()

            logger.info(f"Running VACUUM ANALYZE on {table_name}")
            cur.execute(f"VACUUM ANALYZE {table_name};")

            cur.close()
            conn.close()
            logger.info(f"VACUUM ANALYZE completed for {table_name}")
            return True
        except Exception as e:
            logger.error(f"Error running VACUUM on {table_name}: {e}")
            return False

    def _cleanup_old_data(self):
        """Clean up old market data to maintain performance"""
        try:
            cleanup_sql = """
            DELETE FROM market_data_partitioned 
            WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '90 days'
            AND id NOT IN (
                SELECT id FROM market_data_partitioned
                WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '90 days'
                ORDER BY timestamp DESC
                LIMIT 1000000
            );
            """

            with self.engine.begin() as conn:
                conn.execute(text(cleanup_sql))
                logger.info("Successfully cleaned up old market data")

        except Exception as e:
            logger.error(f"Error cleaning up old data: {str(e)}")

    def _create_historical_partitions(self, table_name: str, start_date: datetime, end_date: datetime = None) -> None:
        """Create partitions for historical data"""
        try:
            if end_date is None:
                end_date = datetime.now()

            current_date = start_date.replace(day=1)
            while current_date <= end_date:
                next_month = (current_date + timedelta(days=32)).replace(day=1)
                partition_name = f"{table_name}_{current_date.strftime('%Y%m')}"

                try:
                    with self.engine.begin() as conn:
                        conn.execute(text(f"""
                        CREATE TABLE IF NOT EXISTS {partition_name}
                        PARTITION OF {table_name}
                        FOR VALUES FROM ('{current_date.strftime('%Y-%m-%d')}')
                        TO ('{next_month.strftime('%Y-%m-%d')}');

                        CREATE INDEX IF NOT EXISTS idx_{partition_name}_timestamp 
                        ON {partition_name} USING btree (timestamp);

                        CREATE INDEX IF NOT EXISTS idx_{partition_name}_symbol_timestamp 
                        ON {partition_name} USING btree (symbol, timestamp);
                        """))
                        logger.info(f"Created historical partition {partition_name}")
                except Exception as e:
                    logger.error(f"Error creating partition {partition_name}: {e}")

                current_date = next_month

        except Exception as e:
            logger.error(f"Error in _create_historical_partitions: {e}")
            raise

    def restore_from_backup(self, backup_table: str, target_symbol: str) -> None:
        """Restore data from backup table with proper partition handling"""
        try:
            # First get the date range from backup
            with self.engine.begin() as conn:
                result = conn.execute(text(f"""
                    SELECT MIN(timestamp) as min_date, 
                           MAX(timestamp) as max_date 
                    FROM {backup_table}
                """)).fetchone()

                if not result or not result[0]:
                    logger.warning(f"No data found in backup table {backup_table}")
                    return

                min_date, max_date = result

                # Create necessary partitions
                for pair in self.trading_pairs:
                    table_name = f"market_data_{pair.lower()}"
                    self._create_historical_partitions(table_name, min_date, max_date)

                # Transfer data
                insert_sql = f"""
                INSERT INTO market_data_partitioned (
                    symbol, timestamp, open, high, low, close, volume
                )
                SELECT 
                    $1 as symbol,
                    timestamp,
                    "Open" as open,
                    "High" as high,
                    "Low" as low,
                    "Close" as close,
                    "Volume" as volume
                FROM {backup_table}
                ON CONFLICT (symbol, timestamp) DO UPDATE SET
                    open = EXCLUDED.open,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    close = EXCLUDED.close,
                    volume = EXCLUDED.volume
                """
                conn.execute(text(insert_sql), [target_symbol])

                logger.info(f"Successfully restored data from {backup_table} to {target_symbol}")

        except Exception as e:
            logger.error(f"Error restoring from backup: {e}")
            raise


def setup_maintenance(db_url: Optional[str] = None) -> DatabaseMaintenance:
    """Setup database maintenance with environment handling"""
    if db_url is None:
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            raise ValueError("DATABASE_URL environment variable not set")

    return DatabaseMaintenance(db_url)