"""Funções de apoio e regras simples reutilizadas pelos serviços."""
import re
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from fastapi import HTTPException

CENTAVOS = Decimal("0.01")


def agora() -> datetime:
    """Data/hora atual (sem fuso, igual à coluna TIMESTAMP do banco)."""
    return datetime.now()


def money(valor) -> Decimal:
    """Arredonda para 2 casas decimais (centavos)."""
    return Decimal(valor).quantize(CENTAVOS, rounding=ROUND_HALF_UP)


def normalizar_cep(cep: str) -> str | None:
    digitos = re.sub(r"\D", "", cep or "")
    if len(digitos) != 8:
        return None
    return f"{digitos[:5]}-{digitos[5:]}"


def normalizar_cnpj(cnpj: str) -> str | None:
    digitos = re.sub(r"\D", "", cnpj or "")
    if len(digitos) != 14:
        return None
    return f"{digitos[:2]}.{digitos[2:5]}.{digitos[5:8]}/{digitos[8:12]}-{digitos[12:]}"


def checar_transicao(mapa: dict, atual: str, novo: str, entidade: str) -> None:
    """RN07: impede avançar para um status incompatível."""
    permitidos = mapa.get(atual, set())
    if novo not in permitidos:
        lista = ", ".join(sorted(permitidos)) if permitidos else "nenhuma"
        raise HTTPException(
            409,
            f"Transição inválida para {entidade}: {atual} -> {novo}. "
            f"Permitidas a partir de {atual}: {lista}.",
        )


def validar_endereco(endereco) -> None:
    """RF14 / RN03: valida o endereço antes de solicitar o entregador."""
    obrigatorios = ("logradouro", "numero", "bairro", "cidade")
    faltando = [c for c in obrigatorios if not (getattr(endereco, c) or "").strip()]
    if faltando:
        raise HTTPException(
            422,
            "Endereço de entrega inválido: campos obrigatórios ausentes "
            f"({', '.join(faltando)}).",
        )
    if len((endereco.estado or "").strip()) != 2:
        raise HTTPException(422, "Endereço de entrega inválido: estado deve ter 2 letras (UF).")
    if not re.fullmatch(r"\d{5}-?\d{3}", (endereco.cep or "").strip()):
        raise HTTPException(422, "Endereço de entrega inválido: CEP deve ter 8 dígitos.")
