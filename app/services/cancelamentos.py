"""Solicitação de cancelamento (cliente) e análise (administrador). RF05, RF37, RN08."""
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants import (
    CANCEL_ABERTAS,
    CANCEL_APROVADA,
    CANCEL_PENDENTE,
    ENTREGA_CANCELADA,
    ENTREGA_FINAIS,
    PAGAMENTO_APROVADO,
    PAGAMENTO_CANCELADO,
    PAGAMENTO_ESTORNADO,
    PAGAMENTO_PENDENTE,
    PEDIDO_CANCELADO,
    PEDIDO_FINAIS,
    TRANSICOES_CANCELAMENTO,
)
from app.models import (
    Administrador,
    Cliente,
    Pedido,
    Produto,
    SolicitacaoCancelamento,
)
from app.services.regras import agora, checar_transicao


def solicitar_cancelamento(
    db: Session, cliente: Cliente, id_pedido: int, motivo: str
) -> SolicitacaoCancelamento:
    pedido = db.get(Pedido, id_pedido)
    if pedido is None or pedido.id_cliente != cliente.id_cliente:
        raise HTTPException(404, "Pedido não encontrado.")
    if pedido.status in PEDIDO_FINAIS:
        raise HTTPException(409, f"Pedido {pedido.status} não pode mais ser cancelado.")
    aberta = db.scalar(
        select(SolicitacaoCancelamento.id_solicitacao).where(
            SolicitacaoCancelamento.id_pedido == id_pedido,
            SolicitacaoCancelamento.status.in_(CANCEL_ABERTAS),
        )
    )
    if aberta is not None:
        raise HTTPException(409, "Já existe uma solicitação de cancelamento em aberto para este pedido.")

    solicitacao = SolicitacaoCancelamento(
        motivo=motivo,
        data_solicitacao=agora(),  # RN08: data e hora
        status=CANCEL_PENDENTE,
        observacao=None,
        id_cliente=cliente.id_cliente,  # RN08: quem solicitou
        id_administrador=None,  # preenchido quando um administrador analisar
        id_pedido=id_pedido,
    )
    db.add(solicitacao)
    db.commit()
    return solicitacao


def _cancelar_pedido(db: Session, pedido: Pedido) -> None:
    """Efeitos de uma solicitação APROVADA: pedido cancelado, estoque devolvido,
    pagamento estornado/cancelado e entrega cancelada (se ainda estiver em aberto)."""
    if pedido.status in PEDIDO_FINAIS:
        raise HTTPException(
            409, f"Pedido já está {pedido.status}; não é possível aprovar o cancelamento."
        )
    # devolve o estoque (produtos travados em ordem para evitar deadlock)
    ids = sorted(item.id_produto for item in pedido.itens)
    if ids:
        produtos = {
            p.id_produto: p
            for p in db.scalars(
                select(Produto).where(Produto.id_produto.in_(ids)).order_by(Produto.id_produto).with_for_update()
            )
        }
        for item in pedido.itens:
            produtos[item.id_produto].estoque += item.quantidade

    pagamento = pedido.pagamento
    if pagamento is not None:
        if pagamento.status_pagamento == PAGAMENTO_APROVADO:
            pagamento.status_pagamento = PAGAMENTO_ESTORNADO  # estorno só registrado
        elif pagamento.status_pagamento == PAGAMENTO_PENDENTE:
            pagamento.status_pagamento = PAGAMENTO_CANCELADO

    entrega = pedido.entrega
    if entrega is not None and entrega.status not in ENTREGA_FINAIS:
        entrega.status = ENTREGA_CANCELADA

    pedido.status = PEDIDO_CANCELADO


def analisar_cancelamento(
    db: Session,
    admin: Administrador,
    id_solicitacao: int,
    decisao: str,
    observacao: str | None,
) -> SolicitacaoCancelamento:
    solicitacao = db.scalar(
        select(SolicitacaoCancelamento)
        .where(SolicitacaoCancelamento.id_solicitacao == id_solicitacao)
        .with_for_update()
    )
    if solicitacao is None:
        raise HTTPException(404, "Solicitação de cancelamento não encontrada.")
    checar_transicao(TRANSICOES_CANCELAMENTO, solicitacao.status, decisao, "solicitação de cancelamento")

    if decisao == CANCEL_APROVADA:
        _cancelar_pedido(db, solicitacao.pedido)

    solicitacao.status = decisao
    solicitacao.id_administrador = admin.id_administrador  # RN08: responsável
    if observacao:
        solicitacao.observacao = observacao
    db.commit()
    return solicitacao
