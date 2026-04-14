from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query

from app.core.deps import CurrentUser, SessionDep, require_roles
from app.modules.professor import service
from app.modules.professor.schemas import ProfessorCreate, ProfessorResponse, ProfessorUpdate

router = APIRouter(prefix="/professores", tags=["Professores"])

SomenteAdmin = Annotated[dict, Depends(require_roles("admin"))]


@router.get("", response_model=dict)
async def list_professores(
    db: SessionDep,
    _: CurrentUser,
    departamento_id: Optional[int] = None,
    titulacao: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    rows, total = await service.list_professores(db, departamento_id, titulacao, page, page_size)
    return {
        "data": [ProfessorResponse.model_validate(r) for r in rows],
        "meta": {"total": total, "page": page, "page_size": page_size},
    }


@router.post("", response_model=ProfessorResponse, status_code=201)
async def create_professor(body: ProfessorCreate, db: SessionDep, _: SomenteAdmin):
    return await service.create_professor(db, body)


@router.get("/{professor_id}", response_model=ProfessorResponse)
async def get_professor(professor_id: int, db: SessionDep, _: CurrentUser):
    return await service.get_professor(db, professor_id)


@router.put("/{professor_id}", response_model=ProfessorResponse)
async def update_professor(
    professor_id: int, body: ProfessorUpdate, db: SessionDep, _: SomenteAdmin
):
    return await service.update_professor(db, professor_id, body)


@router.delete("/{professor_id}", status_code=204)
async def delete_professor(professor_id: int, db: SessionDep, _: SomenteAdmin):
    await service.delete_professor(db, professor_id)


@router.get("/{professor_id}/turmas", response_model=dict)
async def get_turmas(
    professor_id: int,
    db: SessionDep,
    current_user: CurrentUser,
    semestre_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    rows, total = await service.get_turmas_professor(db, professor_id, semestre_id, page, page_size)
    return {
        "data": [{"id": t.id, "codigo": t.codigo, "disciplina_id": t.disciplina_id,
                  "semestre_id": t.semestre_id, "sala": t.sala, "vagas": t.vagas,
                  "status": t.status} for t in rows],
        "meta": {"total": total, "page": page, "page_size": page_size},
    }
