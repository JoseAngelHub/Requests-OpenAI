import datetime
from typing import Optional

from fastapi import HTTPException, Header
import jwt

from bd.conn import get_connect_db
import core.logger as J
from core.config import ALGORITHM, SECRET_KEY

# Function to extract and validate the current user's JWT token from the request header
def get_current_user(authorization: str = Header(None)):
    J.info("Validating JWT token")
    
    # Check if the token is present and correctly formatted (starts with 'Bearer ')
    if not authorization or not authorization.startswith("Bearer "):
        J.warning("Token missing or invalid")
        # Raise HTTP 401 Unauthorized error if the token is missing or malformed
        raise HTTPException(status_code=401, detail={'text':"Token missing or invalid", 'state': False})
    
    token = authorization.split("Bearer ")[1]  # Extract the token part
    try:
        # Decode and verify the JWT token using the secret key and algorithm
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        J.info(f"Token validated for user: {payload['sub']}")
        return payload['sub']  # Return the user identifier (subject) from the token
    except jwt.ExpiredSignatureError:
        # Handle case where the token is expired
        J.warning("Token expired")
        raise HTTPException(status_code=401, detail={'text':"Token expired", 'state': False})
    except jwt.InvalidTokenError:
        # Handle case where the token is invalid
        J.warning("Invalid token")
        raise HTTPException(status_code=401, detail={'text':"Invalid token", 'state': False})
    
# Function to login user by phone number
def login_user(phone: str):
    try:
        cursor = get_connect_db()
        if isinstance(cursor, Exception):
            raise cursor  # Raise if connection failed (cursor is an exception)

        # Use parameterized query to prevent SQL injection
        query = "SELECT name FROM CLIENTS WHERE TELCLI = %s"
        cursor.execute(query, (phone,))
        result = cursor.fetchall()

        # If a user with the provided phone number exists, return True
        if result:
            return True
        else:
            # Raise error if no user found with the phone number
            raise ValueError("User not found")

    except ValueError as e:
        J.error(f"User not found error: {str(e)}")
        return False  # Return False if user not found
    except Exception as e:
        J.error(f"Error verifying user: {str(e)}")
        return False  # Return False in case of any unexpected error
