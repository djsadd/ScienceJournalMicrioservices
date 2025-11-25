from fastapi import HTTPException, Request
from jose import jwt, JWTError

from app.config import SECRET_KEY, ALGORITHM


async def get_current_user(request: Request):
    """Validate JWT from Authorization header and attach user info to request.state."""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    parts = auth_header.split()
    if len(parts) != 2:
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    scheme, token = parts
    if scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization scheme")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        roles = payload.get("roles", [])
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Attach to request state so proxy can forward minimal data
        request.state.user_id = int(user_id)
        request.state.roles = roles

        return {"user_id": int(user_id), "roles": roles}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

