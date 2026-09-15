"""Consulta de expansão de mix pela Data API do Supabase."""
from __future__ import annotations

from datetime import date
from typing import Any

from httpx import HTTPError
from postgrest.exceptions import APIError

from polar.adiantamento import DataAccessError, PermissionDenied, validate_month

LOAD_FUNCTION = "campanha_polar_carregar_mix_produtos"


class ProductMixRepository:
    """Carrega as primeiras compras das famílias de mix durante a campanha."""

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
                raise PermissionDenied(
                    "Faça login novamente para consultar o mix de produtos."
                ) from error
            raise DataAccessError("A Data API recusou a consulta do mix de produtos.") from error
        except HTTPError as error:
            raise DataAccessError("Não foi possível consultar o mix de produtos.") from error

        if data is None:
            return []
        if not isinstance(data, list):
            raise DataAccessError(
                "A consulta do mix de produtos devolveu um formato inesperado."
            )

        rows = []
        for item in data:
            if not isinstance(item, dict):
                raise DataAccessError(
                    "A consulta do mix de produtos devolveu um registro inválido."
                )
            required = {
                "grupo_comercial_id", "nome_grupo_comercial", "data_expansao", "grupo_mix",
                "produtos", "pedidos", "vendedor", "regiao", "segmento",
                "valor_linha_elegivel", "valor_minimo", "situacao_evento", "xp",
            }
            if not required.issubset(item):
                raise DataAccessError(
                    "A função de mix de produtos está desatualizada. Execute novamente "
                    "sql/mix_produtos.sql no Supabase."
                )
            group_id = str(item.get("grupo_comercial_id") or "").strip()
            group_name = str(item.get("nome_grupo_comercial") or "").strip()
            event_date = item.get("data_expansao")
            product_group = str(item.get("grupo_mix") or "").strip()
            if not group_id or not group_name or not event_date or not product_group:
                raise DataAccessError(
                    "A consulta do mix de produtos devolveu identificação incompleta."
                )
            rows.append({
                "grupo_comercial_id": group_id,
                "nome_grupo_comercial": group_name,
                "data_expansao": str(event_date),
                "grupo_mix": product_group,
                "produtos": str(item.get("produtos") or ""),
                "pedidos": str(item.get("pedidos") or ""),
                "vendedor": str(item.get("vendedor") or "Não identificado").strip(),
                "regiao": str(item.get("regiao") or "").strip(),
                "segmento": str(item.get("segmento") or "").strip(),
                "valor_linha_elegivel": float(item.get("valor_linha_elegivel") or 0),
                "valor_minimo": (
                    float(item["valor_minimo"])
                    if item.get("valor_minimo") is not None
                    else None
                ),
                "situacao_evento": str(item.get("situacao_evento") or "Pendente"),
                "xp": float(item.get("xp") or 0),
            })
        return rows
