import os
import re
import json
import time
from fastapi import HTTPException
import pyodbc
from bd import conn
from core.config import OPENAI_API_KEY, SERVER, DATABASE_NAME, USERNAME, PASSWORD, MODEL
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from bd.querys import execute_sql_query, get_context, transform_human
import core.logger as J

class SQLAssistant:
    def __init__(self):
        # Initialize the language model with OpenAI
        self.llm = ChatOpenAI(model=MODEL, openai_api_key=OPENAI_API_KEY)
        
        # Create a prompt template with instructions for generating SQL queries
        self.response_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert assistant in SQL and ERP.  
        Respond in natural language and provide a specific SQL query for SQL Server as the answer,  
        using the provided list of column names to create the correct query.  
        Do not include any additional text or explanations within the SQL query."""),  
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
            J.error(f"Error getting database structure: {e}")

        return structure

    # Obtain the table according to the client's request
    def ask_llm_for_table(self, question: str) -> str:
        try:
            with open(r'tablas.json', 'r') as j:
                pdf_tablas = json.load(j)
                prompt = f"""
            
                You are an assistant responsible for identifying the correct table in a SQL database based on the columns it contains.  
                This is the relevant information about the database: {pdf_tablas}.  
                Here are the data from the tables we have, which are the only ones you can use:
                You must provide the table(s) that make sense based on the columns—do not make up columns or tables.  
                Avoid errors when executing a query with this table, as it could result in 'Invalid column name' if not done properly.  

                Your task is to determine which table logically and accurately groups the fields requested in the user's description.  
                Note that there may be multiple tables containing one or some of the fields, but you must select the table that exactly meets the request.  

                Steps to follow:  
                1. Review all available tables in the database.  
                2. Analyze the columns of each table and check whether they contain the fields mentioned in the description, particularly "clave", "contacto", and "moneda".  
                3. If multiple tables have some of these fields, choose the one that includes the full combination of required fields and logically relates them.  
                4. Prioritize the table that offers a complete and exact set of the requested fields, without unnecessary additional information.  

                Examples:  
                - If the description mentions "contacto", "clave", and "moneda", select the table that contains all three fields instead of one that only has two.  
                - If there are tables containing "clave" and "contacto" but not "moneda", they are not valid if the description explicitly requires all three fields.  

                Use the following description to identify the corresponding table:  
                The user has written the following: "{question}". Search the database structure for the table, as there can be one or more correct table, if the data is relationated whit two tables return both.  
                ##IMPORTANT##
                You have to provide the tables if it is safe to do so, that is, if they ask for all the data and they may contain private data, do not provide them and respond with None.
                Respond only with the name of the table that contains exactly the requested fields, without adding any extra text. 
                "You will have a default text for when you can't find a field, or they send you nonsense, random words,random text string, etc. 'None' or If the message they sent you is a greeting, reply with the text 'None'
                """

                # Invokes the language model to obtain the table
                table = ""
                while not table:
                    response = self.llm.invoke(prompt)
                    table = response.content.strip()
                    return table
        except Exception as e:
            J.error(f"Error when querying the LLM: {e}")
            return ''
    
    def process_q(self, question: str) -> str:
        # Identify the most relevant table for the question
        selected_table = self.ask_llm_for_table(question)
        if not selected_table:
            return "The table could not be determined."

        # Gets the columns of the table
        column_names = get_context(selected_table)
        if not column_names:
            return f"Hola, ¿en qué puedo ayudarte?."
        # Detailed prompt to generate the SQL query
        with open(r'tablas.json', 'r') as j:
            tables = json.load(j)
            formatted_prompt = (
                f"Create the SQL query for the tables {selected_table} maybe you need use JOIN, here you have the tables to watch the relationated columns {tables}, varchars of length one are either F or T\n"
                f"Use the following columns from the table—do not make up any.\n"
                f"Use * for queries that do not specify columns. "
                f"There are columns such as codes where you will need to use LTRIM because they contain spaces, there are many columns dont need to use.\n"
                f"If any column does not have a name, assign it a descriptive one. \n"
                f"###IMPORTANT###\n"
                f"Control that error: Argument data type text is invalid for argument 1 of ltrim function.DB-Lib error message 20018, severity 16"
                f"Use LTRIM for the columns that need it not all\n"
                f"{column_names}\n"
                f"User question: {question}, remember that is a Client who is asking, if he ask something about his order, ask something like, give me your nif or something relationated with the data base.\n"
            )

        # Generates the SQL query using the language model
        response = self.llm.invoke(self.response_prompt.format(input=formatted_prompt))
        response_text = response.content
        J.info(f"LLM Answer: {response_text}")
        
        # Extract the SQL query using a regular expression
        sql_pattern = r"```sql\s*(SELECT .*?)```"
        match = re.search(sql_pattern, response_text, re.DOTALL)
        if match:
            sql_query = match.group(1)
            # We check that no changes are made to the database
            if 'DROP' in sql_query or 'DELETE' in sql_query or 'ALTER' in sql_query or 'REMOVE' in sql_query or 'TRUNCATE' in sql_query or 'UPDATE' in sql_query or 'MERGE' in sql_query:
                return "No puedes hacer eso, solo puedes consultar datos, no puedes modificarlos ni eliminarlos."
            try:
                # Execute the SQL query
                query_result = execute_sql_query(sql_query)
                if query_result is False:
                    empty="No he encontrado nada"
                    return empty
                else: 
                    return transform_human(query_result).strip()

            except Exception as e:
                return f"\n\nError executing SQL query: {e}"
        else:
            return "\n\nNo entiendo que quieres hacer, por favor, repitemelo con otras palabras."
        
    # User login by phone
    def login_user(self, phone:str):
        try:
            conn = pyodbc.connect(
                f"DRIVER={{SQL Server}};SERVER={SERVER};DATABASE={DATABASE_NAME};UID={USERNAME};PWD={PASSWORD}"
            )
            cursor = conn.cursor()
            # We take the user from the clients table that has the phone number with which the request was made
            query= "SELECT name_user FROM CLIENTS WHERE TELCLI='"+phone+"'"
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
    
    
    def get_user(self, nombre:str, password:str):
        query=f"""SELECT NOMBRE, PASSWD FROM USERS WHERE NOMBRE = '{nombre}' AND PASSWD='{password}'"""
        db = conn.get_connect_db()
        db.execute(query)
        result = db.fetchall()
        if len(result)==0:
            return False
        else:
            return True