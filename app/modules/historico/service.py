from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.db.models import (
    Aluno, Disciplina, Frequencia, Historico, Matricula, Nota, Semestre, Turma,
)

MEDIA_APROVACAO = 6.0
FREQUENCIA_MINIMA = 75.0


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_aluno(db: AsyncSession, aluno_id: int) -> Aluno:
    a = await db.scalar(
        select(Aluno).where(Aluno.id == aluno_id, Aluno.deleted_at.is_(None))
    )
    if not a:
        raise NotFoundError("Aluno")
    return a


async def _get_semestre(db: AsyncSession, semestre_id: int) -> Semestre:
    s = await db.scalar(select(Semestre).where(Semestre.id == semestre_id))
    if not s:
        raise NotFoundError("Semestre")
    return s


def _determinar_situacao(media: float | None, freq_pct: float | None, trancada: bool) -> str:
    if trancada:
        return "trancado"
    if media is None or freq_pct is None:
        return "em_andamento"
    if media >= MEDIA_APROVACAO and freq_pct >= FREQUENCIA_MINIMA:
        return "aprovado"
    return "reprovado"


# ── Histórico do aluno ────────────────────────────────────────────────────────

async def get_historico_aluno(
    db: AsyncSession,
    aluno_id: int,
    semestre_id: int | None,
    page: int,
    page_size: int,
) -> tuple[list[dict], int]:
    await _get_aluno(db, aluno_id)

    q = (
        select(
            Historico,
            Disciplina.nome.label("disciplina_nome"),
            Disciplina.codigo.label("disciplina_codigo"),
            Semestre.ano.label("semestre_ano"),
            Semestre.periodo.label("semestre_periodo"),
        )
        .join(Disciplina, Disciplina.id == Historico.disciplina_id)
        .join(Semestre, Semestre.id == Historico.semestre_id)
        .where(Historico.aluno_id == aluno_id)
    )
    if semestre_id:
        q = q.where(Historico.semestre_id == semestre_id)

    q = q.order_by(Semestre.ano.desc(), Semestre.periodo.desc(), Disciplina.nome)

    total_q = select(func.count()).select_from(
        select(Historico).where(
            Historico.aluno_id == aluno_id,
            *([Historico.semestre_id == semestre_id] if semestre_id else []),
        ).subquery()
    )
    total = await db.scalar(total_q)
    offset = (page - 1) * page_size
    rows = (await db.execute(q.offset(offset).limit(page_size))).all()

    resultado = []
    for row in rows:
        h = row[0]
        resultado.append({
            "id": h.id,
            "aluno_id": h.aluno_id,
            "semestre_id": h.semestre_id,
            "disciplina_id": h.disciplina_id,
            "nota_final": float(h.nota_final) if h.nota_final is not None else None,
            "frequencia_pct": float(h.frequencia_pct) if h.frequencia_pct is not None else None,
            "situacao": h.situacao,
            "creditos": h.creditos,
            "created_at": h.created_at,
            "disciplina_nome": row.disciplina_nome,
            "disciplina_codigo": row.disciplina_codigo,
            "semestre_label": f"{row.semestre_ano}/{row.semestre_periodo}",
        })

    return resultado, total


# ── CR ────────────────────────────────────────────────────────────────────────

async def get_cr_aluno(db: AsyncSession, aluno_id: int) -> dict:
    await _get_aluno(db, aluno_id)

    historicos = (await db.execute(
        select(Historico).where(Historico.aluno_id == aluno_id)
    )).scalars().all()

    soma_ponderada = 0.0
    soma_creditos = 0
    aprovadas = 0
    reprovadas = 0
    trancadas = 0

    for h in historicos:
        if h.situacao == "aprovado":
            soma_ponderada += (float(h.nota_final) if h.nota_final else 0.0) * h.creditos
            soma_creditos += h.creditos
            aprovadas += 1
        elif h.situacao == "reprovado":
            reprovadas += 1
        elif h.situacao == "trancado":
            trancadas += 1

    cr = round(soma_ponderada / soma_creditos, 2) if soma_creditos > 0 else None

    return {
        "aluno_id": aluno_id,
        "cr": cr,
        "creditos_aprovados": soma_creditos,
        "disciplinas_aprovadas": aprovadas,
        "disciplinas_reprovadas": reprovadas,
        "disciplinas_trancadas": trancadas,
    }


# ── Consolidação do semestre ──────────────────────────────────────────────────

async def consolidar_semestre(db: AsyncSession, semestre_id: int) -> dict:
    """
    Gera snapshots imutáveis de Historico para todas as matrículas do semestre.
    Só pode ser executado em semestres encerrados.
    """
    semestre = await _get_semestre(db, semestre_id)
    if semestre.status != "encerrado":
        raise ValidationError(
            f"Só é possível consolidar semestres encerrados (status atual: '{semestre.status}')"
        )

    # Busca todas as matrículas de turmas deste semestre
    matriculas = (await db.execute(
        select(Matricula)
        .join(Turma, Turma.id == Matricula.turma_id)
        .where(Turma.semestre_id == semestre_id)
    )).scalars().all()

    detalhes = []
    gerados = 0

    for m in matriculas:
        turma = await db.scalar(select(Turma).where(Turma.id == m.turma_id))
        disciplina = await db.scalar(select(Disciplina).where(Disciplina.id == turma.disciplina_id))

        # Verifica se snapshot já existe (idempotente)
        existente = await db.scalar(
            select(Historico).where(
                Historico.aluno_id == m.aluno_id,
                Historico.semestre_id == semestre_id,
                Historico.disciplina_id == turma.disciplina_id,
            )
        )
        if existente:
            detalhes.append({
                "aluno_id": m.aluno_id,
                "disciplina": disciplina.codigo if disciplina else "?",
                "acao": "ignorado (já existe)",
            })
            continue

        # Calcula média das notas
        notas = (await db.execute(
            select(Nota).where(Nota.matricula_id == m.id)
        )).scalars().all()
        media = round(sum(n.valor for n in notas) / len(notas), 2) if notas else None

        # Calcula frequência
        frequencias = (await db.execute(
            select(Frequencia).where(Frequencia.matricula_id == m.id)
        )).scalars().all()
        total_aulas = len(frequencias)
        presentes = sum(1 for f in frequencias if f.presente)
        freq_pct = round(presentes / total_aulas * 100, 2) if total_aulas else None

        situacao = _determinar_situacao(
            media, freq_pct, trancada=(m.status == "trancada")
        )

        h = Historico(
            aluno_id=m.aluno_id,
            semestre_id=semestre_id,
            disciplina_id=turma.disciplina_id,
            nota_final=media,
            frequencia_pct=freq_pct,
            situacao=situacao,
            creditos=disciplina.creditos if disciplina else 0,
        )
        db.add(h)
        gerados += 1
        detalhes.append({
            "aluno_id": m.aluno_id,
            "disciplina": disciplina.codigo if disciplina else "?",
            "situacao": situacao,
            "media": media,
            "frequencia_pct": freq_pct,
        })

    await db.commit()

    return {
        "semestre_id": semestre_id,
        "semestre_label": f"{semestre.ano}/{semestre.periodo}",
        "snapshots_gerados": gerados,
        "detalhes": detalhes,
    }
