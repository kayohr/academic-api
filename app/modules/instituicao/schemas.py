from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


# ── Campus ──────────────────────────────────────────────────────────────────

class CampusCreate(BaseModel):
    nome: str
    cidade: str
    estado: str
    endereco: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[EmailStr] = None


class CampusUpdate(BaseModel):
    nome: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    endereco: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[EmailStr] = None
    ativo: Optional[bool] = None


class CampusResponse(BaseModel):
    id: int
    nome: str
    cidade: str
    estado: str
    endereco: Optional[str]
    telefone: Optional[str]
    email: Optional[str]
    ativo: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Departamento ─────────────────────────────────────────────────────────────

class DepartamentoCreate(BaseModel):
    campus_id: int
    nome: str
    sigla: str
    email: Optional[EmailStr] = None


class DepartamentoUpdate(BaseModel):
    nome: Optional[str] = None
    sigla: Optional[str] = None
    email: Optional[EmailStr] = None
    ativo: Optional[bool] = None


class DepartamentoResponse(BaseModel):
    id: int
    campus_id: int
    nome: str
    sigla: str
    email: Optional[str]
    ativo: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Curso ────────────────────────────────────────────────────────────────────

class CursoCreate(BaseModel):
    departamento_id: int
    nome: str
    codigo: str
    grau: str
    modalidade: str = "presencial"
    duracao_semestres: int
    creditos_necessarios: int


class CursoUpdate(BaseModel):
    nome: Optional[str] = None
    grau: Optional[str] = None
    modalidade: Optional[str] = None
    duracao_semestres: Optional[int] = None
    creditos_necessarios: Optional[int] = None
    ativo: Optional[bool] = None


class CursoResponse(BaseModel):
    id: int
    departamento_id: int
    nome: str
    codigo: str
    grau: str
    modalidade: str
    duracao_semestres: int
    creditos_necessarios: int
    ativo: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Paginação ─────────────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    data: list
    meta: dict
