-- Migration 001 — Instituição
-- Tabelas: campus, departamento, curso

CREATE TABLE campus (
    id          SERIAL PRIMARY KEY,
    nome        VARCHAR(150) NOT NULL,
    cidade      VARCHAR(100) NOT NULL,
    estado      CHAR(2)      NOT NULL,
    endereco    TEXT,
    telefone    VARCHAR(20),
    email       VARCHAR(150),
    ativo       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    deleted_at  TIMESTAMPTZ
);

CREATE TABLE departamento (
    id          SERIAL PRIMARY KEY,
    campus_id   INTEGER      NOT NULL REFERENCES campus(id) ON DELETE RESTRICT,
    nome        VARCHAR(150) NOT NULL,
    sigla       VARCHAR(20)  NOT NULL,
    email       VARCHAR(150),
    ativo       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    deleted_at  TIMESTAMPTZ
);

CREATE TABLE curso (
    id                   SERIAL PRIMARY KEY,
    departamento_id      INTEGER     NOT NULL REFERENCES departamento(id) ON DELETE RESTRICT,
    nome                 VARCHAR(150) NOT NULL,
    codigo               VARCHAR(20)  NOT NULL UNIQUE,
    grau                 VARCHAR(30)  NOT NULL, -- bacharelado, licenciatura, tecnologo, pos_graduacao
    modalidade           VARCHAR(20)  NOT NULL DEFAULT 'presencial', -- presencial, ead, hibrido
    duracao_semestres    INTEGER      NOT NULL,
    creditos_necessarios INTEGER      NOT NULL,
    ativo                BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    deleted_at           TIMESTAMPTZ
);

CREATE INDEX idx_departamento_campus_id ON departamento(campus_id);
CREATE INDEX idx_departamento_deleted_at ON departamento(deleted_at);
CREATE INDEX idx_campus_deleted_at ON campus(deleted_at);
CREATE INDEX idx_curso_departamento_id ON curso(departamento_id);
CREATE INDEX idx_curso_deleted_at ON curso(deleted_at);
