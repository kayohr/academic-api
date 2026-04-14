-- Migration 006 — Auth
-- Tabelas: usuario, refresh_token, audit_log

CREATE TABLE usuario (
    id            SERIAL PRIMARY KEY,
    email         VARCHAR(150) NOT NULL UNIQUE,
    senha_hash    VARCHAR(255) NOT NULL,
    role          VARCHAR(20)  NOT NULL DEFAULT 'aluno', -- admin, coordenador, professor, aluno
    -- Vinculação polimórfica: apenas um dos campos abaixo deve ser preenchido
    aluno_id      INTEGER REFERENCES aluno(id)      ON DELETE CASCADE,
    professor_id  INTEGER REFERENCES professor(id)  ON DELETE CASCADE,
    funcionario_id INTEGER REFERENCES funcionario(id) ON DELETE CASCADE,
    ativo         BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- Garante que no máximo uma referência está preenchida
    CONSTRAINT usuario_vinculo_check CHECK (
        (aluno_id IS NOT NULL)::int +
        (professor_id IS NOT NULL)::int +
        (funcionario_id IS NOT NULL)::int <= 1
    )
);

CREATE TABLE refresh_token (
    id         SERIAL PRIMARY KEY,
    usuario_id INTEGER     NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    revogado   BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE audit_log (
    id          SERIAL PRIMARY KEY,
    usuario_id  INTEGER,     -- NULL se ação foi feita por sistema
    acao        VARCHAR(100) NOT NULL, -- ex: 'matricula.criar', 'nota.atualizar'
    entidade    VARCHAR(50),           -- ex: 'matricula', 'nota'
    entidade_id INTEGER,
    payload     JSONB,                 -- dados relevantes da ação
    ip          VARCHAR(45),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_usuario_email          ON usuario(email);
CREATE INDEX idx_usuario_role           ON usuario(role);
CREATE INDEX idx_refresh_token_hash     ON refresh_token(token_hash);
CREATE INDEX idx_refresh_token_usuario  ON refresh_token(usuario_id);
CREATE INDEX idx_audit_log_usuario_id   ON audit_log(usuario_id);
CREATE INDEX idx_audit_log_entidade     ON audit_log(entidade, entidade_id);
CREATE INDEX idx_audit_log_created_at   ON audit_log(created_at);
