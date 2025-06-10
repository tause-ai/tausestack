import pytest
from unittest import mock

from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from tausestack.sdk.auth.main import get_current_user, get_optional_current_user, get_auth_backend # Asegúrate de que la ruta sea correcta
from tausestack.sdk.auth.base import User, AbstractAuthBackend
from tausestack.sdk.auth.exceptions import (
    InvalidTokenException,
    UserNotFoundException,
    AccountDisabledException,
    AuthException
)
from pydantic import EmailStr, HttpUrl


@pytest.fixture
def mock_auth_backend():
    """Fixture que mockea una instancia de AbstractAuthBackend."""
    backend = mock.AsyncMock(spec=AbstractAuthBackend)
    return backend


@pytest.fixture(autouse=True) # autouse para que se aplique a todas las pruebas en este módulo
def mock_get_auth_backend_func(mock_auth_backend):
    """Fixture que mockea la función get_auth_backend para que devuelva nuestro backend mockeado."""
    with mock.patch('tausestack.sdk.auth.main.get_auth_backend', return_value=mock_auth_backend) as mocked_func:
        yield mocked_func


@pytest.fixture
def sample_user_data():
    return User(
        id='test_user_uid',
        email='test@example.com',  
        email_verified=True,
        display_name='Test User',
        photo_url='http://example.com/photo.png',  
        disabled=False,
        custom_claims={'role': 'user'},
        created_at=1600000000,
        last_login_at=1600000000
    )


class TestGetCurrentUser:
    @pytest.mark.asyncio
    async def test_get_current_user_success(self, mock_auth_backend, sample_user_data):
        mock_auth_backend.verify_token.return_value = {'uid': 'test_user_uid'}
        mock_auth_backend.get_user_from_token.return_value = sample_user_data
        
        token_creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_token")
        user = await get_current_user(token=token_creds)
        
        assert user == sample_user_data
        mock_auth_backend.verify_token.assert_called_once_with("valid_token")
        mock_auth_backend.get_user_from_token.assert_called_once_with({'uid': 'test_user_uid'})

    @pytest.mark.asyncio
    async def test_get_current_user_no_token(self):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=None)
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "No se proporcionó token de autenticación" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, mock_auth_backend):
        mock_auth_backend.verify_token.side_effect = InvalidTokenException("Token falso!")
        token_creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid_token")
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token_creds)
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Token falso!" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_user_not_found_after_verify(self, mock_auth_backend):
        mock_auth_backend.verify_token.return_value = {'uid': 'unknown_uid'}
        mock_auth_backend.get_user_from_token.return_value = None # O podría lanzar UserNotFoundException
        token_creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_token_for_unknown_user")
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token_creds)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Usuario no encontrado a partir del token" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_user_not_found_exception(self, mock_auth_backend):
        mock_auth_backend.verify_token.return_value = {'uid': 'unknown_uid'}
        mock_auth_backend.get_user_from_token.side_effect = UserNotFoundException("Desde el backend")
        token_creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_token_for_unknown_user")
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token_creds)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Desde el backend" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_account_disabled(self, mock_auth_backend, sample_user_data):
        sample_user_data.disabled = True
        mock_auth_backend.verify_token.return_value = {'uid': 'disabled_user_uid'}
        mock_auth_backend.get_user_from_token.return_value = sample_user_data
        token_creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token_for_disabled_user")
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token_creds)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "La cuenta de usuario está deshabilitada" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_auth_exception_on_verify(self, mock_auth_backend):
        mock_auth_backend.verify_token.side_effect = AuthException("Error de backend en verify")
        token_creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="any_token")

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token_creds)
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Error de autenticación: Error de backend en verify" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_auth_exception_on_get_user(self, mock_auth_backend):
        mock_auth_backend.verify_token.return_value = {'uid': 'any_uid'}
        mock_auth_backend.get_user_from_token.side_effect = AuthException("Error de backend en get_user")
        token_creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="any_token")

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token_creds)
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Error de autenticación: Error de backend en get_user" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_generic_exception(self, mock_auth_backend):
        mock_auth_backend.verify_token.side_effect = Exception("Algo muy malo pasó") # Excepción genérica no Auth
        token_creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="any_token")

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token_creds)
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Error interno del servidor durante la autenticación" in exc_info.value.detail


class TestGetOptionalCurrentUser:
    @pytest.mark.asyncio
    async def test_get_optional_current_user_success(self, mock_auth_backend, sample_user_data):
        mock_auth_backend.verify_token.return_value = {'uid': 'test_user_uid'}
        mock_auth_backend.get_user_from_token.return_value = sample_user_data
        token_creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_token")
        
        user = await get_optional_current_user(token=token_creds)
        
        assert user == sample_user_data
        mock_auth_backend.verify_token.assert_called_once_with("valid_token")
        mock_auth_backend.get_user_from_token.assert_called_once_with({'uid': 'test_user_uid'})

    @pytest.mark.asyncio
    async def test_get_optional_current_user_no_token(self):
        user = await get_optional_current_user(token=None)
        assert user is None

    @pytest.mark.asyncio
    async def test_get_optional_current_user_invalid_token(self, mock_auth_backend):
        mock_auth_backend.verify_token.side_effect = InvalidTokenException("Token también falso")
        token_creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid_token_optional")
        
        user = await get_optional_current_user(token=token_creds)
        assert user is None

    @pytest.mark.asyncio
    async def test_get_optional_current_user_user_not_found(self, mock_auth_backend):
        mock_auth_backend.verify_token.return_value = {'uid': 'unknown_uid_optional'}
        mock_auth_backend.get_user_from_token.return_value = None
        token_creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_token_unknown_optional")
        
        user = await get_optional_current_user(token=token_creds)
        assert user is None

    @pytest.mark.asyncio
    async def test_get_optional_current_user_account_disabled(self, mock_auth_backend, sample_user_data):
        sample_user_data.disabled = True
        mock_auth_backend.verify_token.return_value = {'uid': 'disabled_user_uid_optional'}
        mock_auth_backend.get_user_from_token.return_value = sample_user_data
        token_creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token_disabled_optional")
        
        user = await get_optional_current_user(token=token_creds)
        assert user is None

    @pytest.mark.asyncio
    async def test_get_optional_current_user_auth_exception(self, mock_auth_backend):
        mock_auth_backend.verify_token.side_effect = AuthException("Error de backend opcional")
        token_creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="any_token_optional")

        user = await get_optional_current_user(token=token_creds)
        assert user is None

    @pytest.mark.asyncio
    async def test_get_optional_current_user_generic_exception(self, mock_auth_backend):
        # Esta es la única excepción que get_optional_current_user podría no atrapar internamente
        # si la excepción ocurre antes de la llamada a get_current_user o en un lugar inesperado.
        # Sin embargo, la implementación actual de get_optional_current_user llama a get_current_user
        # y atrapa HTTPException, por lo que una Exception genérica dentro de get_current_user
        # se convertiría en HTTPException(500) y luego sería atrapada por get_optional_current_user
        # resultando en None. Si la Exception ocurre en get_auth_backend, sí podría propagarse.
        
        # Para probar un error que no sea HTTPException y que resulte en None:
        mock_auth_backend.verify_token.side_effect = Exception("Algo muy malo pasó en opcional")
        token_creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="any_token_generic_optional")

        user = await get_optional_current_user(token=token_creds)
        assert user is None
