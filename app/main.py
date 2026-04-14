from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.core.config import settings
from app.core.observability import setup_observabilidade
from app.modules.auth.router import router as auth_router
from app.modules.instituicao.router import router as instituicao_router
from app.modules.aluno.router import router as aluno_router
from app.modules.professor.router import router as professor_router
from app.modules.disciplina.router import router as disciplina_router
from app.modules.turma.router import router as turma_router
from app.modules.matricula.router import router as matricula_router
from app.modules.avaliacao.router import router as avaliacao_router
from app.modules.historico.router import router as historico_router

# ── Respostas de erro padrão reutilizáveis ────────────────────────────────────
_401 = {"description": "Não autenticado — token ausente ou inválido"}
_403 = {"description": "Sem permissão para este recurso"}
_404 = {"description": "Recurso não encontrado"}
_409 = {"description": "Conflito — recurso já existe ou regra de negócio violada"}
_422 = {"description": "Dados inválidos ou regra de negócio não atendida"}

app = FastAPI(
    title="Academic API",
    version=settings.APP_VERSION,
    description=(
        "API REST para gestão acadêmica universitária.\n\n"
        "## Autenticação\n"
        "Use `POST /auth/login` para obter um `access_token` (JWT, 15 min) "
        "e um `refresh_token` (7 dias). Passe o token no header:\n"
        "```\nAuthorization: Bearer <access_token>\n```\n\n"
        "## Roles\n"
        "| Role | Descrição |\n"
        "|------|-----------|\n"
        "| `admin` | Acesso total |\n"
        "| `coordenador` | Gerencia turmas, matrículas e grade |\n"
        "| `professor` | Lança notas e frequência nas próprias turmas |\n"
        "| `aluno` | Consulta suas matrículas, notas e histórico |\n\n"
        "## Paginação\n"
        "Endpoints de listagem retornam `{\"data\": [...], \"meta\": {\"total\", \"page\", \"page_size\"}}`."
    ),
    contact={
        "name": "Kayo Henricky",
        "url": "https://github.com/kayohr/academic-api",
    },
    license_info={
        "name": "MIT",
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "Auth",                 "description": "Registro, login, refresh e logout de usuários"},
        {"name": "Instituição",          "description": "Campus, Departamentos e Cursos"},
        {"name": "Alunos",               "description": "Cadastro e gestão de alunos"},
        {"name": "Professores",          "description": "Cadastro e gestão de professores"},
        {"name": "Disciplinas & Grade",  "description": "Disciplinas, pré-requisitos e grade curricular por curso"},
        {"name": "Semestres & Turmas",   "description": "Semestres letivos e turmas oferecidas"},
        {"name": "Matrículas",           "description": "Matrículas em turmas com validação de pré-requisitos e vagas"},
        {"name": "Notas & Frequência",   "description": "Lançamento de notas (AV1/AV2/AV3) e frequência por aula"},
        {"name": "Histórico Acadêmico",  "description": "Histórico consolidado, CR e consolidação de semestre"},
        {"name": "Health",               "description": "Health checks da aplicação e banco de dados"},
    ],
)

setup_observabilidade(app, log_level=settings.LOG_LEVEL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth_router,        prefix="/auth", tags=["Auth"])
app.include_router(instituicao_router, tags=["Instituição"])
app.include_router(aluno_router)
app.include_router(professor_router)
app.include_router(disciplina_router)
app.include_router(turma_router)
app.include_router(matricula_router)
app.include_router(avaliacao_router)
app.include_router(historico_router)


# ── Health ────────────────────────────────────────────────────────────────────

@app.get(
    "/health",
    tags=["Health"],
    summary="Liveness básico",
    response_description="Aplicação no ar",
)
async def health():
    return {"status": "ok"}


@app.get(
    "/health/ready",
    tags=["Health"],
    summary="Readiness — verifica conexão com o banco",
    responses={503: {"description": "Banco de dados indisponível"}},
)
async def ready():
    from app.db.session import engine
    from sqlalchemy import text
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"ready": True}
    except Exception:
        from fastapi import Response
        return Response(status_code=503, content='{"ready": false}')


@app.get(
    "/health/live",
    tags=["Health"],
    summary="Alive check",
)
async def live():
    return {"alive": True}
