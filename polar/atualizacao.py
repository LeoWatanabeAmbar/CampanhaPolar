"""Consulta do último refresh concluído pelo dataflow comercial."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from httpx import HTTPError
from postgrest.exceptions import APIError

from polar.adiantamento import DataAccessError, data_api_rejection_message

REFRESH_TABLE = "cpv_refresh_controle"
REFRESH_KEYS = ("dataflow_cpv_public", "totvs_supabase")
SAO_PAULO = ZoneInfo("America/Sao_Paulo")


def parse_refresh_datetime(value: object) -> datetime | None:
    """Converte o timestamp do Supabase para o fuso exibido no painel."""
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str) and value.strip():
        try:
            parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=ZoneInfo("UTC"))
    return parsed.astimezone(SAO_PAULO)


class DataRefreshRepository:
    """Lê o marcador de refresh compartilhado com o Gestão Comercial."""

    def __init__(self, client: Any):
        self.client = client

    def load(self) -> datetime | None:
        try:
            response = (
                self.client.table(REFRESH_TABLE)
                .select("chave,status,finalizado_em,atualizado_em")
                .in_("chave", list(REFRESH_KEYS))
                .order("atualizado_em", desc=True)
                .limit(1)
                .execute()
            )
        except APIError as error:
            raise DataAccessError(
                data_api_rejection_message(error, "a consulta da última atualização dos dados")
            ) from error
        except HTTPError as error:
            raise DataAccessError(
                "Não foi possível consultar a última atualização dos dados."
            ) from error

        data = response.data
        if not isinstance(data, list) or not data or not isinstance(data[0], dict):
            return None
        row = data[0]
        return parse_refresh_datetime(row.get("finalizado_em") or row.get("atualizado_em"))
