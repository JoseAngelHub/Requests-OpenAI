from requests import Session
from bd.conn import get_connect_db
import core.logger as J  # Custom logger for logging info and errors

# Retrieves column names for the given table names
def get_context(tables, db: Session = get_connect_db()):
    try:
        if not tables:
            raise ValueError("You must provide at least one table.")

        # Clean and split the input string into a list of table names
        raw_list = tables.replace('\n', ',').replace('\r', ',').split(',')
        table_list = [table.strip() for table in raw_list if table.strip()]
        
        J.info(f"Fetching column metadata for tables: {table_list}")
        
        # Format the list for use in the SQL IN clause
        table_names = "', '".join(table_list)
        query = f"""
            SELECT 
                TABLE_NAME, COLUMN_NAME, DATA_TYPE 
            FROM 
                INFORMATION_SCHEMA.COLUMNS 
            WHERE 
                TABLE_NAME IN ('{table_names}');
        """
        
        # Execute query and fetch results
        db.execute(query)
        result = db.fetchall()

        # Extract only column names from the result
        columns = [row['COLUMN_NAME'] for row in result]
        
        J.info(f"Retrieved columns for {table_list}: {columns}")
        return columns

    except Exception as e:
        # Log the error with the relevant table list (if available)
        J.error(f"Unexpected error getting columns from {table_list if 'table_list' in locals() else tables}: {e}")
        return []

# Executes a raw SQL query and returns the result
def execute_sql_query(sql_query, db: Session = get_connect_db()):
    try:
        J.info(f"Executing SQL query: {sql_query}")
        
        # Run the query and get results
        db.execute(sql_query)
        result = db.fetchall()

        # Check if any rows were returned
        if len(result) == 0:
            J.info(f"Query executed but no rows returned.")
            return False

        J.info(f"Query executed successfully, rows returned: {len(result)}")
        return result
        
    except Exception as e:
        # Log any execution errors
        J.error(f"Unexpected error executing SQL query: {e}")
        return False

# Retrieves the structure (columns) of all views in the database
def get_database_structure():
    structure = {}
    try:
        cursor = get_connect_db()
        if isinstance(cursor, Exception):
            raise cursor  # Raise if connection failed

        # Get all view names from the database
        cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'VIEW'")
        tablas = [row['TABLE_NAME'] for row in cursor.fetchall()]

        # For each view, get its column names
        for tabla in tablas:
            cursor.execute(
                "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = %s", (tabla,)
            )
            columnas = [row['COLUMN_NAME'] for row in cursor.fetchall()]
            structure[tabla] = columnas

    except Exception as e:
        # Log error if retrieving structure fails
        J.error(f"Error getting database structure: {e}")

    return structure
