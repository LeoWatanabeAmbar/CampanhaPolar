"""Consulta de clientes novos pela Data API do Supabase."""
from __future__ import annotations

from datetime import date
from typing import Any

from httpx import HTTPError
from postgrest.exceptions import APIError

from polar.adiantamento import (
    DataAccessError,
    PermissionDenied,
    data_api_rejection_message,
    validate_month,
)

LOAD_FUNCTION = "campanha_polar_carregar_clientes_novos"


class NewCustomersRepository:
    """Carrega os primeiros eventos de compra encontrados desde 2022."""

    def __init__(self, client: Any):
        self.client = client

    def load(self, month: date | None = None) -> list[dict]:
        if month is not None:
            validate_month(month)
        try:
            data = self.client.rpc(
                LOAD_FUNCTION,
                {"p_competencia": month.isoformat() if month else None},
            ).execute().data
        except APIError as error:
            error_text = " ".join((
                str(getattr(error, "code", "") or ""),
                str(getattr(error, "message", "") or ""),
                str(error),
            )).upper()
            if "AUTH_REQUIRED" in error_text or "42501" in error_text:
                raise PermissionDenied("Faça login novamente para consultar os clientes novos.") from error
            raise DataAccessError(
                data_api_rejection_message(error, "a consulta de clientes novos")
            ) from error
        except HTTPError as error:
            raise DataAccessError("Não foi possível consultar os clientes novos.") from error

        if data is None:
            return []
        if not isinstance(data, list):
            raise DataAccessError("A consulta de clientes novos devolveu um formato inesperado.")

        rows = []
        for item in data:
            if not isinstance(item, dict):
                raise DataAccessError("A consulta de clientes novos devolveu um registro inválido.")
            required = {
                "grupo_comercial_id", "nome_grupo_comercial", "data_primeira_compra",
                "pedidos", "vendedor", "regiao", "segmento", "situacao_atribuicao", "xp",
            }
            if not required.issubset(item):
                raise DataAccessError(
                    "A função de clientes novos está desatualizada. Execute novamente "
                    "sql/clientes_novos.sql no Supabase."
                )
            group_id = str(item.get("grupo_comercial_id") or "").strip()
            group_name = str(item.get("nome_grupo_comercial") or "").strip()
            first_purchase = item.get("data_primeira_compra")
            if not group_id or not group_name or not first_purchase:
                raise DataAccessError("A consulta de clientes novos devolveu identificação incompleta.")
            rows.append({
                "grupo_comercial_id": group_id,
                "nome_grupo_comercial": group_name,
                "data_primeira_compra": str(first_purchase),
                "pedidos": str(item.get("pedidos") or ""),
                "vendedor": str(item.get("vendedor") or "Não identificado").strip(),
                "regiao": str(item.get("regiao") or "").strip(),
                "segmento": str(item.get("segmento") or "").strip(),
                "situacao_atribuicao": str(item.get("situacao_atribuicao") or "Pendente"),
                "xp": float(item.get("xp") or 0),
            })
        return rows
