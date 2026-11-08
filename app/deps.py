"""Dependências de autenticação e controle de acesso por perfil (RNF01, RNF06)."""
from dataclasses import dataclass

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.constants import ENTREGADOR_APROVADO, ESTABELECIMENTO_ATIVO, USUARIO_ATIVO
from app.database import get_db
from app.models import Administrador, Cliente, Entregador, Estabelecimento, Usuario
from app.security import decodificar_token

# tokenUrl aponta para o endpoint de formulário usado pelo botão "Authorize" do Swagger.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


@dataclass
class Sessao:
    usuario: Usuario
    perfil: str
    perfil_id: int


def _nao_autenticado() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail="Token inválido ou expirado. Faça login novamente.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_sessao(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> Sessao:
    payload = decodificar_token(token)
    if payload is None:
        raise _nao_autenticado()
    try:
        id_usuario = int(payload["sub"])
        perfil = payload["perfil"]
        perfil_id = int(payload["perfil_id"])
    except (KeyError, ValueError, TypeError):
        raise _nao_autenticado()
    usuario = db.get(Usuario, id_usuario)
    if usuario is None or usuario.status != USUARIO_ATIVO:
        raise _nao_autenticado()
    return Sessao(usuario=usuario, perfil=perfil, perfil_id=perfil_id)


def _exigir_perfil(nome_perfil: str, modelo):
    """Cria uma dependência que só deixa passar o perfil indicado e devolve
    o registro do perfil (Cliente, Estabelecimento, Entregador ou Administrador)."""

    def dependencia(
        sessao: Sessao = Depends(get_sessao), db: Session = Depends(get_db)
    ):
        if sessao.perfil != nome_perfil:
            raise HTTPException(403, f"Acesso restrito ao perfil {nome_perfil}.")
        registro = db.get(modelo, sessao.perfil_id)
        if registro is None or registro.id_usuario != sessao.usuario.id:
            raise _nao_autenticado()
        return registro

    return dependencia


get_cliente_atual = _exigir_perfil("CLIENTE", Cliente)
get_admin_atual = _exigir_perfil("ADMINISTRADOR", Administrador)
_get_estab = _exigir_perfil("ESTABELECIMENTO", Estabelecimento)
_get_entregador = _exigir_perfil("ENTREGADOR", Entregador)


def get_estabelecimento_atual(estab: Estabelecimento = Depends(_get_estab)):
    if estab.status != ESTABELECIMENTO_ATIVO:
        raise HTTPException(403, "Estabelecimento inativo.")
    return estab


def get_entregador_atual(entregador: Entregador = Depends(_get_entregador)):
    # RF17: só entregadores com cadastro aprovado acessam o sistema.
    if entregador.status_aprovacao != ENTREGADOR_APROVADO:
        raise HTTPException(403, "Cadastro de entregador ainda não aprovado.")
    return entregador
