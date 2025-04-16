from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from core.auth import get_current_user, login_user
import core.logger as J
from core.logic import SQLAssistant
from utils.user_queries import get_nif_client

# Initialize FastAPI app and SQL assistant
app = APIRouter()
sql_assistant = SQLAssistant()

# Pydantic model to validate incoming request body for queries
class QueryRequest(BaseModel):
    body: dict
    
# Route to process a query: Validates the input fields and checks if the user exists before processing the query
@app.post("/")
async def process_query(request: QueryRequest, username: str = Depends(get_current_user)):
    J.info(f"Processing query for user: {username}")
    try:
        # Check if required fields are present in the request body ('text' and 'phone')
        if "text" not in request.body or "phone" not in request.body:
            J.warning("Missing required fields in process request")
            raise HTTPException(status_code=400, detail="Missing required fields: 'text', 'phone'")

        phone = request.body["phone"]
        J.info(f"Checking if user exists for phone: {phone}")
        
        # Check if the user exists using the login_user function
        user_exists = login_user(phone)
        clientNif = get_nif_client(phone)
        
        if user_exists:
            # Process the query if the user exists
            print(request.body["text"])
            response = sql_assistant.process_q(request.body["text"], clientNif)
            J.info("Query processed successfully")
            
            # Check if the response contains 'None' or if there's no valid data
            if(str(response).find("None") != -1):
                J.info("No data returned from query")
                return {"success": True, "answer": "Algo no ha funcionado, quizas no tienes permisos, recuerda que solo puedes consultar tus datos de facturas, pedidos y de cliente"}
            
            print(response)
            return {"success": True, "answer": response}
        else:
            # Handle case when the user does not exist or an issue occurred
            J.warning("User does not exist or issue with processing")
            return {"success": False, "answer": "something has not gone well"}

    except ValueError as ve:
        # Handle value errors, such as incorrect data type or format
        J.error(f"ValueError: {str(ve)}")
        return {"success": True, "answer": "something has not gone well"}
    except Exception as e:
        # Handle unexpected internal server errors
        J.error(f"Internal server error: {str(e)}")
        return {"success": True, "answer": "something has not gone well"}
