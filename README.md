# academic-api

API REST para gestão acadêmica universitária — simula um sistema real de controle de alunos, matrículas, notas e histórico.

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Framework | **FastAPI** (Python 3.12) |
| ORM | **SQLAlchemy 2.0** async (`Mapped`, `mapped_column`) |
| Banco | **PostgreSQL 16** |
| Migrations | **Alembic** (autogenerate) |
| Auth | **JWT** via `python-jose` + `bcrypt` |
| Container | **Docker Compose** |
| Docs | **Swagger UI** `/docs` · **ReDoc** `/redoc` |
| Observabilidade | Logs JSON estruturados · Rate limiting · `X-Response-Time` |

## Domínios

| Domínio | Entidades |
|---------|-----------|
| Instituição | Campus, Departamento, Curso |
| Pessoas | Aluno, Professor, Funcionário |
| Acadêmico | Disciplina, Grade Curricular, Pré-requisito, Semestre, Turma |
| Matrículas | Matrícula (ativa / trancada / cancelada) |
| Avaliação | Nota (AV1/AV2/AV3), Frequência |
| Histórico | Histórico Acadêmico, CR (Coeficiente de Rendimento) |
| Auth | Usuário, Refresh Token, Audit Log |

## Início rápido

```bash
# Copiar variáveis de ambiente
cp .env.example .env

# Subir API + banco
docker compose up -d

# Aplicar migrations
docker compose exec api alembic upgrade head

# Verificar
curl http://localhost:8000/health
```

A API fica disponível em `http://localhost:8000`.
Documentação interativa em `http://localhost:8000/docs`.

## Autenticação

```bash
# Login (admin padrão criado pelo seed)
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@academic.com","senha":"Admin@123"}'

# Usar o token retornado
curl http://localhost:8000/alunos \
  -H "Authorization: Bearer <access_token>"
```

### Roles

| Role | Permissões |
|------|-----------|
| `admin` | Acesso total |
| `coordenador` | Gerencia turmas, matrículas e grade |
| `professor` | Lança notas e frequência nas próprias turmas |
| `aluno` | Consulta suas matrículas, notas e histórico |

## Seed de dados

```bash
cd scripts
pip install -r requirements.txt
python seed.py
```

Popula o banco com dados realistas via **Faker pt_BR**: campus, departamentos, cursos, disciplinas, pré-requisitos, grade curricular, 6 professores, 20 alunos, semestre ativo, turmas e matrículas.

Credenciais geradas pelo seed:
- Admin: `admin@academic.com` / `Admin@123`
- Professores: `prof1@academic.edu` ... `prof6@academic.edu` / `Prof@123`
- Alunos: `aluno1@academic.edu` ... `aluno20@academic.edu` / `Aluno@123`

## Relatório PDF

```bash
python scripts/relatorio.py <aluno_id> [saida.pdf]
```

Gera relatório de desempenho acadêmico com histórico de disciplinas, CR e matrículas ativas.

## Estrutura do projeto

```
app/
├── core/           # config, deps, exceptions, security, observabilidade
├── db/             # models SQLAlchemy, session, base
└── modules/
    ├── auth/       # registro, login, JWT, refresh token
    ├── instituicao/ # campus, departamento, curso
    ├── aluno/
    ├── professor/
    ├── disciplina/ # disciplinas, grade, pré-requisitos
    ├── turma/      # semestres e turmas
    ├── matricula/  # matrícula com validação de vagas e pré-requisitos
    ├── avaliacao/  # notas e frequência
    └── historico/  # histórico acadêmico e CR
alembic/            # migrations versionadas
scripts/            # seed.py e relatorio.py
tests/
```

## Endpoints principais

| Módulo | Endpoints |
|--------|-----------|
| Auth | `POST /auth/login` `/auth/register` `/auth/refresh` `/auth/logout` `GET /auth/me` |
| Alunos | `GET/POST /alunos` `GET/PUT/DELETE /alunos/{id}` |
| Professores | `GET/POST /professores` `GET/PUT/DELETE /professores/{id}` `GET /professores/{id}/turmas` |
| Disciplinas | `GET/POST /disciplinas` `GET/PUT /disciplinas/{id}` `/disciplinas/{id}/prerequisitos` |
| Grade | `GET/POST /cursos/{id}/grade` |
| Semestres | `GET/POST /semestres` `PUT /semestres/{id}` `PUT /semestres/{id}/encerrar` |
| Turmas | `GET/POST /turmas` `GET/PUT/DELETE /turmas/{id}` `GET /turmas/{id}/alunos` |
| Matrículas | `GET/POST /matriculas` `PUT /matriculas/{id}/trancar` `PUT /matriculas/{id}/cancelar` `GET /alunos/{id}/matriculas` `GET /turmas/{id}/vagas` |
| Notas | `GET/POST /matriculas/{id}/notas` `PUT /notas/{id}` |
| Frequência | `GET/POST /matriculas/{id}/frequencias` `PUT /frequencias/{id}` `GET /matriculas/{id}/resumo` `GET /turmas/{id}/frequencias` |
| Histórico | `GET /alunos/{id}/historico` `GET /alunos/{id}/historico/cr` `POST /semestres/{id}/consolidar` |
| Health | `GET /health` `/health/ready` `/health/live` |

## Regras de negócio

- **Pré-requisitos**: matrícula só é aceita se o aluno tiver aprovação no histórico de cada disciplina pré-requisito
- **Vagas**: matrícula bloqueada quando `vagas_ocupadas >= turma.vagas`
- **Trancamento**: respeita `data_limite_trancamento` do semestre; aluno só tranca as próprias matrículas
- **Aprovação**: média ≥ 6,0 **e** frequência ≥ 75%
- **CR**: `soma(nota_final × créditos) / soma(créditos)` — apenas disciplinas aprovadas
- **Consolidação**: `POST /semestres/{id}/consolidar` gera snapshots imutáveis de histórico; idempotente
- **Soft delete**: alunos e professores usam `deleted_at` (não são removidos fisicamente)
