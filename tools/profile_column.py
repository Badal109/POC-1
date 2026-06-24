import json
from tools.snowflake_metadata import get_snowflake_connection

def profile_column(table: str, column: str, layer: str) -> dict:
    """
    Runs SQL probe on a column — returns null %, distinct count, freshness.
    """
    full_table = f"RETAIL_DB.{layer}.{table}"
    query = f"""
        SELECT
            COUNT(*) AS total_rows,
            COUNT({column}) AS non_null_rows,
            COUNT(DISTINCT {column}) AS distinct_values,
            ROUND((COUNT(*) - COUNT({column})) * 100.0 / NULLIF(COUNT(*), 0), 1) AS null_pct
        FROM {full_table}
    """
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        total, non_null, distinct, null_pct = row
        quality = "CLEAN" if null_pct < 5 else "DEGRADED" if null_pct < 30 else "POOR"

        return {
            "table": full_table,
            "column": column,
            "total_rows": total,
            "non_null_rows": non_null,
            "distinct_values": distinct,
            "null_pct": float(null_pct or 0),
            "quality": quality
        }
    except Exception as e:
        return {
            "table": full_table,
            "column": column,
            "error": str(e),
            "quality": "UNKNOWN"
        }