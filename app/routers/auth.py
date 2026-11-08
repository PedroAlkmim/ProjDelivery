from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import Sessao, get_sessao
from app.schemas.auth import LoginIn, SessaoOut, TokenOut
from app.services.auth import autenticar

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/login", response_model=TokenOut, summary="Login (JSON)")
def login(dados: LoginIn, db: Session = Depends(get_db)):
    """Login de qualquer perfil (cliente, estabelecimento, entregador ou administrador).
    Devolve o token que deve ser enviado no cabeçalho `Authorization: Bearer <token>`."""
    return autenticar(db, dados.email, dados.senha)


@router.post("/token", response_model=TokenOut, summary="Login (formulário do botão Authorize)")
def login_formulario(
    form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """Usado pelo botão **Authorize** do Swagger. Em `username`, informe o e-mail."""
    return autenticar(db, form.username, form.password)


@router.get("/me", response_model=SessaoOut, summary="Dados do usuário logado")
def me(sessao: Sessao = Depends(get_sessao)):
    return {
        "id_usuario": sessao.usuario.id,
        "nome": sessao.usuario.nome,
        "email": sessao.usuario.email,
        "perfil": sessao.perfil,
        "id_perfil": sessao.perfil_id,
    }
