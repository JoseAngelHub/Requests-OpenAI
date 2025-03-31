import json
import sqlite3

import unidecode
from bd.conn import get_connect_db
from core.logger import setup_logger
from sqlalchemy.orm import Session
from datetime import datetime
from core.config import OPENAI_API_KEY
import core.logger as R
import openai

def get_context(table, db: Session = get_connect_db()):
    """
    Obtiene la informacion de las columnas de una tabla especifica.
    
    Args:
        table (str): Nombre de la tabla a consultar
        db (Session, optional): Sesion de base de datos. Por defecto usa get_connect_db()
    
    Returns:
        list: Lista de nombres de columnas de la tabla
    """
    try:
        # Consulta para obtener metadatos de columnas desde INFORMATION_SCHEMA
        query = f"""
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = '{table}';
        """
        
        db.execute(query)
        result = db.fetchall()
 
        # Extrae solo los nombres de las columnas
        columns = [row['COLUMN_NAME'] for row in result] 
        print(f"Columnas encontradas para {table}: {columns}")  
        return columns
    except Exception as e:
        # Manejo de errores si falla la obtencion de columnas
        print(f"Error inesperado obteniendo columnas de {table}: {e}")
        return []
    
def obtener_consulta_sql(texto_usuario):
    """
    Convierte texto de usuario en una consulta SQL utilizando OpenAI.
    
    Args:
        texto_usuario (str): Solicitud en lenguaje natural
    
    Returns:
        Respuesta de OpenAI con la consulta SQL generada
    """
    # Configura la clave de API de OpenAI
    openai.api_key = OPENAI_API_KEY 
    
    # Carga informacion de tablas desde un archivo JSON
    tablas = json.load(open(r'C:\Users\usuario\Desktop\langchain_sql\tablas.json'))
    
    # Construye un prompt para OpenAI para generar consulta SQL
    prompt = f"Convierte la siguiente solicitud en una consulta SQL valida para SQL server: '{texto_usuario}', van a ser preguntas relacionadas con la tabla clientes, aqui tienes informacion sobre la tabla clientes: '{tablas}' no utilices texto adicional o explicaciones dentro de la consulta SQL."
    
    # Llama a la API de OpenAI para generar la consulta
    respuesta = openai.chat.completions.create(
        model="gpt-4o-mini",  # Modelo de lenguaje utilizado
        messages=[
            {"role": "system", "content": "Eres un asistente experto en bases de datos que hace consultas SQL."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=100,  # Limite de tokens de respuesta 
        temperature=0  # Configuracion para respuestas mas deterministicas
    )
    return respuesta

def ejecutar_consulta_sql(sql_query, db: Session = get_connect_db()):
    """
    Ejecuta una consulta SQL en la base de datos.
    
    Args:
        sql_query (str): Consulta SQL a ejecutar
        db (Session, optional): Sesion de base de datos. Por defecto usa get_connect_db()
    
    Returns:
        list or None: Resultados de la consulta o None si hay un error
    """
    try:
        # Ejecuta la consulta SQL en la base de datos
        db.execute(sql_query)
        
        # Obtiene todos los resultados de la consulta
        result = db.fetchall()
        
        print(f"Resultados de la consulta: {result}")
        devolver_json(result)  # Convierte resultados a JSON y guarda en archivo
        #formatear_json(result)  # Formatea resultados para frontend
        return result
    except Exception as e:
        # Manejo de errores si falla la ejecucion de la consulta
        print(f"Error inesperado ejecutando la consulta SQL: {e}")
        return None
    
def devolver_json(result):
    """
    Convierte los resultados de una consulta SQL a formato JSON.
    
    Args:
        result (list): Resultados de la consulta SQL
    
    Returns:
        str: Resultados en formato JSON
    """
    # Convierte los resultados a JSON
    json_result = json.dumps([dict(row) for row in result], indent=4)
    
    # Guarda el resultado en un archivo JSON
    with open(r'C:\Users\usuario\Desktop\langchain_sql\result.json', 'w', encoding='utf-8') as j:
        j.write(json_result)
    # formatted_result = json.loads(json_result)
    return json_result

# def formatear_json(result):
#     """
#     Utiliza la IA para transformar las tildes y los caracteres
#     especiales para que pueda ser utilizado en el frontend.
    
#     Args:
#         result (list): Lista de diccionarios con los resultados de la consulta SQL.
    
#     Returns:
#         str: Resultados en formato JSON con caracteres normalizados.
#     """
#     try:
#         # Normaliza los caracteres especiales en los resultados
#         formatted_result = [
#             {key: unidecode.unidecode(str(value)) if isinstance(value, str) else value for key, value in row.items()}
#             for row in result
#         ]
        
#         # Convierte a JSON con formato legible
#         json_result = json.dumps(formatted_result, indent=4, ensure_ascii=False)
        
#         return json_result
#     except Exception as e:
#         print(f"Error formateando JSON: {e}")
#         return None