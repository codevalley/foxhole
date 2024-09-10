from jose import JWTError, jwt
from app.core.config import settings
from typing import Optional


def verify_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: Optional[str] = payload.get("sub")
        return user_id
    except JWTError:
        return None
