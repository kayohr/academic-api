import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

BCRYPT_ROUNDS = 12


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(BCRYPT_ROUNDS)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(sub: int, role: str, nome: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRES_MINUTES)
    payload = {"sub": str(sub), "role": role, "nome": nome, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])


def generate_refresh_token() -> str:
    return secrets.token_hex(40)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
