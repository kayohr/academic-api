from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.db.models import Aluno, Frequencia, Matricula, Nota, Professor, Turma, Usuario

MEDIA_APROVACAO = 6.0
FREQUENCIA_MINIMA = 75.0


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_matricula(db: AsyncSession, matricula_id: int) -> Matricula:
    m = await db.scalar(select(Matricula).where(Matricula.id == matricula_id))
    if not m:
        raise NotFoundError("Matrícula")
    return m


async def _get_turma(db: AsyncSession, turma_id: int) -> Turma:
    t = await db.scalar(select(Turma).where(Turma.id == turma_id))
    if not t:
        raise NotFoundError("Turma")
    return t


async def _verificar_professor_da_turma(db: AsyncSession, turma_id: int, usuario: dict) -> None:
    """Admin pode tudo; professor só opera nas próprias turmas."""
    if usuario["role"] in ("admin", "coordenador"):
        return

    if usuario["role"] != "professor":
        raise ForbiddenError("Apenas professores, coordenadores ou admins podem lançar avaliações")

    # Verifica se o usuário logado é o professor da turma
    turma = await _get_turma(db, turma_id)
    vinculo = await db.scalar(
        select(Usuario).where(
            Usuario.id == usuario["id"],
            Usuario.professor_id == turma.professor_id,
        )
    )
    if not vinculo:
        raise ForbiddenError("Professor só pode lançar avaliações nas próprias turmas")


def _calcular_media(notas: list[Nota]) -> float | None:
    """Média simples das notas disponíveis. Retorna None se não há notas."""
    if not notas:
        return None
    return round(sum(n.valor for n in notas) / len(notas), 2)


def _calcular_situacao(media: float | None, frequencia_pct: float | None) -> str:
    if media is None or frequencia_pct is None:
        return "em_andamento"
    if media >= MEDIA_APROVACAO and frequencia_pct >= FREQUENCIA_MINIMA:
        return "aprovado"
    return "reprovado"


# ── Notas ─────────────────────────────────────────────────────────────────────

async def list_notas(db: AsyncSession, matricula_id: int) -> list[Nota]:
    await _get_matricula(db, matricula_id)
    rows = (await db.execute(
        select(Nota).where(Nota.matricula_id == matricula_id).order_by(Nota.tipo)
    )).scalars().all()
    return list(rows)


async def create_nota(db: AsyncSession, matricula_id: int, data, usuario: dict) -> Nota:
    matricula = await _get_matricula(db, matricula_id)

    if matricula.status != "ativa":
        raise ValidationError(
            f"Notas só podem ser lançadas em matrículas ativas (status: '{matricula.status}')"
        )

    await _verificar_professor_da_turma(db, matricula.turma_id, usuario)

    existente = await db.scalar(
        select(Nota).where(Nota.matricula_id == matricula_id, Nota.tipo == data.tipo)
    )
    if existente:
        raise ConflictError(f"Nota {data.tipo} já foi lançada para esta matrícula")

    nota = Nota(matricula_id=matricula_id, tipo=data.tipo, valor=data.valor)
    db.add(nota)
    await db.commit()
    await db.refresh(nota)
    return nota


async def update_nota(db: AsyncSession, nota_id: int, data, usuario: dict) -> Nota:
    nota = await db.scalar(select(Nota).where(Nota.id == nota_id))
    if not nota:
        raise NotFoundError("Nota")

    matricula = await _get_matricula(db, nota.matricula_id)
    await _verificar_professor_da_turma(db, matricula.turma_id, usuario)

    nota.valor = data.valor
    await db.commit()
    await db.refresh(nota)
    return nota


# ── Frequência ────────────────────────────────────────────────────────────────

async def list_frequencias(db: AsyncSession, matricula_id: int) -> list[Frequencia]:
    await _get_matricula(db, matricula_id)
    rows = (await db.execute(
        select(Frequencia)
        .where(Frequencia.matricula_id == matricula_id)
        .order_by(Frequencia.data_aula)
    )).scalars().all()
    return list(rows)


async def create_frequencia(db: AsyncSession, matricula_id: int, data, usuario: dict) -> Frequencia:
    matricula = await _get_matricula(db, matricula_id)

    if matricula.status != "ativa":
        raise ValidationError(
            f"Frequência só pode ser registrada em matrículas ativas (status: '{matricula.status}')"
        )

    await _verificar_professor_da_turma(db, matricula.turma_id, usuario)

    existente = await db.scalar(
        select(Frequencia).where(
            Frequencia.matricula_id == matricula_id,
            Frequencia.data_aula == data.data_aula,
        )
    )
    if existente:
        raise ConflictError(f"Frequência para {data.data_aula} já registrada nesta matrícula")

    freq = Frequencia(matricula_id=matricula_id, data_aula=data.data_aula, presente=data.presente)
    db.add(freq)
    await db.commit()
    await db.refresh(freq)
    return freq


async def update_frequencia(db: AsyncSession, frequencia_id: int, data, usuario: dict) -> Frequencia:
    freq = await db.scalar(select(Frequencia).where(Frequencia.id == frequencia_id))
    if not freq:
        raise NotFoundError("Frequência")

    matricula = await _get_matricula(db, freq.matricula_id)
    await _verificar_professor_da_turma(db, matricula.turma_id, usuario)

    freq.presente = data.presente
    await db.commit()
    await db.refresh(freq)
    return freq


# ── Resumo ────────────────────────────────────────────────────────────────────

async def get_resumo(db: AsyncSession, matricula_id: int) -> dict:
    await _get_matricula(db, matricula_id)

    notas = await list_notas(db, matricula_id)
    frequencias = await list_frequencias(db, matricula_id)

    total_aulas = len(frequencias)
    aulas_presentes = sum(1 for f in frequencias if f.presente)
    frequencia_pct = round(aulas_presentes / total_aulas * 100, 2) if total_aulas else None

    media = _calcular_media(notas)
    situacao = _calcular_situacao(media, frequencia_pct)

    return {
        "matricula_id": matricula_id,
        "notas": notas,
        "media": media,
        "total_aulas": total_aulas,
        "aulas_presentes": aulas_presentes,
        "frequencia_pct": frequencia_pct,
        "situacao": situacao,
    }


# ── Frequência consolidada por turma ─────────────────────────────────────────

async def get_frequencia_turma(db: AsyncSession, turma_id: int) -> list[dict]:
    await _get_turma(db, turma_id)

    matriculas = (await db.execute(
        select(Matricula)
        .where(Matricula.turma_id == turma_id, Matricula.status == "ativa")
        .order_by(Matricula.id)
    )).scalars().all()

    resultado = []
    for m in matriculas:
        aluno = await db.scalar(select(Aluno).where(Aluno.id == m.aluno_id))
        frequencias = (await db.execute(
            select(Frequencia).where(Frequencia.matricula_id == m.id)
        )).scalars().all()

        total = len(frequencias)
        presentes = sum(1 for f in frequencias if f.presente)
        pct = round(presentes / total * 100, 2) if total else None

        resultado.append({
            "aluno_id": m.aluno_id,
            "aluno_nome": aluno.nome if aluno else "?",
            "matricula_id": m.id,
            "total_aulas": total,
            "aulas_presentes": presentes,
            "frequencia_pct": pct,
        })

    return resultado
