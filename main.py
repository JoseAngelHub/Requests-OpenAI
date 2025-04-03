from fastapi import FastAPI, HTTPException, Header, Depends
import jwt
import datetime
from typing import Optional
from pydantic import BaseModel
import core.logger as R
from core.logic import SQLAssistant

# Secret key for signing JWT tokens
SECRET_KEY = ""
ALGORITHM = "HS256"

# Creating the FastAPI application
app = FastAPI()
sql_assistant = SQLAssistant()

# Request form for consultation
class QueryRequest(BaseModel):
    body: dict
    
class TokenRequest(BaseModel):
    body: dict

# Route to obtain an access token with username and password
@app.post("/login")
def login(request: TokenRequest):
    if "username" not in request.body or "password" not in request.body:
        raise HTTPException(status_code=400, detail="Missing required fields: 'username', 'password'")
    if sql_assistant.get_user(request.body["username"], request.body["password"]):
        token = create_jwt_token({"sub": request.body["username"]})
        return {"state": True, "token": token}
    else:
        return {"state": False, "token": "null"}

# Function to create a JWT token with optional expiration time
def create_jwt_token(data: dict, expires_delta: Optional[int] = None):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(hours=expires_delta or 24)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Middleware to validate token from headers
def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token missing or invalid")
    
    token = authorization.split("Bearer ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload['sub']  # Returns the token user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Route to process a query, requires token in headers
@app.post("/process/")
def process_query(request: QueryRequest, username: str = Depends(get_current_user)):
    try:
        # We check if 'text', 'phone' and 'user' are in the body
        if "text" not in request.body or "phone" not in request.body or "user" not in request.body:
            raise HTTPException(status_code=400, detail="Missing required fields: 'text', 'phone', 'user'")

        phone = request.body["phone"]
        print(phone)
        # We check if the user exists in the database
        user_exists = sql_assistant.login_user(phone)
        
        if user_exists:
            response = sql_assistant.process_q(request.body["text"])
            return {"success": True, "answer": response}
        else:
            raise HTTPException(status_code=404, detail="User not found")
    
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        R.error(f"Internal server error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
