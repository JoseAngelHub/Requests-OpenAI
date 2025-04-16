from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import core.logger as J
from core.logic import SQLAssistant
from core.config import SECRET_KEY
from core.utils import create_jwt_token, get_current_user, get_nif_client, login_user, get_user

# Secret key and algorithm for JWT token encoding
Key = SECRET_KEY
ALGORITHM = "HS256"

# Initialize FastAPI app and SQL assistant
app = FastAPI()
sql_assistant = SQLAssistant()

# Pydantic model to validate incoming request body for queries
class QueryRequest(BaseModel):
    body: dict
    
# Pydantic model to validate incoming request body for token requests
class TokenRequest(BaseModel):
    body: dict

# Login route: Validates user credentials and generates a JWT token if successful
@app.post("/login")
def login(request: TokenRequest):
    J.info("Login attempt received")
    # Check if the required fields are present in the request body
    if "username" not in request.body or "password" not in request.body:
        J.warning("Missing required fields in login request")
        raise HTTPException(status_code=400, detail="Missing required fields: 'username', 'password'")
    
    # Validate user credentials using SQLAssistant
    if get_user(request.body["username"], request.body["password"]):
        token = create_jwt_token({"sub": request.body["username"]})
        J.info(f"Login successful for user: {request.body['username']}")
        return {"state": True, "token": token}
    else:
        J.warning(f"Login failed for user: {request.body['username']}")
        return {"state": False, "token": "null"}

# Route to process a query: Validates the input fields and checks if the user exists before processing the query
@app.post("/process/")
def process_query(request: QueryRequest, username: str = Depends(get_current_user)):
    J.info(f"Processing query for user: {username}")
    try:
        # Check if required fields are present in the request body
        if "text" not in request.body or "phone" not in request.body:
            J.warning("Missing required fields in process request")
            raise HTTPException(status_code=400, detail="Missing required fields: 'text', 'phone'")

        phone = request.body["phone"]
        J.info(f"Checking if user exists for phone: {phone}")
        # Check if the user exists using SQLAssistant
        user_exists = login_user(phone)
        clientNif = get_nif_client(phone)
        
        if user_exists:
            # Process the query if the user exists
            print(request.body["text"])
            response = sql_assistant.process_q(request.body["text"], clientNif)
            J.info("Query processed successfully")
            
            if(str(response).find("None") != -1):
                J.info("No data returned from query")
                return {"success": True, "answer": "Algo no ha salido bien"}
            print(response)
            return {"success": True, "answer": response}
        else:
            # Handle case when user does not exist
            J.warning("User does not exist or issue with processing")
            return {"success": False, "answer": "something has not gone well"}

    except ValueError as ve:
        # Handle value errors
        J.error(f"ValueError: {str(ve)}")
        return {"success": True, "answer": "something has not gone well"}
    except Exception as e:
        # Handle unexpected internal server errors
        J.error(f"Internal server error: {str(e)}")
        return {"success": True, "answer": "something has not gone well"}
