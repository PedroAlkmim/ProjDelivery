from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.cliente import EnderecoOut
from app.schemas.comum import Dinheiro, Entrada, Saida


class ItemIn(Entrada):
    id_produto: int = Field(gt=0)
    quantidade: int = Field(gt=0, le=100)


class SimulacaoIn(Entrada):
    id_estabelecimento: int = Field(gt=0)
    codigo_cupom: str | None = Field(default=None, max_length=50)
    itens: list[ItemIn] = Field(min_length=1)

    model_config = {
        "json_schema_extra": {
            "example": {
                "id_estabelecimento": 1,
                "codigo_cupom": None,
                "itens": [{"id_produto": 1, "quantidade": 2}],
            }
        }
    }


class PedidoIn(SimulacaoIn):
    id_endereco: int = Field(gt=0)
    forma_pagamento: Literal["DINHEIRO", "PIX", "DEBITO", "CREDITO"]
    observacao: str | None = Field(default=None, max_length=500)

    model_config = {
        "json_schema_extra": {
            "example": {
                "id_estabelecimento": 1,
                "id_endereco": 1,
                "forma_pagamento": "PIX",
                "codigo_cupom": None,
                "observacao": "Sem cebola",
                "itens": [{"id_produto": 1, "quantidade": 2}],
            }
        }
    }


class ItemPedidoOut(BaseModel):
    id_produto: int
    produto: str
    quantidade: int
    preco_unitario: Dinheiro
    subtotal: Dinheiro


class SimulacaoOut(BaseModel):
    estabelecimento: str
    itens: list[ItemPedidoOut]
    codigo_cupom: str | None
    valor_subtotal: Dinheiro
    taxa_entrega: Dinheiro
    desconto: Dinheiro
    valor_total: Dinheiro


class PagamentoOut(BaseModel):
    id_pagamento: int
    forma_pagamento: str
    status_pagamento: str
    valor: Dinheiro


class EntregaResumoOut(BaseModel):
    id_entrega: int
    status: str
    data_solicitacao: datetime
    data_retirada: datetime | None
    data_entrega: datetime | None
    id_entregador: int | None


class PedidoOut(BaseModel):
    id_pedido: int
    data_hora: datetime
    status: str
    cliente: str
    id_estabelecimento: int
    estabelecimento: str
    endereco_entrega: EnderecoOut
    id_cupom: int | None
    codigo_cupom: str | None
    valor_subtotal: Dinheiro
    taxa_entrega: Dinheiro
    desconto: Dinheiro
    valor_total: Dinheiro
    observacao: str | None
    itens: list[ItemPedidoOut]
    pagamento: PagamentoOut | None
    entrega: EntregaResumoOut | None


class CancelamentoIn(Entrada):
    motivo: str = Field(min_length=5, max_length=500)

    model_config = {
        "json_schema_extra": {"example": {"motivo": "Demora na preparação"}}
    }


class SolicitacaoOut(Saida):
    id_solicitacao: int
    motivo: str
    data_solicitacao: datetime
    status: str
    observacao: str | None
    id_cliente: int
    id_administrador: int | None
    id_pedido: int
