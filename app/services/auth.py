"""Login: valida e-mail/senha, descobre o perfil do usuário e gera o token."""
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.constants import ENTREGADOR_APROVADO, ESTABELECIMENTO_ATIVO, USUARIO_ATIVO
from app.models import Administrador, Cliente, Entregador, Estabelecimento, Usuario
from app.security import criar_token, verificar_senha

# (nome do perfil, classe, nome da coluna de id)
_PERFIS = (
    ("ADMINISTRADOR", Administrador, "id_administrador"),
    ("CLIENTE", Cliente, "id_cliente"),
    ("ENTREGADOR", Entregador, "id_entregador"),
    ("ESTABELECIMENTO", Estabelecimento, "id_estabelecimento"),
)


def descobrir_perfil(db: Session, usuario: Usuario):
    for nome, modelo, coluna_id in _PERFIS:
        registro = db.scalar(select(modelo).where(modelo.id_usuario == usuario.id))
        if registro is not None:
            return nome, registro, getattr(registro, coluna_id)
    return None


def autenticar(db: Session, email: str, senha: str) -> dict:
    usuario = db.scalar(
        select(Usuario).where(func.lower(Usuario.email) == email.strip().lower())
    )
    if usuario is None or not verificar_senha(senha, usuario.senha):
        raise HTTPException(401, "E-mail ou senha inválidos.")
    if usuario.status != USUARIO_ATIVO:
        raise HTTPException(403, "Usuário inativo ou bloqueado.")

    perfil = descobrir_perfil(db, usuario)
    if perfil is None:
        raise HTTPException(403, "Usuário sem perfil associado.")
    nome_perfil, registro, id_perfil = perfil

    # RF17: entregador só acessa com cadastro aprovado
    if nome_perfil == "ENTREGADOR" and registro.status_aprovacao != ENTREGADOR_APROVADO:
        raise HTTPException(403, "Cadastro de entregador ainda não aprovado.")
    if nome_perfil == "ESTABELECIMENTO" and registro.status != ESTABELECIMENTO_ATIVO:
        raise HTTPException(403, "Estabelecimento inativo.")

    return {
        "access_token": criar_token(usuario.id, nome_perfil, id_perfil),
        "token_type": "bearer",
        "perfil": nome_perfil,
        "id_usuario": usuario.id,
        "id_perfil": id_perfil,
        "nome": usuario.nome,
    }
