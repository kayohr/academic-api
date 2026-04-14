from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.db.models import Departamento, Professor, Turma

TITULACOES_VALIDAS = {"graduacao", "especializacao", "mestrado", "doutorado"}
REGIMES_VALIDOS = {"20h", "40h", "DE"}
STATUS_VALIDOS = {"ativo", "inativo", "afastado"}


async def list_professores(
    db: AsyncSession,
    departamento_id: int | None,
    titulacao: str | None,
    page: int,
    page_size: int,
):
    q = select(Professor).where(Professor.deleted_at.is_(None))
    if departamento_id:
        q = q.where(Professor.departamento_id == departamento_id)
    if titulacao:
        q = q.where(Professor.titulacao == titulacao)

    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    offset = (page - 1) * page_size
    rows = (await db.execute(q.order_by(Professor.nome).offset(offset).limit(page_size))).scalars().all()
    return rows, total


async def get_professor(db: AsyncSession, professor_id: int) -> Professor:
    prof = await db.scalar(
        select(Professor).where(Professor.id == professor_id, Professor.deleted_at.is_(None))
    )
    if not prof:
        raise NotFoundError("Professor")
    return prof


async def create_professor(db: AsyncSession, data) -> Professor:
    # Valida departamento
    dep = await db.scalar(
        select(Departamento).where(Departamento.id == data.departamento_id, Departamento.deleted_at.is_(None))
    )
    if not dep:
        raise NotFoundError("Departamento")

    if data.titulacao not in TITULACOES_VALIDAS:
        raise ValidationError(f"Titulação inválida. Use: {', '.join(sorted(TITULACOES_VALIDAS))}")
    if data.regime not in REGIMES_VALIDOS:
        raise ValidationError(f"Regime inválido. Use: {', '.join(sorted(REGIMES_VALIDOS))}")

    if await db.scalar(select(Professor.id).where(Professor.cpf == data.cpf)):
        raise ConflictError("CPF já cadastrado")
    if await db.scalar(select(Professor.id).where(Professor.email == data.email)):
        raise ConflictError("Email já cadastrado")
    if await db.scalar(select(Professor.id).where(Professor.siape == data.siape)):
        raise ConflictError("SIAPE já cadastrado")

    prof = Professor(**data.model_dump())
    db.add(prof)
    await db.commit()
    await db.refresh(prof)
    return prof


async def update_professor(db: AsyncSession, professor_id: int, data) -> Professor:
    prof = await get_professor(db, professor_id)
    payload = data.model_dump(exclude_none=True)

    if "titulacao" in payload and payload["titulacao"] not in TITULACOES_VALIDAS:
        raise ValidationError(f"Titulação inválida. Use: {', '.join(sorted(TITULACOES_VALIDAS))}")
    if "regime" in payload and payload["regime"] not in REGIMES_VALIDOS:
        raise ValidationError(f"Regime inválido. Use: {', '.join(sorted(REGIMES_VALIDOS))}")
    if "status" in payload and payload["status"] not in STATUS_VALIDOS:
        raise ValidationError(f"Status inválido. Use: {', '.join(sorted(STATUS_VALIDOS))}")

    if "email" in payload:
        conflito = await db.scalar(
            select(Professor.id).where(Professor.email == payload["email"], Professor.id != professor_id)
        )
        if conflito:
            raise ConflictError("Email já cadastrado")

    for field, value in payload.items():
        setattr(prof, field, value)

    await db.commit()
    await db.refresh(prof)
    return prof


async def delete_professor(db: AsyncSession, professor_id: int) -> None:
    prof = await get_professor(db, professor_id)

    turmas_ativas = await db.scalar(
        select(func.count(Turma.id)).where(
            Turma.professor_id == professor_id,
            Turma.status.in_(["aberta", "em_andamento"]),
        )
    )
    if turmas_ativas:
        raise ValidationError(f"Professor possui {turmas_ativas} turma(s) ativa(s) e não pode ser removido")

    prof.deleted_at = datetime.now(timezone.utc)
    prof.status = "inativo"
    await db.commit()


async def get_turmas_professor(
    db: AsyncSession,
    professor_id: int,
    semestre_id: int | None,
    page: int,
    page_size: int,
):
    await get_professor(db, professor_id)

    q = select(Turma).where(Turma.professor_id == professor_id)
    if semestre_id:
        q = q.where(Turma.semestre_id == semestre_id)

    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    offset = (page - 1) * page_size
    rows = (await db.execute(q.order_by(Turma.id).offset(offset).limit(page_size))).scalars().all()
    return rows, total
