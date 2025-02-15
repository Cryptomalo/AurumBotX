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
        self.maintenance_interval = timedelta(hours=1)  # Run every hour
        self.vacuum_threshold = 10  # Run VACUUM when dead tuples > 10%
        self.analyze_interval = timedelta(hours=6)  # Run ANALYZE every 6 hours
        self.partition_check_interval = timedelta(days=1)  # Check partitions daily
        self.last_analyze = None
        self.last_partition_check = None
        self._initialize_maintenance()

    def _initialize_maintenance(self) -> None:
        """Perform initial maintenance tasks"""
        try:
            logger.info("Starting initial maintenance...")

            # Get list of market data tables
            tables = self._get_market_data_tables()

            # Setup partitioning for each table
            for table in tables:
                if table != 'market_data_template':
                    self._setup_table_partitioning(table)

            # Run initial VACUUM ANALYZE
            self._vacuum_analyze_all_tables()

            logger.info("Initial maintenance completed successfully")
        except Exception as e:
            logger.error(f"Error during initial maintenance: {e}")

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

    def _setup_table_partitioning(self, table_name: str) -> None:
        """Setup partitioning for a table"""
        try:
            with self.engine.connect() as conn:
                # Create partitioned table
                conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {table_name}_new (
                    LIKE market_data_template INCLUDING ALL
                ) PARTITION BY RANGE (timestamp);
                """))

                # Create current month partition
                current_month = datetime.now().replace(day=1)
                next_month = (current_month + timedelta(days=32)).replace(day=1)
                partition_name = f"{table_name}_y{current_month.year}m{current_month.month:02d}"

                conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {partition_name}
                PARTITION OF {table_name}_new
                FOR VALUES FROM ('{current_month.strftime('%Y-%m-%d')}')
                TO ('{next_month.strftime('%Y-%m-%d')}');
                """))

                logger.info(f"Partitioning setup completed for {table_name}")
        except Exception as e:
            logger.error(f"Error setting up partitioning for {table_name}: {e}")

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

    def manage_partitions(self) -> None:
        """Manage table partitions automatically"""
        try:
            tables = self._get_market_data_tables()
            for table_name in tables:
                if table_name == 'market_data_template':
                    continue

                # Create next month's partition if needed
                next_month = datetime.now() + timedelta(days=32)
                partition_name = f"{table_name}_y{next_month.year}m{next_month.month:02d}"

                with self.engine.connect() as conn:
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

    def _get_table_stats(self, conn) -> Dict[str, Dict]:
        """Get statistics for all tables"""
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