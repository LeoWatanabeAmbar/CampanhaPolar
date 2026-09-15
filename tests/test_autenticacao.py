from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from supabase_auth.errors import AuthApiError

from polar.autenticacao import SupabaseAuthenticator, is_privileged_key


def user():
    return SimpleNamespace(id="user-id", email="usuario@ambar.tech", is_anonymous=False)


def session():
    return SimpleNamespace(access_token="access-token", refresh_token="refresh-token")


@pytest.fixture
def authenticator():
    return SupabaseAuthenticator("https://project.supabase.co", "sb_publishable_test")


def test_authenticator_only_accepts_publishable_key():
    assert is_privileged_key("sb_secret_test") is True
    assert is_privileged_key("sb_publishable_test") is False
    with pytest.raises(ValueError):
        SupabaseAuthenticator("https://project.supabase.co", "sb_secret_test")


def test_sign_in_uses_normalized_email_without_persisting_password(authenticator):
    client = Mock()
    client.auth.sign_in_with_password.return_value = SimpleNamespace(
        user=user(), session=session(),
    )
    with patch.object(SupabaseAuthenticator, "_client", return_value=client):
        result = authenticator.sign_in(" USUARIO@AMBAR.TECH ", "senha")

    client.auth.sign_in_with_password.assert_called_once_with({
        "email": "usuario@ambar.tech", "password": "senha",
    })
    assert result == {
        "id": "user-id",
        "email": "usuario@ambar.tech",
        "access_token": "access-token",
        "refresh_token": "refresh-token",
    }


def test_invalid_credentials_return_generic_failure(authenticator):
    client = Mock()
    client.auth.sign_in_with_password.side_effect = AuthApiError(
        "Invalid login credentials", 400, "invalid_credentials",
    )
    with patch.object(SupabaseAuthenticator, "_client", return_value=client):
        assert authenticator.sign_in("usuario@ambar.tech", "errada") is None


def test_restore_session_revalidates_user_and_updates_tokens(authenticator):
    client = Mock()
    client.auth.set_session.return_value = SimpleNamespace(user=user(), session=session())
    client.auth.get_user.return_value = SimpleNamespace(user=user())
    with patch.object(SupabaseAuthenticator, "_client", return_value=client):
        result = authenticator.restore_session({
            "access_token": "old-access", "refresh_token": "old-refresh",
        })

    client.auth.set_session.assert_called_once_with("old-access", "old-refresh")
    client.auth.get_user.assert_called_once_with("access-token")
    assert result["email"] == "usuario@ambar.tech"
    assert result["access_token"] == "access-token"


def test_sign_out_revokes_only_current_session(authenticator):
    client = Mock()
    with patch.object(SupabaseAuthenticator, "_client", return_value=client):
        authenticator.sign_out({
            "access_token": "access-token", "refresh_token": "refresh-token",
        })

    client.auth.sign_out.assert_called_once_with({"scope": "local"})
