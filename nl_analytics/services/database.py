import os
import time
import logging
import duckdb
import pandas as pd
from services.observability import log_span

logger = logging.getLogger(__name__)

# Global DuckDB connection singleton for non-Streamlit context
_conn = None

def get_connection() -> duckdb.DuckDBPyConnection:
    """
    Returns the global in-memory DuckDB connection.
    Uses Streamlit session state if running inside Streamlit to survive hot-reloads.
    """
    try:
        import streamlit as st
        if st.runtime.exists():
            if "duckdb_conn" not in st.session_state:
                st.session_state.duckdb_conn = duckdb.connect(database=':memory:', read_only=False)
                logger.info("Created new DuckDB connection in st.session_state.")
            return st.session_state.duckdb_conn
    except Exception as e:
        logger.warning(f"Failed to use Streamlit session state for DuckDB: {e}")

    global _conn
    if _conn is None:
        _conn = duckdb.connect(database=':memory:', read_only=False)
        logger.info("Created new global in-memory DuckDB connection.")
    return _conn

def load_csv(filepath: str):
    """
    Loads a CSV file into the DuckDB connection registered under the table name 'df'.
    """
    conn = get_connection()
    if not os.path.exists(filepath):
        logger.error(f"Failed to load CSV: {filepath} does not exist.")
        raise FileNotFoundError(f"CSV file not found: {filepath}")
    
    try:
        # Use DuckDB native read_csv_auto for proper DATE and numeric type inference
        conn.execute(f"CREATE OR REPLACE TABLE df AS SELECT * FROM read_csv_auto('{filepath}')")
        count = conn.execute("SELECT COUNT(*) FROM df").fetchone()[0]
        logger.info(f"Successfully loaded CSV {filepath} via read_csv_auto ({count} rows).")
    except Exception as e:
        logger.warning(f"read_csv_auto failed, falling back to pandas: {e}")
        try:
            df = pd.read_csv(filepath)
            conn.register('df_temp', df)
            conn.execute("CREATE OR REPLACE TABLE df AS SELECT * FROM df_temp")
            conn.unregister('df_temp')
            logger.info(f"Successfully loaded CSV {filepath} via pandas fallback ({len(df)} rows).")
        except Exception as e2:
            logger.error(f"Error loading CSV {filepath}: {e2}")
            raise e2

def execute_query(sql: str, trace=None) -> pd.DataFrame:
    """
    Executes a SQL query on the DuckDB connection and returns a pandas DataFrame.
    """
    conn = get_connection()
    start_time = time.time()
    try:
        res = conn.execute(sql).fetchdf()
        latency = time.time() - start_time
        log_span(trace, "duckdb_execute", {"sql": sql}, {"row_count": len(res)}, latency)
        return res
    except Exception as e:
        latency = time.time() - start_time
        log_span(trace, "duckdb_execute_error", {"sql": sql}, {"error": str(e)}, latency)
        logger.error(f"SQL execution error for query '{sql}': {e}")
        raise e

def get_schema(filepath: str) -> dict:
    """
    Reads a CSV schema directly from DuckDB table description.
    """
    conn = get_connection()
    try:
        res = conn.execute("DESCRIBE df").fetchall()
        return {row[0]: row[1] for row in res}
    except Exception as e:
        logger.warning(f"DESCRIBE df failed, extracting from pandas: {e}")
        if not os.path.exists(filepath):
            return {}
        try:
            df = pd.read_csv(filepath)
            return {col: str(df[col].dtype) for col in df.columns}
        except Exception:
            return {}
