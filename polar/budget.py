"""Contrato Python do indicador de budget anual.

O SQL calcula o realizado. Este módulo valida o formato, preserva precisão
decimal e acrescenta o budget fixo usado na apresentação.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from httpx import HTTPError
from postgrest.exceptions import APIError

from polar.adiantamento import (
    DataAccessError,
    PermissionDenied,
    data_api_rejection_message,
)

# Decimal evita que arredondamentos binários alterem o percentual exibido.
ANNUAL_BUDGET = Decimal("119000000")
LOAD_FUNCTION = "campanha_polar_carregar_budget_anual"


class BudgetRepository:
    """Carrega o realizado elegível de 2026 pela Data API autenticada."""

    def __init__(self, client: Any):
        self.client = client

    def load(self) -> dict:
        try:
            data = self.client.rpc(LOAD_FUNCTION, {}).execute().data
        except APIError as error:
            error_text = " ".join((
                str(getattr(error, "code", "") or ""),
                str(getattr(error, "message", "") or ""),
                str(error),
            )).upper()
            if "AUTH_REQUIRED" in error_text or "42501" in error_text:
                raise PermissionDenied("Faça login novamente para consultar o budget anual.") from error
            raise DataAccessError(
                data_api_rejection_message(error, "a consulta do budget anual")
            ) from error
        except HTTPError as error:
            raise DataAccessError("Não foi possível consultar o budget anual.") from error

        # A RPC deve sempre produzir exatamente uma linha, inclusive quando o
        # realizado é zero. Qualquer outro formato indica contrato incompatível.
        if not isinstance(data, list) or len(data) != 1 or not isinstance(data[0], dict):
            raise DataAccessError("A consulta do budget anual devolveu um formato inesperado.")
        item = data[0]
        if not {"data_referencia", "realizado"}.issubset(item):
            raise DataAccessError(
                "A função do budget anual está desatualizada. Execute novamente "
                "sql/budget_anual.sql no Supabase."
            )
        try:
            realized = Decimal(str(item.get("realizado") or 0))
        except (InvalidOperation, ValueError) as error:
            raise DataAccessError("A consulta do budget anual devolveu um valor inválido.") from error
        return {
            "data_referencia": str(item.get("data_referencia") or ""),
            "realizado": realized,
            "budget": ANNUAL_BUDGET,
            "atingimento_pct": realized * Decimal("100") / ANNUAL_BUDGET,
        }
