import os
import re
import json
import pyodbc
from core.config import OPENAI_API_KEY, SERVER, DATABASE_NAME, USERNAME, PASSWORD, MODEL
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from bd.querys import ejecutar_consulta_sql, get_context
import core.logger as R

class SQLAssistant:
    def __init__(self):
        """
        Inicializa el asistente SQL con un modelo de lenguaje y un prompt de respuesta.
        
        - Configura ChatOpenAI con el modelo y clave API especificados
        - Crea una plantilla de prompt para generar respuestas con contexto SQL
        - Obtiene la estructura de la base de datos
        """
        # Inicializa el modelo de lenguaje con OpenAI
        self.llm = ChatOpenAI(model=MODEL, openai_api_key=OPENAI_API_KEY)
        
        # Crea una plantilla de prompt con instrucciones para generar consultas SQL
        self.response_prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres un asistente experto en SQL y ERP. 
            Responde en lenguaje natural y proporciona una consulta para SQL Server especifica para la respuesta, 
            utiliza la lista de nombres de columnas que se te proporciona para elaborar la consulta correcta.
            No incluyas texto adicional o explicaciones dentro de la consulta SQL."""), 
            ("human", "{input}")
        ])
        
        # Obtiene la estructura completa de la base de datos
        self.db_context = self.get_database_structure()

    def get_database_structure(self):
        """
        Obtiene la estructura completa de la base de datos.
        
        - Conecta a la base de datos SQL Server
        - Recupera todos los nombres de tablas
        - Para cada tabla, obtiene sus columnas
        - Guarda la estructura en un archivo JSON
        
        Returns:
            dict: Diccionario con tablas y sus columnas
        """
        estructura = {}
        try:
            # Establece conexion con la base de datos usando parametros de configuracion
            conn = pyodbc.connect(
                f"DRIVER={{SQL Server}};SERVER={SERVER};DATABASE={DATABASE_NAME};UID={USERNAME};PWD={PASSWORD}"
            )
            cursor = conn.cursor()

            # Obtiene todos los nombres de tablas
            cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'")
            tablas = [row[0] for row in cursor.fetchall()]

            # Para cada tabla, obtiene sus columnas
            for tabla in tablas:
                cursor.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{tabla}'")
                columnas = [row[0] for row in cursor.fetchall()]
                estructura[tabla] = columnas

            cursor.close()
            conn.close()

            # Guarda la estructura de la base de datos en un archivo JSON
            with open(r'C:\Users\usuario\Desktop\langchain_sql\col.json', 'w') as j:
                json.dump(estructura, j, indent=4)

        except Exception as e:
            # Registra cualquier error en la obtencion de la estructura
            R.error(f"Error al obtener la estructura de la base de datos: {e}")

        return estructura

    def ask_llm_for_table(self, question: str) -> str:
        """
        Identifica la tabla mas relevante para una pregunta dada.
        
        Args:
            question (str): Pregunta del usuario
        
        Returns:
            str: Nombre de la tabla mas relevante
        """
        try:
            # Crea un prompt para identificar la tabla basandose en la descripcion
            prompt = f"""
            Eres un asistente que ayuda a identificar tablas en una base de datos SQL.
            Esta es la informacion relevante de la base de datos: {self.db_context}
            Basandote en la siguiente descripcion, indica el nombre de la tabla mas relevante:
            Descripcion del usuario: "{question}"
            Responde con el nombre de la tabla, no escribas texto extra, solamente el nombre de la tabla correctamente en base al contexto que te he pasado.
            """
            # Invoca al modelo de lenguaje para obtener la tabla
            response = self.llm.invoke(prompt)
            return response.content.strip()
        except Exception as e:
            # Registra cualquier error en la consulta al LLM
            R.error(f"Error al realizar la consulta al LLM: {e}")
            return ''

    def process_q(self, question: str) -> str:
        """
        Procesa una pregunta del usuario, generando y ejecutando una consulta SQL.
        
        Args:
            question (str): Pregunta del usuario
        
        Returns:
            str: Resultado de la consulta o mensaje de error
        """
        
        # Identifica la tabla mas relevante para la pregunta
        selected_table = self.ask_llm_for_table(question)
        print(selected_table)
        if not selected_table:
            return "No se pudo determinar la tabla."

        # Obtiene las columnas de la tabla
        column_names = get_context(selected_table)
        if not column_names:
            return f"No se encontraron columnas para la tabla {selected_table}."

        # Prepara un prompt detallado para generar la consulta SQL
        formatted_prompt = (
            f"Elabora la consulta para la tabla {selected_table}\n"
            f"Utiliza las siguientes columnas de la tabla, no inventes ninguna. "
            f"Utiliza * para consultas que no especifiquen columnas. "
            f"Hay columnas como los codigos que tendras que usar ltrim porque contienen espacios.\n"
            f"{column_names}\n"
            f"Pregunta del usuario: {question}"
        )
        
        # Genera la consulta SQL usando el modelo de lenguaje
        response = self.llm.invoke(self.response_prompt.format(input=formatted_prompt))
        response_text = response.content
        R.info(f"Respuesta LLM: {response_text}")
        
        # Extrae la consulta SQL usando una expresion regular
        sql_pattern = r"```sql\s*(SELECT .*?)```"
        match = re.search(sql_pattern, response_text, re.DOTALL)
        if match:
            sql_query = match.group(1).strip()
            try:
                # Ejecuta la consulta SQL
                resultado_consulta = ejecutar_consulta_sql(sql_query)
                
                # Leer el historial de consultas desde el JSON (si existe)
                json_path = r'C:\Users\usuario\Desktop\langchain_sql\consultas.json'
                if os.path.exists(json_path):
                    try:
                        with open(json_path, 'r', encoding='utf-8') as j:
                            consultas = json.load(j)
                    except json.JSONDecodeError:
                        consultas = []
                else:
                    consultas = []

                # Guardar consulta y resultado en el historial
                consulta_info = {
                    "consulta": sql_query,
                    "respuesta": resultado_consulta
                }
                consultas.append(consulta_info)
                
                # Guarda el historial de consultas
                with open(json_path, 'w', encoding='utf-8') as j:
                    json.dump(consultas, j, indent=4, ensure_ascii=False)
                
                return resultado_consulta

            except Exception as e:
                return f"\n\nError al ejecutar la consulta SQL: {e}"
        else:
            return "\n\nNo se encontro una consulta SQL en la respuesta."