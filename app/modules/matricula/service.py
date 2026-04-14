from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.db.models import (
    Aluno, Disciplina, GradeCurricular, Historico,
    Matricula, Prerequisito, Semestre, Turma,
)

STATUS_VALIDOS = {"ativa", "trancada", "cancelada"}


# ── Helpers internos ──────────────────────────────────────────────────────────

async def _get_aluno(db: AsyncSession, aluno_id: int) -> Aluno:
    a = await db.scalar(
        select(Aluno).where(Aluno.id == aluno_id, Aluno.deleted_at.is_(None))
    )
    if not a:
        raise NotFoundError("Aluno")
    return a


async def _get_turma(db: AsyncSession, turma_id: int) -> Turma:
    t = await db.scalar(select(Turma).where(Turma.id == turma_id))
    if not t:
        raise NotFoundError("Turma")
    return t


async def _get_matricula(db: AsyncSession, matricula_id: int) -> Matricula:
    m = await db.scalar(select(Matricula).where(Matricula.id == matricula_id))
    if not m:
        raise NotFoundError("Matrícula")
    return m


async def _verificar_prerequisitos(db: AsyncSession, aluno_id: int, disciplina_id: int) -> None:
    """Garante que o aluno tenha aprovação em todos os pré-requisitos da disciplina."""
    prerequisitos = (await db.execute(
        select(Prerequisito).where(Prerequisito.disciplina_id == disciplina_id)
    )).scalars().all()

    if not prerequisitos:
        return

    for pre in prerequisitos:
        aprovado = await db.scalar(
            select(Historico).where(
                Historico.aluno_id == aluno_id,
                Historico.disciplina_id == pre.prerequisito_id,
                Historico.situacao == "aprovado",
            )
        )
        if not aprovado:
            # Busca nome da disciplina pré-requisito para mensagem clara
            disc = await db.scalar(
                select(Disciplina).where(Disciplina.id == pre.prerequisito_id)
            )
            nome = disc.nome if disc else f"id={pre.prerequisito_id}"
            raise ValidationError(
                f"Pré-requisito não cumprido: '{nome}'. "
                "O aluno precisa ter aprovação nessa disciplina antes de se matricular."
            )


async def _contar_vagas_ocupadas(db: AsyncSession, turma_id: int) -> int:
    return await db.scalar(
        select(func.count(Matricula.id)).where(
            Matricula.turma_id == turma_id,
            Matricula.status == "ativa",
        )
    ) or 0


# ── CRUD ──────────────────────────────────────────────────────────────────────

async def list_matriculas(
    db: AsyncSession,
    aluno_id: int | None,
    turma_id: int | None,
    status: str | None,
    page: int,
    page_size: int,
):
    q = select(Matricula)
    if aluno_id:
        q = q.where(Matricula.aluno_id == aluno_id)
    if turma_id:
        q = q.where(Matricula.turma_id == turma_id)
    if status:
        q = q.where(Matricula.status == status)

    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    offset = (page - 1) * page_size
    rows = (await db.execute(
        q.order_by(Matricula.id).offset(offset).limit(page_size)
    )).scalars().all()
    return rows, total


async def get_matricula(db: AsyncSession, matricula_id: int) -> Matricula:
    return await _get_matricula(db, matricula_id)


async def create_matricula(db: AsyncSession, data) -> Matricula:
    aluno = await _get_aluno(db, data.aluno_id)
    if aluno.status != "ativo":
        raise ValidationError("Aluno inativo não pode realizar matrículas")

    turma = await _get_turma(db, data.turma_id)
    if turma.status not in ("aberta", "em_andamento"):
        raise ValidationError(
            f"Turma com status '{turma.status}' não aceita novas matrículas"
        )

    # Semestre deve estar ativo
    semestre = await db.scalar(select(Semestre).where(Semestre.id == turma.semestre_id))
    if semestre and semestre.status != "ativo":
        raise ValidationError(
            f"Semestre com status '{semestre.status}' não está aberto para matrículas"
        )

    # Duplicata
    existente = await db.scalar(
        select(Matricula).where(
            Matricula.aluno_id == data.aluno_id,
            Matricula.turma_id == data.turma_id,
        )
    )
    if existente:
        if existente.status == "cancelada":
            raise ConflictError(
                "Matrícula cancelada nesta turma. Entre em contato com a secretaria para reativação."
            )
        raise ConflictError("Aluno já está matriculado nesta turma")

    # Verifica se o aluno já tem matrícula ativa em outra turma da MESMA disciplina no mesmo semestre
    conflito_disciplina = await db.scalar(
        select(Matricula)
        .join(Turma, Turma.id == Matricula.turma_id)
        .where(
            Matricula.aluno_id == data.aluno_id,
            Matricula.status == "ativa",
            Turma.disciplina_id == turma.disciplina_id,
            Turma.semestre_id == turma.semestre_id,
        )
    )
    if conflito_disciplina:
        raise ConflictError("Aluno já possui matrícula ativa nesta disciplina no semestre corrente")

    # Pré-requisitos
    await _verificar_prerequisitos(db, data.aluno_id, turma.disciplina_id)

    # Vagas
    ocupadas = await _contar_vagas_ocupadas(db, data.turma_id)
    if ocupadas >= turma.vagas:
        raise ValidationError(
            f"Turma sem vagas disponíveis ({ocupadas}/{turma.vagas})"
        )

    m = Matricula(aluno_id=data.aluno_id, turma_id=data.turma_id, status="ativa")
    db.add(m)
    await db.commit()
    await db.refresh(m)
    return m


async def trancar_matricula(db: AsyncSession, matricula_id: int, usuario_atual: dict) -> Matricula:
    m = await _get_matricula(db, matricula_id)

    if m.status != "ativa":
        raise ValidationError(
            f"Apenas matrículas ativas podem ser trancadas (status atual: '{m.status}')"
        )

    # Busca semestre via turma para verificar prazo
    turma = await _get_turma(db, m.turma_id)
    semestre = await db.scalar(select(Semestre).where(Semestre.id == turma.semestre_id))

    if semestre and semestre.data_limite_trancamento:
        from datetime import date
        if date.today() > semestre.data_limite_trancamento:
            raise ValidationError(
                f"Prazo de trancamento encerrado em {semestre.data_limite_trancamento.strftime('%d/%m/%Y')}"
            )

    # Aluno só pode trancar suas próprias matrículas; admin/coordenador podem trancar qualquer uma
    if usuario_atual["role"] == "aluno":
        aluno = await db.scalar(
            select(Aluno).join(
                "usuario", isouter=False
            ).where(Aluno.id == m.aluno_id)
        )
        # Verifica via usuario_id associado ao aluno
        from app.db.models import Usuario
        vinculo = await db.scalar(
            select(Usuario).where(
                Usuario.id == usuario_atual["id"],
                Usuario.aluno_id == m.aluno_id,
            )
        )
        if not vinculo:
            raise ValidationError("Aluno só pode trancar suas próprias matrículas")

    m.status = "trancada"
    await db.commit()
    await db.refresh(m)
    return m


async def cancelar_matricula(db: AsyncSession, matricula_id: int) -> Matricula:
    m = await _get_matricula(db, matricula_id)

    if m.status == "cancelada":
        raise ValidationError("Matrícula já está cancelada")

    m.status = "cancelada"
    await db.commit()
    await db.refresh(m)
    return m


async def get_matriculas_aluno(
    db: AsyncSession,
    aluno_id: int,
    page: int,
    page_size: int,
):
    """Retorna matrículas do aluno com dados desnormalizados (turma, disciplina, semestre)."""
    await _get_aluno(db, aluno_id)

    q = (
        select(
            Matricula,
            Turma.codigo.label("turma_codigo"),
            Disciplina.nome.label("disciplina_nome"),
            Disciplina.codigo.label("disciplina_codigo"),
            Semestre.ano.label("semestre_ano"),
            Semestre.periodo.label("semestre_periodo"),
        )
        .join(Turma, Turma.id == Matricula.turma_id)
        .join(Disciplina, Disciplina.id == Turma.disciplina_id)
        .join(Semestre, Semestre.id == Turma.semestre_id)
        .where(Matricula.aluno_id == aluno_id)
        .order_by(Semestre.ano.desc(), Semestre.periodo.desc(), Matricula.id)
    )

    total = await db.scalar(
        select(func.count()).select_from(
            select(Matricula).where(Matricula.aluno_id == aluno_id).subquery()
        )
    )
    offset = (page - 1) * page_size
    rows = (await db.execute(q.offset(offset).limit(page_size))).all()

    resultado = []
    for row in rows:
        m = row[0]
        resultado.append({
            "id": m.id,
            "aluno_id": m.aluno_id,
            "turma_id": m.turma_id,
            "status": m.status,
            "created_at": m.created_at,
            "updated_at": m.updated_at,
            "turma_codigo": row.turma_codigo,
            "disciplina_nome": row.disciplina_nome,
            "disciplina_codigo": row.disciplina_codigo,
            "semestre_label": f"{row.semestre_ano}/{row.semestre_periodo}",
        })

    return resultado, total


async def get_vagas_turma(db: AsyncSession, turma_id: int) -> dict:
    """Retorna situação de vagas de uma turma."""
    turma = await _get_turma(db, turma_id)
    ocupadas = await _contar_vagas_ocupadas(db, turma_id)
    return {
        "turma_id": turma_id,
        "vagas_total": turma.vagas,
        "vagas_ocupadas": ocupadas,
        "vagas_disponiveis": max(0, turma.vagas - ocupadas),
    }
