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

    def _initialize_maintenance(self) -> None:
        """Initialize maintenance with improved error handling"""
        try:
            logger.info("Starting initial database maintenance...")
            self._create_template_table()

            # Setup partitioning for all trading pairs
            for pair in self.trading_pairs:
                table_name = f"market_data_{pair.lower()}"
                self._setup_table_partitioning(table_name)

            self._create_advance_partitions()
            logger.info("Initial maintenance completed successfully")
        except Exception as e:
            logger.error(f"Error during initial maintenance: {e}")
            raise

    def _create_template_table(self) -> None:
        """Create or update the template table"""
        try:
            with self.engine.begin() as conn:
                conn.execute(text("""
                CREATE TABLE IF NOT EXISTS market_data_template (
                    timestamp TIMESTAMP PRIMARY KEY,
                    "Open" DOUBLE PRECISION,
                    "High" DOUBLE PRECISION,
                    "Low" DOUBLE PRECISION,
                    "Close" DOUBLE PRECISION,
                    "Volume" DOUBLE PRECISION,
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
                    "BB_Width" DOUBLE PRECISION
                );
                """))
        except Exception as e:
            logger.error(f"Error creating template table: {e}")
            raise

    def _create_advance_partitions(self) -> None:
        """Create partitions for future months with improved error handling"""
        try:
            current_date = datetime.now()

            # Create partitions for each trading pair
            for pair in self.trading_pairs:
                table_name = f"market_data_{pair.lower()}"

                # Ensure base table exists and is partitioned
                self._setup_table_partitioning(table_name)

                # Create partitions for next N months
                for month_offset in range(self.partition_advance_months):
                    # Calculate dates for partition
                    partition_date = (current_date + timedelta(days=32 * month_offset)).replace(day=1)
                    next_month = (partition_date + timedelta(days=32)).replace(day=1)

                    partition_name = f"{table_name}_y{partition_date.year}m{partition_date.month:02d}"

                    try:
                        with self.engine.begin() as conn:
                            # Create partition as a direct child of the main table
                            conn.execute(text(f"""
                            CREATE TABLE IF NOT EXISTS {partition_name}
                            PARTITION OF {table_name}
                            FOR VALUES FROM ('{partition_date.strftime('%Y-%m-%d')}')
                            TO ('{next_month.strftime('%Y-%m-%d')}');
                            """))

                            # Create optimized indexes on partition
                            conn.execute(text(f"""
                            CREATE INDEX IF NOT EXISTS idx_{partition_name}_timestamp_btree 
                            ON {partition_name} USING btree (timestamp);

                            CREATE INDEX IF NOT EXISTS idx_{partition_name}_close_timestamp_btree 
                            ON {partition_name} USING btree ("Close", timestamp);
                            """))

                        logger.info(f"Successfully created partition {partition_name}")
                    except Exception as e:
                        if "already exists" not in str(e):
                            logger.error(f"Error creating partition {partition_name}: {e}")
                            raise
                        else:
                            logger.debug(f"Partition {partition_name} already exists")

            logger.info("Advance partitions created successfully")
        except Exception as e:
            logger.error(f"Error in _create_advance_partitions: {e}")
            raise

    def _setup_table_partitioning(self, table_name: str) -> None:
        """Setup partitioning for a table with improved backup handling"""
        try:
            # Skip backup tables
            if self._is_backup_table(table_name):
                logger.info(f"Skipping partitioning setup for backup table: {table_name}")
                return

            with self.engine.begin() as conn:
                # Check if table exists
                exists_query = text(f"""
                SELECT EXISTS (
                    SELECT FROM pg_tables 
                    WHERE schemaname = 'public' 
                    AND tablename = '{table_name}'
                )
                """)
                table_exists = conn.execute(exists_query).scalar()

                if table_exists:
                    # Check if table is partitioned
                    is_partitioned_query = text(f"""
                    SELECT EXISTS (
                        SELECT 1 
                        FROM pg_partitioned_table pt 
                        JOIN pg_class pc ON pt.partrelid = pc.oid 
                        WHERE pc.relname = '{table_name}'
                    )
                    """)
                    is_partitioned = conn.execute(is_partitioned_query).scalar()

                    if not is_partitioned:
                        # Backup existing data
                        backup_table = f"{table_name}_backup_{int(time.time())}"
                        conn.execute(text(f"ALTER TABLE {table_name} RENAME TO {backup_table}"))
                        logger.info(f"Backed up existing table to {backup_table}")

                # Create new partitioned table
                conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    LIKE market_data_template INCLUDING ALL
                ) PARTITION BY RANGE (timestamp);
                """))

                logger.info(f"Partitioning setup completed for {table_name}")
        except Exception as e:
            logger.error(f"Error setting up partitioning for {table_name}: {e}")
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
                self.manage_partitions()
                self.last_partition_check = current_time

            # Run VACUUM ANALYZE on tables with high dead tuples
            with self.engine.connect() as conn:
                stats = self._get_table_stats(conn)
                for table_name, table_stats in stats.items():
                    if (table_stats['dead_tuple_pct'] > self.vacuum_threshold or 
                        table_stats.get('modifications', 0) > 1000):
                        logger.info(f"Table {table_name} needs maintenance:")
                        logger.info(f"Dead tuples: {table_stats['dead_tuple_pct']}%")
                        logger.info(f"Modifications: {table_stats.get('modifications', 0)}")
                        self._vacuum_analyze_table(table_name)

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
                dead_tuple_pct = (row.dead_rows / (row.live_rows + row.dead_rows) * 100 
                                if (row.live_rows + row.dead_rows) > 0 else 0)
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
        """Manage table partitions with backup table handling"""
        try:
            tables = self._get_market_data_tables()
            for table_name in tables:
                # Skip template and backup tables
                if table_name == 'market_data_template' or self._is_backup_table(table_name):
                    continue

                # Create next month's partition
                next_month = datetime.now() + timedelta(days=32)
                partition_name = f"{table_name}_y{next_month.year}m{next_month.month:02d}"

                with self.engine.connect() as conn:
                    # Create the partition directly under the main table
                    conn.execute(text(f"""
                    CREATE TABLE IF NOT EXISTS {partition_name}
                    PARTITION OF {table_name}
                    FOR VALUES FROM 
                    ('{next_month.replace(day=1).strftime('%Y-%m-%d')}')
                    TO 
                    ('{(next_month.replace(day=1) + timedelta(days=32)).replace(day=1).strftime('%Y-%m-%d')}');
                    """))

                    # Create indexes on partition
                    conn.execute(text(f"""
                    CREATE INDEX IF NOT EXISTS idx_{partition_name}_timestamp 
                    ON {partition_name} (timestamp);

                    CREATE INDEX IF NOT EXISTS idx_{partition_name}_close_timestamp 
                    ON {partition_name} ("Close", timestamp);
                    """))

                logger.info(f"Created partition {partition_name}")

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



def setup_maintenance(db_url: Optional[str] = None) -> DatabaseMaintenance:
    """Setup database maintenance with environment handling"""
    if db_url is None:
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            raise ValueError("DATABASE_URL environment variable not set")

    return DatabaseMaintenance(db_url)