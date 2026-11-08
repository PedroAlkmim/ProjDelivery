from app.schemas.comum import Dinheiro, Saida


class EstabelecimentoOut(Saida):
    id_estabelecimento: int
    nome_fantasia: str
    categoria: str
    status: str


class ProdutoOut(Saida):
    id_produto: int
    nome: str
    descricao: str | None
    preco: Dinheiro
    estoque: int
    imagem: str | None
    ativo: bool
    id_estabelecimento: int
