from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.db.models import Campus, Curso, Departamento


# ── Helpers ──────────────────────────────────────────────────────────────────

def _paginate(query, page: int, page_size: int):
    offset = (page - 1) * page_size
    return query.offset(offset).limit(page_size)


# ── Campus ───────────────────────────────────────────────────────────────────

async def list_campus(db: AsyncSession, page: int = 1, page_size: int = 20, apenas_ativos: bool = True):
    q = select(Campus).where(Campus.deleted_at.is_(None))
    if apenas_ativos:
        q = q.where(Campus.ativo == True)

    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    rows = (await db.execute(_paginate(q.order_by(Campus.nome), page, page_size))).scalars().all()

    return rows, total


async def get_campus(db: AsyncSession, campus_id: int) -> Campus:
    campus = await db.scalar(
        select(Campus).where(Campus.id == campus_id, Campus.deleted_at.is_(None))
    )
    if not campus:
        raise NotFoundError("Campus")
    return campus


async def create_campus(db: AsyncSession, data) -> Campus:
    campus = Campus(**data.model_dump())
    db.add(campus)
    await db.commit()
    await db.refresh(campus)
    return campus


async def update_campus(db: AsyncSession, campus_id: int, data) -> Campus:
    campus = await get_campus(db, campus_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(campus, field, value)
    await db.commit()
    await db.refresh(campus)
    return campus


async def delete_campus(db: AsyncSession, campus_id: int) -> None:
    campus = await get_campus(db, campus_id)

    # Verifica se há departamentos ativos vinculados
    total_deps = await db.scalar(
        select(func.count(Departamento.id)).where(
            Departamento.campus_id == campus_id,
            Departamento.deleted_at.is_(None),
        )
    )
    if total_deps:
        raise ValidationError(f"Campus possui {total_deps} departamento(s) ativo(s) e não pode ser removido")

    from datetime import datetime, timezone
    campus.deleted_at = datetime.now(timezone.utc)
    campus.ativo = False
    await db.commit()


# ── Departamento ─────────────────────────────────────────────────────────────

async def list_departamentos(
    db: AsyncSession, campus_id: int | None = None, page: int = 1, page_size: int = 20
):
    q = select(Departamento).where(Departamento.deleted_at.is_(None))
    if campus_id:
        q = q.where(Departamento.campus_id == campus_id)

    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    rows = (await db.execute(_paginate(q.order_by(Departamento.nome), page, page_size))).scalars().all()
    return rows, total


async def get_departamento(db: AsyncSession, dep_id: int) -> Departamento:
    dep = await db.scalar(
        select(Departamento).where(Departamento.id == dep_id, Departamento.deleted_at.is_(None))
    )
    if not dep:
        raise NotFoundError("Departamento")
    return dep


async def create_departamento(db: AsyncSession, data) -> Departamento:
    # Valida campus
    await get_campus(db, data.campus_id)

    dep = Departamento(**data.model_dump())
    db.add(dep)
    await db.commit()
    await db.refresh(dep)
    return dep


async def update_departamento(db: AsyncSession, dep_id: int, data) -> Departamento:
    dep = await get_departamento(db, dep_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(dep, field, value)
    await db.commit()
    await db.refresh(dep)
    return dep


async def delete_departamento(db: AsyncSession, dep_id: int) -> None:
    dep = await get_departamento(db, dep_id)

    total_cursos = await db.scalar(
        select(func.count(Curso.id)).where(
            Curso.departamento_id == dep_id,
            Curso.deleted_at.is_(None),
        )
    )
    if total_cursos:
        raise ValidationError(f"Departamento possui {total_cursos} curso(s) e não pode ser removido")

    from datetime import datetime, timezone
    dep.deleted_at = datetime.now(timezone.utc)
    dep.ativo = False
    await db.commit()


# ── Curso ────────────────────────────────────────────────────────────────────

GRAUS_VALIDOS = {"bacharelado", "licenciatura", "tecnologo", "pos_graduacao"}
MODALIDADES_VALIDAS = {"presencial", "ead", "hibrido"}


async def list_cursos(
    db: AsyncSession,
    campus_id: int | None = None,
    modalidade: str | None = None,
    page: int = 1,
    page_size: int = 20,
):
    q = select(Curso).where(Curso.deleted_at.is_(None), Curso.ativo == True)
    if modalidade:
        q = q.where(Curso.modalidade == modalidade)
    if campus_id:
        q = q.join(Departamento).where(Departamento.campus_id == campus_id)

    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    rows = (await db.execute(_paginate(q.order_by(Curso.nome), page, page_size))).scalars().all()
    return rows, total


async def get_curso(db: AsyncSession, curso_id: int) -> Curso:
    curso = await db.scalar(
        select(Curso).where(Curso.id == curso_id, Curso.deleted_at.is_(None))
    )
    if not curso:
        raise NotFoundError("Curso")
    return curso


async def create_curso(db: AsyncSession, data) -> Curso:
    if data.grau not in GRAUS_VALIDOS:
        raise ValidationError(f"Grau inválido. Use: {', '.join(sorted(GRAUS_VALIDOS))}")
    if data.modalidade not in MODALIDADES_VALIDAS:
        raise ValidationError(f"Modalidade inválida. Use: {', '.join(sorted(MODALIDADES_VALIDAS))}")

    # Valida departamento
    await get_departamento(db, data.departamento_id)

    existing = await db.scalar(select(Curso).where(Curso.codigo == data.codigo))
    if existing:
        raise ConflictError(f"Código '{data.codigo}' já está em uso")

    curso = Curso(**data.model_dump())
    db.add(curso)
    await db.commit()
    await db.refresh(curso)
    return curso


async def update_curso(db: AsyncSession, curso_id: int, data) -> Curso:
    curso = await get_curso(db, curso_id)
    payload = data.model_dump(exclude_none=True)

    if "grau" in payload and payload["grau"] not in GRAUS_VALIDOS:
        raise ValidationError(f"Grau inválido. Use: {', '.join(sorted(GRAUS_VALIDOS))}")
    if "modalidade" in payload and payload["modalidade"] not in MODALIDADES_VALIDAS:
        raise ValidationError(f"Modalidade inválida. Use: {', '.join(sorted(MODALIDADES_VALIDAS))}")

    for field, value in payload.items():
        setattr(curso, field, value)
    await db.commit()
    await db.refresh(curso)
    return curso


async def delete_curso(db: AsyncSession, curso_id: int) -> None:
    from app.db.models import Aluno
    curso = await get_curso(db, curso_id)

    alunos_ativos = await db.scalar(
        select(func.count(Aluno.id)).where(
            Aluno.curso_id == curso_id,
            Aluno.status == "ativo",
            Aluno.deleted_at.is_(None),
        )
    )
    if alunos_ativos:
        raise ValidationError(f"Curso possui {alunos_ativos} aluno(s) ativo(s) e não pode ser removido")

    from datetime import datetime, timezone
    curso.deleted_at = datetime.now(timezone.utc)
    curso.ativo = False
    await db.commit()
