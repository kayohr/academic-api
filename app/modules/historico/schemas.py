from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class HistoricoItemResponse(BaseModel):
    id: int
    aluno_id: int
    semestre_id: int
    disciplina_id: int
    nota_final: Optional[float]
    frequencia_pct: Optional[float]
    situacao: str       # aprovado, reprovado, trancado
    creditos: int
    created_at: datetime

    # Campos desnormalizados
    disciplina_nome: Optional[str] = None
    disciplina_codigo: Optional[str] = None
    semestre_label: Optional[str] = None   # "2025/1"

    model_config = {"from_attributes": True}


class CRResponse(BaseModel):
    aluno_id: int
    cr: Optional[float]           # None se não há disciplinas aprovadas
    creditos_aprovados: int
    disciplinas_aprovadas: int
    disciplinas_reprovadas: int
    disciplinas_trancadas: int


class ConsolidarSemestreResponse(BaseModel):
    semestre_id: int
    semestre_label: str
    snapshots_gerados: int
    detalhes: list[dict]
