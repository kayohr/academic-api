-- Migration 004 — Matrícula
-- Tabela: matricula

CREATE TABLE matricula (
    id         SERIAL PRIMARY KEY,
    aluno_id   INTEGER     NOT NULL REFERENCES aluno(id) ON DELETE RESTRICT,
    turma_id   INTEGER     NOT NULL REFERENCES turma(id) ON DELETE RESTRICT,
    status     VARCHAR(20) NOT NULL DEFAULT 'ativa',
    -- ativa, trancada, cancelada, aprovada, reprovada, reprovada_falta
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (aluno_id, turma_id)
);

CREATE INDEX idx_matricula_aluno_id  ON matricula(aluno_id);
CREATE INDEX idx_matricula_turma_id  ON matricula(turma_id);
CREATE INDEX idx_matricula_status    ON matricula(status);
