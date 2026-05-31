import os
from fastapi import HTTPException, status, Depends
from jose import jwt, JWTError # Assuming python-jose for JWT handling

# Load JWT secret from environment variable (CRITICAL for production)
# Fallback to a dummy secret for local development/testing, but WARN
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-key-not-for-production")
ALGORITHM = "HS256" # Or a stronger algorithm like RS256

async def authenticate_user(authorization: str = Depends(lambda x: x.headers.get("Authorization"))):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split(" ")[1]
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        # Decode and verify the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub") # 'sub' is typically the subject/user ID
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token (no user ID)",
                headers={"WWW-Authenticate": "Bearer"},
            )
        # In a real app, you'd return a user object or ID here
        return user_id
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
