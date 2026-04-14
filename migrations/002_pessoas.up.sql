-- Migration 002 — Pessoas
-- Tabelas: professor, aluno, funcionario

CREATE TABLE professor (
    id              SERIAL PRIMARY KEY,
    departamento_id INTEGER      NOT NULL REFERENCES departamento(id) ON DELETE RESTRICT,
    nome            VARCHAR(150) NOT NULL,
    cpf             CHAR(11)     NOT NULL UNIQUE,
    email           VARCHAR(150) NOT NULL UNIQUE,
    siape           VARCHAR(20)  NOT NULL UNIQUE,
    titulacao       VARCHAR(30)  NOT NULL, -- graduacao, especializacao, mestrado, doutorado
    regime          VARCHAR(10)  NOT NULL DEFAULT '40h', -- 20h, 40h, DE
    telefone        VARCHAR(20),
    data_nascimento DATE,
    status          VARCHAR(20)  NOT NULL DEFAULT 'ativo', -- ativo, inativo, afastado
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ
);

CREATE TABLE aluno (
    id                SERIAL PRIMARY KEY,
    curso_id          INTEGER      NOT NULL REFERENCES curso(id) ON DELETE RESTRICT,
    matricula         VARCHAR(20)  NOT NULL UNIQUE,
    nome              VARCHAR(150) NOT NULL,
    cpf               CHAR(11)     NOT NULL UNIQUE,
    email             VARCHAR(150) NOT NULL UNIQUE,
    telefone          VARCHAR(20),
    data_nascimento   DATE,
    endereco          JSONB,
    -- { "logradouro", "numero", "complemento", "bairro", "cidade", "estado", "cep" }
    semestre_ingresso VARCHAR(7)   NOT NULL, -- formato: 2024/1
    status            VARCHAR(20)  NOT NULL DEFAULT 'ativo', -- ativo, trancado, formado, cancelado
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    deleted_at        TIMESTAMPTZ
);

CREATE TABLE funcionario (
    id         SERIAL PRIMARY KEY,
    campus_id  INTEGER      NOT NULL REFERENCES campus(id) ON DELETE RESTRICT,
    nome       VARCHAR(150) NOT NULL,
    cpf        CHAR(11)     NOT NULL UNIQUE,
    email      VARCHAR(150) NOT NULL UNIQUE,
    matricula  VARCHAR(20)  NOT NULL UNIQUE,
    cargo      VARCHAR(100) NOT NULL,
    setor      VARCHAR(100),
    status     VARCHAR(20)  NOT NULL DEFAULT 'ativo',
    created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_professor_departamento_id ON professor(departamento_id);
CREATE INDEX idx_professor_cpf             ON professor(cpf);
CREATE INDEX idx_professor_status          ON professor(status);
CREATE INDEX idx_professor_deleted_at      ON professor(deleted_at);
CREATE INDEX idx_aluno_curso_id            ON aluno(curso_id);
CREATE INDEX idx_aluno_matricula           ON aluno(matricula);
CREATE INDEX idx_aluno_cpf                 ON aluno(cpf);
CREATE INDEX idx_aluno_status              ON aluno(status);
CREATE INDEX idx_aluno_deleted_at          ON aluno(deleted_at);
CREATE INDEX idx_funcionario_campus_id     ON funcionario(campus_id);
