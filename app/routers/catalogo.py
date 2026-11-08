"""Consulta de estabelecimentos, cardápio e avaliações (RF28, RF29). Exige login."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants import ESTABELECIMENTO_ATIVO
from app.database import get_db
from app.deps import get_sessao
from app.models import Avaliacao, Estabelecimento, Produto
from app.schemas.catalogo import EstabelecimentoOut, ProdutoOut
from app.schemas.cliente import AvaliacaoOut

router = APIRouter(
    prefix="/estabelecimentos",
    tags=["Catálogo"],
    dependencies=[Depends(get_sessao)],  # qualquer usuário logado
)


@router.get("", response_model=list[EstabelecimentoOut], summary="Buscar estabelecimentos")
def buscar_estabelecimentos(
    nome: str | None = None,
    categoria: str | None = None,
    db: Session = Depends(get_db),
):
    """RF28: busca por nome (nome fantasia) ou categoria; só estabelecimentos ativos."""
    consulta = select(Estabelecimento).where(
        Estabelecimento.status == ESTABELECIMENTO_ATIVO
    )
    if nome:
        consulta = consulta.where(Estabelecimento.nome_fantasia.ilike(f"%{nome.strip()}%"))
    if categoria:
        consulta = consulta.where(Estabelecimento.categoria.ilike(f"%{categoria.strip()}%"))
    return db.scalars(consulta.order_by(Estabelecimento.nome_fantasia)).all()


def _estabelecimento_ativo(db: Session, id_estabelecimento: int) -> Estabelecimento:
    estab = db.get(Estabelecimento, id_estabelecimento)
    if estab is None or estab.status != ESTABELECIMENTO_ATIVO:
        raise HTTPException(404, "Estabelecimento não encontrado.")
    return estab


@router.get(
    "/{id_estabelecimento}/produtos",
    response_model=list[ProdutoOut],
    summary="Ver cardápio",
)
def cardapio(id_estabelecimento: int, db: Session = Depends(get_db)):
    """RF29: produtos ativos do estabelecimento, com preço, estoque e imagem."""
    _estabelecimento_ativo(db, id_estabelecimento)
    return db.scalars(
        select(Produto)
        .where(Produto.id_estabelecimento == id_estabelecimento, Produto.ativo.is_(True))
        .order_by(Produto.nome)
    ).all()


@router.get(
    "/{id_estabelecimento}/avaliacoes",
    response_model=list[AvaliacaoOut],
    summary="Ver avaliações do estabelecimento",
)
def avaliacoes(id_estabelecimento: int, db: Session = Depends(get_db)):
    _estabelecimento_ativo(db, id_estabelecimento)
    return db.scalars(
        select(Avaliacao)
        .where(Avaliacao.id_estabelecimento == id_estabelecimento)
        .order_by(Avaliacao.id_avaliacao.desc())
    ).all()
