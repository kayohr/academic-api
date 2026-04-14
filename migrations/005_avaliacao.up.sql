-- Migration 005 — Avaliação
-- Tabelas: nota, frequencia, historico

CREATE TABLE nota (
    id           SERIAL PRIMARY KEY,
    matricula_id INTEGER        NOT NULL REFERENCES matricula(id) ON DELETE CASCADE,
    tipo         VARCHAR(10)    NOT NULL, -- AV1, AV2, AV3 (substitutiva)
    valor        NUMERIC(4, 2)  NOT NULL CHECK (valor >= 0 AND valor <= 10),
    created_at   TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    UNIQUE (matricula_id, tipo)
);

CREATE TABLE frequencia (
    id           SERIAL      PRIMARY KEY,
    matricula_id INTEGER     NOT NULL REFERENCES matricula(id) ON DELETE CASCADE,
    data_aula    DATE        NOT NULL,
    presente     BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (matricula_id, data_aula)
);

-- Snapshot imutável gerado ao encerrar o semestre
CREATE TABLE historico (
    id               SERIAL PRIMARY KEY,
    aluno_id         INTEGER       NOT NULL REFERENCES aluno(id) ON DELETE RESTRICT,
    semestre_id      INTEGER       NOT NULL REFERENCES semestre(id) ON DELETE RESTRICT,
    disciplina_id    INTEGER       NOT NULL REFERENCES disciplina(id) ON DELETE RESTRICT,
    nota_final       NUMERIC(4, 2),
    frequencia_pct   NUMERIC(5, 2), -- percentual de presença
    situacao         VARCHAR(20)   NOT NULL, -- aprovado, reprovado, reprovado_falta, trancado
    creditos         INTEGER       NOT NULL,
    created_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    UNIQUE (aluno_id, semestre_id, disciplina_id)
);

CREATE INDEX idx_nota_matricula_id       ON nota(matricula_id);
CREATE INDEX idx_frequencia_matricula_id ON frequencia(matricula_id);
CREATE INDEX idx_frequencia_data_aula    ON frequencia(data_aula);
CREATE INDEX idx_historico_aluno_id      ON historico(aluno_id);
CREATE INDEX idx_historico_semestre_id   ON historico(semestre_id);
