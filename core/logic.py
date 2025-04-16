import re
import json
import openai
import pyodbc
from core.config import OPENAI_API_KEY, SERVER, DATABASE_NAME, USERNAME, PASSWORD, MODEL
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import core.logger as J
from bd.querys import execute_sql_query, get_context, get_database_structure
from utils.prompts import prompt_human, prompt_query, prompt_table

class SQLAssistant:
    def __init__(self):
        # Initialize the language model using OpenAI API
        self.llm = ChatOpenAI(model=MODEL, openai_api_key=OPENAI_API_KEY)
        
        # Create a prompt template for generating SQL queries based on user input
        self.response_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert assistant in SQL and ERP.
            Respond with natural language and provide a specific SQL query for SQL Server as the response,
            using the provided column names list to create the correct query.
            Do not include any additional text or explanations in the SQL query."""),  
            ("human", "{input}")  
        ])
        
        # Fetch the complete structure of the database at initialization
        get_database_structure()

    # Function to obtain the relevant table for a client's question
    def ask_llm_for_table(self, question: str) -> str:
        try:
            with open(r'evals\tablas.json', 'r') as j:
                # Load the table data from a JSON file
                pdf_tablas = json.load(j)
                # Generate the prompt for the language model
                prompt = prompt_table(pdf_tablas, question)

                table = ""
                while not table:
                    # Request the LLM (Language Model) for a table name
                    response = self.llm.invoke(prompt)
                    table = response.content.strip()
                    print(table)  # Log the result for debugging
                    return table
        except Exception as e:
            J.error(f"Error when querying the LLM: {e}")
            return 'None'  # Return 'None' in case of error
    
    # Function to process a question and generate a response in the form of an SQL query
    def process_q(self, question: str, clientNif:str) -> str:
        # Identify the most relevant table for the question
        selected_table = self.ask_llm_for_table(question)
        if not selected_table:
            return "The table could not be determined."
       
        # Retrieve the column names for the selected table
        column_names = get_context(selected_table)
        if not column_names:
            return f"Something went wrong, please try again."
        
        # Load the table data from the JSON file again for the detailed prompt
        with open(r'evals\tablas.json', 'r') as j:
            tables = json.load(j)
        
            # Generate a detailed prompt for SQL query creation
            prompt = prompt_query(tables, question, selected_table, column_names, clientNif)
            
        # Generate the SQL query using the language model
        response = self.llm.invoke(self.response_prompt.format(input=prompt))
        response_text = response.content
        J.info(f"LLM Answer: {response_text}")
        
        # Extract the SQL query using a regular expression
        sql_pattern = r"(?:```sql\s*)?(SELECT .*?)(?:```)?$"
        match = re.search(sql_pattern, response_text, re.DOTALL | re.IGNORECASE)

        if match:
            sql_query = match.group(1)  # Get the SQL query from the matched result
            
            # Check if the query contains dangerous SQL keywords
            dangerous_keywords = [
                'DROP', 'DELETE', 'ALTER', 'REMOVE', 'TRUNCATE', 'RECEIVE', 'REFERENCES',
                'UPDATE', 'MERGE', 'INSERT', 'CREATE', 'EXEC', 'EXECUTE', 'GRANT',
                'REVOKE', 'BEGIN', 'COMMIT', 'ROLLBACK', 'SAVEPOINT',
            ]
            if any(keyword in sql_query.upper() for keyword in dangerous_keywords):
                return "You can't do that, only queries for data retrieval are allowed, modifications or deletions are not permitted."

            try:
                # Execute the generated SQL query
                query_result = execute_sql_query(sql_query)
                if query_result is False:
                    return 'No results found.'
                else: 
                    return SQLAssistant.transform_human(query_result).strip()  # Transform the result to human-readable format

            except Exception as e:
                return f"\n\nError executing SQL query: {e}"
        
    # Function to transform the result of a SQL query into a human-readable message
    def transform_human(lenguaje_json):
        try:
            J.info("Transforming JSON result into human-readable format")
            
            openai.api_key = OPENAI_API_KEY  # Set OpenAI API key for transformation
            
            prompt = prompt_human(lenguaje_json)  # Generate prompt for transformation

            # Request transformation using OpenAI model (e.g., GPT-4)
            answer = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages = [
                    {"role": "system", "content": "You are an expert assistant in databases that understands SQL queries and transforms them into a human-readable format."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4096,  # Max token limit for the model (higher = more content)
                temperature=0.2  # Temperature setting for response randomness (lower is more predictable)
            )
            J.info("Transformation to human-readable format successful")
            return answer.choices[0].message.content
        except Exception as e:
            J.error(f"Error in transforming JSON to human-readable format: {e}")
            return "Oops, something went wrong, please try again by rephrasing your request, I don't understand.."
