"""Configurações lidas do arquivo .env (ou das variáveis de ambiente)."""
import os
from decimal import Decimal

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/delivery",
)
SECRET_KEY = os.getenv("SECRET_KEY", "chave-de-desenvolvimento-troque-depois")
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = int(os.getenv("TOKEN_EXPIRE_MINUTES", "120"))

# Taxa de entrega fixa (o banco não tem taxa por estabelecimento).
TAXA_ENTREGA = Decimal(os.getenv("TAXA_ENTREGA", "5.00"))
