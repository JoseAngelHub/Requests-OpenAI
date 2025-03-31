from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from core.logic import SQLAssistant
import core.logger as R

app = FastAPI()
sql_assistant = SQLAssistant()

class QueryRequest(BaseModel):
    body: dict

@app.post("/process/")
def process_query(request: QueryRequest):
    """
    Procesa una consulta enviada en el body de la peticion.
    
    Args:
        request (QueryRequest): Objeto con el cuerpo de la peticion.
    
    Returns:
        dict: Respuesta con el resultado de la consulta SQL.
    """
    try:
        # Verifica que el campo text exista en el body
        if "text" not in request.body:
            raise HTTPException(status_code=400, detail={"error": "El campo text es requerido en el body."})
        
        # Procesa la consulta
        response = sql_assistant.process_q(request.body["text"])
        return {"success": True, "data": response}
    
    except HTTPException as e:
        raise e 
    
    except Exception as e:
        # Registra el error y devuelve una respuesta con codigo 500
        R.error(f"Error interno del servidor: {str(e)}")
        raise HTTPException(status_code=500, detail={"error": "Error interno del servidor"})

@app.get("/process2/")
def process_query(text: str):
    """
    Procesa una consulta SQL enviada como parametro en la URL.
    
    Args:
        text (str): Texto de la consulta enviada en la URL.
    
    Returns:
        dict: Respuesta con el resultado de la consulta SQL.
    """
    try:
        # Verifica que el parametro 'text' no este vacio
        if not text:
            raise HTTPException(status_code=400, detail={"error": "El parametro 'text' es requerido en la URL."})
        
        # Procesa la consulta
        response = sql_assistant.process_q(text)
        return {"success": True, "data": response}
    
    except Exception as e:
        # Registra el error y devuelve una respuesta con codigo 500
        R.error(f"Error interno del servidor: {str(e)}")
        raise HTTPException(status_code=500, detail={"error": "Error interno del servidor"})
