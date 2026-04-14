from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.db.models import Aluno, Curso

STATUS_VALIDOS = {"ativo", "trancado", "formado", "cancelado"}


def _gerar_matricula(ano: int, sequencial: int) -> str:
    return f"{ano}{sequencial:04d}"


async def _proximo_sequencial(db: AsyncSession, ano: int) -> int:
    prefixo = str(ano)
    resultado = await db.scalar(
        select(func.count(Aluno.id)).where(Aluno.matricula.like(f"{prefixo}%"))
    )
    return (resultado or 0) + 1


async def list_alunos(
    db: AsyncSession,
    curso_id: int | None,
    status: str | None,
    busca: str | None,
    page: int,
    page_size: int,
):
    q = select(Aluno).where(Aluno.deleted_at.is_(None))
    if curso_id:
        q = q.where(Aluno.curso_id == curso_id)
    if status:
        q = q.where(Aluno.status == status)
    if busca:
        q = q.where(or_(
            Aluno.nome.ilike(f"%{busca}%"),
            Aluno.matricula.ilike(f"%{busca}%"),
        ))

    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    offset = (page - 1) * page_size
    rows = (await db.execute(q.order_by(Aluno.nome).offset(offset).limit(page_size))).scalars().all()
    return rows, total


async def get_aluno(db: AsyncSession, aluno_id: int) -> Aluno:
    aluno = await db.scalar(
        select(Aluno).where(Aluno.id == aluno_id, Aluno.deleted_at.is_(None))
    )
    if not aluno:
        raise NotFoundError("Aluno")
    return aluno


async def create_aluno(db: AsyncSession, data) -> Aluno:
    # Valida curso
    curso = await db.scalar(select(Curso).where(Curso.id == data.curso_id, Curso.deleted_at.is_(None)))
    if not curso:
        raise NotFoundError("Curso")

    # Unicidade
    if await db.scalar(select(Aluno.id).where(Aluno.cpf == data.cpf)):
        raise ConflictError("CPF já cadastrado")
    if await db.scalar(select(Aluno.id).where(Aluno.email == data.email)):
        raise ConflictError("Email já cadastrado")

    ano = datetime.now(timezone.utc).year
    seq = await _proximo_sequencial(db, ano)
    matricula = _gerar_matricula(ano, seq)

    payload = data.model_dump()
    if payload.get("endereco"):
        payload["endereco"] = payload["endereco"]  # já é dict pelo Pydantic

    aluno = Aluno(**payload, matricula=matricula)
    db.add(aluno)
    await db.commit()
    await db.refresh(aluno)
    return aluno


async def update_aluno(db: AsyncSession, aluno_id: int, data, current_user: dict) -> Aluno:
    aluno = await get_aluno(db, aluno_id)

    # Aluno só pode editar seus próprios dados
    if current_user["role"] == "aluno":
        usuario_aluno_id = await _get_aluno_id_do_usuario(db, current_user["id"])
        if usuario_aluno_id != aluno_id:
            raise ForbiddenError("Você só pode editar seus próprios dados")

    payload = data.model_dump(exclude_none=True)

    if "status" in payload and payload["status"] not in STATUS_VALIDOS:
        raise ValidationError(f"Status inválido. Use: {', '.join(sorted(STATUS_VALIDOS))}")

    if "email" in payload:
        conflito = await db.scalar(
            select(Aluno.id).where(Aluno.email == payload["email"], Aluno.id != aluno_id)
        )
        if conflito:
            raise ConflictError("Email já cadastrado")

    for field, value in payload.items():
        setattr(aluno, field, value)

    await db.commit()
    await db.refresh(aluno)
    return aluno


async def delete_aluno(db: AsyncSession, aluno_id: int) -> None:
    aluno = await get_aluno(db, aluno_id)
    aluno.deleted_at = datetime.now(timezone.utc)
    aluno.status = "cancelado"
    await db.commit()


async def _get_aluno_id_do_usuario(db: AsyncSession, usuario_id: int) -> int | None:
    from app.db.models import Usuario
    usuario = await db.scalar(select(Usuario).where(Usuario.id == usuario_id))
    return usuario.aluno_id if usuario else None
