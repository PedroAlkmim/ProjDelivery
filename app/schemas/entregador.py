from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.comum import Dinheiro, Entrada


class DisponibilidadeIn(Entrada):
    disponibilidade: bool

    model_config = {"json_schema_extra": {"example": {"disponibilidade": True}}}


class DisponibilidadeOut(BaseModel):
    id_entregador: int
    disponibilidade: bool


class EntregaStatusIn(Entrada):
    status: Literal["EM_ROTA", "ENTREGUE", "DEVOLVIDA"]

    model_config = {"json_schema_extra": {"example": {"status": "EM_ROTA"}}}


class DestinoOut(BaseModel):
    logradouro: str
    numero: str
    complemento: str | None
    bairro: str
    cidade: str
    estado: str
    cep: str


class EntregaOut(BaseModel):
    id_entrega: int
    status: str
    data_solicitacao: datetime
    data_retirada: datetime | None
    data_entrega: datetime | None
    id_pedido: int
    id_entregador: int | None
    status_pedido: str
    estabelecimento: str
    cliente: str
    destino: DestinoOut
    valor_total: Dinheiro


class EntregaDisponivelOut(BaseModel):
    """Solicitação ainda sem entregador: mostra só o necessário para decidir aceitar."""

    id_entrega: int
    id_pedido: int
    data_solicitacao: datetime
    estabelecimento: str
    bairro_destino: str
    cidade_destino: str
