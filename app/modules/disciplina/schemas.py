from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel


# ── Disciplina ────────────────────────────────────────────────────────────────

class DisciplinaCreate(BaseModel):
    departamento_id: int
    codigo: str
    nome: str
    ementa: Optional[str] = None
    carga_horaria: int
    creditos: int


class DisciplinaUpdate(BaseModel):
    nome: Optional[str] = None
    ementa: Optional[str] = None
    carga_horaria: Optional[int] = None
    creditos: Optional[int] = None
    ativa: Optional[bool] = None


class DisciplinaResponse(BaseModel):
    id: int
    departamento_id: int
    codigo: str
    nome: str
    ementa: Optional[str]
    carga_horaria: int
    creditos: int
    ativa: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Grade Curricular ──────────────────────────────────────────────────────────

class GradeItemCreate(BaseModel):
    disciplina_id: int
    periodo: int
    tipo: str = "obrigatoria"  # obrigatoria, optativa, eletiva


class GradeItemResponse(BaseModel):
    id: int
    curso_id: int
    disciplina_id: int
    periodo: int
    tipo: str
    disciplina: Optional[DisciplinaResponse] = None

    model_config = {"from_attributes": True}


# ── Pré-requisito ─────────────────────────────────────────────────────────────

class PreRequisitoAdd(BaseModel):
    prerequisito_id: int


# ── Semestre ──────────────────────────────────────────────────────────────────

class SemestreCreate(BaseModel):
    ano: int
    periodo: int
    data_inicio: str   # YYYY-MM-DD
    data_fim: str
    data_limite_trancamento: Optional[str] = None


class SemestreUpdate(BaseModel):
    data_inicio: Optional[str] = None
    data_fim: Optional[str] = None
    data_limite_trancamento: Optional[str] = None
    status: Optional[str] = None


class SemestreResponse(BaseModel):
    id: int
    ano: int
    periodo: int
    data_inicio: date
    data_fim: date
    data_limite_trancamento: Optional[date]
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Turma ─────────────────────────────────────────────────────────────────────

class HorarioItem(BaseModel):
    dia: str           # segunda, terca, quarta, quinta, sexta, sabado
    hora_inicio: str   # HH:MM
    hora_fim: str      # HH:MM


class TurmaCreate(BaseModel):
    disciplina_id: int
    professor_id: int
    semestre_id: int
    codigo: str
    sala: Optional[str] = None
    horario: Optional[list[HorarioItem]] = None
    vagas: int = 40


class TurmaUpdate(BaseModel):
    sala: Optional[str] = None
    horario: Optional[list[HorarioItem]] = None
    vagas: Optional[int] = None
    status: Optional[str] = None


class TurmaResponse(BaseModel):
    id: int
    disciplina_id: int
    professor_id: int
    semestre_id: int
    codigo: str
    sala: Optional[str]
    horario: Optional[list]
    vagas: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
