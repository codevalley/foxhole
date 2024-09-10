import secrets
import string
from urllib.parse import urlencode
from jose import JWTError, jwt
from datetime import datetime, timedelta, UTC
from app.core.config import settings
from typing import Dict, Optional


def generate_secure_url(base_url: str, params: dict) -> str:
    """
    Generates a secure URL by adding a random token to the query parameters.

    :param base_url: The base URL to append parameters to
    :param params: A dictionary of query parameters
    :return: A secure URL with an added token parameter
    """
    secure_params = {k: v for k, v in params.items()}
    secure_params["token"] = secrets.token_urlsafe(16)
    return f"{base_url}?{urlencode(secure_params)}"


def generate_secret_code(length: int = 8) -> str:
    """
    Generates a random secret code of specified length.

    :param length: The length of the secret code (default is 8)
    :return: A random string of letters and digits
    """
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def create_access_token(data: Dict[str, str]) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": str(int(expire.timestamp()))})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return str(encoded_jwt)


def verify_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: Optional[str] = payload.get("sub")
        return user_id
    except JWTError:
        return None
