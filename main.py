from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from core.logic import SQLAssistant
import core.logger as R

app = FastAPI()
sql_assistant = SQLAssistant()

class QueryRequest(BaseModel):
    body: dict


#End point para que puedan conectarse a hacer peticiones
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
        # Verifica que el campo text, phone y user exista en el body
        if "text" not in request.body or "phone" not in request.body or "user" not in request.body:
            raise HTTPException(status_code=400, detail={"error": "El campo text,phone y user son requeridos en el body."})
        
        #Guarda el phone
        phone = request.body["phone"]
        #Login con el numero de telefono que envia el mensaje
        user_exists = SQLAssistant.login_user(phone=phone)
        #Si el login esta bien
        if user_exists:
            #Si el login es exitoso hacemos la consulta para que trabaje la IA
            response = sql_assistant.process_q(request.body["text"])
            #Le devolvemos True para que el servidor php funcione y la respuesta
            return {"success": True, "respuesta": response}
        #Si el login esta mal
        else:
            return {"sucess": user_exists}
            
    except HTTPException as e:
        raise e 
    except Exception as e:
        # Registra el error y devuelve una respuesta con codigo 500
        R.error(f"Error interno del servidor: {str(e)}")
        raise HTTPException(status_code=500, detail={"error": "Error interno del servidor"})