from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.modules.auth.router import router as auth_router
from app.modules.instituicao.router import router as instituicao_router
from app.modules.aluno.router import router as aluno_router
from app.modules.professor.router import router as professor_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="REST API for academic management — FastAPI, PostgreSQL, JWT",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(instituicao_router, tags=["Instituição"])
app.include_router(aluno_router)
app.include_router(professor_router)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}


@app.get("/health/ready", tags=["Health"])
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


@app.get("/health/live", tags=["Health"])
async def live():
    return {"alive": True}
