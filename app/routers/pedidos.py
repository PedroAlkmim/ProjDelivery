"""Pedidos do cliente: simular, finalizar, consultar e solicitar cancelamento."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_cliente_atual
from app.models import Cliente, Pedido
from app.schemas.pedido import (
    CancelamentoIn,
    PedidoIn,
    PedidoOut,
    SimulacaoIn,
    SimulacaoOut,
    SolicitacaoOut,
)
from app.services.cancelamentos import solicitar_cancelamento
from app.services.pedidos import (
    calcular_pedido,
    calculo_para_dict,
    criar_pedido,
    pedido_para_dict,
)

router = APIRouter(prefix="/pedidos", tags=["Cliente - Pedidos"])


@router.post("/simular", response_model=SimulacaoOut, summary="Simular valores do pedido")
def simular(
    dados: SimulacaoIn,
    cliente: Cliente = Depends(get_cliente_atual),
    db: Session = Depends(get_db),
):
    """RF32 / RF34: mostra subtotal, taxa de entrega, desconto do cupom e total,
    sem gravar nada. Os valores são calculados com os preços do banco."""
    return calculo_para_dict(calcular_pedido(db, dados))


@router.post("", response_model=PedidoOut, status_code=201, summary="Finalizar pedido")
def finalizar_pedido(
    dados: PedidoIn,
    cliente: Cliente = Depends(get_cliente_atual),
    db: Session = Depends(get_db),
):
    """RF30 / RF31 / RF33: o carrinho vai no corpo da requisição (lista `itens`).
    O backend valida estoque, calcula os valores, baixa o estoque e registra o
    pagamento como PENDENTE (nenhuma cobrança real é feita)."""
    return pedido_para_dict(criar_pedido(db, cliente, dados))


@router.get("", response_model=list[PedidoOut], summary="Meus pedidos")
def listar_pedidos(
    status: str | None = None,
    cliente: Cliente = Depends(get_cliente_atual),
    db: Session = Depends(get_db),
):
    """RF36 / RF39: histórico dos pedidos do cliente logado (filtro opcional por status)."""
    consulta = select(Pedido).where(Pedido.id_cliente == cliente.id_cliente)
    if status:
        consulta = consulta.where(Pedido.status == status.strip().upper())
    pedidos = db.scalars(consulta.order_by(Pedido.id_pedido.desc())).all()
    return [pedido_para_dict(p) for p in pedidos]


@router.get("/{id_pedido}", response_model=PedidoOut, summary="Acompanhar um pedido")
def obter_pedido(
    id_pedido: int,
    cliente: Cliente = Depends(get_cliente_atual),
    db: Session = Depends(get_db),
):
    pedido = db.get(Pedido, id_pedido)
    if pedido is None or pedido.id_cliente != cliente.id_cliente:
        raise HTTPException(404, "Pedido não encontrado.")
    return pedido_para_dict(pedido)


@router.post(
    "/{id_pedido}/cancelamento",
    response_model=SolicitacaoOut,
    status_code=201,
    summary="Solicitar cancelamento",
)
def pedir_cancelamento(
    id_pedido: int,
    dados: CancelamentoIn,
    cliente: Cliente = Depends(get_cliente_atual),
    db: Session = Depends(get_db),
):
    """RF37 / RN08: registra motivo, data/hora e o cliente solicitante.
    Quem decide (aprova ou recusa) é o administrador."""
    return solicitar_cancelamento(db, cliente, id_pedido, dados.motivo)
