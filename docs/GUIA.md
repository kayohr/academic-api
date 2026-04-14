# Guia completo — academic-api

Este documento explica **o que é cada arquivo e pasta**, **por que cada decisão foi tomada** e **como o projeto foi construído passo a passo**. É um guia de referência para quem quer entender a arquitetura, reproduzir o projeto ou evoluí-lo.

---

## Índice

1. [Visão geral](#1-visão-geral)
2. [Estrutura de pastas](#2-estrutura-de-pastas)
3. [Stack e decisões técnicas](#3-stack-e-decisões-técnicas)
4. [Passo a passo: como rodar localmente](#4-passo-a-passo-como-rodar-localmente)
5. [Camada de banco de dados](#5-camada-de-banco-de-dados)
6. [Camada core](#6-camada-core)
7. [Módulos de negócio](#7-módulos-de-negócio)
8. [Fluxo de uma requisição](#8-fluxo-de-uma-requisição)
9. [Autenticação e autorização](#9-autenticação-e-autorização)
10. [Migrations com Alembic](#10-migrations-com-alembic)
11. [Scripts auxiliares](#11-scripts-auxiliares)
12. [Observabilidade](#12-observabilidade)
13. [Como adicionar um novo módulo](#13-como-adicionar-um-novo-módulo)

---

## 1. Visão geral

O **academic-api** é uma API REST que simula o sistema de gestão acadêmica de uma universidade. Ele cobre o ciclo completo: instituição → pessoas → disciplinas → semestres → matrículas → notas → histórico.

Foi construído de forma incremental usando **GitHub Issues como roadmap**, com cada issue representando uma feature entregável. O objetivo é servir como projeto de portfólio demonstrando boas práticas de arquitetura backend com Python.

---

## 2. Estrutura de pastas

```
academic-api/
│
├── app/                        # Código principal da API
│   ├── main.py                 # Bootstrap da aplicação FastAPI
│   ├── core/                   # Infraestrutura transversal
│   │   ├── config.py           # Variáveis de ambiente (pydantic-settings)
│   │   ├── deps.py             # Dependências injetáveis (sessão, usuário atual)
│   │   ├── exceptions.py       # Exceções HTTP customizadas
│   │   ├── security.py         # JWT, bcrypt, tokens
│   │   └── observability.py    # Logs JSON, rate limiting, middleware
│   ├── db/                     # Banco de dados
│   │   ├── base.py             # DeclarativeBase do SQLAlchemy
│   │   ├── models.py           # Todos os 19 models em um único arquivo
│   │   └── session.py          # Engine async e gerador de sessão
│   └── modules/                # Domínios de negócio
│       ├── auth/               # Autenticação e JWT
│       ├── instituicao/        # Campus, Departamento, Curso
│       ├── aluno/              # Cadastro de alunos
│       ├── professor/          # Cadastro de professores
│       ├── disciplina/         # Disciplinas, grade, pré-requisitos
│       ├── turma/              # Semestres e turmas
│       ├── matricula/          # Matrículas com validações de negócio
│       ├── avaliacao/          # Notas e frequência
│       └── historico/          # Histórico acadêmico e CR
│
├── alembic/                    # Migrations de banco de dados
│   ├── env.py                  # Configuração do Alembic (async)
│   ├── script.py.mako          # Template de migration
│   └── versions/               # Arquivos de migration gerados
│
├── scripts/                    # Scripts utilitários Python
│   ├── seed.py                 # Popula o banco com dados realistas
│   ├── relatorio.py            # Gera relatório PDF de desempenho
│   ├── requirements.txt        # Dependências dos scripts
│   └── Dockerfile.python       # Imagem para rodar scripts em container
│
├── docs/                       # Documentação
│   └── GUIA.md                 # Este arquivo
│
├── tests/                      # Testes (estrutura reservada)
├── Dockerfile                  # Multi-stage build (dev e prod)
├── docker-compose.yml          # Orquestração local (api + postgres)
├── requirements.txt            # Dependências da API
├── alembic.ini                 # Configuração do Alembic
├── .env.example                # Exemplo de variáveis de ambiente
└── README.md                   # Documentação resumida
```

### Por que essa organização?

A estrutura **por domínio** (`modules/auth`, `modules/aluno`, etc.) foi escolhida porque:

- Cada módulo é auto-contido: tem seu próprio `router.py`, `service.py` e `schemas.py`
- Facilita navegar pelo código sem precisar conhecer o projeto inteiro
- Reflete os domínios de negócio (não os tipos de arquivo), tornando o código mais legível
- Escala bem: adicionar um novo domínio é criar uma nova pasta sem tocar nas outras

---

## 3. Stack e decisões técnicas

### FastAPI

Escolhido por ser o framework Python mais moderno para APIs REST:

- **Async nativo**: todas as rotas e queries ao banco são `async/await`, o que permite alta concorrência sem bloquear a thread
- **Validação automática**: via Pydantic — se o payload não bater com o schema, o FastAPI retorna 422 automaticamente
- **Documentação grátis**: Swagger UI em `/docs` e ReDoc em `/redoc` gerados automaticamente a partir dos tipos Python
- **Dependency injection**: o sistema de `Depends()` elimina código repetitivo para autenticação, sessão de banco, etc.

### SQLAlchemy 2.0 (async)

- **ORM tipado**: `Mapped[int]`, `mapped_column()` — o editor entende os tipos sem precisar de stubs externos
- **Async**: todas as queries usam `await`, compatível com o modelo async do FastAPI
- **Não escreve SQL manual**: o ORM gera as queries, evitando erros e SQL injection

### Alembic

- **Autogenerate**: compara os models Python com o estado atual do banco e gera o diff de migration automaticamente
- **Versionado**: cada migration é um arquivo com um hash único, permitindo rastrear a evolução do schema no git

### PostgreSQL 16

- Banco relacional robusto com suporte a **JSONB** (usado em `Turma.horario` e `Aluno.endereco`)
- **asyncpg** como driver: driver PostgreSQL puro Python para uso async, mais rápido que psycopg2 em I/O assíncrono

### JWT + bcrypt

- **JWT** (`python-jose`): tokens stateless com payload `{ sub, role, nome }`. Access token expira em 15 min; refresh token em 7 dias
- **bcrypt direto** (sem passlib): a passlib tem um bug de compatibilidade com Python 3.12. Usamos `bcrypt.hashpw`/`bcrypt.checkpw` diretamente com custo 12

### Docker Compose

- **Multi-stage Dockerfile**: stage `dev` com `--reload` para desenvolvimento; stage `prod` com workers múltiplos para produção
- O `docker-compose.yml` define dois serviços: `api` (porta 8000) e `postgres` (porta 5432)
- `depends_on` com `healthcheck` garante que a API só sobe após o banco estar pronto

---

## 4. Passo a passo: como rodar localmente

### Pré-requisitos

- Docker e Docker Compose instalados
- Git

### 1. Clonar o repositório

```bash
git clone git@github.com:kayohr/academic-api.git
cd academic-api
```

### 2. Configurar variáveis de ambiente

```bash
cp .env.example .env
# Edite o .env se necessário (o padrão já funciona para desenvolvimento local)
```

O `.env.example` contém:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/academic_api
JWT_SECRET=change_me_to_a_strong_random_secret_at_least_32_chars
JWT_EXPIRES_MINUTES=15
JWT_REFRESH_EXPIRES_DAYS=7
DEBUG=false
LOG_LEVEL=info
```

> **Atenção**: em produção, troque `JWT_SECRET` por uma string aleatória longa.

### 3. Subir os containers

```bash
docker compose up -d
```

Isso inicia o banco PostgreSQL e a API com hot reload.

### 4. Aplicar as migrations

```bash
docker compose exec api alembic upgrade head
```

Isso cria todas as tabelas no banco de dados.

### 5. Criar o usuário admin

```bash
docker compose exec api python -c "
import asyncio, bcrypt
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.db.models import Usuario
from app.core.config import settings

async def main():
    engine = create_async_engine(settings.ASYNC_DATABASE_URL)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as db:
        h = bcrypt.hashpw(b'Admin@123', bcrypt.gensalt(12)).decode()
        db.add(Usuario(email='admin@academic.com', senha_hash=h, role='admin'))
        await db.commit()
    print('Admin criado: admin@academic.com / Admin@123')

asyncio.run(main())
"
```

Ou rode o seed completo (recomendado):

```bash
cd scripts
pip install -r requirements.txt
python seed.py
```

### 6. Testar

```bash
# Health check
curl http://localhost:8000/health

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@academic.com","senha":"Admin@123"}'

# Documentação interativa
open http://localhost:8000/docs
```

---

## 5. Camada de banco de dados

### `app/db/base.py`

Define o `DeclarativeBase` do SQLAlchemy. Todos os models herdam dessa classe. É separado de `models.py` para evitar importações circulares (o Alembic importa o `Base` antes dos models).

```python
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
```

### `app/db/models.py`

Contém **todos os 19 models em um único arquivo**. Essa decisão foi tomada porque o Alembic precisa enxergar todos os models para fazer o autogenerate corretamente — se os models ficassem espalhados, seria necessário importar cada arquivo manualmente no `env.py`.

Os models são organizados por grupo:

| Grupo | Models |
|-------|--------|
| Instituição | `Campus`, `Departamento`, `Curso` |
| Pessoas | `Professor`, `Aluno`, `Funcionario` |
| Acadêmico | `Semestre`, `Disciplina`, `GradeCurricular`, `Prerequisito`, `Turma` |
| Matrícula | `Matricula` |
| Avaliação | `Nota`, `Frequencia` |
| Histórico | `Historico` |
| Auth | `Usuario`, `RefreshToken`, `AuditLog` |

**Campos especiais:**

- `Turma.horario`: `JSONB` com lista de `{"dia", "hora_inicio", "hora_fim"}` — flexível sem criar tabela separada
- `Aluno.endereco`: `JSONB` — endereço é um dado variável, não vale a complexidade de tabela separada
- `Usuario`: tem um `CHECK CONSTRAINT` que garante que no máximo um dos campos `aluno_id`, `professor_id`, `funcionario_id` esteja preenchido — um usuário não pode ser aluno e professor ao mesmo tempo

**Soft delete:**

Alunos e professores têm `deleted_at: datetime | None`. Quando "deletados", esse campo recebe o timestamp atual. As queries sempre filtram `WHERE deleted_at IS NULL`. Isso evita perda de dados e mantém integridade referencial (matrículas, notas e histórico continuam apontando para o registro).

### `app/db/session.py`

Configura o engine async e o `AsyncSessionLocal`. O `get_session()` é um gerador async que o FastAPI usa via `Depends()` para injetar a sessão em cada endpoint.

```python
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
```

O `expire_on_commit=False` evita que os objetos expirem após o `commit`, o que causaria erros ao acessar atributos do objeto retornado pelo endpoint.

---

## 6. Camada core

### `app/core/config.py`

Usa `pydantic-settings` para ler variáveis de ambiente e validar tipos automaticamente. O `DATABASE_URL` vem do `.env` e é transformado em `ASYNC_DATABASE_URL` trocando o prefixo de driver.

### `app/core/exceptions.py`

Define hierarquia de exceções HTTP que todos os módulos usam:

```
AppException (base)
├── NotFoundError    → 404
├── UnauthorizedError → 401
├── ForbiddenError   → 403
├── ConflictError    → 409
└── ValidationError  → 422
```

Usar exceções customizadas em vez de `HTTPException` direta mantém o código dos services limpo e a estrutura de erro consistente em toda a API: `{"error": "NOT_FOUND", "message": "Aluno not found"}`.

### `app/core/deps.py`

Define as dependências injetáveis do FastAPI:

- `SessionDep`: injeta a sessão do banco em cada endpoint
- `CurrentUser`: decodifica o JWT e retorna `{"id", "role", "nome"}`
- `require_roles(*roles)`: factory que retorna um `Depends` que verifica se o usuário tem a role necessária

```python
# Exemplo de uso nos routers:
AdminOuCoordenador = Annotated[dict, Depends(require_roles("admin", "coordenador"))]

@router.post("/matriculas")
async def create_matricula(body: MatriculaCreate, db: SessionDep, _: AdminOuCoordenador):
    ...
```

### `app/core/security.py`

Funções de criptografia isoladas:

- `hash_password` / `verify_password`: usa `bcrypt` diretamente com custo 12
- `create_access_token` / `decode_access_token`: JWT via `python-jose`
- `generate_refresh_token`: `secrets.token_hex(40)` — 80 caracteres hexadecimais, criptograficamente seguro
- `hash_token`: SHA-256 do refresh token para armazenar no banco sem guardar o valor real

### `app/core/observability.py`

Três responsabilidades:

1. **Logs JSON**: via `python-json-logger`. Cada requisição gera dois logs: `request_start` e `request_end` com `request_id`, `method`, `path`, `status_code` e `duration_ms`
2. **Rate limiting**: via `slowapi` (wrapper do `limits` para FastAPI). Limite padrão de 200 req/min por IP. Retorna 429 com header `Retry-After: 60`
3. **Headers de rastreabilidade**: `X-Request-ID` (UUID curto) e `X-Response-Time` (em ms) em toda resposta

---

## 7. Módulos de negócio

Cada módulo segue a mesma estrutura de três arquivos:

```
modulo/
├── __init__.py   # vazio, marca como pacote Python
├── schemas.py    # Pydantic: validação de entrada e formato de saída
├── service.py    # Lógica de negócio e queries ao banco
└── router.py     # Endpoints FastAPI: recebe request, chama service, retorna response
```

**Por que separar em três arquivos?**

- `schemas.py` cuida apenas de validação — nenhuma lógica de banco
- `service.py` cuida apenas de negócio — nenhuma lógica HTTP
- `router.py` cuida apenas de HTTP — nenhuma lógica de banco ou negócio
- Isso torna cada arquivo testável e legível isoladamente

### auth

Gerencia o ciclo de vida de sessão:

- **Registro**: cria `Usuario` com `senha_hash` (bcrypt)
- **Login**: valida senha, gera `access_token` (JWT, 15 min) e `refresh_token` (token hex, 7 dias). O refresh token é armazenado como hash SHA-256 em `RefreshToken`
- **Refresh**: valida o refresh token, gera novo access token e **rotaciona** o refresh token (invalida o antigo, emite novo). Se um refresh token já revogado é reutilizado, todos os tokens da sessão são revogados (detecção de roubo)
- **Logout**: revoga o refresh token

### instituicao

CRUD simples para `Campus`, `Departamento` e `Curso`. Segue hierarquia: Campus → Departamento → Curso. Usa soft delete em `deleted_at`.

### aluno

Além do CRUD padrão, o cadastro de aluno gera automaticamente o número de matrícula no formato `AAAA9999` (ano + sequencial com zero-padding). O CPF é validado (11 dígitos numéricos) e indexado como único.

### professor

Além do CRUD, ao criar um professor o service verifica se `Usuario` com o e-mail já existe para evitar duplicata. Um professor com turmas ativas não pode ser deletado (soft delete protegido).

### disciplina

Três sub-recursos:

- **Disciplinas**: CRUD com código único por departamento
- **Pré-requisitos**: `POST /disciplinas/{id}/prerequisitos` adiciona uma relação na tabela `Prerequisito`. Valida que não há ciclo (A → B e B → A)
- **Grade curricular**: `GET/POST /cursos/{id}/grade` associa disciplinas a um curso com período e tipo (obrigatória/optativa/eletiva)

### turma

Dois sub-domínios: **Semestre** e **Turma**.

O service de turma valida conflito de horário do professor: ao criar/atualizar uma turma, busca todas as outras turmas do mesmo professor no mesmo semestre e verifica sobreposição de `{dia, hora_inicio, hora_fim}`.

### matricula

O módulo mais complexo — concentra as principais regras de negócio:

1. **Status do aluno**: deve ser `ativo`
2. **Status da turma**: deve ser `aberta` ou `em_andamento`
3. **Status do semestre**: deve ser `ativo`
4. **Duplicata**: aluno não pode ter duas matrículas na mesma turma
5. **Mesma disciplina**: aluno não pode ter matrículas ativas em duas turmas da mesma disciplina no mesmo semestre
6. **Pré-requisitos**: para cada `Prerequisito` da disciplina, verifica se existe um `Historico` do aluno com `situacao = 'aprovado'`
7. **Vagas**: conta `Matricula` com `status = 'ativa'` na turma e compara com `Turma.vagas`

O **trancamento** respeita a `data_limite_trancamento` do semestre e verifica ownership (aluno só tranca suas próprias matrículas via join com `Usuario.aluno_id`).

### avaliacao

Lançamento de notas (`AV1`, `AV2`, `AV3`) e frequência (por data de aula). O professor só pode operar em turmas onde é o professor responsável — validado via `Usuario.professor_id == Turma.professor_id`.

O endpoint `GET /matriculas/{id}/resumo` calcula em tempo real:
- Média aritmética das notas disponíveis
- `frequencia_pct = (aulas presentes / total de aulas) × 100`
- Situação: `aprovado` se média ≥ 6,0 e freq ≥ 75%; `reprovado` se não; `em_andamento` se faltar dados

### historico

`GET /alunos/{id}/historico` — lê snapshots imutáveis da tabela `Historico` com join em `Disciplina` e `Semestre` para retornar dados desnormalizados.

`GET /alunos/{id}/historico/cr` — calcula o CR:

```
CR = soma(nota_final × créditos) / soma(créditos)
```

Apenas disciplinas com `situacao = 'aprovado'` entram no cálculo.

`POST /semestres/{id}/consolidar` — gera os snapshots de `Historico` para todas as matrículas do semestre encerrado. Lê as notas e frequências de cada matrícula, calcula média e situação, e insere em `Historico`. É idempotente: se o snapshot já existe, ignora.

---

## 8. Fluxo de uma requisição

Exemplo: `POST /matriculas` (realizar matrícula)

```
Cliente
  │
  ├─ HTTP POST /matriculas
  │   Header: Authorization: Bearer <jwt>
  │   Body: {"aluno_id": 1, "turma_id": 5}
  │
  ▼
FastAPI (app/main.py)
  │
  ├─ Middleware de observabilidade → loga request_start, inicia timer
  ├─ Rate limiter → verifica limite por IP
  │
  ▼
Router (app/modules/matricula/router.py)
  │
  ├─ Pydantic valida o body → MatriculaCreate(aluno_id=1, turma_id=5)
  ├─ Depends(get_session) → abre sessão async com o banco
  ├─ Depends(require_roles("admin","coordenador")) →
  │     └─ get_current_user() → decodifica JWT → {"id":1, "role":"admin"}
  │
  ▼
Service (app/modules/matricula/service.py)
  │
  ├─ Busca aluno → valida status "ativo"
  ├─ Busca turma → valida status "aberta"/"em_andamento"
  ├─ Busca semestre → valida status "ativo"
  ├─ Verifica duplicata
  ├─ Verifica disciplina duplicada no semestre
  ├─ Verifica pré-requisitos → consulta Historico
  ├─ Conta vagas ocupadas → compara com turma.vagas
  ├─ db.add(Matricula(...))
  ├─ await db.commit()
  └─ await db.refresh(matricula)
  │
  ▼
Router
  │
  └─ return MatriculaResponse.model_validate(matricula)
  │
  ▼
FastAPI
  │
  ├─ Serializa para JSON
  ├─ Middleware → loga request_end com status_code e duration_ms
  └─ Adiciona headers X-Request-ID e X-Response-Time
  │
  ▼
Cliente
  HTTP 201 Created
  {"id": 42, "aluno_id": 1, "turma_id": 5, "status": "ativa", ...}
```

---

## 9. Autenticação e autorização

### Fluxo de login

```
POST /auth/login {"email": "...", "senha": "..."}
  │
  ├─ Busca Usuario por email
  ├─ bcrypt.checkpw(senha, senha_hash)
  ├─ Gera access_token JWT (15 min)
  │     payload: {"sub": "42", "role": "admin", "nome": "Kayo"}
  ├─ Gera refresh_token = secrets.token_hex(40)
  ├─ Salva hash SHA-256 do refresh_token em RefreshToken
  └─ Retorna {"access_token": "...", "refresh_token": "..."}
```

### Proteção de endpoints

Cada endpoint declara sua exigência de role:

```python
# Qualquer usuário autenticado
@router.get("/alunos/{id}")
async def get_aluno(db: SessionDep, _: CurrentUser): ...

# Apenas admin ou coordenador
AdminOuCoordenador = Annotated[dict, Depends(require_roles("admin", "coordenador"))]

@router.post("/matriculas")
async def create_matricula(db: SessionDep, _: AdminOuCoordenador): ...
```

### Rotação de refresh token

A cada `POST /auth/refresh`, o token antigo é revogado e um novo é emitido. Se alguém tentar reutilizar um token já revogado, **todos** os tokens da sessão são revogados — isso detecta vazamento de refresh token.

---

## 10. Migrations com Alembic

### Configuração

O `alembic/env.py` foi configurado para funcionar de forma assíncrona (o SQLAlchemy async não funciona com o modo síncrono padrão do Alembic). Ele lê a `DATABASE_URL` do `.env` e a converte para o driver `asyncpg`.

O `env.py` importa `app.db.models` (o arquivo com todos os models) para que o Alembic detecte todas as tabelas via `Base.metadata`.

### Como criar uma nova migration

```bash
# 1. Altere ou adicione um model em app/db/models.py

# 2. Gere a migration automaticamente
docker compose exec api alembic revision --autogenerate -m "descricao da mudanca"

# 3. Revise o arquivo gerado em alembic/versions/

# 4. Aplique
docker compose exec api alembic upgrade head
```

### Migrations existentes

| Hash | Descrição |
|------|-----------|
| `e45a74860ea7` | Schema inicial com todos os 18 models |
| `cd17aded154b` | Adiciona tabela `prerequisito` |

---

## 11. Scripts auxiliares

### `scripts/seed.py`

Popula o banco com dados realistas usando **Faker pt_BR**. É **idempotente**: verifica se cada registro já existe antes de inserir, então pode ser rodado múltiplas vezes sem duplicar dados.

O que é criado:
- 2 campus, 3 departamentos, 3 cursos
- 9 disciplinas com pré-requisitos e grade curricular
- 6 professores com usuário vinculado (`Prof@123`)
- 20 alunos com usuário vinculado (`Aluno@123`)
- 1 semestre ativo com 6 turmas e matrículas

```bash
python scripts/seed.py
```

### `scripts/relatorio.py`

Gera um relatório PDF de desempenho acadêmico de um aluno usando **reportlab**. O PDF inclui:
- Dados do aluno e curso
- CR atual
- Tabela de histórico com cores por situação (verde = aprovado, vermelho = reprovado, amarelo = trancado)
- Matrículas ativas no semestre corrente

```bash
python scripts/relatorio.py 1              # gera relatorio_aluno_1.pdf
python scripts/relatorio.py 1 saida.pdf   # nome customizado
```

---

## 12. Observabilidade

### Logs estruturados

Todos os logs são emitidos em JSON. Exemplo de output:

```json
{"asctime": "2026-04-14T17:34:40", "levelname": "INFO", "name": "academic_api",
 "message": "request_start", "request_id": "d7f7ef96", "method": "GET",
 "path": "/alunos", "client": "172.21.0.1"}

{"asctime": "2026-04-14T17:34:40", "levelname": "INFO", "name": "academic_api",
 "message": "request_end", "request_id": "d7f7ef96", "method": "GET",
 "path": "/alunos", "status_code": 200, "duration_ms": 4.21}
```

Logs em JSON são o padrão para ambientes com agregadores de log (Datadog, Loki, CloudWatch). É fácil filtrar por `request_id` para rastrear uma requisição específica.

### Rate limiting

```
200 requisições/minuto por IP (padrão)
```

Se excedido, retorna:
```json
HTTP 429
{"error": "RATE_LIMIT_EXCEEDED", "message": "Muitas requisições. Tente novamente em instantes."}
Retry-After: 60
```

### Headers de rastreabilidade

Toda resposta inclui:
- `X-Request-ID`: identificador único da requisição (útil para correlacionar logs)
- `X-Response-Time`: tempo de processamento em ms (útil para detectar endpoints lentos)

---

## 13. Como adicionar um novo módulo

Exemplo: adicionar o módulo `boleto` para geração de boletos acadêmicos.

### 1. Criar a pasta

```bash
mkdir app/modules/boleto
touch app/modules/boleto/__init__.py
```

### 2. Criar o model (se necessário)

Em `app/db/models.py`, adicione:

```python
class Boleto(Base):
    __tablename__ = "boleto"

    id:         Mapped[int]      = mapped_column(Integer, primary_key=True)
    aluno_id:   Mapped[int]      = mapped_column(ForeignKey("aluno.id"), nullable=False)
    valor:      Mapped[float]    = mapped_column(Numeric(10, 2), nullable=False)
    vencimento: Mapped[date]     = mapped_column(Date, nullable=False)
    status:     Mapped[str]      = mapped_column(String(20), default="pendente")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    aluno: Mapped["Aluno"] = relationship()
```

### 3. Gerar a migration

```bash
docker compose exec api alembic revision --autogenerate -m "add boleto table"
docker compose exec api alembic upgrade head
```

### 4. Criar os schemas

`app/modules/boleto/schemas.py`:

```python
from pydantic import BaseModel
from datetime import date, datetime

class BoletoCreate(BaseModel):
    aluno_id: int
    valor: float
    vencimento: date

class BoletoResponse(BaseModel):
    id: int
    aluno_id: int
    valor: float
    vencimento: date
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
```

### 5. Criar o service

`app/modules/boleto/service.py`:

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Boleto
from app.core.exceptions import NotFoundError

async def create_boleto(db: AsyncSession, data) -> Boleto:
    b = Boleto(aluno_id=data.aluno_id, valor=data.valor, vencimento=data.vencimento)
    db.add(b)
    await db.commit()
    await db.refresh(b)
    return b
```

### 6. Criar o router

`app/modules/boleto/router.py`:

```python
from fastapi import APIRouter
from app.core.deps import SessionDep, CurrentUser
from app.modules.boleto import service
from app.modules.boleto.schemas import BoletoCreate, BoletoResponse

router = APIRouter(tags=["Boletos"])

@router.post("/boletos", response_model=BoletoResponse, status_code=201)
async def create_boleto(body: BoletoCreate, db: SessionDep, _: CurrentUser):
    return await service.create_boleto(db, body)
```

### 7. Registrar em `app/main.py`

```python
from app.modules.boleto.router import router as boleto_router

# ...
app.include_router(boleto_router)
```

### 8. Adicionar a tag no OpenAPI (opcional)

Em `app/main.py`, no `openapi_tags`:

```python
{"name": "Boletos", "description": "Geração e consulta de boletos acadêmicos"},
```
