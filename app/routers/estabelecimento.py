"""Painel do estabelecimento: só acessa os próprios produtos e pedidos."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_estabelecimento_atual
from app.models import Estabelecimento, Pedido, Produto
from app.schemas.catalogo import ProdutoOut
from app.schemas.entregador import EntregaOut
from app.schemas.estabelecimento import PedidoStatusIn, ProdutoIn, ProdutoUpdate
from app.schemas.pedido import PedidoOut
from app.services.entregas import entrega_para_dict, solicitar_entregador
from app.services.pedidos import (
    atualizar_status_pelo_estabelecimento,
    confirmar_pagamento,
    pedido_para_dict,
)

router = APIRouter(prefix="/estabelecimento", tags=["Estabelecimento"])


def _meu_pedido(db: Session, estab: Estabelecimento, id_pedido: int) -> Pedido:
    pedido = db.get(Pedido, id_pedido)
    if pedido is None or pedido.id_estabelecimento != estab.id_estabelecimento:
        raise HTTPException(404, "Pedido não encontrado.")
    return pedido


def _meu_produto(db: Session, estab: Estabelecimento, id_produto: int) -> Produto:
    produto = db.get(Produto, id_produto)
    if produto is None or produto.id_estabelecimento != estab.id_estabelecimento:
        raise HTTPException(404, "Produto não encontrado.")
    return produto


# ------------------------------------------------------------------ pedidos
@router.get("/pedidos", response_model=list[PedidoOut], summary="Pedidos recebidos")
def pedidos_recebidos(
    status: str | None = None,
    estab: Estabelecimento = Depends(get_estabelecimento_atual),
    db: Session = Depends(get_db),
):
    consulta = select(Pedido).where(Pedido.id_estabelecimento == estab.id_estabelecimento)
    if status:
        consulta = consulta.where(Pedido.status == status.strip().upper())
    pedidos = db.scalars(consulta.order_by(Pedido.id_pedido.desc())).all()
    return [pedido_para_dict(p) for p in pedidos]


@router.get("/pedidos/{id_pedido}", response_model=PedidoOut, summary="Detalhar um pedido")
def detalhar_pedido(
    id_pedido: int,
    estab: Estabelecimento = Depends(get_estabelecimento_atual),
    db: Session = Depends(get_db),
):
    return pedido_para_dict(_meu_pedido(db, estab, id_pedido))


@router.patch(
    "/pedidos/{id_pedido}/status",
    response_model=PedidoOut,
    summary="Atualizar status do pedido",
)
def atualizar_status(
    id_pedido: int,
    dados: PedidoStatusIn,
    estab: Estabelecimento = Depends(get_estabelecimento_atual),
    db: Session = Depends(get_db),
):
    """RF11 / RN07: transições permitidas ao estabelecimento:
    `CRIADO → CONFIRMADO → EM_PREPARO`. As demais (EM_ROTA, CONCLUIDO, DEVOLVIDO)
    acontecem pelas ações do entregador, e CANCELADO pela análise do administrador."""
    pedido = _meu_pedido(db, estab, id_pedido)
    atualizar_status_pelo_estabelecimento(db, pedido, dados.status.strip().upper())
    return pedido_para_dict(pedido)


@router.post(
    "/pedidos/{id_pedido}/confirmar-pagamento",
    response_model=PedidoOut,
    summary="Confirmar pagamento",
)
def confirmar_pagamento_pedido(
    id_pedido: int,
    estab: Estabelecimento = Depends(get_estabelecimento_atual),
    db: Session = Depends(get_db),
):
    """RF13 / RN04: marca o pagamento como APROVADO (simulado, sem cobrança real)."""
    pedido = _meu_pedido(db, estab, id_pedido)
    confirmar_pagamento(db, pedido)
    return pedido_para_dict(pedido)


@router.post(
    "/pedidos/{id_pedido}/solicitar-entregador",
    response_model=EntregaOut,
    status_code=201,
    summary="Solicitar entregador",
)
def pedir_entregador(
    id_pedido: int,
    estab: Estabelecimento = Depends(get_estabelecimento_atual),
    db: Session = Depends(get_db),
):
    """RF12 / RF14: valida o endereço e cria a entrega SOLICITADA (sem entregador).
    O pedido precisa estar EM_PREPARO."""
    entrega = solicitar_entregador(db, estab, id_pedido)
    return entrega_para_dict(entrega)


# ------------------------------------------------------------------ produtos
@router.get("/produtos", response_model=list[ProdutoOut], summary="Meus produtos")
def listar_produtos(
    estab: Estabelecimento = Depends(get_estabelecimento_atual),
    db: Session = Depends(get_db),
):
    """Lista todos os produtos do estabelecimento, inclusive os desativados."""
    return db.scalars(
        select(Produto)
        .where(Produto.id_estabelecimento == estab.id_estabelecimento)
        .order_by(Produto.id_produto)
    ).all()


@router.post("/produtos", response_model=ProdutoOut, status_code=201, summary="Cadastrar produto")
def cadastrar_produto(
    dados: ProdutoIn,
    estab: Estabelecimento = Depends(get_estabelecimento_atual),
    db: Session = Depends(get_db),
):
    produto = Produto(id_estabelecimento=estab.id_estabelecimento, **dados.model_dump())
    db.add(produto)
    db.commit()
    return produto


@router.put("/produtos/{id_produto}", response_model=ProdutoOut, summary="Editar produto")
def editar_produto(
    id_produto: int,
    dados: ProdutoUpdate,
    estab: Estabelecimento = Depends(get_estabelecimento_atual),
    db: Session = Depends(get_db),
):
    """Altera apenas os campos enviados (nome, descrição, preço, estoque, imagem, ativo)."""
    produto = _meu_produto(db, estab, id_produto)
    campos = dados.model_dump(exclude_unset=True)
    # nome, preco, estoque e ativo são obrigatórios no banco: não aceitam null
    for obrigatorio in ("nome", "preco", "estoque", "ativo"):
        if obrigatorio in campos and campos[obrigatorio] is None:
            raise HTTPException(422, f"O campo '{obrigatorio}' não pode ser nulo.")
    for campo, valor in campos.items():
        setattr(produto, campo, valor)
    db.commit()
    return produto


@router.patch(
    "/produtos/{id_produto}/desativar",
    response_model=ProdutoOut,
    summary="Desativar produto",
)
def desativar_produto(
    id_produto: int,
    estab: Estabelecimento = Depends(get_estabelecimento_atual),
    db: Session = Depends(get_db),
):
    """O produto deixa de aparecer no cardápio, mas continua no histórico dos pedidos."""
    produto = _meu_produto(db, estab, id_produto)
    produto.ativo = False
    db.commit()
    return produto
