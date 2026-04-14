from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query

from app.core.deps import CurrentUser, SessionDep, require_roles
from app.modules.matricula import service
from app.modules.matricula.schemas import MatriculaCreate, MatriculaDetalhe, MatriculaResponse

router = APIRouter(tags=["Matrículas"])

AdminOuCoordenador = Annotated[dict, Depends(require_roles("admin", "coordenador"))]


# ── Listagem geral ─────────────────────────────────────────────────────────────

@router.get("/matriculas", response_model=dict, summary="Listar matrículas", description="Filtros: `aluno_id`, `turma_id`, `status` (ativa/trancada/cancelada).")
async def list_matriculas(
    db: SessionDep,
    _: AdminOuCoordenador,
    aluno_id: Optional[int] = None,
    turma_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    rows, total = await service.list_matriculas(db, aluno_id, turma_id, status, page, page_size)
    return {
        "data": [MatriculaResponse.model_validate(r) for r in rows],
        "meta": {"total": total, "page": page, "page_size": page_size},
    }


# ── CRUD básico ────────────────────────────────────────────────────────────────

@router.post("/matriculas", response_model=MatriculaResponse, status_code=201, summary="Realizar matrícula",
    description="Valida pré-requisitos, vagas disponíveis, status do aluno/turma/semestre e duplicatas.",
    responses={409: {"description": "Duplicata ou sem vagas"}, 422: {"description": "Pré-requisito não cumprido ou regra de negócio violada"}})
async def create_matricula(body: MatriculaCreate, db: SessionDep, _: AdminOuCoordenador):
    return await service.create_matricula(db, body)


@router.get("/matriculas/{matricula_id}", response_model=MatriculaResponse, summary="Buscar matrícula por ID",
    responses={404: {"description": "Matrícula não encontrada"}})
async def get_matricula(matricula_id: int, db: SessionDep, _: CurrentUser):
    return await service.get_matricula(db, matricula_id)


# ── Ações de estado ────────────────────────────────────────────────────────────

@router.put("/matriculas/{matricula_id}/trancar", response_model=MatriculaResponse)
async def trancar_matricula(
    matricula_id: int,
    db: SessionDep,
    usuario_atual: CurrentUser,
):
    """
    Tranca a matrícula.
    - Aluno: só pode trancar as próprias matrículas, respeitando prazo do semestre.
    - Admin/Coordenador: pode trancar qualquer matrícula.
    """
    return await service.trancar_matricula(db, matricula_id, usuario_atual)


@router.put("/matriculas/{matricula_id}/cancelar", response_model=MatriculaResponse)
async def cancelar_matricula(matricula_id: int, db: SessionDep, _: AdminOuCoordenador):
    return await service.cancelar_matricula(db, matricula_id)


# ── Endpoints auxiliares ───────────────────────────────────────────────────────

@router.get("/alunos/{aluno_id}/matriculas", response_model=dict)
async def get_matriculas_aluno(
    aluno_id: int,
    db: SessionDep,
    _: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Histórico de matrículas de um aluno com dados da turma/disciplina/semestre."""
    rows, total = await service.get_matriculas_aluno(db, aluno_id, page, page_size)
    return {
        "data": [MatriculaDetalhe.model_validate(r) for r in rows],
        "meta": {"total": total, "page": page, "page_size": page_size},
    }


@router.get("/turmas/{turma_id}/vagas", response_model=dict)
async def get_vagas_turma(turma_id: int, db: SessionDep, _: CurrentUser):
    """Retorna situação de vagas da turma (total, ocupadas, disponíveis)."""
    return await service.get_vagas_turma(db, turma_id)
