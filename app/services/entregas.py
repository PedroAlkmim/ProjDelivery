"""Fluxo da entrega: solicitar (estabelecimento), aceitar e atualizar (entregador)."""
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants import (
    ENTREGA_AGUARDANDO_RETIRADA,
    ENTREGA_DEVOLVIDA,
    ENTREGA_EM_ROTA,
    ENTREGA_ENTREGUE,
    ENTREGA_SOLICITADA,
    FORMA_SEM_APROVACAO_PREVIA,
    PAGAMENTO_APROVADO,
    PAGAMENTO_PENDENTE,
    PEDIDO_CONCLUIDO,
    PEDIDO_DEVOLVIDO,
    PEDIDO_EM_PREPARO,
    PEDIDO_EM_ROTA,
    TRANSICOES_ENTREGA_ENTREGADOR,
)
from app.models import Entrega, Entregador, Estabelecimento, Pedido
from app.services.regras import agora, checar_transicao, validar_endereco


def solicitar_entregador(db: Session, estab: Estabelecimento, id_pedido: int) -> Entrega:
    """RF12 / RF14: cria a entrega SOLICITADA (sem entregador) após validar o endereço."""
    pedido = db.get(Pedido, id_pedido)
    if pedido is None or pedido.id_estabelecimento != estab.id_estabelecimento:
        raise HTTPException(404, "Pedido não encontrado.")
    if pedido.status != PEDIDO_EM_PREPARO:
        raise HTTPException(
            409,
            f"O entregador só pode ser solicitado com o pedido {PEDIDO_EM_PREPARO} "
            f"(status atual: {pedido.status}).",
        )
    if pedido.entrega is not None:
        raise HTTPException(409, "Já existe uma entrega para este pedido.")
    validar_endereco(pedido.endereco)  # RN03

    entrega = Entrega(
        data_solicitacao=agora(),
        data_retirada=None,
        data_entrega=None,
        status=ENTREGA_SOLICITADA,
        id_pedido=pedido.id_pedido,
        id_entregador=None,
    )
    db.add(entrega)
    db.commit()
    return entrega


def aceitar_entrega(db: Session, entregador: Entregador, id_entrega: int) -> Entrega:
    """RF19: o entregador disponível aceita uma solicitação em aberto."""
    entrega = db.scalar(
        select(Entrega).where(Entrega.id_entrega == id_entrega).with_for_update()
    )
    if entrega is None or entrega.status != ENTREGA_SOLICITADA or entrega.id_entregador is not None:
        raise HTTPException(404, "Solicitação de entrega não encontrada ou já aceita.")
    if not entregador.disponibilidade:
        raise HTTPException(409, "Você está indisponível. Informe disponibilidade antes de aceitar.")
    entrega.id_entregador = entregador.id_entregador
    entrega.status = ENTREGA_AGUARDANDO_RETIRADA
    db.commit()
    return entrega


def atualizar_status_entrega(
    db: Session, entregador: Entregador, id_entrega: int, novo_status: str
) -> Entrega:
    """RF20 / RF21: retirada, entrega ou devolução, só nas entregas do próprio entregador."""
    entrega = db.scalar(
        select(Entrega).where(Entrega.id_entrega == id_entrega).with_for_update()
    )
    if entrega is None or entrega.id_entregador != entregador.id_entregador:
        raise HTTPException(404, "Entrega não encontrada.")
    checar_transicao(TRANSICOES_ENTREGA_ENTREGADOR, entrega.status, novo_status, "entrega")

    pedido = entrega.pedido
    entrega.status = novo_status
    if novo_status == ENTREGA_EM_ROTA:  # retirada no estabelecimento
        entrega.data_retirada = agora()
        pedido.status = PEDIDO_EM_ROTA
    elif novo_status == ENTREGA_ENTREGUE:
        entrega.data_entrega = agora()
        pedido.status = PEDIDO_CONCLUIDO
        pagamento = pedido.pagamento
        # pagamento em dinheiro é recebido na entrega
        if (
            pagamento is not None
            and pagamento.forma_pagamento == FORMA_SEM_APROVACAO_PREVIA
            and pagamento.status_pagamento == PAGAMENTO_PENDENTE
        ):
            pagamento.status_pagamento = PAGAMENTO_APROVADO
    elif novo_status == ENTREGA_DEVOLVIDA:  # cliente ausente (RN05)
        pedido.status = PEDIDO_DEVOLVIDO
    db.commit()
    return entrega


def entrega_para_dict(e: Entrega) -> dict:
    p = e.pedido
    end = p.endereco
    return {
        "id_entrega": e.id_entrega,
        "status": e.status,
        "data_solicitacao": e.data_solicitacao,
        "data_retirada": e.data_retirada,
        "data_entrega": e.data_entrega,
        "id_pedido": e.id_pedido,
        "id_entregador": e.id_entregador,
        "status_pedido": p.status,
        "estabelecimento": p.estabelecimento.nome_fantasia,
        "cliente": p.cliente.usuario.nome,
        "destino": {
            "logradouro": end.logradouro,
            "numero": end.numero,
            "complemento": end.complemento,
            "bairro": end.bairro,
            "cidade": end.cidade,
            "estado": end.estado,
            "cep": end.cep,
        },
        "valor_total": p.valor_total,
    }


def entrega_disponivel_para_dict(e: Entrega) -> dict:
    p = e.pedido
    return {
        "id_entrega": e.id_entrega,
        "id_pedido": e.id_pedido,
        "data_solicitacao": e.data_solicitacao,
        "estabelecimento": p.estabelecimento.nome_fantasia,
        "bairro_destino": p.endereco.bairro,
        "cidade_destino": p.endereco.cidade,
    }
