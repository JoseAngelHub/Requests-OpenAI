import datetime
from decimal import Decimal
from typing import Optional
from fastapi import HTTPException, Header
import jwt
import pyodbc
from bd import conn
from core.config import SERVER, DATABASE_NAME, USERNAME, PASSWORD
import core.logger as J
from core.config import SECRET_KEY
from bd.conn import get_connect_db
from sqlalchemy.orm import Session

Key = SECRET_KEY
ALGORITHM = "HS256"

def get_user(nombre:str, password:str):
    query=f"""SELECT NOMBRE, PASSWD FROM USERS WHERE NOMBRE = '{nombre}' AND PASSWD='{password}'"""
    db = conn.get_connect_db()
    db.execute(query)
    result = db.fetchall()
    if len(result)==0:
        return False
    else:
        return True
  
# Function to create a JWT token with an optional expiration time
def create_jwt_token(data: dict, expires_delta: Optional[int] = None):
    J.info("Creating JWT token")
    to_encode = data.copy()
    # Set the expiration time to 24 hours or the provided expiration delta
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=expires_delta or 24)
    to_encode.update({"exp": expire})
    # Encode and return the JWT token
    return jwt.encode(to_encode, Key, algorithm=ALGORITHM)
  
# Function to extract and validate the current user's JWT token from the request header
def get_current_user(authorization: str = Header(None)):
    J.info("Validating JWT token")
    # Check if the token is present and correctly formatted
    if not authorization or not authorization.startswith("Bearer "):
        J.warning("Token missing or invalid")
        raise HTTPException(status_code=401, detail={'text':"Token missing or invalid", 'state': False})
    
    token = authorization.split("Bearer ")[1]
    try:
        # Decode and verify the token
        payload = jwt.decode(token, Key, algorithms=[ALGORITHM])
        J.info(f"Token validated for user: {payload['sub']}")
        return payload['sub']
    except jwt.ExpiredSignatureError:
        # Handle expired token error
        J.warning("Token expired")
        raise HTTPException(status_code=401, detail={'text':"Token expired", 'state': False})
    except jwt.InvalidTokenError:
        # Handle invalid token error
        J.warning("Invalid token")
        raise HTTPException(status_code=401, detail={'text':"Invalid token", 'state': False})
    
# User login by phone
def login_user(phone:str):
    try:
        conn = pyodbc.connect(
            f"DRIVER={{SQL Server}};SERVER={SERVER};DATABASE={DATABASE_NAME};UID={USERNAME};PWD={PASSWORD}"
        )
        cursor = conn.cursor()
        # We take the user from the clients table that has the phone number with which the request was made
        query= "SELECT name FROM CLIENTS WHERE TELCLI='"+phone+"'"
        cursor.execute(query)
        result = cursor.fetchall()
        if result:
            # We return true so that the endpoint can advance and do the process_q
            return True
        else:
            # False is returned so that it does not continue and does not consume the OPENAI request.
            raise ValueError("Something has not gone as we expected")
        
    except Exception as e:
        J.error(f"Error verifying user: {str(e)}")
        return False
    except ValueError as e:
        J.error(f"User not found error: {str(e)}")
        return False
    
def get_nif_client(telcli:int):
    query=f"SELECT CLIENT_NIF FROM Clients WHERE telcli = '{telcli}'"
    result = execute_sql_query(query)
    if not result:
        J.error(f"No results found for telcli: {telcli}")
        return None
    if len(result) == 1:
        clientNif = result[0]['CLIENT_NIF']
        J.info(f"Client code for telcli {telcli}: {clientNif}")
        return clientNif
    else:
        J.error(f"Multiple results found for telcli {telcli}, expected only one.")
        return None
    
# To avoid errors when converting it to JSON, we change the data types.
def convert_decimals(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    return str(obj)

# We take the data from the tables that is passed to us
def get_context(tables, db: Session = get_connect_db()):
    try:
        if not tables:
            raise ValueError("You must provide at least one table.")

        table_list = [table.strip() for table in tables.split(',')]
        # Save it in a list in case we get several tables
        J.info(f"Fetching column metadata for tables: {table_list}")
        
        table_names = "','".join(table_list)
        query = f"""
            SELECT 
                COLUMN_NAME, DATA_TYPE 
            FROM 
                INFORMATION_SCHEMA.COLUMNS 
            WHERE 
                TABLE_NAME IN ('{table_names}');
        """
        
        db.execute(query)
        result = db.fetchall()

        columns = [row['COLUMN_NAME'] for row in result]
        
        J.info(f"Retrieved columns for {table_list}: {columns}")
        return columns
    except Exception as e:
        J.error(f"Unexpected error getting columns from {table_list}: {e}")
        return []

# Execute the SQL query on the server
def execute_sql_query(sql_query, db: Session = get_connect_db()):
    try:
        J.info(f"Executing SQL query: {sql_query}")
        
        db.execute(sql_query)
        result = db.fetchall()
        if len(result)== 0:
            J.info(f"Query executed failed, rows returned: {len(result)}")
            return False
        J.info(f"Query executed successfully, rows returned: {len(result)}")
        return result
        
    except Exception as e:
        J.error(f"Unexpected error executing SQL query: {e}")
        return False