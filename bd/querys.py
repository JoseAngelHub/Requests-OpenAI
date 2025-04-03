from decimal import Decimal
import json
from bd.conn import get_connect_db
from sqlalchemy.orm import Session
from core.config import OPENAI_API_KEY
import openai

# We take the data from the table that is passed to us
def get_context(table, db: Session = get_connect_db()):
    try:
    # Query to get column metadata from INFORMATION_SCHEMA
        query = f"""SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table}';"""
        
        db.execute(query)
        result = db.fetchall()

        # Extract only the column names
        columns = [row['COLUMN_NAME'] for row in result]
        
        return columns
    except Exception as e:
        print(f"Unexpected error getting columns from {table}: {e}")
        return []

# Execute the SQL query on the server
def execute_sql_query(sql_query, db: Session = get_connect_db()):
    try:
        # Execute the SQL query in the database
        db.execute(sql_query)
        
        # Gets all the results of the query
        result = db.fetchall()
        
        return result
    except Exception as e:
        print(f"Unexpected error executing SQL query: {e}")
        return None
    
def verify_user(api_secret: str):
    query =f"SELECT API_SECRET FROM AUTH_TOKEN WHERE API_SECRET ='{api_secret}';"
    db = get_connect_db()
    db.execute(query)
    result = db.fetchall()
    sql = [row['API_SECRET'] for row in result if row['API_SECRET']]
    print(", ".join(sql))
    

# Transforms the query result into a json
def return_json(result):
    # Converts results to JSON
    json_result = json.dumps([dict((k, convert_decimals(v)) for k, v in row.items()) for row in result], indent=4)
    
    return json_result

# Transforms the result of the SQL query and develops it into a message to make it clearer
def transform_human(lenguaje_json):
    openai.api_key = OPENAI_API_KEY 
    lenguaje_json = json.dumps(lenguaje_json, default=convert_decimals)
    prompt = (
    f"You are a smart virtual customer service assistant working for SQL.\n"
    f"You are an expert in SQL. Your goal is to provide the following data '{lenguaje_json}'"
    f"so that someone who doesn't know how to read JSON can understand the result. "
    f"Provide the result in a format that is readable, do not add line breaks. Keep in mind that the result you provide will be seen on WhatsApp,\n"
    f"do not add unnecessary text, and if you cannot provide a coherent response, reply with \n"
    f"'Ups, algo salió mal, por favor inténtalo de nuevo reformulando tu solicitud, no lo entiendo. :)'"
)
    
    answer = openai.chat.completions.create(
        model="gpt-4o-mini",  # Language model used
        messages = [
            {"role": "system", "content": "You are an expert assistant in databases who understands SQL queries and transforms them so that the results of the queries are understandable to a human who has no knowledge of JSON"},
            {"role": "user", "content": prompt}
        ],
        max_tokens=100,  # Response token limit
        temperature=0  # Configuration for more deterministic responses
    )
    return answer.choices[0].message.content
    
# To avoid errors when converting it to JSON, we change the data types.
def convert_decimals(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    return obj
      