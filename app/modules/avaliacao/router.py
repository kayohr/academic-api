from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.deps import CurrentUser, SessionDep, require_roles
from app.modules.avaliacao import service
from app.modules.avaliacao.schemas import (
    FrequenciaCreate,
    FrequenciaResponse,
    FrequenciaUpdate,
    FrequenciaTurmaItem,
    NotaCreate,
    NotaResponse,
    NotaUpdate,
    ResumoAvaliacaoResponse,
)

router = APIRouter(tags=["Notas & Frequência"])

ProfessorOuSuperior = Annotated[dict, Depends(require_roles("admin", "coordenador", "professor"))]


# ── Notas ─────────────────────────────────────────────────────────────────────

@router.get("/matriculas/{matricula_id}/notas", response_model=list[NotaResponse])
async def list_notas(matricula_id: int, db: SessionDep, _: CurrentUser):
    return await service.list_notas(db, matricula_id)


@router.post("/matriculas/{matricula_id}/notas", response_model=NotaResponse, status_code=201)
async def create_nota(
    matricula_id: int,
    body: NotaCreate,
    db: SessionDep,
    usuario_atual: ProfessorOuSuperior,
):
    return await service.create_nota(db, matricula_id, body, usuario_atual)


@router.put("/notas/{nota_id}", response_model=NotaResponse)
async def update_nota(
    nota_id: int,
    body: NotaUpdate,
    db: SessionDep,
    usuario_atual: ProfessorOuSuperior,
):
    return await service.update_nota(db, nota_id, body, usuario_atual)


# ── Frequência ────────────────────────────────────────────────────────────────

@router.get("/matriculas/{matricula_id}/frequencias", response_model=list[FrequenciaResponse])
async def list_frequencias(matricula_id: int, db: SessionDep, _: CurrentUser):
    return await service.list_frequencias(db, matricula_id)


@router.post("/matriculas/{matricula_id}/frequencias", response_model=FrequenciaResponse, status_code=201)
async def create_frequencia(
    matricula_id: int,
    body: FrequenciaCreate,
    db: SessionDep,
    usuario_atual: ProfessorOuSuperior,
):
    return await service.create_frequencia(db, matricula_id, body, usuario_atual)


@router.put("/frequencias/{frequencia_id}", response_model=FrequenciaResponse)
async def update_frequencia(
    frequencia_id: int,
    body: FrequenciaUpdate,
    db: SessionDep,
    usuario_atual: ProfessorOuSuperior,
):
    return await service.update_frequencia(db, frequencia_id, body, usuario_atual)


# ── Resumo e consolidado ──────────────────────────────────────────────────────

@router.get("/matriculas/{matricula_id}/resumo", response_model=ResumoAvaliacaoResponse)
async def get_resumo(matricula_id: int, db: SessionDep, _: CurrentUser):
    """Retorna notas, média, frequência e situação atual da matrícula."""
    return await service.get_resumo(db, matricula_id)


@router.get("/turmas/{turma_id}/frequencias", response_model=list[FrequenciaTurmaItem])
async def get_frequencia_turma(
    turma_id: int,
    db: SessionDep,
    _: ProfessorOuSuperior,
):
    """Frequência consolidada de todos os alunos da turma."""
    return await service.get_frequencia_turma(db, turma_id)
