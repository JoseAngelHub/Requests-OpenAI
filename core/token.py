import datetime
from typing import Optional

import jwt
import core.logger as J
from core.config import ALGORITHM, SECRET_KEY


# Function to create a JWT token with an optional expiration time
def create_jwt_token(data: dict, expires_delta: Optional[int] = None):
    J.info("Creating JWT token")
    
    # Make a copy of the input data to ensure the original is not modified
    to_encode = data.copy()
    
    # Set the expiration time for the token:
    # Default expiration is 24 hours, or use the provided `expires_delta` in hours
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=expires_delta or 24)
    
    # Update the data dictionary with the expiration time (`exp` field)
    to_encode.update({"exp": expire})
    
    # Encode the data into a JWT token using the secret key and algorithm
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
