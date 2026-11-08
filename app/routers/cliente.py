"""Cadastro e endereços do cliente, e avaliações (RF03, RF25, RF27, RF40)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants import PEDIDO_CONCLUIDO
from app.database import get_db
from app.deps import get_cliente_atual
from app.models import Avaliacao, Cliente, Endereco, Estabelecimento, Pedido
from app.schemas.cliente import (
    AvaliacaoIn,
    AvaliacaoOut,
    ClienteCreate,
    ClienteOut,
    EnderecoIn,
    EnderecoOut,
)
from app.services.regras import agora
from app.services.usuarios import criar_usuario

router = APIRouter(tags=["Cliente"])


@router.post(
    "/clientes",
    response_model=ClienteOut,
    status_code=201,
    summary="Cadastrar cliente (público)",
)
def cadastrar_cliente(dados: ClienteCreate, db: Session = Depends(get_db)):
    """RF03 / RF25: cria usuário + cliente + endereço em uma única transação."""
    usuario = criar_usuario(db, dados.nome, dados.email, dados.senha, dados.telefone)
    cliente = Cliente(id_usuario=usuario.id)
    db.add(cliente)
    db.flush()
    endereco = Endereco(id_cliente=cliente.id_cliente, **dados.endereco.model_dump())
    db.add(endereco)
    db.commit()
    return {
        "id_cliente": cliente.id_cliente,
        "id_usuario": usuario.id,
        "nome": usuario.nome,
        "email": usuario.email,
        "telefone": usuario.telefone,
        "endereco": endereco,
    }


@router.get(
    "/clientes/me/enderecos",
    response_model=list[EnderecoOut],
    summary="Listar meus endereços",
)
def listar_enderecos(
    cliente: Cliente = Depends(get_cliente_atual), db: Session = Depends(get_db)
):
    return db.scalars(
        select(Endereco)
        .where(Endereco.id_cliente == cliente.id_cliente)
        .order_by(Endereco.id_endereco)
    ).all()


@router.post(
    "/clientes/me/enderecos",
    response_model=EnderecoOut,
    status_code=201,
    summary="Cadastrar endereço alternativo",
)
def cadastrar_endereco(
    dados: EnderecoIn,
    cliente: Cliente = Depends(get_cliente_atual),
    db: Session = Depends(get_db),
):
    """RF27: endereço alternativo de entrega."""
    endereco = Endereco(id_cliente=cliente.id_cliente, **dados.model_dump())
    db.add(endereco)
    db.commit()
    return endereco


@router.post(
    "/avaliacoes",
    response_model=AvaliacaoOut,
    status_code=201,
    summary="Avaliar estabelecimento",
)
def avaliar_estabelecimento(
    dados: AvaliacaoIn,
    cliente: Cliente = Depends(get_cliente_atual),
    db: Session = Depends(get_db),
):
    """RF40: só é possível avaliar um estabelecimento onde o cliente tem pedido CONCLUIDO.
    (A avaliação do entregador não é possível: a tabela `avaliacao` não tem esse vínculo.)"""
    if db.get(Estabelecimento, dados.id_estabelecimento) is None:
        raise HTTPException(404, "Estabelecimento não encontrado.")
    concluido = db.scalar(
        select(Pedido.id_pedido)
        .where(
            Pedido.id_cliente == cliente.id_cliente,
            Pedido.id_estabelecimento == dados.id_estabelecimento,
            Pedido.status == PEDIDO_CONCLUIDO,
        )
        .limit(1)
    )
    if concluido is None:
        raise HTTPException(
            403, "Só é possível avaliar um estabelecimento após um pedido CONCLUIDO nele."
        )
    avaliacao = Avaliacao(
        nota=dados.nota,
        comentario=dados.comentario,
        data=agora(),
        id_cliente=cliente.id_cliente,
        id_estabelecimento=dados.id_estabelecimento,
    )
    db.add(avaliacao)
    db.commit()
    return avaliacao
