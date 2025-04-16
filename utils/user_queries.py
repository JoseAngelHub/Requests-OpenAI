from bd import conn
from bd.querys import execute_sql_query
import core.logger as J

# Function to get user credentials from the database by checking the username and password
def get_user(nombre: str, password: str):
    # SQL query to check if the username and password match any record in the USERS table
    query = f"""SELECT NOMBRE, PASSWD FROM USERS WHERE NOMBRE = '{nombre}' AND PASSWD='{password}'"""
    db = conn.get_connect_db()  # Establish database connection
    db.execute(query)  # Execute the query
    result = db.fetchall()  # Fetch all the results from the query
    # If no results, return False indicating invalid credentials
    if len(result) == 0:
        return False
    else:
        return True  # Return True if the user credentials are valid

# Function to get the NIF (tax identification number) of a client based on their phone number
def get_nif_client(telcli: int):
    # SQL query to retrieve the CLIENT_NIF based on the phone number
    query = f"SELECT CLIENT_NIF FROM Clients WHERE telcli = '{telcli}'"
    result = execute_sql_query(query)  # Execute the SQL query using a helper function
    # If no results are returned, log an error and return None
    if not result:
        J.error(f"No results found for telcli: {telcli}")
        return None
    # If exactly one result is returned, log the client NIF and return it
    if len(result) == 1:
        clientNif = result[0]['CLIENT_NIF']
        J.info(f"Client code for telcli {telcli}: {clientNif}")
        return clientNif
    # If multiple results are found, log an error and return None
    else:
        J.error(f"Multiple results found for telcli {telcli}, expected only one.")
        return None
