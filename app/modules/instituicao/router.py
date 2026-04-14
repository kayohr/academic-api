from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query

from app.core.deps import CurrentUser, SessionDep, require_roles
from app.modules.instituicao import service
from app.modules.instituicao.schemas import (
    CampusCreate, CampusResponse, CampusUpdate,
    CursoCreate, CursoResponse, CursoUpdate,
    DepartamentoCreate, DepartamentoResponse, DepartamentoUpdate,
)

router = APIRouter()

AdminOuCoordenador = Annotated[dict, Depends(require_roles("admin", "coordenador"))]
SomenteAdmin = Annotated[dict, Depends(require_roles("admin"))]


# ── Campus ───────────────────────────────────────────────────────────────────

@router.get("/campus", response_model=dict, tags=["Instituição"])
async def list_campus(
    db: SessionDep,
    _: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    apenas_ativos: bool = True,
):
    rows, total = await service.list_campus(db, page, page_size, apenas_ativos)
    return {
        "data": [CampusResponse.model_validate(r) for r in rows],
        "meta": {"total": total, "page": page, "page_size": page_size},
    }


@router.post("/campus", response_model=CampusResponse, status_code=201, tags=["Instituição"])
async def create_campus(body: CampusCreate, db: SessionDep, _: SomenteAdmin):
    return await service.create_campus(db, body)


@router.get("/campus/{campus_id}", response_model=CampusResponse, tags=["Instituição"])
async def get_campus(campus_id: int, db: SessionDep, _: CurrentUser):
    return await service.get_campus(db, campus_id)


@router.put("/campus/{campus_id}", response_model=CampusResponse, tags=["Instituição"])
async def update_campus(campus_id: int, body: CampusUpdate, db: SessionDep, _: SomenteAdmin):
    return await service.update_campus(db, campus_id, body)


@router.delete("/campus/{campus_id}", status_code=204, tags=["Instituição"])
async def delete_campus(campus_id: int, db: SessionDep, _: SomenteAdmin):
    await service.delete_campus(db, campus_id)


# ── Departamento ─────────────────────────────────────────────────────────────

@router.get("/departamentos", response_model=dict, tags=["Instituição"])
async def list_departamentos(
    db: SessionDep,
    _: CurrentUser,
    campus_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    rows, total = await service.list_departamentos(db, campus_id, page, page_size)
    return {
        "data": [DepartamentoResponse.model_validate(r) for r in rows],
        "meta": {"total": total, "page": page, "page_size": page_size},
    }


@router.post("/departamentos", response_model=DepartamentoResponse, status_code=201, tags=["Instituição"])
async def create_departamento(body: DepartamentoCreate, db: SessionDep, _: SomenteAdmin):
    return await service.create_departamento(db, body)


@router.get("/departamentos/{dep_id}", response_model=DepartamentoResponse, tags=["Instituição"])
async def get_departamento(dep_id: int, db: SessionDep, _: CurrentUser):
    return await service.get_departamento(db, dep_id)


@router.put("/departamentos/{dep_id}", response_model=DepartamentoResponse, tags=["Instituição"])
async def update_departamento(dep_id: int, body: DepartamentoUpdate, db: SessionDep, _: SomenteAdmin):
    return await service.update_departamento(db, dep_id, body)


@router.delete("/departamentos/{dep_id}", status_code=204, tags=["Instituição"])
async def delete_departamento(dep_id: int, db: SessionDep, _: SomenteAdmin):
    await service.delete_departamento(db, dep_id)


# ── Curso ────────────────────────────────────────────────────────────────────

@router.get("/cursos", response_model=dict, tags=["Instituição"])
async def list_cursos(
    db: SessionDep,
    _: CurrentUser,
    campus_id: Optional[int] = None,
    modalidade: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    rows, total = await service.list_cursos(db, campus_id, modalidade, page, page_size)
    return {
        "data": [CursoResponse.model_validate(r) for r in rows],
        "meta": {"total": total, "page": page, "page_size": page_size},
    }


@router.post("/cursos", response_model=CursoResponse, status_code=201, tags=["Instituição"])
async def create_curso(body: CursoCreate, db: SessionDep, _: AdminOuCoordenador):
    return await service.create_curso(db, body)


@router.get("/cursos/{curso_id}", response_model=CursoResponse, tags=["Instituição"])
async def get_curso(curso_id: int, db: SessionDep, _: CurrentUser):
    return await service.get_curso(db, curso_id)


@router.put("/cursos/{curso_id}", response_model=CursoResponse, tags=["Instituição"])
async def update_curso(curso_id: int, body: CursoUpdate, db: SessionDep, _: AdminOuCoordenador):
    return await service.update_curso(db, curso_id, body)


@router.delete("/cursos/{curso_id}", status_code=204, tags=["Instituição"])
async def delete_curso(curso_id: int, db: SessionDep, _: AdminOuCoordenador):
    await service.delete_curso(db, curso_id)
