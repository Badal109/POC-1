import snowflake.connector
from config import SNOWFLAKE_CONFIG

def get_snowflake_connection():
    return snowflake.connector.connect(**SNOWFLAKE_CONFIG)

def fetch_all_metadata() -> dict:
    """
    Returns {layer: {table: [col1, col2, ...]}} for BRONZE, SILVER, GOLD
    """
    query = """
        SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME
        FROM CPG_DB.INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA IN ('BRONZE', 'SILVER', 'GOLD')
        ORDER BY TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION
    """
    conn = get_snowflake_connection()
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    metadata = {"BRONZE": {}, "SILVER": {}, "GOLD": {}}
    for schema, table, column in rows:
        if table not in metadata[schema]:
            metadata[schema][table] = []
        metadata[schema][table].append(column)
    return metadata

if __name__ == "__main__":
    meta = fetch_all_metadata()
    for layer, tables in meta.items():
        print(f"\n=== {layer} ===")
        for table, cols in tables.items():
            print(f"  {table}: {len(cols)} columns")