from core.config import OPENAI_API_KEY, SERVER, DATABASE_NAME, USERNAME, PASSWORD, MODEL
import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
import pyodbc
import urllib
from typing import List
import re
import json


with open(r'C:\Users\usuario\Documents\code\multi-agent\evals\eval_cases\db_schema.json', 'r') as j:
    db_context = json.load(j)

class AppLogic:
    def __init__(self):
        self.llm = ChatOpenAI(model=MODEL)
        self.response_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", """Eres un asistente experto en SQL y ERP. 
                Responde en lenguaje natural y proporciona una consulta para SQL Server específica para la respuesta, utiliza la lista de nombres de columnas que se te proporciona para elaborar la consulta correcta.
                No incluyas texto adicional o explicaciones dentro de la consulta SQL."""),
                ("human", "{input}")
            ]
        )
        self.conversacion_contexto = []
        self.db = self.connect_to_db()
        self.table_names = ['__CLIENTES', '__PROVEED', 'ARTICULO', 'COBROS']

    def get_context(self, table):
        try:
            query = f"""
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = '{table}';
            """
            result = self.db.run(query)
            return result
        except Exception as e:
            print('Error inesperado', e)
            return ''
        
    def ask_llm_for_table(self, user_input: str) -> str:
        prompt = f"""
        Eres un asistente que ayuda a identificar tablas en una base de datos SQL.
        Esta es la informacion relevante de la base de datos: {db_context}
        Basándote en la siguiente descripción, indica el nombre de la tabla más relevante:
        Descripción del usuario: "{user_input}"
        Responde con el nombre de la tabla, no escribas texto extra, solamente el nombre de la tabla correctamente ern base al contexto que te he pasado.
        """
        response = self.llm.invoke(prompt)
        return response.content.strip()

    def process_q(self,  question: str) -> str:
        selected_table = self.ask_llm_for_table(question)
        column_names = self.get_context(selected_table)

        formatted_prompt = f"Elabora la consulta para la tabla {selected_table}\nUtiliza las siguientes olumnas de la tabla, no inventes ninguna. Utiliza * para consultas que no especifiquen columnas. Hay columnas como los codigos que tendras que usar ltrim por que contienen espacios\n{column_names}\nPregunta del usuario: {question}"
        
        response = self.llm.invoke(self.response_prompt.format(input=formatted_prompt))
        response_text = response.content
        print(response_text)

        sql_pattern = r"```sql\s*(SELECT .*?)```"
        match = re.search(sql_pattern, response_text, re.DOTALL)

        if match:
            sql_query = match.group(1).strip()  # Solo el SQL
            try:
                resultado_consulta = self.db.run(sql_query)
                consulta_con_resultado = f"Esto es el resultado de una consulta:\n{resultado_consulta}\n Presenta estos resultados de forma atractiva en una lista. Limitate a presentarlos, no digas nada adicional"
                response_with_results = self.llm.invoke(input=consulta_con_resultado)
                
                return response_with_results.content
            except Exception as e:
                return f"\n\nError al ejecutar la consulta SQL: {e}"
        else:
            return "\n\nNo se encontró una consulta SQL en la respuesta."

