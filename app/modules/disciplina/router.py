from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query

from app.core.deps import CurrentUser, SessionDep, require_roles
from app.modules.disciplina import service
from app.modules.disciplina.schemas import (
    DisciplinaCreate, DisciplinaResponse, DisciplinaUpdate,
    GradeItemCreate, GradeItemResponse,
    PreRequisitoAdd,
)

router = APIRouter(tags=["Disciplinas & Grade"])

AdminOuCoordenador = Annotated[dict, Depends(require_roles("admin", "coordenador"))]


# ── Disciplinas ───────────────────────────────────────────────────────────────

@router.get("/disciplinas", response_model=dict)
async def list_disciplinas(
    db: SessionDep, _: CurrentUser,
    departamento_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    rows, total = await service.list_disciplinas(db, departamento_id, page, page_size)
    return {
        "data": [DisciplinaResponse.model_validate(r) for r in rows],
        "meta": {"total": total, "page": page, "page_size": page_size},
    }


@router.post("/disciplinas", response_model=DisciplinaResponse, status_code=201)
async def create_disciplina(body: DisciplinaCreate, db: SessionDep, _: AdminOuCoordenador):
    return await service.create_disciplina(db, body)


@router.get("/disciplinas/{disciplina_id}", response_model=DisciplinaResponse)
async def get_disciplina(disciplina_id: int, db: SessionDep, _: CurrentUser):
    return await service.get_disciplina(db, disciplina_id)


@router.put("/disciplinas/{disciplina_id}", response_model=DisciplinaResponse)
async def update_disciplina(
    disciplina_id: int, body: DisciplinaUpdate, db: SessionDep, _: AdminOuCoordenador
):
    return await service.update_disciplina(db, disciplina_id, body)


# ── Pré-requisitos ────────────────────────────────────────────────────────────

@router.post("/disciplinas/{disciplina_id}/prerequisitos", status_code=201)
async def add_prerequisito(
    disciplina_id: int, body: PreRequisitoAdd, db: SessionDep, _: AdminOuCoordenador
):
    await service.add_prerequisito(db, disciplina_id, body.prerequisito_id)
    return {"message": "Pré-requisito adicionado"}


@router.delete("/disciplinas/{disciplina_id}/prerequisitos/{prerequisito_id}", status_code=204)
async def remove_prerequisito(
    disciplina_id: int, prerequisito_id: int, db: SessionDep, _: AdminOuCoordenador
):
    await service.remove_prerequisito(db, disciplina_id, prerequisito_id)


# ── Grade Curricular ──────────────────────────────────────────────────────────

@router.get("/cursos/{curso_id}/grade", response_model=list[GradeItemResponse])
async def get_grade(curso_id: int, db: SessionDep, _: CurrentUser):
    return await service.get_grade(db, curso_id)


@router.post("/cursos/{curso_id}/grade", response_model=GradeItemResponse, status_code=201)
async def add_disciplina_grade(
    curso_id: int, body: GradeItemCreate, db: SessionDep, _: AdminOuCoordenador
):
    return await service.add_disciplina_grade(db, curso_id, body)


@router.delete("/cursos/{curso_id}/grade/{disciplina_id}", status_code=204)
async def remove_disciplina_grade(
    curso_id: int, disciplina_id: int, db: SessionDep, _: AdminOuCoordenador
):
    await service.remove_disciplina_grade(db, curso_id, disciplina_id)
