"""Painel do administrador (RF01–RF05, RF07, RF10, RF16, RF17)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.constants import (
    ENTREGADOR_PENDENTE,
    ESTABELECIMENTO_ATIVO,
)
from app.database import get_db
from app.deps import get_admin_atual
from app.models import (
    Administrador,
    Cliente,
    Cupom,
    Entrega,
    Entregador,
    Estabelecimento,
    Pedido,
    SolicitacaoCancelamento,
    Usuario,
)
from app.schemas.admin import (
    AnaliseCancelamentoIn,
    AprovacaoIn,
    CupomIn,
    CupomOut,
    CupomUpdate,
    EntregadorAdminOut,
    EntregadorCreate,
    EstabelecimentoAdminOut,
    EstabelecimentoCreate,
    RelatorioEntregasEntregadorOut,
    RelatorioPedidosStatusOut,
    UsuarioAdminOut,
    UsuarioStatusIn,
)
from app.schemas.entregador import EntregaOut
from app.schemas.pedido import PedidoOut, SolicitacaoOut
from app.services.auth import descobrir_perfil
from app.services.cancelamentos import analisar_cancelamento
from app.services.entregas import entrega_para_dict
from app.services.pedidos import pedido_para_dict
from app.services.usuarios import criar_usuario

# Todas as rotas deste arquivo exigem o perfil ADMINISTRADOR.
router = APIRouter(
    prefix="/admin",
    tags=["Administrador"],
    dependencies=[Depends(get_admin_atual)],
)


# ------------------------------------------------------------------ cadastros (RF01, RF02)
@router.post(
    "/estabelecimentos",
    response_model=EstabelecimentoAdminOut,
    status_code=201,
    summary="Cadastrar estabelecimento",
)
def cadastrar_estabelecimento(dados: EstabelecimentoCreate, db: Session = Depends(get_db)):
    if db.scalar(select(Estabelecimento.id_estabelecimento).where(Estabelecimento.cnpj == dados.cnpj)):
        raise HTTPException(409, "CNPJ já cadastrado.")
    usuario = criar_usuario(db, dados.nome, dados.email, dados.senha, dados.telefone)
    estab = Estabelecimento(
        id_usuario=usuario.id,
        nome_fantasia=dados.nome_fantasia,
        cnpj=dados.cnpj,
        categoria=dados.categoria,
        status=ESTABELECIMENTO_ATIVO,
    )
    db.add(estab)
    db.commit()
    return {
        "id_estabelecimento": estab.id_estabelecimento,
        "id_usuario": usuario.id,
        "email": usuario.email,
        "nome_fantasia": estab.nome_fantasia,
        "cnpj": estab.cnpj,
        "categoria": estab.categoria,
        "status": estab.status,
    }


@router.post(
    "/entregadores",
    response_model=EntregadorAdminOut,
    status_code=201,
    summary="Cadastrar entregador",
)
def cadastrar_entregador(dados: EntregadorCreate, db: Session = Depends(get_db)):
    """O entregador nasce com aprovação PENDENTE e indisponível; só acessa o sistema
    depois de aprovado (RF17)."""
    usuario = criar_usuario(db, dados.nome, dados.email, dados.senha, dados.telefone)
    entregador = Entregador(
        id_usuario=usuario.id,
        disponibilidade=False,
        status_aprovacao=ENTREGADOR_PENDENTE,
    )
    db.add(entregador)
    db.commit()
    return {
        "id_entregador": entregador.id_entregador,
        "id_usuario": usuario.id,
        "nome": usuario.nome,
        "email": usuario.email,
        "disponibilidade": entregador.disponibilidade,
        "status_aprovacao": entregador.status_aprovacao,
    }


@router.patch(
    "/entregadores/{id_entregador}/aprovacao",
    response_model=EntregadorAdminOut,
    summary="Aprovar ou reprovar entregador",
)
def aprovar_entregador(
    id_entregador: int, dados: AprovacaoIn, db: Session = Depends(get_db)
):
    entregador = db.get(Entregador, id_entregador)
    if entregador is None:
        raise HTTPException(404, "Entregador não encontrado.")
    entregador.status_aprovacao = dados.status_aprovacao
    db.commit()
    return {
        "id_entregador": entregador.id_entregador,
        "id_usuario": entregador.id_usuario,
        "nome": entregador.usuario.nome,
        "email": entregador.usuario.email,
        "disponibilidade": entregador.disponibilidade,
        "status_aprovacao": entregador.status_aprovacao,
    }


# ------------------------------------------------------------------ usuários (RF01–RF03, RF08)
@router.get("/usuarios", response_model=list[UsuarioAdminOut], summary="Listar usuários")
def listar_usuarios(
    perfil: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    """Filtros opcionais: `perfil` (ADMINISTRADOR, CLIENTE, ENTREGADOR, ESTABELECIMENTO)
    e `status` (ATIVO, INATIVO, BLOQUEADO)."""
    consulta = (
        select(
            Usuario,
            Administrador.id_administrador,
            Cliente.id_cliente,
            Entregador.id_entregador,
            Estabelecimento.id_estabelecimento,
        )
        .outerjoin(Administrador, Administrador.id_usuario == Usuario.id)
        .outerjoin(Cliente, Cliente.id_usuario == Usuario.id)
        .outerjoin(Entregador, Entregador.id_usuario == Usuario.id)
        .outerjoin(Estabelecimento, Estabelecimento.id_usuario == Usuario.id)
        .order_by(Usuario.id)
    )
    if status:
        consulta = consulta.where(Usuario.status == status.strip().upper())

    resultado = []
    for u, adm, cli, ent, est in db.execute(consulta):
        if adm is not None:
            nome_perfil = "ADMINISTRADOR"
        elif cli is not None:
            nome_perfil = "CLIENTE"
        elif ent is not None:
            nome_perfil = "ENTREGADOR"
        elif est is not None:
            nome_perfil = "ESTABELECIMENTO"
        else:
            nome_perfil = "SEM_PERFIL"
        if perfil and nome_perfil != perfil.strip().upper():
            continue
        resultado.append(
            {
                "id": u.id,
                "nome": u.nome,
                "email": u.email,
                "telefone": u.telefone,
                "status": u.status,
                "perfil": nome_perfil,
            }
        )
    return resultado


@router.patch(
    "/usuarios/{id_usuario}/status",
    response_model=UsuarioAdminOut,
    summary="Ativar, inativar ou bloquear usuário",
)
def alterar_status_usuario(
    id_usuario: int,
    dados: UsuarioStatusIn,
    admin: Administrador = Depends(get_admin_atual),
    db: Session = Depends(get_db),
):
    """RF08: controle de acesso. Usuários inativos ou bloqueados não conseguem logar."""
    if id_usuario == admin.id_usuario:
        raise HTTPException(400, "Você não pode alterar o status do seu próprio usuário.")
    usuario = db.get(Usuario, id_usuario)
    if usuario is None:
        raise HTTPException(404, "Usuário não encontrado.")
    usuario.status = dados.status
    db.commit()
    return usuario_para_dict(db, usuario)


def usuario_para_dict(db: Session, usuario: Usuario) -> dict:
    perfil = descobrir_perfil(db, usuario)
    return {
        "id": usuario.id,
        "nome": usuario.nome,
        "email": usuario.email,
        "telefone": usuario.telefone,
        "status": usuario.status,
        "perfil": perfil[0] if perfil else "SEM_PERFIL",
    }


# ------------------------------------------------------------------ pedidos e entregas (RF04, RF16)
@router.get("/pedidos", response_model=list[PedidoOut], summary="Acompanhar pedidos")
def listar_pedidos(status: str | None = None, db: Session = Depends(get_db)):
    consulta = select(Pedido)
    if status:
        consulta = consulta.where(Pedido.status == status.strip().upper())
    pedidos = db.scalars(consulta.order_by(Pedido.id_pedido.desc())).all()
    return [pedido_para_dict(p) for p in pedidos]


@router.get("/entregas", response_model=list[EntregaOut], summary="Acompanhar entregas")
def listar_entregas(
    status: str | None = None,
    id_entregador: int | None = None,
    db: Session = Depends(get_db),
):
    consulta = select(Entrega)
    if status:
        consulta = consulta.where(Entrega.status == status.strip().upper())
    if id_entregador is not None:
        consulta = consulta.where(Entrega.id_entregador == id_entregador)
    entregas = db.scalars(consulta.order_by(Entrega.id_entrega.desc())).all()
    return [entrega_para_dict(e) for e in entregas]


# ------------------------------------------------------------------ cancelamentos (RF05)
@router.get(
    "/cancelamentos",
    response_model=list[SolicitacaoOut],
    summary="Listar solicitações de cancelamento",
)
def listar_cancelamentos(status: str | None = None, db: Session = Depends(get_db)):
    consulta = select(SolicitacaoCancelamento)
    if status:
        consulta = consulta.where(SolicitacaoCancelamento.status == status.strip().upper())
    return db.scalars(consulta.order_by(SolicitacaoCancelamento.id_solicitacao.desc())).all()


@router.patch(
    "/cancelamentos/{id_solicitacao}",
    response_model=SolicitacaoOut,
    summary="Analisar solicitação de cancelamento",
)
def analisar(
    id_solicitacao: int,
    dados: AnaliseCancelamentoIn,
    admin: Administrador = Depends(get_admin_atual),
    db: Session = Depends(get_db),
):
    """Decisões: `EM_ANALISE` (marca como em análise), `APROVADA` ou `RECUSADA`.
    Ao **aprovar**: o pedido vira CANCELADO, o estoque é devolvido, o pagamento é
    estornado (ou cancelado, se ainda estava pendente) e a entrega aberta é cancelada.
    O administrador responsável fica registrado na solicitação (RN08)."""
    return analisar_cancelamento(db, admin, id_solicitacao, dados.decisao, dados.observacao)


# ------------------------------------------------------------------ cupons (RF10)
@router.post("/cupons", response_model=CupomOut, status_code=201, summary="Cadastrar cupom")
def cadastrar_cupom(dados: CupomIn, db: Session = Depends(get_db)):
    codigo = dados.codigo.upper()
    if db.scalar(select(Cupom.id_cupom).where(func.upper(Cupom.codigo) == codigo)):
        raise HTTPException(409, "Já existe um cupom com este código.")
    campos = dados.model_dump()
    campos["codigo"] = codigo
    cupom = Cupom(**campos)
    db.add(cupom)
    db.commit()
    return cupom


@router.get("/cupons", response_model=list[CupomOut], summary="Listar cupons")
def listar_cupons(ativo: bool | None = None, db: Session = Depends(get_db)):
    consulta = select(Cupom)
    if ativo is not None:
        consulta = consulta.where(Cupom.ativo.is_(ativo))
    return db.scalars(consulta.order_by(Cupom.id_cupom)).all()


@router.patch("/cupons/{id_cupom}", response_model=CupomOut, summary="Ativar/desativar cupom")
def atualizar_cupom(id_cupom: int, dados: CupomUpdate, db: Session = Depends(get_db)):
    cupom = db.get(Cupom, id_cupom)
    if cupom is None:
        raise HTTPException(404, "Cupom não encontrado.")
    campos = dados.model_dump(exclude_unset=True)
    if "ativo" in campos and campos["ativo"] is None:
        raise HTTPException(422, "O campo 'ativo' não pode ser nulo.")
    if campos.get("data_fim", ...) is None:
        raise HTTPException(422, "O campo 'data_fim' não pode ser nulo.")
    if "data_fim" in campos and campos["data_fim"] < cupom.data_inicio:
        raise HTTPException(422, "data_fim deve ser maior ou igual a data_inicio.")
    for campo, valor in campos.items():
        setattr(cupom, campo, valor)
    db.commit()
    return cupom


# ------------------------------------------------------------------ relatórios (RF07, RF16)
@router.get(
    "/relatorios/pedidos-por-status",
    response_model=list[RelatorioPedidosStatusOut],
    summary="Relatório: pedidos por status",
)
def relatorio_pedidos_por_status(db: Session = Depends(get_db)):
    linhas = db.execute(
        select(
            Pedido.status,
            func.count(Pedido.id_pedido),
            func.coalesce(func.sum(Pedido.valor_total), 0),
        )
        .group_by(Pedido.status)
        .order_by(Pedido.status)
    )
    return [
        {"status": status, "quantidade": qtd, "valor_total": total}
        for status, qtd, total in linhas
    ]


@router.get(
    "/relatorios/entregas-por-entregador",
    response_model=list[RelatorioEntregasEntregadorOut],
    summary="Relatório: entregas por entregador e status",
)
def relatorio_entregas_por_entregador(db: Session = Depends(get_db)):
    linhas = db.execute(
        select(
            Entregador.id_entregador,
            Usuario.nome,
            Entrega.status,
            func.count(Entrega.id_entrega),
        )
        .select_from(Entrega)
        .outerjoin(Entregador, Entregador.id_entregador == Entrega.id_entregador)
        .outerjoin(Usuario, Usuario.id == Entregador.id_usuario)
        .group_by(Entregador.id_entregador, Usuario.nome, Entrega.status)
        .order_by(Usuario.nome, Entrega.status)
    )
    return [
        {
            "id_entregador": id_ent,
            "entregador": nome or "Sem entregador",
            "status": status,
            "quantidade": qtd,
        }
        for id_ent, nome, status, qtd in linhas
    ]
