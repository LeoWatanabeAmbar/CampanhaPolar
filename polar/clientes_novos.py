"""Consulta de clientes novos pela Data API do Supabase."""
from __future__ import annotations

from datetime import date
from typing import Any

from httpx import HTTPError
from postgrest.exceptions import APIError

from polar.adiantamento import DataAccessError, PermissionDenied, validate_month

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
            raise DataAccessError("A Data API recusou a consulta de clientes novos.") from error
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
                "quantidade_pedidos": int(item.get("quantidade_pedidos") or 0),
                "vendedores": str(item.get("vendedores") or ""),
                "regioes": str(item.get("regioes") or ""),
                "segmento": str(item.get("segmento") or ""),
                "valor_liquido_elegivel": float(item.get("valor_liquido_elegivel") or 0),
                "quantidade_vendedores": int(item.get("quantidade_vendedores") or 0),
                "situacao_atribuicao": str(item.get("situacao_atribuicao") or "Pendente"),
                "xp_evento": float(item.get("xp_evento") or 0),
                "xp_por_vendedor": float(item.get("xp_por_vendedor") or 0),
            })
        return rows
