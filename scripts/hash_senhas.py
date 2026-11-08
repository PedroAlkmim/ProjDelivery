"""Converte as senhas em texto puro da tabela `usuario` para hash bcrypt.

Altera somente DADOS (coluna senha); a estrutura do banco não é tocada.
É seguro rodar mais de uma vez: senhas que já são hash são ignoradas.

Execute na pasta do projeto:   python -m scripts.hash_senhas
"""
from sqlalchemy import select

from app.database import SessionLocal
from app.models import Usuario
from app.security import gerar_hash


def main() -> None:
    convertidas = 0
    with SessionLocal() as db:
        for usuario in db.scalars(select(Usuario)):
            if usuario.senha.startswith("$2"):  # já é hash bcrypt
                continue
            usuario.senha = gerar_hash(usuario.senha)
            convertidas += 1
        db.commit()
    print(f"Senhas convertidas para hash: {convertidas}")


if __name__ == "__main__":
    main()
