from decimal import Decimal
import json
from bd.conn import get_connect_db
from sqlalchemy.orm import Session
from core.config import OPENAI_API_KEY
import openai

# Cogemos los datos de la tabla que nos pasan
def get_context(table, db: Session = get_connect_db()):
    try:
    # Consulta para obtener metadatos de columnas desde INFORMATION_SCHEMA
        query = f"""SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table}';"""
        
        db.execute(query)
        result = db.fetchall()

        # Extrae solo los nombres de las columnas
        columns = [row['COLUMN_NAME'] for row in result]
        
        return columns
    except Exception as e:
        print(f"Error inesperado obteniendo columnas de {table}: {e}")
        return []

# Ejecuta la consulta SQL en el servidor
def ejecutar_consulta_sql(sql_query, db: Session = get_connect_db()):
    try:
        # Ejecuta la consulta SQL en la base de datos
        db.execute(sql_query)
        
        # Obtiene todos los resultados de la consulta
        result = db.fetchall()
        
        devolver_json(result)  # Convierte resultados a JSON y guarda en archivo
        return result
    except Exception as e:
        print(f"Error inesperado ejecutando la consulta SQL: {e}")
        return None
    
# Transforma el resultado de la consulta a un json
def devolver_json(result):
    # Convierte los resultados a JSON
    json_result = json.dumps([dict((k, convertir_decimales(v)) for k, v in row.items()) for row in result], indent=4)
    
    return json_result

# Transforma el resultado de la consulta SQL y lo desarrolla en un mensaje para que quede mas claro
def transformar_humano(lenguaje_json):
    openai.api_key = OPENAI_API_KEY 
    lenguaje_json = json.dumps(lenguaje_json, default=convertir_decimales)
    prompt = (
        f"Eres un asistente virtual de atención al cliente inteligente que trabaja para SQL.\n"
        f"Eres un experto en SQL. Tu objetivo es dar los siguientes datos '{lenguaje_json}'"
        f"para que una persona que no sepa leer JSON pueda entender el resultado "
        f"Da el resultado, en un formato que sea legible, no añadas saltos de linea. Ten en cuenta que el resultado que tu des sera visto desde WhatsApp,\n"
        f"no añadas texto innecesario y en caso de que no vayas a responder nada coherente responde \n"
        f"'Ups, algo ha fallado, vuelve a intentarlo cambiando la peticion, por favor, formula mejor tu pregunta, no la estoy entendiendo :)'"
    )
    
    respuesta = openai.chat.completions.create(
        model="gpt-4o-mini",  # Modelo de lenguaje utilizado
        messages=[
            {"role": "system", "content": "Eres un asistente experto en bases de datos que entiende consultas SQL y las transforma para que los resultados de las consultas lo entienda un humano que no tenga ni idea de JSON"},
            {"role": "user", "content": prompt}
        ],
        max_tokens=100,  # Limite de tokens de respuesta 
        temperature=0  # Configuracion para respuestas mas deterministicas
    )
    return respuesta.choices[0].message.content
    
#Para que no de errores al pasarlo a un json cambiamos los tipos de datos
def convertir_decimales(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    return obj
      
