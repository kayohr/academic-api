from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
import re


class RegisterRequest(BaseModel):
    email: EmailStr
    senha: str
    role: str
    aluno_id: Optional[int] = None
    professor_id: Optional[int] = None
    funcionario_id: Optional[int] = None

    @field_validator("senha")
    @classmethod
    def senha_forte(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Senha deve ter no mínimo 8 caracteres")
        if len(v) > 72:
            raise ValueError("Senha deve ter no máximo 72 caracteres")
        return v

    @field_validator("role")
    @classmethod
    def role_valida(cls, v: str) -> str:
        roles = {"admin", "coordenador", "professor", "aluno"}
        if v not in roles:
            raise ValueError(f"Role inválida. Use: {', '.join(sorted(roles))}")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    id: int
    email: str
    role: str
    nome: str


class RegisterResponse(BaseModel):
    id: int
    email: str
    role: str
