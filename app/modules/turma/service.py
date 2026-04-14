from datetime import date
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.db.models import Disciplina, Matricula, Professor, Semestre, Turma

STATUS_SEMESTRE = {"planejado", "ativo", "encerrado"}
STATUS_TURMA = {"aberta", "em_andamento", "encerrada", "cancelada"}
DIAS_VALIDOS = {"segunda", "terca", "quarta", "quinta", "sexta", "sabado"}


# ── Semestre ──────────────────────────────────────────────────────────────────

async def list_semestres(db: AsyncSession, page: int, page_size: int):
    q = select(Semestre).order_by(Semestre.ano.desc(), Semestre.periodo.desc())
    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    offset = (page - 1) * page_size
    rows = (await db.execute(q.offset(offset).limit(page_size))).scalars().all()
    return rows, total


async def get_semestre(db: AsyncSession, semestre_id: int) -> Semestre:
    s = await db.scalar(select(Semestre).where(Semestre.id == semestre_id))
    if not s:
        raise NotFoundError("Semestre")
    return s


async def create_semestre(db: AsyncSession, data) -> Semestre:
    if data.periodo not in (1, 2):
        raise ValidationError("Período deve ser 1 ou 2")

    existing = await db.scalar(
        select(Semestre).where(Semestre.ano == data.ano, Semestre.periodo == data.periodo)
    )
    if existing:
        raise ConflictError(f"Semestre {data.ano}/{data.periodo} já existe")

    d_inicio = date.fromisoformat(data.data_inicio)
    d_fim = date.fromisoformat(data.data_fim)
    if d_fim <= d_inicio:
        raise ValidationError("data_fim deve ser posterior a data_inicio")

    payload = data.model_dump()
    s = Semestre(
        ano=payload["ano"],
        periodo=payload["periodo"],
        data_inicio=d_inicio,
        data_fim=d_fim,
        data_limite_trancamento=date.fromisoformat(payload["data_limite_trancamento"])
        if payload.get("data_limite_trancamento") else None,
    )
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return s


async def update_semestre(db: AsyncSession, semestre_id: int, data) -> Semestre:
    s = await get_semestre(db, semestre_id)
    if s.status == "encerrado":
        raise ValidationError("Semestre encerrado não pode ser alterado")

    payload = data.model_dump(exclude_none=True)
    if "status" in payload and payload["status"] not in STATUS_SEMESTRE:
        raise ValidationError(f"Status inválido. Use: {', '.join(sorted(STATUS_SEMESTRE))}")

    for field, value in payload.items():
        if field in ("data_inicio", "data_fim", "data_limite_trancamento") and value:
            value = date.fromisoformat(value)
        setattr(s, field, value)

    await db.commit()
    await db.refresh(s)
    return s


async def encerrar_semestre(db: AsyncSession, semestre_id: int) -> Semestre:
    s = await get_semestre(db, semestre_id)
    if s.status == "encerrado":
        raise ValidationError("Semestre já está encerrado")

    s.status = "encerrado"

    # Encerra todas as turmas do semestre
    turmas = (await db.execute(
        select(Turma).where(Turma.semestre_id == semestre_id, Turma.status == "em_andamento")
    )).scalars().all()
    for turma in turmas:
        turma.status = "encerrada"

    await db.commit()
    await db.refresh(s)
    return s


# ── Turma ─────────────────────────────────────────────────────────────────────

async def list_turmas(
    db: AsyncSession,
    semestre_id: int | None,
    disciplina_id: int | None,
    professor_id: int | None,
    page: int,
    page_size: int,
):
    q = select(Turma)
    if semestre_id:
        q = q.where(Turma.semestre_id == semestre_id)
    if disciplina_id:
        q = q.where(Turma.disciplina_id == disciplina_id)
    if professor_id:
        q = q.where(Turma.professor_id == professor_id)

    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    offset = (page - 1) * page_size
    rows = (await db.execute(q.order_by(Turma.id).offset(offset).limit(page_size))).scalars().all()
    return rows, total


async def get_turma(db: AsyncSession, turma_id: int) -> Turma:
    t = await db.scalar(select(Turma).where(Turma.id == turma_id))
    if not t:
        raise NotFoundError("Turma")
    return t


async def create_turma(db: AsyncSession, data) -> Turma:
    # Valida referências
    semestre = await get_semestre(db, data.semestre_id)
    if semestre.status == "encerrado":
        raise ValidationError("Não é possível criar turma em semestre encerrado")

    prof = await db.scalar(select(Professor).where(Professor.id == data.professor_id, Professor.deleted_at.is_(None)))
    if not prof:
        raise NotFoundError("Professor")

    disc = await db.scalar(select(Disciplina).where(Disciplina.id == data.disciplina_id, Disciplina.ativa == True))
    if not disc:
        raise NotFoundError("Disciplina")

    # Código único no semestre
    existing = await db.scalar(
        select(Turma).where(Turma.codigo == data.codigo, Turma.semestre_id == data.semestre_id)
    )
    if existing:
        raise ConflictError(f"Código '{data.codigo}' já existe neste semestre")

    # Conflito de horário do professor
    if data.horario:
        await _verificar_conflito_horario(db, data.professor_id, data.semestre_id, data.horario, exclude_turma_id=None)

    payload = data.model_dump()
    if payload.get("horario"):
        payload["horario"] = [h.model_dump() if hasattr(h, "model_dump") else h for h in payload["horario"]]

    t = Turma(**payload)
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return t


async def update_turma(db: AsyncSession, turma_id: int, data) -> Turma:
    t = await get_turma(db, turma_id)
    if t.status in ("encerrada", "cancelada"):
        raise ValidationError("Turma encerrada/cancelada não pode ser alterada")

    payload = data.model_dump(exclude_none=True)

    if "status" in payload and payload["status"] not in STATUS_TURMA:
        raise ValidationError(f"Status inválido. Use: {', '.join(sorted(STATUS_TURMA))}")

    if "horario" in payload and payload["horario"]:
        await _verificar_conflito_horario(db, t.professor_id, t.semestre_id, payload["horario"], exclude_turma_id=turma_id)
        payload["horario"] = [h.model_dump() if hasattr(h, "model_dump") else h for h in payload["horario"]]

    for field, value in payload.items():
        setattr(t, field, value)

    await db.commit()
    await db.refresh(t)
    return t


async def delete_turma(db: AsyncSession, turma_id: int) -> None:
    t = await get_turma(db, turma_id)

    matriculas = await db.scalar(
        select(func.count(Matricula.id)).where(Matricula.turma_id == turma_id)
    )
    if matriculas:
        raise ValidationError(f"Turma possui {matriculas} matrícula(s) e não pode ser cancelada")

    t.status = "cancelada"
    await db.commit()


async def get_alunos_turma(db: AsyncSession, turma_id: int, page: int, page_size: int):
    await get_turma(db, turma_id)

    from app.db.models import Aluno
    q = (
        select(Aluno)
        .join(Matricula, Matricula.aluno_id == Aluno.id)
        .where(Matricula.turma_id == turma_id, Matricula.status == "ativa")
    )
    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    offset = (page - 1) * page_size
    rows = (await db.execute(q.order_by(Aluno.nome).offset(offset).limit(page_size))).scalars().all()
    return rows, total


async def _verificar_conflito_horario(db, professor_id, semestre_id, novo_horario, exclude_turma_id):
    """Verifica se o professor tem conflito de horário no semestre."""
    q = select(Turma).where(
        Turma.professor_id == professor_id,
        Turma.semestre_id == semestre_id,
        Turma.status.notin_(["cancelada", "encerrada"]),
        Turma.horario.isnot(None),
    )
    if exclude_turma_id:
        q = q.where(Turma.id != exclude_turma_id)

    turmas_existentes = (await db.execute(q)).scalars().all()

    for turma in turmas_existentes:
        if not turma.horario:
            continue
        for h_existente in turma.horario:
            for h_novo in novo_horario:
                dia_novo = h_novo.dia if hasattr(h_novo, "dia") else h_novo["dia"]
                dia_existente = h_existente.get("dia") if isinstance(h_existente, dict) else h_existente

                if dia_novo != dia_existente:
                    continue

                ini_novo = h_novo.hora_inicio if hasattr(h_novo, "hora_inicio") else h_novo["hora_inicio"]
                fim_novo = h_novo.hora_fim if hasattr(h_novo, "hora_fim") else h_novo["hora_fim"]
                ini_ex = h_existente.get("hora_inicio") if isinstance(h_existente, dict) else h_existente
                fim_ex = h_existente.get("hora_fim") if isinstance(h_existente, dict) else h_existente

                # Sobreposição: ini_novo < fim_ex AND fim_novo > ini_ex
                if ini_novo < fim_ex and fim_novo > ini_ex:
                    raise ConflictError(
                        f"Professor já tem aula na {dia_novo} entre {ini_ex} e {fim_ex} (turma {turma.codigo})"
                    )
