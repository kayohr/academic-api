"""
Todos os models SQLAlchemy do sistema.
Importados em um único arquivo para o Alembic detectar automaticamente.
"""

from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import (
    BigInteger, Boolean, CheckConstraint, Date, DateTime,
    ForeignKey, Integer, Numeric, String, Text, UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def now_utc():
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Instituição
# ---------------------------------------------------------------------------

class Campus(Base):
    __tablename__ = "campus"

    id:         Mapped[int]          = mapped_column(Integer, primary_key=True)
    nome:       Mapped[str]          = mapped_column(String(150), nullable=False)
    cidade:     Mapped[str]          = mapped_column(String(100), nullable=False)
    estado:     Mapped[str]          = mapped_column(String(2),   nullable=False)
    endereco:   Mapped[Optional[str]] = mapped_column(Text)
    telefone:   Mapped[Optional[str]] = mapped_column(String(20))
    email:      Mapped[Optional[str]] = mapped_column(String(150))
    ativo:      Mapped[bool]         = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime]     = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime]     = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    departamentos: Mapped[list["Departamento"]] = relationship(back_populates="campus")
    funcionarios:  Mapped[list["Funcionario"]]  = relationship(back_populates="campus")


class Departamento(Base):
    __tablename__ = "departamento"

    id:         Mapped[int]           = mapped_column(Integer, primary_key=True)
    campus_id:  Mapped[int]           = mapped_column(ForeignKey("campus.id", ondelete="RESTRICT"), nullable=False)
    nome:       Mapped[str]           = mapped_column(String(150), nullable=False)
    sigla:      Mapped[str]           = mapped_column(String(20),  nullable=False)
    email:      Mapped[Optional[str]] = mapped_column(String(150))
    ativo:      Mapped[bool]          = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    campus:      Mapped["Campus"]          = relationship(back_populates="departamentos")
    cursos:      Mapped[list["Curso"]]     = relationship(back_populates="departamento")
    professores: Mapped[list["Professor"]] = relationship(back_populates="departamento")
    disciplinas: Mapped[list["Disciplina"]] = relationship(back_populates="departamento")


class Curso(Base):
    __tablename__ = "curso"

    id:                   Mapped[int]           = mapped_column(Integer, primary_key=True)
    departamento_id:      Mapped[int]           = mapped_column(ForeignKey("departamento.id", ondelete="RESTRICT"), nullable=False)
    nome:                 Mapped[str]           = mapped_column(String(150), nullable=False)
    codigo:               Mapped[str]           = mapped_column(String(20),  nullable=False, unique=True)
    grau:                 Mapped[str]           = mapped_column(String(30),  nullable=False)
    modalidade:           Mapped[str]           = mapped_column(String(20),  nullable=False, default="presencial")
    duracao_semestres:    Mapped[int]           = mapped_column(Integer, nullable=False)
    creditos_necessarios: Mapped[int]           = mapped_column(Integer, nullable=False)
    ativo:                Mapped[bool]          = mapped_column(Boolean, default=True)
    created_at:           Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:           Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at:           Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    departamento:      Mapped["Departamento"]         = relationship(back_populates="cursos")
    alunos:            Mapped[list["Aluno"]]          = relationship(back_populates="curso")
    grade_curricular:  Mapped[list["GradeCurricular"]] = relationship(back_populates="curso")


# ---------------------------------------------------------------------------
# Pessoas
# ---------------------------------------------------------------------------

class Professor(Base):
    __tablename__ = "professor"

    id:              Mapped[int]           = mapped_column(Integer, primary_key=True)
    departamento_id: Mapped[int]           = mapped_column(ForeignKey("departamento.id", ondelete="RESTRICT"), nullable=False)
    nome:            Mapped[str]           = mapped_column(String(150), nullable=False)
    cpf:             Mapped[str]           = mapped_column(String(11),  nullable=False, unique=True)
    email:           Mapped[str]           = mapped_column(String(150), nullable=False, unique=True)
    siape:           Mapped[str]           = mapped_column(String(20),  nullable=False, unique=True)
    titulacao:       Mapped[str]           = mapped_column(String(30),  nullable=False)
    regime:          Mapped[str]           = mapped_column(String(10),  nullable=False, default="40h")
    telefone:        Mapped[Optional[str]] = mapped_column(String(20))
    data_nascimento: Mapped[Optional[date]] = mapped_column(Date)
    status:          Mapped[str]           = mapped_column(String(20),  nullable=False, default="ativo")
    created_at:      Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:      Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at:      Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    departamento: Mapped["Departamento"]  = relationship(back_populates="professores")
    turmas:       Mapped[list["Turma"]]   = relationship(back_populates="professor")
    usuario:      Mapped[Optional["Usuario"]] = relationship(back_populates="professor")


class Aluno(Base):
    __tablename__ = "aluno"

    id:                Mapped[int]           = mapped_column(Integer, primary_key=True)
    curso_id:          Mapped[int]           = mapped_column(ForeignKey("curso.id", ondelete="RESTRICT"), nullable=False)
    matricula:         Mapped[str]           = mapped_column(String(20),  nullable=False, unique=True)
    nome:              Mapped[str]           = mapped_column(String(150), nullable=False)
    cpf:               Mapped[str]           = mapped_column(String(11),  nullable=False, unique=True)
    email:             Mapped[str]           = mapped_column(String(150), nullable=False, unique=True)
    telefone:          Mapped[Optional[str]] = mapped_column(String(20))
    data_nascimento:   Mapped[Optional[date]] = mapped_column(Date)
    endereco:          Mapped[Optional[dict]] = mapped_column(JSONB)
    semestre_ingresso: Mapped[str]           = mapped_column(String(7), nullable=False)
    status:            Mapped[str]           = mapped_column(String(20), nullable=False, default="ativo")
    created_at:        Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:        Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at:        Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    curso:      Mapped["Curso"]            = relationship(back_populates="alunos")
    matriculas: Mapped[list["Matricula"]]  = relationship(back_populates="aluno")
    historicos: Mapped[list["Historico"]]  = relationship(back_populates="aluno")
    usuario:    Mapped[Optional["Usuario"]] = relationship(back_populates="aluno")


class Funcionario(Base):
    __tablename__ = "funcionario"

    id:         Mapped[int]           = mapped_column(Integer, primary_key=True)
    campus_id:  Mapped[int]           = mapped_column(ForeignKey("campus.id", ondelete="RESTRICT"), nullable=False)
    nome:       Mapped[str]           = mapped_column(String(150), nullable=False)
    cpf:        Mapped[str]           = mapped_column(String(11),  nullable=False, unique=True)
    email:      Mapped[str]           = mapped_column(String(150), nullable=False, unique=True)
    matricula:  Mapped[str]           = mapped_column(String(20),  nullable=False, unique=True)
    cargo:      Mapped[str]           = mapped_column(String(100), nullable=False)
    setor:      Mapped[Optional[str]] = mapped_column(String(100))
    status:     Mapped[str]           = mapped_column(String(20),  nullable=False, default="ativo")
    created_at: Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    campus:  Mapped["Campus"] = relationship(back_populates="funcionarios")
    usuario: Mapped[Optional["Usuario"]] = relationship(back_populates="funcionario")


# ---------------------------------------------------------------------------
# Acadêmico
# ---------------------------------------------------------------------------

class Semestre(Base):
    __tablename__ = "semestre"
    __table_args__ = (UniqueConstraint("ano", "periodo"),)

    id:                      Mapped[int]           = mapped_column(Integer, primary_key=True)
    ano:                     Mapped[int]           = mapped_column(Integer, nullable=False)
    periodo:                 Mapped[int]           = mapped_column(Integer, nullable=False)
    data_inicio:             Mapped[date]          = mapped_column(Date, nullable=False)
    data_fim:                Mapped[date]          = mapped_column(Date, nullable=False)
    data_limite_trancamento: Mapped[Optional[date]] = mapped_column(Date)
    status:                  Mapped[str]           = mapped_column(String(20), nullable=False, default="planejado")
    created_at:              Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:              Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    turmas: Mapped[list["Turma"]] = relationship(back_populates="semestre")


class Disciplina(Base):
    __tablename__ = "disciplina"

    id:              Mapped[int]           = mapped_column(Integer, primary_key=True)
    departamento_id: Mapped[int]           = mapped_column(ForeignKey("departamento.id", ondelete="RESTRICT"), nullable=False)
    codigo:          Mapped[str]           = mapped_column(String(20),  nullable=False, unique=True)
    nome:            Mapped[str]           = mapped_column(String(150), nullable=False)
    ementa:          Mapped[Optional[str]] = mapped_column(Text)
    carga_horaria:   Mapped[int]           = mapped_column(Integer, nullable=False)
    creditos:        Mapped[int]           = mapped_column(Integer, nullable=False)
    ativa:           Mapped[bool]          = mapped_column(Boolean, default=True)
    created_at:      Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:      Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    departamento:    Mapped["Departamento"]          = relationship(back_populates="disciplinas")
    grade_curricular: Mapped[list["GradeCurricular"]] = relationship(back_populates="disciplina")
    turmas:          Mapped[list["Turma"]]           = relationship(back_populates="disciplina")


class GradeCurricular(Base):
    __tablename__ = "grade_curricular"
    __table_args__ = (UniqueConstraint("curso_id", "disciplina_id"),)

    id:            Mapped[int]  = mapped_column(Integer, primary_key=True)
    curso_id:      Mapped[int]  = mapped_column(ForeignKey("curso.id", ondelete="CASCADE"), nullable=False)
    disciplina_id: Mapped[int]  = mapped_column(ForeignKey("disciplina.id", ondelete="RESTRICT"), nullable=False)
    periodo:       Mapped[int]  = mapped_column(Integer, nullable=False)
    tipo:          Mapped[str]  = mapped_column(String(20), nullable=False, default="obrigatoria")
    created_at:    Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    curso:      Mapped["Curso"]      = relationship(back_populates="grade_curricular")
    disciplina: Mapped["Disciplina"] = relationship(back_populates="grade_curricular")


class Prerequisito(Base):
    __tablename__ = "prerequisito"
    __table_args__ = (UniqueConstraint("disciplina_id", "prerequisito_id"),)

    id:             Mapped[int] = mapped_column(Integer, primary_key=True)
    disciplina_id:  Mapped[int] = mapped_column(ForeignKey("disciplina.id", ondelete="CASCADE"), nullable=False)
    prerequisito_id: Mapped[int] = mapped_column(ForeignKey("disciplina.id", ondelete="CASCADE"), nullable=False)
    created_at:     Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Turma(Base):
    __tablename__ = "turma"
    __table_args__ = (UniqueConstraint("codigo", "semestre_id"),)

    id:            Mapped[int]            = mapped_column(Integer, primary_key=True)
    disciplina_id: Mapped[int]            = mapped_column(ForeignKey("disciplina.id", ondelete="RESTRICT"), nullable=False)
    professor_id:  Mapped[int]            = mapped_column(ForeignKey("professor.id",  ondelete="RESTRICT"), nullable=False)
    semestre_id:   Mapped[int]            = mapped_column(ForeignKey("semestre.id",   ondelete="RESTRICT"), nullable=False)
    codigo:        Mapped[str]            = mapped_column(String(20), nullable=False)
    sala:          Mapped[Optional[str]]  = mapped_column(String(50))
    horario:       Mapped[Optional[dict]] = mapped_column(JSONB)
    vagas:         Mapped[int]            = mapped_column(Integer, nullable=False, default=40)
    status:        Mapped[str]            = mapped_column(String(20), nullable=False, default="aberta")
    created_at:    Mapped[datetime]       = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:    Mapped[datetime]       = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    disciplina: Mapped["Disciplina"]    = relationship(back_populates="turmas")
    professor:  Mapped["Professor"]     = relationship(back_populates="turmas")
    semestre:   Mapped["Semestre"]      = relationship(back_populates="turmas")
    matriculas: Mapped[list["Matricula"]] = relationship(back_populates="turma")


# ---------------------------------------------------------------------------
# Matrícula
# ---------------------------------------------------------------------------

class Matricula(Base):
    __tablename__ = "matricula"
    __table_args__ = (UniqueConstraint("aluno_id", "turma_id"),)

    id:         Mapped[int]      = mapped_column(Integer, primary_key=True)
    aluno_id:   Mapped[int]      = mapped_column(ForeignKey("aluno.id",  ondelete="RESTRICT"), nullable=False)
    turma_id:   Mapped[int]      = mapped_column(ForeignKey("turma.id",  ondelete="RESTRICT"), nullable=False)
    status:     Mapped[str]      = mapped_column(String(20), nullable=False, default="ativa")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    aluno:      Mapped["Aluno"]        = relationship(back_populates="matriculas")
    turma:      Mapped["Turma"]        = relationship(back_populates="matriculas")
    notas:      Mapped[list["Nota"]]   = relationship(back_populates="matricula")
    frequencias: Mapped[list["Frequencia"]] = relationship(back_populates="matricula")


# ---------------------------------------------------------------------------
# Avaliação
# ---------------------------------------------------------------------------

class Nota(Base):
    __tablename__ = "nota"
    __table_args__ = (UniqueConstraint("matricula_id", "tipo"),)

    id:           Mapped[int]   = mapped_column(Integer, primary_key=True)
    matricula_id: Mapped[int]   = mapped_column(ForeignKey("matricula.id", ondelete="CASCADE"), nullable=False)
    tipo:         Mapped[str]   = mapped_column(String(10), nullable=False)  # AV1, AV2, AV3
    valor:        Mapped[float] = mapped_column(Numeric(4, 2), nullable=False)
    created_at:   Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:   Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    matricula: Mapped["Matricula"] = relationship(back_populates="notas")


class Frequencia(Base):
    __tablename__ = "frequencia"
    __table_args__ = (UniqueConstraint("matricula_id", "data_aula"),)

    id:           Mapped[int]      = mapped_column(Integer, primary_key=True)
    matricula_id: Mapped[int]      = mapped_column(ForeignKey("matricula.id", ondelete="CASCADE"), nullable=False)
    data_aula:    Mapped[date]     = mapped_column(Date, nullable=False)
    presente:     Mapped[bool]     = mapped_column(Boolean, nullable=False, default=True)
    created_at:   Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    matricula: Mapped["Matricula"] = relationship(back_populates="frequencias")


class Historico(Base):
    __tablename__ = "historico"
    __table_args__ = (UniqueConstraint("aluno_id", "semestre_id", "disciplina_id"),)

    id:             Mapped[int]            = mapped_column(Integer, primary_key=True)
    aluno_id:       Mapped[int]            = mapped_column(ForeignKey("aluno.id",      ondelete="RESTRICT"), nullable=False)
    semestre_id:    Mapped[int]            = mapped_column(ForeignKey("semestre.id",   ondelete="RESTRICT"), nullable=False)
    disciplina_id:  Mapped[int]            = mapped_column(ForeignKey("disciplina.id", ondelete="RESTRICT"), nullable=False)
    nota_final:     Mapped[Optional[float]] = mapped_column(Numeric(4, 2))
    frequencia_pct: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    situacao:       Mapped[str]            = mapped_column(String(20), nullable=False)
    creditos:       Mapped[int]            = mapped_column(Integer, nullable=False)
    created_at:     Mapped[datetime]       = mapped_column(DateTime(timezone=True), server_default=func.now())

    aluno:      Mapped["Aluno"]      = relationship(back_populates="historicos")
    semestre:   Mapped["Semestre"]   = relationship()
    disciplina: Mapped["Disciplina"] = relationship()


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class Usuario(Base):
    __tablename__ = "usuario"
    __table_args__ = (
        CheckConstraint(
            "(aluno_id IS NOT NULL)::int + (professor_id IS NOT NULL)::int + (funcionario_id IS NOT NULL)::int <= 1",
            name="usuario_vinculo_check",
        ),
    )

    id:             Mapped[int]           = mapped_column(Integer, primary_key=True)
    email:          Mapped[str]           = mapped_column(String(150), nullable=False, unique=True)
    senha_hash:     Mapped[str]           = mapped_column(String(255), nullable=False)
    role:           Mapped[str]           = mapped_column(String(20),  nullable=False, default="aluno")
    aluno_id:       Mapped[Optional[int]] = mapped_column(ForeignKey("aluno.id",       ondelete="CASCADE"))
    professor_id:   Mapped[Optional[int]] = mapped_column(ForeignKey("professor.id",   ondelete="CASCADE"))
    funcionario_id: Mapped[Optional[int]] = mapped_column(ForeignKey("funcionario.id", ondelete="CASCADE"))
    ativo:          Mapped[bool]          = mapped_column(Boolean, nullable=False, default=True)
    created_at:     Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:     Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    aluno:       Mapped[Optional["Aluno"]]       = relationship(back_populates="usuario")
    professor:   Mapped[Optional["Professor"]]   = relationship(back_populates="usuario")
    funcionario: Mapped[Optional["Funcionario"]] = relationship(back_populates="usuario")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="usuario")


class RefreshToken(Base):
    __tablename__ = "refresh_token"

    id:         Mapped[int]      = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int]      = mapped_column(ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str]      = mapped_column(String(255), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revogado:   Mapped[bool]     = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    usuario: Mapped["Usuario"] = relationship(back_populates="refresh_tokens")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id:          Mapped[int]           = mapped_column(Integer, primary_key=True)
    usuario_id:  Mapped[Optional[int]] = mapped_column(Integer)
    acao:        Mapped[str]           = mapped_column(String(100), nullable=False)
    entidade:    Mapped[Optional[str]] = mapped_column(String(50))
    entidade_id: Mapped[Optional[int]] = mapped_column(Integer)
    payload:     Mapped[Optional[dict]] = mapped_column(JSONB)
    ip:          Mapped[Optional[str]] = mapped_column(String(45))
    created_at:  Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now())
