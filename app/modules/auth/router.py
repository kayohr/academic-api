from fastapi import APIRouter

from app.core.deps import CurrentUser, SessionDep
from app.modules.auth import service
from app.modules.auth.schemas import (
    LoginRequest,
    LogoutRequest,
    MeResponse,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)

router = APIRouter()


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=201,
    summary="Cadastrar novo usuário",
    responses={409: {"description": "E-mail já cadastrado"}},
)
async def register(body: RegisterRequest, db: SessionDep):
    return await service.register(db, body)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login — retorna access_token e refresh_token",
    responses={401: {"description": "Credenciais inválidas"}},
)
async def login(body: LoginRequest, db: SessionDep):
    return await service.login(db, body)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Renovar access_token via refresh_token",
    responses={401: {"description": "Refresh token inválido ou revogado"}},
)
async def refresh(body: RefreshRequest, db: SessionDep):
    return await service.refresh(db, body.refresh_token)


@router.post(
    "/logout",
    status_code=204,
    summary="Revogar refresh_token",
)
async def logout(body: LogoutRequest, db: SessionDep):
    await service.logout(db, body.refresh_token)


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Dados do usuário autenticado",
    responses={401: {"description": "Token ausente ou inválido"}},
)
async def me(current_user: CurrentUser, db: SessionDep):
    return await service.me(db, current_user["id"])
