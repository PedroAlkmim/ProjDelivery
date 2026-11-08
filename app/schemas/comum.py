"""Tipos e classes-base compartilhados pelos schemas."""
from decimal import Decimal
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, PlainSerializer


class Entrada(BaseModel):
    """Base para dados recebidos: remove espaços nas pontas dos textos."""

    model_config = ConfigDict(str_strip_whitespace=True)


class Saida(BaseModel):
    """Base para dados devolvidos: pode ser criada a partir de objetos do banco."""

    model_config = ConfigDict(from_attributes=True)


# Valores em dinheiro saem como número no JSON (ex.: 41.0), não como texto.
Dinheiro = Annotated[
    Decimal, PlainSerializer(lambda v: float(v), return_type=float, when_used="json")
]


def _limite_bytes_senha(valor: str) -> str:
    # o bcrypt só aceita senhas de até 72 bytes
    if len(valor.encode("utf-8")) > 72:
        raise ValueError("A senha deve ter no máximo 72 bytes.")
    return valor


Senha = Annotated[
    str, Field(min_length=6, max_length=72), AfterValidator(_limite_bytes_senha)
]
Email = Annotated[
    str,
    Field(min_length=5, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$"),
]
