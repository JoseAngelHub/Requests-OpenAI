import os
import re
import json
from fastapi import HTTPException
import pyodbc
from bd import conn
from core.config import OPENAI_API_KEY, SERVER, DATABASE_NAME, USERNAME, PASSWORD, MODEL
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from bd.querys import execute_sql_query, get_context, transform_human
import core.logger as R

class SQLAssistant:
    def __init__(self):
        # Initialize the language model with OpenAI
        self.llm = ChatOpenAI(model=MODEL, openai_api_key=OPENAI_API_KEY)
        
        # Create a prompt template with instructions for generating SQL queries
        self.response_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert assistant in SQL and ERP. 
            Respond in natural language and provide a specific SQL query for SQL Server for the answer, 
            using the list of column names provided to create the correct query. 
            Do not include additional text or explanations within the SQL query."""), 
            ("human", "{input}")
        ])

        # Gets the complete structure of the database
        self.db_context = self.get_database_structure()

    def get_database_structure(self):
        structure = {}
        try:
            conn = pyodbc.connect(
                f"DRIVER={{SQL Server}};SERVER={SERVER};DATABASE={DATABASE_NAME};UID={USERNAME};PWD={PASSWORD}"
            )
            cursor = conn.cursor()

            # Get all table names
            cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='VIEW'")
            tablas = [row[0] for row in cursor.fetchall()]

            # For each table, get its columns
            for tabla in tablas:
                cursor.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{tabla}'")
                columns = [row[0] for row in cursor.fetchall()]
                structure[tabla] = columns

            cursor.close()
            conn.close()

        except Exception as e:
            # Log any errors in obtaining the structure
            R.error(f"Error getting database structure: {e}")

        return structure

    # Obtain the table according to the client's request
    def ask_llm_for_table(self, question: str) -> str:
        try:
            prompt = f"""
               You are an assistant responsible for identifying the correct table in an SQL database based on the columns it contains. 
                This is the relevant information from the database: {self.db_context}.
                You must give tables that make sense with the columns; do not invent columns or tables. Avoid errors in case a query is executed with this table, as it may result in 'Invalid column name' if not done correctly.
                Your task is to determine which table coherently and accurately groups the fields requested in the user's description. Keep in mind that there may be multiple tables that contain one or some of the fields, but you should select the table that offers exactly what is requested.

                Steps to follow:
                1. Review all available tables in the database.
                2. Analyze the columns of each table and verify if they contain the fields mentioned in the description, particularly "clave", "contacto", and "moneda".
                3. If there are multiple tables with some of these fields, choose the one that includes the complete combination of the required fields and logically links them.
                4. Prioritize the table that offers a complete and exact set of the requested fields, without unnecessary extra information.

                Examples:
                - If the description mentions "contacto", "clave", and "moneda", select the table that contains all three fields instead of a table with only two of them.
                - If there are tables that contain "clave" and "contacto" but not "moneda", they are not valid if the description explicitly requires all three fields.

                Use the following description to identify the corresponding table:
                The user has written the following: "{question}", search in the database structure for the table, there can only be one correct table.
                Respond only with the name of the table that contains exactly the requested fields, without adding any additional text.

                """
                # Invokes the language model to obtain the table
            table = ""
            while not table:
                response = self.llm.invoke(prompt)
                table = response.content.strip()
                return table
        except Exception as e:
            R.error(f"Error when querying the LLM: {e}")
            return ''
    
    def process_q(self, question: str) -> str:
        # Identify the most relevant table for the question
        selected_table = self.ask_llm_for_table(question)
        print(selected_table)
        if not selected_table:
            return "The table could not be determined."

        # Gets the columns of the table
        column_names = get_context(selected_table)
        if not column_names:
            return f"No columns found for the table {selected_table}."

        # Detailed prompt to generate the SQL query
        formatted_prompt = (
            f"Create the query for the table {selected_table}\n"
            f"Use the following columns from the table, do not invent any. "
            f"Use * for queries that do not specify columns. "
            f"There are columns like codes that you'll need to use LTRIM for because they contain spaces.\n"
            f"{column_names}\n"
            f"In case some column may not have a name, give it a descriptive one, the columns must exist in the database '{self.db_context}'"
            f"User's question: {question}"
        )
        
        # Generates the SQL query using the language model
        response = self.llm.invoke(self.response_prompt.format(input=formatted_prompt))
        response_text = response.content
        R.info(f"LLM Answer: {response_text}")
        
        # Extract the SQL query using a regular expression
        sql_pattern = r"```sql\s*(SELECT .*?)```"
        match = re.search(sql_pattern, response_text, re.DOTALL)
        if match:
            sql_query = match.group(1).strip()
            try:
                # Execute the SQL query
                query_result = execute_sql_query(sql_query)
                
                cordial = "Esta es la respuesta esperada? En caso de que no lo sea proporcioname más información"
                return transform_human(query_result) + "\n"+cordial

            except Exception as e:
                return f"\n\nError executing SQL query: {e}"
        else:
            return "\n\nNo SQL query was found in the response."
        
    # User login by phone
    def login_user(self, phone:str):
        try:
            conn = pyodbc.connect(
                f"DRIVER={{SQL Server}};SERVER={SERVER};DATABASE={DATABASE_NAME};UID={USERNAME};PWD={PASSWORD}"
            )
            cursor = conn.cursor()
            # We take the user from the clients table that has the phone number with which the request was made
            query= "SELECT USUARIO FROM CLIENTES WHERE TELCLI='"+phone+"'"
            cursor.execute(query)
            result = cursor.fetchall()
            if result:
                # We return true so that the endpoint can advance and do the process_q
                return True
            else:
                # False is returned so that it does not continue and does not consume the OPENAI request.
                raise ValueError("Something has not gone as we expected")
            
        except Exception as e:
            R.error(f"Error verifying user: {str(e)}")
            return False
        except ValueError as e:
            R.error(f"User not found error: {str(e)}")
            return False
    
    def get_user(self, nombre:str, password:str):
        query=f"""SELECT NOMBRE, PASSWD FROM USERS WHERE NOMBRE = '{nombre}' AND PASSWD='{password}'"""
        db = conn.get_connect_db()
        db.execute(query)
        result = db.fetchall()
        print(result)
        if len(result)==0:
            return False
        else:
            return True