import os
import array
import threading
import logging
import oracledb
from contextlib import contextmanager
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)


#region Database Connection Manager
class RAGDBConnection:
    """Singleton for database connection pool and operations."""
    _instance = None
    _initialized = False
    _pool = None
    _persistent_connection = None
    _persistent_lock = threading.RLock()

    #region Lifecycle
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if RAGDBConnection._initialized:
            return
        RAGDBConnection._initialized = True
        
        self._config_dir = os.getenv("DB_WALLET_PATH")
        self._user = os.getenv("DB_USER")
        self._password = os.getenv("DB_PASSWORD")
        self._dsn = os.getenv("DB_DSN")
        self._wallet_location = os.getenv("DB_WALLET_PATH")
        self._wallet_password = os.getenv("DB_WALLET_PASSWORD")
        self.table_prefix = "edge_demo"
        self._connection_mode = os.getenv("DB_CONNECTION_MODE", "persistent").strip().lower()
    #endregion

    #region Pool + Connection
    def _get_pool(self) -> oracledb.ConnectionPool:
        """Get or create the connection pool (lazy initialization)."""
        if RAGDBConnection._pool is None:
            RAGDBConnection._pool = oracledb.create_pool(
                user=self._user,
                password=self._password,
                dsn=self._dsn,
                config_dir=self._config_dir,
                wallet_location=self._wallet_location,
                wallet_password=self._wallet_password,
                min=1,
                max=5,
                increment=1,
            )
        return RAGDBConnection._pool

    def _is_connection_healthy(self, conn: oracledb.Connection | None) -> bool:
        if conn is None:
            return False
        try:
            conn.ping()
            return True
        except Exception:
            return False

    def _get_persistent_connection(self) -> oracledb.Connection:
        """Return a live singleton connection, reconnecting if needed."""
        with RAGDBConnection._persistent_lock:
            if self._is_connection_healthy(RAGDBConnection._persistent_connection):
                return RAGDBConnection._persistent_connection

            RAGDBConnection._persistent_connection = self.connect_db()
            logger.info("Initialized persistent Oracle DB connection")
            return RAGDBConnection._persistent_connection

    def warmup_connection(self):
        """Initialize the configured connection strategy ahead of first request."""
        if self._connection_mode == "persistent":
            self._get_persistent_connection()
            return

        with self.get_connection():
            return

    @contextmanager
    def get_connection(self):
        if self._connection_mode == "persistent":
            with RAGDBConnection._persistent_lock:
                conn = self._get_persistent_connection()
                try:
                    yield conn
                finally:
                    # Keep connection open for reuse;
                    pass
            return

        pool = self._get_pool()
        conn = pool.acquire()
        try:
            yield conn
        finally:
            pool.release(conn)
    #endregion

    #region Direct Connection Helpers
    def connect_db(self) -> oracledb.Connection:
        try:
            return oracledb.connect(
                user=self._user,
                password=self._password,
                dsn=self._dsn,
                config_dir=self._config_dir,
                wallet_location=self._wallet_location,
                wallet_password=self._wallet_password,
            )
        except oracledb.Error as exc:
            print(f"ERROR: DB connection failed: {exc}")
            raise exc

    def disconnect(self, connection: oracledb.Connection):
        connection.close()

    def close_persistent_connection(self):
        with RAGDBConnection._persistent_lock:
            conn = RAGDBConnection._persistent_connection
            RAGDBConnection._persistent_connection = None
            if conn is not None:
                conn.close()

    def get_cursor(self):
        self.db_connection = self.connect_db()
        self.cursor = self.db_connection.cursor()
    #endregion

    #region Query Operations
    def execute_query(self, conn: oracledb.Connection, sql: str):
        """Execute SQL query and return column names and rows."""
        with conn.cursor() as cur:
            cur.execute(sql)
            return [d[0] for d in cur.description], cur.fetchall()

    def create_table(self, conn: oracledb.Connection):
        """Drop and create embedding table."""
        print("Creating table for embeddings...")

        # Prefix keeps per-user/demo data isolated in shared environments.
        sql_statements = [
            f"DROP TABLE {self.table_prefix}_embedding PURGE",
            f"""
            CREATE TABLE {self.table_prefix}_embedding (
                id NUMBER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                text VARCHAR2(4000),
                vec VECTOR,
                source VARCHAR2(100)
            )
            """
        ]

        with conn.cursor() as cur:
            for stmt in sql_statements:
                try:
                    cur.execute(stmt)
                except Exception as e:
                    print(f"Skipping error: {e}")

    def insert_embedding(self, conn: oracledb.Connection, embeddings, texts, splits):
        for i, emb in enumerate(embeddings):
            # Keep margin under VARCHAR2(4000) to avoid overflow on inserts.
            chunk_text = texts[i][:3900]
            metadata_source = f"{splits[i].metadata.get('source', 'pdf-doc')}_start_{splits[i].metadata.get('start_index', 0)}"

            with conn.cursor() as cur:
                cur.execute(
                    f"INSERT INTO {self.table_prefix}_embedding (text, vec, source) VALUES (:1, :2, :3)",
                    [chunk_text, array.array("f", emb), metadata_source],
                )

        conn.commit()
    #endregion
#endregion
