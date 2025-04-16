import re
import json
import openai
import pyodbc
from core.config import OPENAI_API_KEY, SERVER, DATABASE_NAME, USERNAME, PASSWORD, MODEL
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import core.logger as J
from core.utils import execute_sql_query, get_context
from prompts import prompt_human, prompt_query, prompt_table

class SQLAssistant:
    def __init__(self):
        # Initialize the language model with OpenAI
        self.llm = ChatOpenAI(model=MODEL, openai_api_key=OPENAI_API_KEY)
        
        # Create a prompt template with instructions for generating SQL queries
        self.response_prompt = ChatPromptTemplate.from_messages([
        ("system", """Eres un asistente experto en SQL y ERP.
        Responde con lenguaje natural y proporciona una consulta SQL específica para SQL Server como respuesta,
        utilizando la lista de nombres de columna proporcionada para crear la consulta correcta.
        No incluyas texto adicional ni explicaciones en la consulta SQL."""),  
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
                prompt = prompt_table(pdf_tablas, question)

                table = ""
                while not table:
                    response = self.llm.invoke(prompt)
                    table = response.content.strip()
                    print(table)
                    return table
        except Exception as e:
            J.error(f"Error when querying the LLM: {e}")
            return 'None'
    
    def process_q(self, question: str, clientNif:str) -> str:
        # Identify the most relevant table for the question
        selected_table = self.ask_llm_for_table(question)
        if not selected_table:
            return "The table could not be determined."
       
        # Gets the columns of the table
        column_names = get_context(selected_table)
        if not column_names:
            return f"Algo no ha funcionado, prueba a repetirlo de nuevo, por favor."
        # Detailed prompt to generate the SQL query
        with open(r'tablas.json', 'r') as j:
            tables = json.load(j)
        
            prompt = prompt_query(tables, question, selected_table, column_names, clientNif)
            
        # Generates the SQL query using the language model
        response = self.llm.invoke(self.response_prompt.format(input=prompt))
        response_text = response.content
        J.info(f"LLM Answer: {response_text}")
        
        # Extract the SQL query using a regular expression
        sql_pattern = r"(?:```sql\s*)?(SELECT .*?)(?:```)?$"
        match = re.search(sql_pattern, response_text, re.DOTALL | re.IGNORECASE)

        if match:
            sql_query = match.group(1)
            # We check that no changes are made to the database

            dangerous_keywords = [
                'DROP', 'DELETE', 'ALTER', 'REMOVE', 'TRUNCATE', 'RECEIVE', 'REFERENCES'
                'UPDATE', 'MERGE', 'INSERT', 'CREATE', 'EXEC', 'EXECUTE', 'GRANT',
                'REVOKE', 'BEGIN', 'COMMIT', 'ROLLBACK', 'SAVEPOINT',
                
            ]
            if any(keyword in sql_query.upper() for keyword in dangerous_keywords):
                return "No puedes hacer eso, solo puedes consultar datos, no puedes modificarlos ni eliminarlos."

            try:
                # Execute the SQL query
                query_result = execute_sql_query(sql_query)
                if query_result is False:
                    return 'No hemos encontrado nada'
                else: 
                    return SQLAssistant.transform_human(query_result).strip()

            except Exception as e:
                return f"\n\nError executing SQL query: {e}"
        
    # Transforms the result of the SQL query and develops it into a message to make it clearer
    def transform_human(lenguaje_json):
        try:
            J.info("Transforming JSON result into human-readable format")
            
            openai.api_key = OPENAI_API_KEY 
            
           
            prompt = prompt_human(lenguaje_json)

            answer = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages = [
                    {"role": "system", "content": "Eres un asistente experto en bases de datos que entiende las consultas SQL y las transforma para que los resultados de las consultas sean comprensibles para un humano que no tiene conocimientos de JSON."},
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