"""Ponto de entrada da API. Execute com:  uvicorn app.main:app --reload"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.routers import (
    admin,
    auth,
    catalogo,
    cliente,
    entregador,
    estabelecimento,
    pedidos,
)

DESCRICAO = """
API do aplicativo de delivery (projeto acadêmico).

**Como testar:** faça login em `POST /auth/login`, copie o `access_token`, clique em
**Authorize** (cadeado) e informe o e-mail e a senha, ou use o formulário do próprio
botão. Cada perfil (cliente, estabelecimento, entregador, administrador) só enxerga
as rotas e os dados da sua função.

Pagamentos são **simulados**: apenas a forma e o status são registrados.
"""

app = FastAPI(
    title="Delivery API",
    description=DESCRICAO,
    version="1.0.0",
)

app.include_router(auth.router)
app.include_router(cliente.router)
app.include_router(catalogo.router)
app.include_router(pedidos.router)
app.include_router(estabelecimento.router)
app.include_router(entregador.router)
app.include_router(admin.router)


@app.exception_handler(IntegrityError)
async def tratar_integridade(request: Request, exc: IntegrityError):
    """Rede de segurança: violação de UNIQUE/FK/CHECK do banco vira 409 em vez de erro 500."""
    return JSONResponse(
        status_code=409,
        content={"detail": "Conflito de dados: registro duplicado ou violação de restrição do banco."},
    )


@app.get("/", tags=["Sistema"], summary="Verificar se a API está no ar")
def raiz():
    return {"status": "ok", "documentacao": "/docs"}
