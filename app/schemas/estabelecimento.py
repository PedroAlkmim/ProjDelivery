from decimal import Decimal

from pydantic import Field

from app.schemas.comum import Entrada


class ProdutoIn(Entrada):
    nome: str = Field(min_length=1, max_length=150)
    descricao: str | None = Field(default=None, max_length=1000)
    preco: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    estoque: int = Field(ge=0)
    imagem: str | None = Field(default=None, max_length=500)
    ativo: bool = True

    model_config = {
        "json_schema_extra": {
            "example": {
                "nome": "X-Salada",
                "descricao": "Pao, hamburguer, queijo e salada",
                "preco": 20.00,
                "estoque": 30,
                "imagem": None,
                "ativo": True,
            }
        }
    }


class ProdutoUpdate(Entrada):
    """Todos os campos são opcionais: só o que for enviado é alterado."""

    nome: str | None = Field(default=None, min_length=1, max_length=150)
    descricao: str | None = Field(default=None, max_length=1000)
    preco: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    estoque: int | None = Field(default=None, ge=0)
    imagem: str | None = Field(default=None, max_length=500)
    ativo: bool | None = None

    model_config = {"json_schema_extra": {"example": {"preco": 21.5, "estoque": 25}}}


class PedidoStatusIn(Entrada):
    status: str = Field(min_length=1, max_length=30)

    model_config = {"json_schema_extra": {"example": {"status": "CONFIRMADO"}}}
