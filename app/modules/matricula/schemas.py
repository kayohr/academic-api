from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class MatriculaCreate(BaseModel):
    aluno_id: int
    turma_id: int


class MatriculaUpdate(BaseModel):
    status: str  # ativa, trancada, cancelada


class MatriculaResponse(BaseModel):
    id: int
    aluno_id: int
    turma_id: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MatriculaDetalhe(BaseModel):
    """Response com dados da turma e disciplina embutidos."""
    id: int
    aluno_id: int
    turma_id: int
    status: str
    created_at: datetime
    updated_at: datetime

    # Dados desnormalizados para leitura
    turma_codigo: Optional[str] = None
    disciplina_nome: Optional[str] = None
    disciplina_codigo: Optional[str] = None
    semestre_label: Optional[str] = None  # "2025/1"

    model_config = {"from_attributes": True}
