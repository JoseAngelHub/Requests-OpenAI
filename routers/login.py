from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.token import create_jwt_token
import core.logger as J
from utils.user_queries import get_user

# Initialize FastAPI app and SQL assistant
app = APIRouter()

# Pydantic model to validate incoming request body for token requests
class TokenRequest(BaseModel):
    body: dict

# Login route: Validates user credentials and generates a JWT token if successful
@app.post("/")
async def login(request: TokenRequest):
    J.info("Login attempt received")
    
    # Check if the required fields are present in the request body ('username' and 'password')
    if "username" not in request.body or "password" not in request.body:
        J.warning("Missing required fields in login request")
        raise HTTPException(status_code=400, detail="Missing required fields: 'username', 'password'")
    
    # Validate user credentials using the get_user function (likely queries the database)
    if get_user(request.body["username"], request.body["password"]):
        # If credentials are correct, generate a JWT token for the user
        token = create_jwt_token({"sub": request.body["username"]})
        J.info(f"Login successful for user: {request.body['username']}")
        # Return the token and state as True
        return {"state": True, "token": token}
    else:
        # If credentials are invalid, return state as False and a null token
        J.warning(f"Login failed for user: {request.body['username']}")
        return {"state": False, "token": "null"}
