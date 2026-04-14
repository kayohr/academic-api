from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.db.models import RefreshToken, Usuario


def _get_nome(usuario: Usuario) -> str:
    if usuario.aluno:
        return usuario.aluno.nome
    if usuario.professor:
        return usuario.professor.nome
    if usuario.funcionario:
        return usuario.funcionario.nome
    return usuario.email


def _refresh_expires_at() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_EXPIRES_DAYS)


async def register(db: AsyncSession, data) -> dict:
    existing = await db.scalar(select(Usuario).where(Usuario.email == data.email))
    if existing:
        raise ConflictError("Email já cadastrado")

    usuario = Usuario(
        email=data.email,
        senha_hash=hash_password(data.senha),
        role=data.role,
        aluno_id=data.aluno_id,
        professor_id=data.professor_id,
        funcionario_id=data.funcionario_id,
    )
    db.add(usuario)
    await db.commit()
    await db.refresh(usuario)
    return {"id": usuario.id, "email": usuario.email, "role": usuario.role}


async def login(db: AsyncSession, data) -> dict:
    INVALID = "Credenciais inválidas"

    result = await db.execute(
        select(Usuario)
        .where(Usuario.email == data.email, Usuario.ativo == True)
        .options(
            *_usuario_load_options()
        )
    )
    usuario = result.scalar_one_or_none()
    if not usuario or not verify_password(data.senha, usuario.senha_hash):
        raise UnauthorizedError(INVALID)

    nome = _get_nome(usuario)
    access_token = create_access_token(usuario.id, usuario.role, nome)

    raw = generate_refresh_token()
    db.add(RefreshToken(
        usuario_id=usuario.id,
        token_hash=hash_token(raw),
        expires_at=_refresh_expires_at(),
    ))
    await db.commit()

    return {"access_token": access_token, "refresh_token": raw, "token_type": "bearer"}


async def refresh(db: AsyncSession, raw_token: str) -> dict:
    INVALID = "Refresh token inválido ou expirado"
    token_hash = hash_token(raw_token)

    stored = await db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revogado == False,
            RefreshToken.expires_at > datetime.now(timezone.utc),
        )
    )
    if not stored:
        raise UnauthorizedError(INVALID)

    # Rotação: invalida token atual
    stored.revogado = True

    result = await db.execute(
        select(Usuario)
        .where(Usuario.id == stored.usuario_id, Usuario.ativo == True)
        .options(*_usuario_load_options())
    )
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise UnauthorizedError(INVALID)

    nome = _get_nome(usuario)
    access_token = create_access_token(usuario.id, usuario.role, nome)

    new_raw = generate_refresh_token()
    db.add(RefreshToken(
        usuario_id=usuario.id,
        token_hash=hash_token(new_raw),
        expires_at=_refresh_expires_at(),
    ))
    await db.commit()

    return {"access_token": access_token, "refresh_token": new_raw, "token_type": "bearer"}


async def logout(db: AsyncSession, raw_token: str) -> None:
    token_hash = hash_token(raw_token)
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.token_hash == token_hash)
        .values(revogado=True)
    )
    await db.commit()


async def me(db: AsyncSession, usuario_id: int) -> dict:
    result = await db.execute(
        select(Usuario)
        .where(Usuario.id == usuario_id, Usuario.ativo == True)
        .options(*_usuario_load_options())
    )
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise UnauthorizedError("Usuário não encontrado")

    return {
        "id": usuario.id,
        "email": usuario.email,
        "role": usuario.role,
        "nome": _get_nome(usuario),
    }


def _usuario_load_options():
    from sqlalchemy.orm import selectinload
    return [
        selectinload(Usuario.aluno),
        selectinload(Usuario.professor),
        selectinload(Usuario.funcionario),
    ]
