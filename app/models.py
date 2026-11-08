"""Mapeamento ORM das 14 tabelas que JÁ EXISTEM no banco.
Estas classes apenas descrevem as tabelas; nada é criado nem alterado no PostgreSQL."""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# ENUM nativo que já existe no banco (create_type=False: não tenta criá-lo).
FormaPagamentoDB = ENUM(
    "DINHEIRO", "PIX", "DEBITO", "CREDITO", name="forma_pagamento", create_type=False
)



class Usuario(Base):
    __tablename__ = "usuario"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(150))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    senha: Mapped[str] = mapped_column(String(255))
    telefone: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(30))


class Administrador(Base):
    __tablename__ = "administrador"

    id_administrador: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuario.id"), unique=True)
    nivel_acesso: Mapped[str] = mapped_column(String(30))

    usuario: Mapped["Usuario"] = relationship()


class Cliente(Base):
    __tablename__ = "cliente"

    id_cliente: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuario.id"), unique=True)

    usuario: Mapped["Usuario"] = relationship()


class Entregador(Base):
    __tablename__ = "entregador"

    id_entregador: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuario.id"), unique=True)
    disponibilidade: Mapped[bool] = mapped_column(Boolean)
    status_aprovacao: Mapped[str] = mapped_column(String(30))

    usuario: Mapped["Usuario"] = relationship()


class Estabelecimento(Base):
    __tablename__ = "estabelecimento"

    id_estabelecimento: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuario.id"), unique=True)
    nome_fantasia: Mapped[str] = mapped_column(String(150))
    cnpj: Mapped[str] = mapped_column(String(18), unique=True)
    categoria: Mapped[str] = mapped_column(String(60))
    status: Mapped[str] = mapped_column(String(30))

    usuario: Mapped["Usuario"] = relationship()


# ---------------------------------------------------------------- Cadastros
class Endereco(Base):
    __tablename__ = "endereco"

    id_endereco: Mapped[int] = mapped_column(Integer, primary_key=True)
    logradouro: Mapped[str] = mapped_column(String(150))
    numero: Mapped[str] = mapped_column(String(20))
    complemento: Mapped[str | None] = mapped_column(String(100))
    bairro: Mapped[str] = mapped_column(String(100))
    cidade: Mapped[str] = mapped_column(String(100))
    estado: Mapped[str] = mapped_column(String(2))
    cep: Mapped[str] = mapped_column(String(9))
    tipo: Mapped[str] = mapped_column(String(30))
    id_cliente: Mapped[int] = mapped_column(ForeignKey("cliente.id_cliente"))


class Produto(Base):
    __tablename__ = "produto"

    id_produto: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(150))
    descricao: Mapped[str | None] = mapped_column(Text)
    preco: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    estoque: Mapped[int] = mapped_column(Integer)
    imagem: Mapped[str | None] = mapped_column(String(500))
    ativo: Mapped[bool] = mapped_column(Boolean)
    id_estabelecimento: Mapped[int] = mapped_column(
        ForeignKey("estabelecimento.id_estabelecimento")
    )


class Cupom(Base):
    __tablename__ = "cupom"

    id_cupom: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True)
    percentual_desconto: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    valor_desconto: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    valor_minimo_pedido: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    data_inicio: Mapped[datetime] = mapped_column(DateTime)
    data_fim: Mapped[datetime] = mapped_column(DateTime)
    ativo: Mapped[bool] = mapped_column(Boolean)


# ---------------------------------------------------------------- Pedido e dependentes
class Pedido(Base):
    __tablename__ = "pedido"

    id_pedido: Mapped[int] = mapped_column(Integer, primary_key=True)
    data_hora: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(30))
    valor_subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    taxa_entrega: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    valor_total: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    observacao: Mapped[str | None] = mapped_column(Text)
    id_cliente: Mapped[int] = mapped_column(ForeignKey("cliente.id_cliente"))
    id_estabelecimento: Mapped[int] = mapped_column(
        ForeignKey("estabelecimento.id_estabelecimento")
    )
    id_endereco: Mapped[int] = mapped_column(ForeignKey("endereco.id_endereco"))
    id_cupom: Mapped[int | None] = mapped_column(ForeignKey("cupom.id_cupom"))

    cliente: Mapped["Cliente"] = relationship()
    estabelecimento: Mapped["Estabelecimento"] = relationship()
    endereco: Mapped["Endereco"] = relationship()
    cupom: Mapped[Optional["Cupom"]] = relationship()
    itens: Mapped[list["ItemPedido"]] = relationship(
        back_populates="pedido", order_by="ItemPedido.id_produto"
    )
    pagamento: Mapped[Optional["Pagamento"]] = relationship(
        back_populates="pedido", uselist=False
    )
    entrega: Mapped[Optional["Entrega"]] = relationship(
        back_populates="pedido", uselist=False
    )


class ItemPedido(Base):
    __tablename__ = "item_pedido"

    # Chave primária composta (não existe id próprio no modelo).
    id_pedido: Mapped[int] = mapped_column(
        ForeignKey("pedido.id_pedido"), primary_key=True, autoincrement=False
    )
    id_produto: Mapped[int] = mapped_column(
        ForeignKey("produto.id_produto"), primary_key=True, autoincrement=False
    )
    quantidade: Mapped[int] = mapped_column(Integer)
    preco_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    pedido: Mapped["Pedido"] = relationship(back_populates="itens")
    produto: Mapped["Produto"] = relationship()


class Pagamento(Base):
    __tablename__ = "pagamento"

    id_pagamento: Mapped[int] = mapped_column(Integer, primary_key=True)
    forma_pagamento: Mapped[str] = mapped_column(FormaPagamentoDB)
    status_pagamento: Mapped[str] = mapped_column(String(30))
    valor: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    id_pedido: Mapped[int] = mapped_column(ForeignKey("pedido.id_pedido"), unique=True)

    pedido: Mapped["Pedido"] = relationship(back_populates="pagamento")


class Entrega(Base):
    __tablename__ = "entrega"

    id_entrega: Mapped[int] = mapped_column(Integer, primary_key=True)
    data_solicitacao: Mapped[datetime] = mapped_column(DateTime)
    data_retirada: Mapped[datetime | None] = mapped_column(DateTime)
    data_entrega: Mapped[datetime | None] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(30))
    id_pedido: Mapped[int] = mapped_column(ForeignKey("pedido.id_pedido"), unique=True)
    id_entregador: Mapped[int | None] = mapped_column(
        ForeignKey("entregador.id_entregador")
    )

    pedido: Mapped["Pedido"] = relationship(back_populates="entrega")
    entregador: Mapped[Optional["Entregador"]] = relationship()


class Avaliacao(Base):
    __tablename__ = "avaliacao"

    id_avaliacao: Mapped[int] = mapped_column(Integer, primary_key=True)
    nota: Mapped[int] = mapped_column(Integer)
    comentario: Mapped[str | None] = mapped_column(Text)
    data: Mapped[datetime] = mapped_column(DateTime)
    id_cliente: Mapped[int] = mapped_column(ForeignKey("cliente.id_cliente"))
    id_estabelecimento: Mapped[int] = mapped_column(
        ForeignKey("estabelecimento.id_estabelecimento")
    )

    cliente: Mapped["Cliente"] = relationship()


class SolicitacaoCancelamento(Base):
    __tablename__ = "solicitacao_cancelamento"

    id_solicitacao: Mapped[int] = mapped_column(Integer, primary_key=True)
    motivo: Mapped[str] = mapped_column(Text)
    data_solicitacao: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(30))
    observacao: Mapped[str | None] = mapped_column(Text)
    id_cliente: Mapped[int] = mapped_column(ForeignKey("cliente.id_cliente"))
    id_administrador: Mapped[int | None] = mapped_column(
        ForeignKey("administrador.id_administrador")
    )
    id_pedido: Mapped[int] = mapped_column(ForeignKey("pedido.id_pedido"))

    pedido: Mapped["Pedido"] = relationship()
