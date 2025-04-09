from decimal import Decimal
import json
import time
from bd.conn import get_connect_db
from sqlalchemy.orm import Session
from core.config import OPENAI_API_KEY
import openai
import core.logger as J
import datetime

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

# Transforms the result of the SQL query and develops it into a message to make it clearer
def transform_human(lenguaje_json):
    try:
        J.info("Transforming JSON result into human-readable format")
        
        openai.api_key = OPENAI_API_KEY 
        
        try:
            lenguaje_json_str = json.dumps(lenguaje_json, default=convert_decimals)
        except Exception as e:
            J.error(f"Error serializing JSON: {e}")
            return "There was a problem processing the data."
        default_text = "None."
        greeting = "Hola, ¿en qué puedo ayudarte?"
        prompt = (
            f"You are a smart virtual customer service assistant working for SQL.\n"
            f"You are an expert in SQL. Your goal is to provide the following data '{lenguaje_json_str}'"
            f"If they give you a very long answer, take the most relevant data and that's it.\n"
            f"so that someone who doesn't know how to read JSON can understand the result. "
            f"do not add unnecessary text, answer in Spanish. If they don't give you anything that makes sense, don't hurt anything.\n"
            f"Answer with all the information you can, but don't add anything that doesn't make sense.\n"
            f"Check to avoid sending duplicate data unless asked to do so"
            f"##IMPORTANT##\n"
            f"Do not add any additional text or explanations within the SQL query.\n"
            f"##IMPORTANT##\n"
            f"ADD ALL THE DATA FROM THE JSON '{lenguaje_json_str}'.\n"
            f"##IMPORTANT##\n"
            f"Don't give it in table format, give it as a list"
            f"You will have a default text for when you can't find a field, or they send you nonsense, random words, etc. '{default_text}'"
            f"Max 65.536 caracteres"
            f"##IMPORTANT##\n"
            f"If the message they sent you is a greeting, reply with the text '{greeting}'\n"
            f"##IMPORTANT##\n"
            f"If you are given a field that is repeated many times, show it once and no more, for example a name, an id..."
        )
        answer = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages = [
                {"role": "system", "content": "You are an expert assistant in databases who understands SQL queries and transforms them so that the results of the queries are understandable to a human who has no knowledge of JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4096, #The more tokens we put in, the more it will consume, but the better the response would be.
            temperature=0.2 # The temperature is the randomness of the response, the lower the value, the more predictable the response will be.
        )
        J.info("Transformation to human-readable format successful")
        return answer.choices[0].message.content
    except Exception as e:
        J.error(f"Error in transforming JSON to human-readable format: {e}")
        return "Oops, something went wrong, please try again by rephrasing your request, I don't understand.."

# To avoid errors when converting it to JSON, we change the data types.
def convert_decimals(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    return str(obj)
