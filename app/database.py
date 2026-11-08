"""Conexão com o PostgreSQL (SQLAlchemy). O banco já existe; nada é criado aqui."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """Abre uma sessão por requisição e garante o fechamento (rollback se houve erro)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
