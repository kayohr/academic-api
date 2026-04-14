from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query

from app.core.deps import CurrentUser, SessionDep, require_roles
from app.modules.historico import service
from app.modules.historico.schemas import (
    CRResponse,
    ConsolidarSemestreResponse,
    HistoricoItemResponse,
)

router = APIRouter(tags=["Histórico Acadêmico"])

SomenteAdmin = Annotated[dict, Depends(require_roles("admin"))]


@router.get("/alunos/{aluno_id}/historico", response_model=dict)
async def get_historico_aluno(
    aluno_id: int,
    db: SessionDep,
    _: CurrentUser,
    semestre_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Histórico acadêmico completo do aluno, agrupado por semestre."""
    rows, total = await service.get_historico_aluno(db, aluno_id, semestre_id, page, page_size)
    return {
        "data": [HistoricoItemResponse.model_validate(r) for r in rows],
        "meta": {"total": total, "page": page, "page_size": page_size},
    }


@router.get("/alunos/{aluno_id}/historico/cr", response_model=CRResponse)
async def get_cr_aluno(aluno_id: int, db: SessionDep, _: CurrentUser):
    """Coeficiente de Rendimento (CR) e contadores de situação do aluno."""
    return await service.get_cr_aluno(db, aluno_id)


@router.post("/semestres/{semestre_id}/consolidar", response_model=ConsolidarSemestreResponse)
async def consolidar_semestre(semestre_id: int, db: SessionDep, _: SomenteAdmin):
    """
    Gera snapshots imutáveis de histórico para todas as matrículas do semestre.
    O semestre deve estar encerrado. Operação idempotente.
    """
    return await service.consolidar_semestre(db, semestre_id)
