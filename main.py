from fastapi import FastAPI, HTTPException, Header, Depends
import jwt
import datetime
from typing import Optional
from pydantic import BaseModel
import core.logger as J
from core.logic import SQLAssistant
from core.config import SECRET_KEY

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
    if sql_assistant.get_user(request.body["username"], request.body["password"]):
        token = create_jwt_token({"sub": request.body["username"]})
        J.info(f"Login successful for user: {request.body['username']}")
        return {"state": True, "token": token}
    else:
        J.warning(f"Login failed for user: {request.body['username']}")
        return {"state": False, "token": "null"}

# Function to create a JWT token with an optional expiration time
def create_jwt_token(data: dict, expires_delta: Optional[int] = None):
    J.info("Creating JWT token")
    to_encode = data.copy()
    # Set the expiration time to 24 hours or the provided expiration delta
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=expires_delta or 24)
    to_encode.update({"exp": expire})
    # Encode and return the JWT token
    return jwt.encode(to_encode, Key, algorithm=ALGORITHM)

# Function to extract and validate the current user's JWT token from the request header
def get_current_user(authorization: str = Header(None)):
    J.info("Validating JWT token")
    # Check if the token is present and correctly formatted
    if not authorization or not authorization.startswith("Bearer "):
        J.warning("Token missing or invalid")
        raise HTTPException(status_code=401, detail={'text':"Token missing or invalid", 'state': False})
    
    token = authorization.split("Bearer ")[1]
    try:
        # Decode and verify the token
        payload = jwt.decode(token, Key, algorithms=[ALGORITHM])
        J.info(f"Token validated for user: {payload['sub']}")
        return payload['sub']
    except jwt.ExpiredSignatureError:
        # Handle expired token error
        J.warning("Token expired")
        raise HTTPException(status_code=401, detail={'text':"Token expired", 'state': False})
    except jwt.InvalidTokenError:
        # Handle invalid token error
        J.warning("Invalid token")
        raise HTTPException(status_code=401, detail={'text':"Invalid token", 'state': False})

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
        user_exists = sql_assistant.login_user(phone)
        
        if user_exists:
            # Process the query if the user exists
            print(request.body["text"])
            response = sql_assistant.process_q(request.body["text"])
            J.info("Query processed successfully")
            return {"success": True, "answer": response}
        else:
            # Handle case when user does not exist
            J.warning("User does not exist or issue with processing")
            return {"success": False, "answer": "something has not gone well"}
    
    except ValueError as ve:
        # Handle value errors
        J.error(f"ValueError: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        # Handle unexpected internal server errors
        J.error(f"Internal server error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
