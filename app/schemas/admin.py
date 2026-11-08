from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.comum import Dinheiro, Email, Entrada, Saida, Senha
from app.services.regras import normalizar_cnpj


class EstabelecimentoCreate(Entrada):
    nome: str = Field(min_length=2, max_length=150, description="Nome do usuário responsável")
    email: Email
    senha: Senha
    telefone: str | None = Field(default=None, max_length=20)
    nome_fantasia: str = Field(min_length=1, max_length=150)
    cnpj: str = Field(description="14 dígitos, com ou sem máscara")
    categoria: str = Field(min_length=1, max_length=60)

    @field_validator("cnpj")
    @classmethod
    def _validar_cnpj(cls, valor: str) -> str:
        normalizado = normalizar_cnpj(valor)
        if normalizado is None:
            raise ValueError("CNPJ deve ter 14 dígitos.")
        return normalizado

    model_config = {
        "json_schema_extra": {
            "example": {
                "nome": "Pizzaria Bella",
                "email": "pizzaria@email.com",
                "senha": "123456",
                "telefone": "62999990020",
                "nome_fantasia": "Pizzaria Bella",
                "cnpj": "98.765.432/0001-10",
                "categoria": "Pizzaria",
            }
        }
    }


class EstabelecimentoAdminOut(BaseModel):
    id_estabelecimento: int
    id_usuario: int
    email: str
    nome_fantasia: str
    cnpj: str
    categoria: str
    status: str


class EntregadorCreate(Entrada):
    nome: str = Field(min_length=2, max_length=150)
    email: Email
    senha: Senha
    telefone: str | None = Field(default=None, max_length=20)

    model_config = {
        "json_schema_extra": {
            "example": {
                "nome": "Ana Entregadora",
                "email": "ana.entregadora@email.com",
                "senha": "123456",
                "telefone": "62999990030",
            }
        }
    }


class EntregadorAdminOut(BaseModel):
    id_entregador: int
    id_usuario: int
    nome: str
    email: str
    disponibilidade: bool
    status_aprovacao: str


class UsuarioAdminOut(BaseModel):
    id: int
    nome: str
    email: str
    telefone: str | None
    status: str
    perfil: str


class UsuarioStatusIn(Entrada):
    status: Literal["ATIVO", "INATIVO", "BLOQUEADO"]

    model_config = {"json_schema_extra": {"example": {"status": "BLOQUEADO"}}}


class AprovacaoIn(Entrada):
    status_aprovacao: Literal["APROVADO", "REPROVADO"]

    model_config = {"json_schema_extra": {"example": {"status_aprovacao": "APROVADO"}}}


class AnaliseCancelamentoIn(Entrada):
    decisao: Literal["EM_ANALISE", "APROVADA", "RECUSADA"]
    observacao: str | None = Field(default=None, max_length=500)

    model_config = {
        "json_schema_extra": {
            "example": {"decisao": "APROVADA", "observacao": "Cancelamento aceito."}
        }
    }


class CupomIn(Entrada):
    codigo: str = Field(min_length=3, max_length=50)
    percentual_desconto: Decimal | None = Field(
        default=None, gt=0, le=100, max_digits=5, decimal_places=2
    )
    valor_desconto: Decimal | None = Field(
        default=None, gt=0, max_digits=10, decimal_places=2
    )
    valor_minimo_pedido: Decimal | None = Field(
        default=None, ge=0, max_digits=10, decimal_places=2
    )
    data_inicio: datetime
    data_fim: datetime
    ativo: bool = True

    @model_validator(mode="after")
    def _validar(self):
        # exatamente um tipo de desconto
        if (self.percentual_desconto is None) == (self.valor_desconto is None):
            raise ValueError(
                "Informe percentual_desconto OU valor_desconto (apenas um dos dois)."
            )
        # o banco usa TIMESTAMP sem fuso: descarta o fuso se vier informado
        self.data_inicio = self.data_inicio.replace(tzinfo=None)
        self.data_fim = self.data_fim.replace(tzinfo=None)
        if self.data_fim < self.data_inicio:
            raise ValueError("data_fim deve ser maior ou igual a data_inicio.")
        return self

    model_config = {
        "json_schema_extra": {
            "example": {
                "codigo": "PROMO10",
                "percentual_desconto": 10,
                "valor_desconto": None,
                "valor_minimo_pedido": 30,
                "data_inicio": "2026-01-01T00:00:00",
                "data_fim": "2026-12-31T23:59:59",
                "ativo": True,
            }
        }
    }


class CupomUpdate(Entrada):
    ativo: bool | None = None
    data_fim: datetime | None = None

    @model_validator(mode="after")
    def _ajustar(self):
        if self.data_fim is not None:
            self.data_fim = self.data_fim.replace(tzinfo=None)
        return self

    model_config = {"json_schema_extra": {"example": {"ativo": False}}}


class CupomOut(Saida):
    id_cupom: int
    codigo: str
    percentual_desconto: Dinheiro | None
    valor_desconto: Dinheiro | None
    valor_minimo_pedido: Dinheiro | None
    data_inicio: datetime
    data_fim: datetime
    ativo: bool


class RelatorioPedidosStatusOut(BaseModel):
    status: str
    quantidade: int
    valor_total: Dinheiro


class RelatorioEntregasEntregadorOut(BaseModel):
    id_entregador: int | None
    entregador: str
    status: str
    quantidade: int
