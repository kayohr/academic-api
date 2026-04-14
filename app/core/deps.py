from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.db.session import get_session

security = HTTPBearer()

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> dict:
    try:
        payload = decode_access_token(credentials.credentials)
        return {"id": int(payload["sub"]), "role": payload["role"], "nome": payload["nome"]}
    except (JWTError, KeyError):
        raise UnauthorizedError("Token inválido ou expirado")


CurrentUser = Annotated[dict, Depends(get_current_user)]


def require_roles(*roles: str):
    """Decorator de dependência que exige uma das roles listadas."""

    async def checker(current_user: CurrentUser):
        if current_user["role"] not in roles:
            raise ForbiddenError("Você não tem permissão para acessar este recurso")
        return current_user

    return checker
