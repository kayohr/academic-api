from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query

from app.core.deps import CurrentUser, SessionDep, require_roles
from app.modules.aluno import service
from app.modules.aluno.schemas import AlunoCreate, AlunoResponse, AlunoUpdate

router = APIRouter(prefix="/alunos", tags=["Alunos"])

AdminOuCoordenador = Annotated[dict, Depends(require_roles("admin", "coordenador"))]


@router.get("", response_model=dict, summary="Listar alunos", description="Filtros: `curso_id`, `status` (ativo/inativo/formado/transferido), `busca` (nome, CPF ou matrícula).")
async def list_alunos(
    db: SessionDep,
    _: CurrentUser,
    curso_id: Optional[int] = None,
    status: Optional[str] = None,
    busca: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    rows, total = await service.list_alunos(db, curso_id, status, busca, page, page_size)
    return {
        "data": [AlunoResponse.model_validate(r) for r in rows],
        "meta": {"total": total, "page": page, "page_size": page_size},
    }


@router.post("", response_model=AlunoResponse, status_code=201, summary="Cadastrar aluno", responses={409: {"description": "CPF ou e-mail já cadastrado"}})
async def create_aluno(body: AlunoCreate, db: SessionDep, _: AdminOuCoordenador):
    return await service.create_aluno(db, body)


@router.get("/{aluno_id}", response_model=AlunoResponse, summary="Buscar aluno por ID", responses={404: {"description": "Aluno não encontrado"}})
async def get_aluno(aluno_id: int, db: SessionDep, _: CurrentUser):
    return await service.get_aluno(db, aluno_id)


@router.put("/{aluno_id}", response_model=AlunoResponse, summary="Atualizar aluno", responses={404: {"description": "Aluno não encontrado"}})
async def update_aluno(
    aluno_id: int, body: AlunoUpdate, db: SessionDep, current_user: CurrentUser
):
    return await service.update_aluno(db, aluno_id, body, current_user)


@router.delete("/{aluno_id}", status_code=204, summary="Remover aluno (soft delete)", responses={404: {"description": "Aluno não encontrado"}})
async def delete_aluno(aluno_id: int, db: SessionDep, _: AdminOuCoordenador):
    await service.delete_aluno(db, aluno_id)
