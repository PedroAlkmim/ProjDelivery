"""Painel do entregador: só acessa as entregas atribuídas a ele."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants import ENTREGA_SOLICITADA
from app.database import get_db
from app.deps import get_entregador_atual
from app.models import Entrega, Entregador
from app.schemas.entregador import (
    DisponibilidadeIn,
    DisponibilidadeOut,
    EntregaDisponivelOut,
    EntregaOut,
    EntregaStatusIn,
)
from app.services.entregas import (
    aceitar_entrega,
    atualizar_status_entrega,
    entrega_disponivel_para_dict,
    entrega_para_dict,
)

router = APIRouter(prefix="/entregador", tags=["Entregador"])


@router.get("/entregas", response_model=list[EntregaOut], summary="Minhas entregas")
def minhas_entregas(
    status: str | None = None,
    entregador: Entregador = Depends(get_entregador_atual),
    db: Session = Depends(get_db),
):
    """RF22 / RF23: entregas atribuídas ao entregador logado, inclusive o histórico
    (filtro opcional por status: AGUARDANDO_RETIRADA, EM_ROTA, ENTREGUE, DEVOLVIDA, CANCELADA)."""
    consulta = select(Entrega).where(Entrega.id_entregador == entregador.id_entregador)
    if status:
        consulta = consulta.where(Entrega.status == status.strip().upper())
    entregas = db.scalars(consulta.order_by(Entrega.id_entrega.desc())).all()
    return [entrega_para_dict(e) for e in entregas]


@router.get(
    "/entregas/disponiveis",
    response_model=list[EntregaDisponivelOut],
    summary="Solicitações de entrega em aberto",
)
def entregas_disponiveis(
    entregador: Entregador = Depends(get_entregador_atual),
    db: Session = Depends(get_db),
):
    """RF19: solicitações ainda sem entregador. Só mostra o necessário para decidir
    (nome do estabelecimento e bairro/cidade de destino). Só aparecem se você estiver disponível."""
    if not entregador.disponibilidade:
        return []
    entregas = db.scalars(
        select(Entrega)
        .where(Entrega.status == ENTREGA_SOLICITADA, Entrega.id_entregador.is_(None))
        .order_by(Entrega.id_entrega)
    ).all()
    return [entrega_disponivel_para_dict(e) for e in entregas]


@router.post(
    "/entregas/{id_entrega}/aceitar",
    response_model=EntregaOut,
    summary="Aceitar entrega",
)
def aceitar(
    id_entrega: int,
    entregador: Entregador = Depends(get_entregador_atual),
    db: Session = Depends(get_db),
):
    """Atribui a entrega a você e muda o status para AGUARDANDO_RETIRADA."""
    return entrega_para_dict(aceitar_entrega(db, entregador, id_entrega))


@router.patch(
    "/entregas/{id_entrega}/status",
    response_model=EntregaOut,
    summary="Atualizar status da entrega",
)
def atualizar_status(
    id_entrega: int,
    dados: EntregaStatusIn,
    entregador: Entregador = Depends(get_entregador_atual),
    db: Session = Depends(get_db),
):
    """RF20 / RF21. Sequência: `AGUARDANDO_RETIRADA → EM_ROTA → ENTREGUE` (ou `DEVOLVIDA`
    se o cliente estiver ausente). O status do pedido acompanha automaticamente
    (EM_ROTA, CONCLUIDO ou DEVOLVIDO)."""
    entrega = atualizar_status_entrega(db, entregador, id_entrega, dados.status)
    return entrega_para_dict(entrega)


@router.patch(
    "/disponibilidade",
    response_model=DisponibilidadeOut,
    summary="Informar disponibilidade",
)
def alterar_disponibilidade(
    dados: DisponibilidadeIn,
    entregador: Entregador = Depends(get_entregador_atual),
    db: Session = Depends(get_db),
):
    """RF18: informa se está disponível para receber entregas."""
    entregador.disponibilidade = dados.disponibilidade
    db.commit()
    return {
        "id_entregador": entregador.id_entregador,
        "disponibilidade": entregador.disponibilidade,
    }
