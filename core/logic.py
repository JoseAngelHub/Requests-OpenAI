import os
import re
import json
import pyodbc
from core.config import OPENAI_API_KEY, SERVER, DATABASE_NAME, USERNAME, PASSWORD, MODEL
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from bd.querys import ejecutar_consulta_sql, get_context, transformar_humano
import core.logger as R

class SQLAssistant:
    def __init__(self):
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
        estructura = {}
        try:
            conn = pyodbc.connect(
                f"DRIVER={{SQL Server}};SERVER={SERVER};DATABASE={DATABASE_NAME};UID={USERNAME};PWD={PASSWORD}"
            )
            cursor = conn.cursor()

            # Obtiene todos los nombres de tablas
            cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='VIEW'")
            tablas = [row[0] for row in cursor.fetchall()]

            # Para cada tabla, obtiene sus columnas
            for tabla in tablas:
                cursor.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{tabla}'")
                columnas = [row[0] for row in cursor.fetchall()]
                estructura[tabla] = columnas

            cursor.close()
            conn.close()

        except Exception as e:
            # Registra cualquier error en la obtencion de la estructura
            R.error(f"Error al obtener la estructura de la base de datos: {e}")

        return estructura

    #Obtener la tabla acorde a la peticion del cliente
    def ask_llm_for_table(self, question: str) -> str:
        try:
            prompt = f"""
                Eres un asistente encargado de identificar la tabla correcta en una base de datos SQL basándote en las columnas que ésta contiene.
                Esta es la información relevante de la base de datos: {self.db_context}.
                Tienes que dar tablas que tengan sentido con las columnas, no inventes columnas ni tablas. Que no de errores en casso de querer ejecutar una consulta con esta tabla, ya que puede dar 'Invalid column name' si no lo haces bien
                Tu tarea es determinar cuál es la tabla que agrupa de forma coherente y exacta los campos solicitados en la descripción del usuario. Ten en cuenta que pueden existir varias tablas que contengan uno o algunos de los campos, pero debes seleccionar la tabla que ofrezca exactamente lo que se pide.

                Pasos a seguir:
                1. Revisa todas las tablas disponibles en la base de datos.
                2. Analiza las columnas de cada tabla y verifica si contienen los campos mencionados en la descripción, en particular "clave", "contacto" y "moneda".
                3. Si existen varias tablas con alguno de estos campos, elige aquella que incluya la combinación completa de los campos requeridos y que estén lógicamente vinculados.
                4. Prioriza la tabla que ofrezca un conjunto completo y exacto de los campos solicitados, sin información extra innecesaria.

                Ejemplos:
                - Si la descripción menciona "contacto", "clave" y "moneda", selecciona la tabla que contenga los tres campos en lugar de una tabla que tenga solo dos de ellos.
                - Si hay tablas que contienen "clave" y "contacto" pero no "moneda", no son válidas si la descripción requiere explícitamente los tres campos.

                Utiliza la siguiente descripción para identificar la tabla correspondiente:
                El usuario nos ha escrito lo siguiente: "{question}", busca en la estructura de la base de datos la tabla, solo puede haber una tabla correcta
                Responde únicamente con el nombre de la tabla que contiene exactamente los campos solicitados, sin agregar texto adicional.
                """
                # Invoca al modelo de lenguaje para obtener la tabla
            tablas = ""
            while not tablas:
                response = self.llm.invoke(prompt)
                tablas = response.content.strip()
                return tablas
        except Exception as e:
            R.error(f"Error al realizar la consulta al LLM: {e}")
            return ''
    
    def process_q(self, question: str) -> str:
        # Identifica la tabla mas relevante para la pregunta
        selected_table = self.ask_llm_for_table(question)
        print(selected_table)
        if not selected_table:
            return "No se pudo determinar la tabla."

        # Obtiene las columnas de la tabla
        column_names = get_context(selected_table)
        if not column_names:
            return f"No se encontraron columnas para la tabla {selected_table}."

        # Prompt detallado para generar la consulta SQL
        formatted_prompt = (
            f"Elabora la consulta para la tabla {selected_table}\n"
            f"Utiliza las siguientes columnas de la tabla, no inventes ninguna. "
            f"Utiliza * para consultas que no especifiquen columnas. "
            f"Hay columnas como los codigos que tendras que usar ltrim porque contienen espacios.\n"
            f"{column_names}\n"
            f"En caso de que puede que no tenga nombre de columna ponle uno descriptivo, tienen que existir las columnas en la base de datos '{self.db_context}'"
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
                # print(resultado_consulta)
                # print(transformar_humano(resultado_consulta))
                cordial = "Esta es la respuesta esperada? En caso de que no lo sea proporcioname más información"
                return transformar_humano(resultado_consulta) + "\n"+cordial

            except Exception as e:
                return f"\n\nError al ejecutar la consulta SQL: {e}"
        else:
            return "\n\nNo se encontro una consulta SQL en la respuesta."
        
    #Login del usuario por el telefono
    def login_user(phone):
        try:
            conn = pyodbc.connect(
                f"DRIVER={{SQL Server}};SERVER={SERVER};DATABASE={DATABASE_NAME};UID={USERNAME};PWD={PASSWORD}"
            )
            cursor = conn.cursor()
            # Cogemos el usuario de la tabla clientes que tenga el numero de telefono con el que se ha hecho la peticion
            query= "SELECT USUARIO FROM CLIENTES WHERE TELCLI='"+phone+"'"
            cursor.execute(query)
            result = cursor.fetchall()
            if result:
                #Devolvemos true para que en el endpoint avance y pueda hacer el proces_q
                return True
            else:
                # Se devuelve false para que no siga y no consuma peticion de OPENAI
                raise ValueError("HA PETAO")
            
        except Exception as e:
            R.error(f"Error verificando usuario: {str(e)}")
            return False
        except ValueError as e:
            R.error(f"Error usuario no encontrado: {str(e)}")
            return False
        