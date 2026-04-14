from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query

from app.core.deps import CurrentUser, SessionDep, require_roles
from app.modules.aluno.schemas import AlunoResponse
from app.modules.turma import service
from app.modules.disciplina.schemas import SemestreCreate, SemestreResponse, SemestreUpdate, TurmaCreate, TurmaResponse, TurmaUpdate

router = APIRouter(tags=["Semestres & Turmas"])

AdminOuCoordenador = Annotated[dict, Depends(require_roles("admin", "coordenador"))]
SomenteAdmin = Annotated[dict, Depends(require_roles("admin"))]


# ── Semestres ─────────────────────────────────────────────────────────────────

@router.get("/semestres", response_model=dict)
async def list_semestres(
    db: SessionDep, _: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    rows, total = await service.list_semestres(db, page, page_size)
    return {
        "data": [SemestreResponse.model_validate(r) for r in rows],
        "meta": {"total": total, "page": page, "page_size": page_size},
    }


@router.post("/semestres", response_model=SemestreResponse, status_code=201)
async def create_semestre(body: SemestreCreate, db: SessionDep, _: SomenteAdmin):
    return await service.create_semestre(db, body)


@router.get("/semestres/{semestre_id}", response_model=SemestreResponse)
async def get_semestre(semestre_id: int, db: SessionDep, _: CurrentUser):
    return await service.get_semestre(db, semestre_id)


@router.put("/semestres/{semestre_id}", response_model=SemestreResponse)
async def update_semestre(semestre_id: int, body: SemestreUpdate, db: SessionDep, _: SomenteAdmin):
    return await service.update_semestre(db, semestre_id, body)


@router.put("/semestres/{semestre_id}/encerrar", response_model=SemestreResponse)
async def encerrar_semestre(semestre_id: int, db: SessionDep, _: SomenteAdmin):
    return await service.encerrar_semestre(db, semestre_id)


# ── Turmas ────────────────────────────────────────────────────────────────────

@router.get("/turmas", response_model=dict)
async def list_turmas(
    db: SessionDep, _: CurrentUser,
    semestre_id: Optional[int] = None,
    disciplina_id: Optional[int] = None,
    professor_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    rows, total = await service.list_turmas(db, semestre_id, disciplina_id, professor_id, page, page_size)
    return {
        "data": [TurmaResponse.model_validate(r) for r in rows],
        "meta": {"total": total, "page": page, "page_size": page_size},
    }


@router.post("/turmas", response_model=TurmaResponse, status_code=201)
async def create_turma(body: TurmaCreate, db: SessionDep, _: AdminOuCoordenador):
    return await service.create_turma(db, body)


@router.get("/turmas/{turma_id}", response_model=TurmaResponse)
async def get_turma(turma_id: int, db: SessionDep, _: CurrentUser):
    return await service.get_turma(db, turma_id)


@router.put("/turmas/{turma_id}", response_model=TurmaResponse)
async def update_turma(turma_id: int, body: TurmaUpdate, db: SessionDep, _: AdminOuCoordenador):
    return await service.update_turma(db, turma_id, body)


@router.delete("/turmas/{turma_id}", status_code=204)
async def delete_turma(turma_id: int, db: SessionDep, _: AdminOuCoordenador):
    await service.delete_turma(db, turma_id)


@router.get("/turmas/{turma_id}/alunos", response_model=dict)
async def get_alunos_turma(
    turma_id: int, db: SessionDep, _: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    rows, total = await service.get_alunos_turma(db, turma_id, page, page_size)
    return {
        "data": [AlunoResponse.model_validate(r) for r in rows],
        "meta": {"total": total, "page": page, "page_size": page_size},
    }
