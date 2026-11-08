"""Regras de pedido: cálculo de valores no backend, validação de estoque e cupom,
criação do pedido e montagem das respostas."""
from dataclasses import dataclass
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import config
from app.constants import (
    ESTABELECIMENTO_ATIVO,
    FORMA_SEM_APROVACAO_PREVIA,
    PAGAMENTO_APROVADO,
    PAGAMENTO_PENDENTE,
    PEDIDO_CONFIRMADO,
    PEDIDO_CRIADO,
    TRANSICOES_PEDIDO_ESTABELECIMENTO,
)
from app.models import (
    Cliente,
    Cupom,
    Endereco,
    Estabelecimento,
    ItemPedido,
    Pagamento,
    Pedido,
    Produto,
)
from app.services.regras import agora, checar_transicao, money


@dataclass
class Calculo:
    estabelecimento: Estabelecimento
    linhas: list  # [(Produto, quantidade)]
    cupom: Cupom | None
    subtotal: Decimal
    taxa: Decimal
    desconto: Decimal
    total: Decimal


# ------------------------------------------------------------------ cupom
def aplicar_cupom(db: Session, codigo: str, subtotal: Decimal):
    """RF34 / RF35 / RN02: valida o cupom e devolve (cupom, desconto)."""
    codigo = codigo.strip().upper()
    cupom = db.scalar(select(Cupom).where(func.upper(Cupom.codigo) == codigo))
    if cupom is None:
        raise HTTPException(404, "Cupom não encontrado.")
    if not cupom.ativo:
        raise HTTPException(400, "Cupom inativo.")
    momento = agora()
    if momento < cupom.data_inicio or momento > cupom.data_fim:
        raise HTTPException(400, "Cupom fora do período de validade.")
    if cupom.valor_minimo_pedido is not None and subtotal < cupom.valor_minimo_pedido:
        raise HTTPException(
            400,
            f"Pedido mínimo para este cupom: R$ {cupom.valor_minimo_pedido:.2f}.",
        )
    if cupom.percentual_desconto is not None:
        desconto = money(subtotal * cupom.percentual_desconto / Decimal(100))
    elif cupom.valor_desconto is not None:
        desconto = money(cupom.valor_desconto)
    else:
        desconto = Decimal("0.00")
    return cupom, min(desconto, subtotal)  # o desconto nunca passa do subtotal


# ------------------------------------------------------------------ cálculo
def calcular_pedido(db: Session, dados, bloquear: bool = False) -> Calculo:
    """Calcula tudo com os preços do banco. Com bloquear=True, trava as linhas
    dos produtos até o commit (evita vender o mesmo estoque duas vezes)."""
    estab = db.get(Estabelecimento, dados.id_estabelecimento)
    if estab is None or estab.status != ESTABELECIMENTO_ATIVO:
        raise HTTPException(404, "Estabelecimento não encontrado ou inativo.")

    # Junta itens repetidos (mesmo produto duas vezes no carrinho) somando as quantidades.
    quantidades: dict[int, int] = {}
    for item in dados.itens:
        quantidades[item.id_produto] = quantidades.get(item.id_produto, 0) + item.quantidade

    consulta = (
        select(Produto)
        .where(Produto.id_produto.in_(list(quantidades)))
        .order_by(Produto.id_produto)
    )
    if bloquear:
        consulta = consulta.with_for_update()
    encontrados = {p.id_produto: p for p in db.scalars(consulta)}

    linhas = []
    subtotal = Decimal("0.00")
    for id_produto, qtd in sorted(quantidades.items()):
        produto = encontrados.get(id_produto)
        if produto is None or produto.id_estabelecimento != estab.id_estabelecimento:
            raise HTTPException(
                400, f"Produto {id_produto} não pertence a este estabelecimento."
            )
        if not produto.ativo:
            raise HTTPException(400, f"Produto '{produto.nome}' está indisponível.")
        if produto.estoque < qtd:
            raise HTTPException(
                400,
                f"Estoque insuficiente para '{produto.nome}': "
                f"disponível {produto.estoque}, solicitado {qtd}.",
            )
        linhas.append((produto, qtd))
        subtotal += money(produto.preco * qtd)

    subtotal = money(subtotal)
    taxa = money(config.TAXA_ENTREGA)
    cupom, desconto = None, Decimal("0.00")
    if dados.codigo_cupom:
        cupom, desconto = aplicar_cupom(db, dados.codigo_cupom, subtotal)
    total = money(subtotal + taxa - desconto)
    return Calculo(estab, linhas, cupom, subtotal, taxa, desconto, total)


def criar_pedido(db: Session, cliente: Cliente, dados) -> Pedido:
    endereco = db.get(Endereco, dados.id_endereco)
    if endereco is None or endereco.id_cliente != cliente.id_cliente:
        raise HTTPException(404, "Endereço não encontrado para este cliente.")

    calculo = calcular_pedido(db, dados, bloquear=True)

    pedido = Pedido(
        data_hora=agora(),
        status=PEDIDO_CRIADO,
        valor_subtotal=calculo.subtotal,
        taxa_entrega=calculo.taxa,
        valor_total=calculo.total,
        observacao=dados.observacao,
        id_cliente=cliente.id_cliente,
        id_estabelecimento=calculo.estabelecimento.id_estabelecimento,
        id_endereco=endereco.id_endereco,
        id_cupom=calculo.cupom.id_cupom if calculo.cupom else None,
    )
    for produto, qtd in calculo.linhas:
        pedido.itens.append(
            ItemPedido(
                id_produto=produto.id_produto,
                quantidade=qtd,
                preco_unitario=produto.preco,  # preço no momento da compra
                subtotal=money(produto.preco * qtd),
            )
        )
        produto.estoque -= qtd  # baixa o estoque
    # Pagamento só é REGISTRADO (nada é cobrado de verdade).
    pedido.pagamento = Pagamento(
        forma_pagamento=dados.forma_pagamento,
        status_pagamento=PAGAMENTO_PENDENTE,
        valor=calculo.total,
    )
    db.add(pedido)
    db.commit()
    return pedido


# ------------------------------------------------------------------ status (estabelecimento)
def atualizar_status_pelo_estabelecimento(db: Session, pedido: Pedido, novo_status: str) -> Pedido:
    checar_transicao(TRANSICOES_PEDIDO_ESTABELECIMENTO, pedido.status, novo_status, "pedido")
    # RN04: o pagamento deve estar confirmado antes de o pedido ser confirmado/produzido
    if novo_status == PEDIDO_CONFIRMADO:
        pagamento = pedido.pagamento
        if pagamento is None:
            raise HTTPException(409, "Pedido sem pagamento registrado.")
        if (
            pagamento.forma_pagamento != FORMA_SEM_APROVACAO_PREVIA
            and pagamento.status_pagamento != PAGAMENTO_APROVADO
        ):
            raise HTTPException(
                409,
                "Confirme o pagamento antes de confirmar o pedido "
                "(somente DINHEIRO dispensa a aprovação prévia).",
            )
    pedido.status = novo_status
    db.commit()
    return pedido


def confirmar_pagamento(db: Session, pedido: Pedido) -> Pedido:
    """RF13: o estabelecimento confirma o pagamento do pedido."""
    pagamento = pedido.pagamento
    if pagamento is None:
        raise HTTPException(409, "Pedido sem pagamento registrado.")
    if pedido.status != PEDIDO_CRIADO:
        raise HTTPException(
            409, f"O pagamento só pode ser confirmado com o pedido {PEDIDO_CRIADO}."
        )
    if pagamento.status_pagamento != PAGAMENTO_PENDENTE:
        raise HTTPException(409, f"Pagamento já está {pagamento.status_pagamento}.")
    pagamento.status_pagamento = PAGAMENTO_APROVADO
    db.commit()
    return pedido


# ------------------------------------------------------------------ montagem das respostas
def endereco_para_dict(e: Endereco) -> dict:
    return {
        "id_endereco": e.id_endereco,
        "logradouro": e.logradouro,
        "numero": e.numero,
        "complemento": e.complemento,
        "bairro": e.bairro,
        "cidade": e.cidade,
        "estado": e.estado,
        "cep": e.cep,
        "tipo": e.tipo,
        "id_cliente": e.id_cliente,
    }


def _itens_para_dict(itens) -> list[dict]:
    return [
        {
            "id_produto": i.id_produto,
            "produto": i.produto.nome,
            "quantidade": i.quantidade,
            "preco_unitario": i.preco_unitario,
            "subtotal": i.subtotal,
        }
        for i in itens
    ]


def pedido_para_dict(p: Pedido) -> dict:
    pag, ent = p.pagamento, p.entrega
    return {
        "id_pedido": p.id_pedido,
        "data_hora": p.data_hora,
        "status": p.status,
        "cliente": p.cliente.usuario.nome,
        "id_estabelecimento": p.id_estabelecimento,
        "estabelecimento": p.estabelecimento.nome_fantasia,
        "endereco_entrega": endereco_para_dict(p.endereco),
        "id_cupom": p.id_cupom,
        "codigo_cupom": p.cupom.codigo if p.cupom else None,
        "valor_subtotal": p.valor_subtotal,
        "taxa_entrega": p.taxa_entrega,
        # o banco não tem coluna de desconto: é derivado de subtotal + taxa - total
        "desconto": money(p.valor_subtotal + p.taxa_entrega - p.valor_total),
        "valor_total": p.valor_total,
        "observacao": p.observacao,
        "itens": _itens_para_dict(p.itens),
        "pagamento": (
            {
                "id_pagamento": pag.id_pagamento,
                "forma_pagamento": pag.forma_pagamento,
                "status_pagamento": pag.status_pagamento,
                "valor": pag.valor,
            }
            if pag
            else None
        ),
        "entrega": (
            {
                "id_entrega": ent.id_entrega,
                "status": ent.status,
                "data_solicitacao": ent.data_solicitacao,
                "data_retirada": ent.data_retirada,
                "data_entrega": ent.data_entrega,
                "id_entregador": ent.id_entregador,
            }
            if ent
            else None
        ),
    }


def calculo_para_dict(c: Calculo) -> dict:
    return {
        "estabelecimento": c.estabelecimento.nome_fantasia,
        "itens": [
            {
                "id_produto": p.id_produto,
                "produto": p.nome,
                "quantidade": qtd,
                "preco_unitario": p.preco,
                "subtotal": money(p.preco * qtd),
            }
            for p, qtd in c.linhas
        ],
        "codigo_cupom": c.cupom.codigo if c.cupom else None,
        "valor_subtotal": c.subtotal,
        "taxa_entrega": c.taxa,
        "desconto": c.desconto,
        "valor_total": c.total,
    }
