"""Senha (hash bcrypt) e token de login (JWT)."""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app import config


def gerar_hash(senha: str) -> str:
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_senha(senha: str, senha_hash: str) -> bool:
    try:
        return bcrypt.checkpw(senha.encode("utf-8"), senha_hash.encode("utf-8"))
    except (ValueError, TypeError):
        # hash inválido (ex.: senha ainda em texto puro) ou senha longa demais
        return False


def criar_token(id_usuario: int, perfil: str, id_perfil: int) -> str:
    expira = datetime.now(timezone.utc) + timedelta(minutes=config.TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(id_usuario),
        "perfil": perfil,
        "perfil_id": id_perfil,
        "exp": expira,
    }
    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.JWT_ALGORITHM)


def decodificar_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, config.SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None
