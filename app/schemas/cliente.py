from datetime import datetime

from pydantic import Field, field_validator

from app.schemas.comum import Email, Entrada, Saida, Senha
from app.services.regras import normalizar_cep


class EnderecoIn(Entrada):
    logradouro: str = Field(min_length=1, max_length=150)
    numero: str = Field(min_length=1, max_length=20)
    complemento: str | None = Field(default=None, max_length=100)
    bairro: str = Field(min_length=1, max_length=100)
    cidade: str = Field(min_length=1, max_length=100)
    estado: str = Field(min_length=2, max_length=2, description="UF, ex.: GO")
    cep: str = Field(description="8 dígitos, com ou sem hífen")
    tipo: str = Field(default="RESIDENCIAL", min_length=1, max_length=30)

    @field_validator("cep")
    @classmethod
    def _validar_cep(cls, valor: str) -> str:
        normalizado = normalizar_cep(valor)
        if normalizado is None:
            raise ValueError("CEP deve ter 8 dígitos.")
        return normalizado

    @field_validator("estado")
    @classmethod
    def _validar_uf(cls, valor: str) -> str:
        if not valor.isalpha():
            raise ValueError("Estado deve ter 2 letras (UF).")
        return valor.upper()


class EnderecoOut(Saida):
    id_endereco: int
    logradouro: str
    numero: str
    complemento: str | None
    bairro: str
    cidade: str
    estado: str
    cep: str
    tipo: str
    id_cliente: int


class ClienteCreate(Entrada):
    nome: str = Field(min_length=2, max_length=150)
    email: Email
    senha: Senha
    telefone: str | None = Field(default=None, max_length=20)
    endereco: EnderecoIn

    model_config = {
        "json_schema_extra": {
            "example": {
                "nome": "Maria Cliente",
                "email": "maria@email.com",
                "senha": "123456",
                "telefone": "62999990010",
                "endereco": {
                    "logradouro": "Rua 10",
                    "numero": "250",
                    "complemento": "Apto 302",
                    "bairro": "Setor Oeste",
                    "cidade": "Goiania",
                    "estado": "GO",
                    "cep": "74120-020",
                    "tipo": "RESIDENCIAL",
                },
            }
        }
    }


class ClienteOut(Saida):
    id_cliente: int
    id_usuario: int
    nome: str
    email: str
    telefone: str | None
    endereco: EnderecoOut


class AvaliacaoIn(Entrada):
    id_estabelecimento: int = Field(gt=0)
    nota: int = Field(ge=1, le=5)
    comentario: str | None = Field(default=None, max_length=1000)

    model_config = {
        "json_schema_extra": {
            "example": {"id_estabelecimento": 1, "nota": 5, "comentario": "Muito bom!"}
        }
    }


class AvaliacaoOut(Saida):
    id_avaliacao: int
    nota: int
    comentario: str | None
    data: datetime
    id_cliente: int
    id_estabelecimento: int
