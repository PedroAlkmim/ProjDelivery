"""Criação de usuário base (usada no cadastro de cliente e pelo administrador)."""
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.constants import USUARIO_ATIVO
from app.models import Usuario
from app.security import gerar_hash


def criar_usuario(db: Session, nome: str, email: str, senha: str, telefone: str | None) -> Usuario:
    """Insere em `usuario` (sem commit; quem chama confirma a transação)."""
    email = email.strip().lower()
    existente = db.scalar(select(Usuario.id).where(func.lower(Usuario.email) == email))
    if existente is not None:
        raise HTTPException(409, "E-mail já cadastrado.")
    usuario = Usuario(
        nome=nome,
        email=email,
        senha=gerar_hash(senha),
        telefone=telefone,
        status=USUARIO_ATIVO,
    )
    db.add(usuario)
    db.flush()  # gera o id do usuário para os perfis usarem
    return usuario
