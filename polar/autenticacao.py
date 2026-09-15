"""Autenticação do painel com usuários cadastrados no Supabase Auth."""
from __future__ import annotations

import base64
from dataclasses import dataclass
import json
from typing import Any

from httpx import HTTPError
from supabase import ClientOptions, create_client
from supabase_auth.errors import AuthApiError


class AuthenticationServiceError(RuntimeError):
    """Indica indisponibilidade ou sessão inválida no serviço de autenticação."""


def is_privileged_key(key: str) -> bool:
    """Impede o uso acidental de service role ou secret key no login."""
    if key.startswith("sb_secret_"):
        return True
    parts = key.split(".")
    if len(parts) != 3:
        return False
    try:
        payload = parts[1] + "=" * (-len(parts[1]) % 4)
        contents = json.loads(base64.urlsafe_b64decode(payload).decode("utf-8"))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        return False
    return contents.get("role") == "service_role"


@dataclass(frozen=True)
class SupabaseAuthenticator:
    """Cria clientes isolados por operação e não persiste tokens globalmente."""

    url: str
    publishable_key: str

    def __post_init__(self):
        normalized_url = self.url.strip().rstrip("/")
        key = self.publishable_key.strip()
        if not normalized_url.startswith("https://") or not key:
            raise ValueError("Configure a URL e a chave publicável do Supabase Auth.")
        if is_privileged_key(key):
            raise ValueError("Use uma chave publicável do Supabase Auth, nunca uma chave secreta.")
        object.__setattr__(self, "url", normalized_url)
        object.__setattr__(self, "publishable_key", key)

    def _client(self):
        return create_client(
            self.url,
            self.publishable_key,
            options=ClientOptions(auto_refresh_token=False, persist_session=False),
        )

    @staticmethod
    def _session_data(user: Any, session: Any) -> dict[str, str]:
        if user is None or session is None or not user.id or not user.email:
            raise AuthenticationServiceError("A conta autenticada não possui identificação completa.")
        if getattr(user, "is_anonymous", False):
            raise AuthenticationServiceError("Contas anônimas não podem acessar o painel.")
        return {
            "id": str(user.id),
            "email": str(user.email).strip().lower(),
            "access_token": str(session.access_token),
            "refresh_token": str(session.refresh_token),
        }

    def sign_in(self, email: str, password: str) -> dict[str, str] | None:
        """Autentica e devolve somente os dados necessários da sessão."""
        normalized_email = email.strip().lower()
        if not normalized_email or not password:
            return None
        try:
            response = self._client().auth.sign_in_with_password({
                "email": normalized_email,
                "password": password,
            })
        except AuthApiError as error:
            if error.status in {400, 401}:
                return None
            raise AuthenticationServiceError("Falha no Supabase Auth.") from error
        except HTTPError as error:
            raise AuthenticationServiceError("Falha de comunicação com o Supabase Auth.") from error
        if response.user is None or response.session is None:
            return None
        return self._session_data(response.user, response.session)

    def restore_session(self, saved_session: dict[str, str]) -> dict[str, str]:
        """Revalida o usuário e substitui tokens renovados na sessão do Streamlit."""
        try:
            client = self._client()
            response = client.auth.set_session(
                saved_session["access_token"],
                saved_session["refresh_token"],
            )
            if response.user is None or response.session is None:
                raise AuthenticationServiceError("Sessão inválida.")
            validated_user = client.auth.get_user(response.session.access_token).user
            return self._session_data(validated_user, response.session)
        except (AuthApiError, HTTPError, KeyError, AttributeError) as error:
            raise AuthenticationServiceError("Não foi possível validar a sessão.") from error

    def sign_out(self, saved_session: dict[str, str]):
        """Revoga somente a sessão usada neste navegador."""
        try:
            client = self._client()
            client.auth.set_session(
                saved_session["access_token"],
                saved_session["refresh_token"],
            )
            client.auth.sign_out({"scope": "local"})
        except (AuthApiError, HTTPError, KeyError) as error:
            raise AuthenticationServiceError("Não foi possível encerrar a sessão.") from error
