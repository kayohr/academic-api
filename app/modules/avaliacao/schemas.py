from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, field_validator


# ── Nota ─────────────────────────────────────────────────────────────────────

TIPOS_NOTA = {"AV1", "AV2", "AV3"}


class NotaCreate(BaseModel):
    tipo: str   # AV1, AV2, AV3
    valor: float

    @field_validator("tipo")
    @classmethod
    def tipo_valido(cls, v):
        if v not in TIPOS_NOTA:
            raise ValueError(f"tipo deve ser um de: {', '.join(sorted(TIPOS_NOTA))}")
        return v

    @field_validator("valor")
    @classmethod
    def valor_valido(cls, v):
        if not (0.0 <= v <= 10.0):
            raise ValueError("valor deve estar entre 0.0 e 10.0")
        return round(v, 2)


class NotaUpdate(BaseModel):
    valor: float

    @field_validator("valor")
    @classmethod
    def valor_valido(cls, v):
        if not (0.0 <= v <= 10.0):
            raise ValueError("valor deve estar entre 0.0 e 10.0")
        return round(v, 2)


class NotaResponse(BaseModel):
    id: int
    matricula_id: int
    tipo: str
    valor: float
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Frequência ────────────────────────────────────────────────────────────────

class FrequenciaCreate(BaseModel):
    data_aula: date
    presente: bool = True


class FrequenciaUpdate(BaseModel):
    presente: bool


class FrequenciaResponse(BaseModel):
    id: int
    matricula_id: int
    data_aula: date
    presente: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Resumo por matrícula ──────────────────────────────────────────────────────

class ResumoAvaliacaoResponse(BaseModel):
    matricula_id: int
    notas: list[NotaResponse]
    media: Optional[float]          # None se não há notas suficientes
    total_aulas: int
    aulas_presentes: int
    frequencia_pct: Optional[float]  # None se não há aulas registradas
    situacao: str                    # aprovado, reprovado, em_andamento

    model_config = {"from_attributes": True}


# ── Frequência consolidada por turma ─────────────────────────────────────────

class FrequenciaTurmaItem(BaseModel):
    aluno_id: int
    aluno_nome: str
    matricula_id: int
    total_aulas: int
    aulas_presentes: int
    frequencia_pct: Optional[float]
