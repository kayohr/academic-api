from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.db.models import Departamento, Disciplina, GradeCurricular, Prerequisito, Turma

TIPOS_VALIDOS = {"obrigatoria", "optativa", "eletiva"}


# ── Disciplina ────────────────────────────────────────────────────────────────

async def list_disciplinas(
    db: AsyncSession,
    departamento_id: int | None,
    page: int,
    page_size: int,
):
    q = select(Disciplina).where(Disciplina.ativa == True)
    if departamento_id:
        q = q.where(Disciplina.departamento_id == departamento_id)

    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    offset = (page - 1) * page_size
    rows = (await db.execute(q.order_by(Disciplina.codigo).offset(offset).limit(page_size))).scalars().all()
    return rows, total


async def get_disciplina(db: AsyncSession, disciplina_id: int) -> Disciplina:
    d = await db.scalar(select(Disciplina).where(Disciplina.id == disciplina_id))
    if not d:
        raise NotFoundError("Disciplina")
    return d


async def create_disciplina(db: AsyncSession, data) -> Disciplina:
    dep = await db.scalar(
        select(Departamento).where(Departamento.id == data.departamento_id, Departamento.deleted_at.is_(None))
    )
    if not dep:
        raise NotFoundError("Departamento")

    if await db.scalar(select(Disciplina.id).where(Disciplina.codigo == data.codigo)):
        raise ConflictError(f"Código '{data.codigo}' já está em uso")

    d = Disciplina(**data.model_dump())
    db.add(d)
    await db.commit()
    await db.refresh(d)
    return d


async def update_disciplina(db: AsyncSession, disciplina_id: int, data) -> Disciplina:
    d = await get_disciplina(db, disciplina_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(d, field, value)
    await db.commit()
    await db.refresh(d)
    return d


# ── Grade Curricular ──────────────────────────────────────────────────────────

async def get_grade(db: AsyncSession, curso_id: int) -> list:
    rows = (
        await db.execute(
            select(GradeCurricular)
            .where(GradeCurricular.curso_id == curso_id)
            .options(selectinload(GradeCurricular.disciplina))
            .order_by(GradeCurricular.periodo, GradeCurricular.id)
        )
    ).scalars().all()
    return rows


async def add_disciplina_grade(db: AsyncSession, curso_id: int, data) -> GradeCurricular:
    from app.db.models import Curso
    curso = await db.scalar(select(Curso).where(Curso.id == curso_id, Curso.deleted_at.is_(None)))
    if not curso:
        raise NotFoundError("Curso")

    await get_disciplina(db, data.disciplina_id)

    if data.tipo not in TIPOS_VALIDOS:
        raise ValidationError(f"Tipo inválido. Use: {', '.join(sorted(TIPOS_VALIDOS))}")

    existing = await db.scalar(
        select(GradeCurricular).where(
            GradeCurricular.curso_id == curso_id,
            GradeCurricular.disciplina_id == data.disciplina_id,
        )
    )
    if existing:
        raise ConflictError("Disciplina já está na grade deste curso")

    item = GradeCurricular(curso_id=curso_id, **data.model_dump())
    db.add(item)
    await db.commit()

    item = await db.scalar(
        select(GradeCurricular)
        .where(GradeCurricular.id == item.id)
        .options(selectinload(GradeCurricular.disciplina))
    )
    return item


async def remove_disciplina_grade(db: AsyncSession, curso_id: int, disciplina_id: int) -> None:
    # Bloqueia se houver turmas abertas para essa disciplina no curso
    turmas_abertas = await db.scalar(
        select(func.count(Turma.id)).where(
            Turma.disciplina_id == disciplina_id,
            Turma.status.in_(["aberta", "em_andamento"]),
        )
    )
    if turmas_abertas:
        raise ValidationError("Não é possível remover disciplina com turmas abertas")

    item = await db.scalar(
        select(GradeCurricular).where(
            GradeCurricular.curso_id == curso_id,
            GradeCurricular.disciplina_id == disciplina_id,
        )
    )
    if not item:
        raise NotFoundError("Disciplina na grade")

    await db.delete(item)
    await db.commit()


# ── Pré-requisitos ────────────────────────────────────────────────────────────

async def add_prerequisito(db: AsyncSession, disciplina_id: int, prerequisito_id: int) -> None:
    await get_disciplina(db, disciplina_id)
    await get_disciplina(db, prerequisito_id)

    if disciplina_id == prerequisito_id:
        raise ValidationError("Uma disciplina não pode ser pré-requisito de si mesma")

    # Detecta ciclo: verifica se disciplina_id já é pré-requisito de prerequisito_id
    if await _tem_ciclo(db, prerequisito_id, disciplina_id):
        raise ValidationError("Ciclo detectado: adicionando esse pré-requisito criaria uma dependência circular")

    existing = await db.scalar(
        select(Prerequisito).where(
            Prerequisito.disciplina_id == disciplina_id,
            Prerequisito.prerequisito_id == prerequisito_id,
        )
    )
    if existing:
        raise ConflictError("Pré-requisito já cadastrado")

    db.add(Prerequisito(disciplina_id=disciplina_id, prerequisito_id=prerequisito_id))
    await db.commit()


async def remove_prerequisito(db: AsyncSession, disciplina_id: int, prerequisito_id: int) -> None:
    item = await db.scalar(
        select(Prerequisito).where(
            Prerequisito.disciplina_id == disciplina_id,
            Prerequisito.prerequisito_id == prerequisito_id,
        )
    )
    if not item:
        raise NotFoundError("Pré-requisito")
    await db.delete(item)
    await db.commit()


async def _tem_ciclo(db: AsyncSession, origem: int, destino: int) -> bool:
    """BFS: verifica se 'destino' é alcançável a partir de 'origem' pelos pré-requisitos."""
    visitados = set()
    fila = [origem]
    while fila:
        atual = fila.pop(0)
        if atual == destino:
            return True
        if atual in visitados:
            continue
        visitados.add(atual)
        filhos = (await db.execute(
            select(Prerequisito.prerequisito_id).where(Prerequisito.disciplina_id == atual)
        )).scalars().all()
        fila.extend(filhos)
    return False
