-- Migration 003 — Acadêmico
-- Tabelas: semestre, disciplina, grade_curricular, prerequisito, turma

CREATE TABLE semestre (
    id                       SERIAL PRIMARY KEY,
    ano                      INTEGER     NOT NULL,
    periodo                  INTEGER     NOT NULL CHECK (periodo IN (1, 2)),
    data_inicio              DATE        NOT NULL,
    data_fim                 DATE        NOT NULL,
    data_limite_trancamento  DATE,
    status                   VARCHAR(20) NOT NULL DEFAULT 'planejado', -- planejado, ativo, encerrado
    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (ano, periodo)
);

CREATE TABLE disciplina (
    id              SERIAL PRIMARY KEY,
    departamento_id INTEGER      NOT NULL REFERENCES departamento(id) ON DELETE RESTRICT,
    codigo          VARCHAR(20)  NOT NULL UNIQUE,
    nome            VARCHAR(150) NOT NULL,
    ementa          TEXT,
    carga_horaria   INTEGER      NOT NULL, -- em horas
    creditos        INTEGER      NOT NULL,
    ativa           BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE grade_curricular (
    id             SERIAL PRIMARY KEY,
    curso_id       INTEGER     NOT NULL REFERENCES curso(id) ON DELETE CASCADE,
    disciplina_id  INTEGER     NOT NULL REFERENCES disciplina(id) ON DELETE RESTRICT,
    periodo        INTEGER     NOT NULL, -- 1º ao 10º semestre do curso
    tipo           VARCHAR(20) NOT NULL DEFAULT 'obrigatoria', -- obrigatoria, optativa, eletiva
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (curso_id, disciplina_id)
);

-- Pré-requisitos: para cursar disciplina_id, precisa ter aprovado em prerequisito_id
CREATE TABLE prerequisito (
    disciplina_id   INTEGER NOT NULL REFERENCES disciplina(id) ON DELETE CASCADE,
    prerequisito_id INTEGER NOT NULL REFERENCES disciplina(id) ON DELETE CASCADE,
    PRIMARY KEY (disciplina_id, prerequisito_id),
    CHECK (disciplina_id <> prerequisito_id)
);

CREATE TABLE turma (
    id            SERIAL PRIMARY KEY,
    disciplina_id INTEGER     NOT NULL REFERENCES disciplina(id) ON DELETE RESTRICT,
    professor_id  INTEGER     NOT NULL REFERENCES professor(id) ON DELETE RESTRICT,
    semestre_id   INTEGER     NOT NULL REFERENCES semestre(id) ON DELETE RESTRICT,
    codigo        VARCHAR(20) NOT NULL,
    sala          VARCHAR(50),
    horario       JSONB,
    -- [{ "dia": "segunda", "hora_inicio": "08:00", "hora_fim": "10:00" }]
    vagas         INTEGER     NOT NULL DEFAULT 40,
    status        VARCHAR(20) NOT NULL DEFAULT 'aberta', -- aberta, em_andamento, encerrada, cancelada
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (codigo, semestre_id)
);

CREATE INDEX idx_disciplina_departamento_id  ON disciplina(departamento_id);
CREATE INDEX idx_grade_curso_id              ON grade_curricular(curso_id);
CREATE INDEX idx_grade_disciplina_id         ON grade_curricular(disciplina_id);
CREATE INDEX idx_turma_disciplina_id         ON turma(disciplina_id);
CREATE INDEX idx_turma_professor_id          ON turma(professor_id);
CREATE INDEX idx_turma_semestre_id           ON turma(semestre_id);
CREATE INDEX idx_turma_status                ON turma(status);
