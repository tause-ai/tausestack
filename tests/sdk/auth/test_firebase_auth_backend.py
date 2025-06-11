import pytest
from unittest import mock
import firebase_admin
import time

from tausestack.sdk.auth.backends.firebase_admin import FirebaseAuthBackend
from tausestack.sdk.auth.base import User
from tausestack.sdk.auth.exceptions import (
    AuthException,
    InvalidTokenException,
    UserNotFoundException,
    AccountDisabledException,
)

# Mock para las credenciales de Firebase
@pytest.fixture
def mock_firebase_credentials():
    with mock.patch('firebase_admin.credentials.Certificate') as mock_cert:
        yield mock_cert

# Mock para la inicialización de la app de Firebase
@pytest.fixture
def mock_firebase_initialize_app():
    with mock.patch('firebase_admin.initialize_app') as mock_init_app, \
         mock.patch('firebase_admin.get_app') as mock_get_app:
        mock_app = mock.MagicMock(spec=firebase_admin.App)
        mock_app.name = "[DEFAULT]"
        mock_init_app.return_value = mock_app
        mock_get_app.return_value = mock_app

        original_default_app = FirebaseAuthBackend._default_app
        FirebaseAuthBackend._default_app = mock_app
        
        yield mock_init_app
        
        FirebaseAuthBackend._default_app = original_default_app

# Mock para el módulo firebase_admin.auth
@pytest.fixture
def mock_firebase_auth_module():
    with mock.patch('tausestack.sdk.auth.backends.firebase_admin.auth') as mock_auth:
        # Define simple, local exception classes to avoid import and metaclass issues.
        # The backend only cares about the exception type's name, not its implementation.
        class AuthError(Exception):
            def __init__(self, message, cause=None, http_response=None):
                super().__init__(message)
                self.code = 'UNKNOWN_ERROR' # Default code
                self.cause = cause
                self.http_response = http_response

        class RevokedIdTokenError(AuthError): pass
        class UserDisabledError(AuthError): pass
        class InvalidIdTokenError(AuthError): pass
        class UserNotFoundError(AuthError): pass
        class EmailAlreadyExistsError(AuthError): pass
        class UidAlreadyExistsError(AuthError): pass

        # Assign the simple local classes to the mock
        mock_auth.AuthError = AuthError
        mock_auth.RevokedIdTokenError = RevokedIdTokenError
        mock_auth.UserDisabledError = UserDisabledError
        mock_auth.InvalidIdTokenError = InvalidIdTokenError
        mock_auth.UserNotFoundError = UserNotFoundError
        mock_auth.EmailAlreadyExistsError = EmailAlreadyExistsError
        mock_auth.UidAlreadyExistsError = UidAlreadyExistsError
        yield mock_auth

@pytest.fixture
def firebase_auth_backend(mock_firebase_credentials, mock_firebase_initialize_app):
    FirebaseAuthBackend._default_app = None 
    backend = FirebaseAuthBackend(service_account_key_dict={'type': 'service_account'})
    return backend

@pytest.fixture
def mock_user_record():
    """Fixture for a mocked Firebase UserRecord. Uses plain strings for data."""
    user = mock.MagicMock()
    user.uid = 'test_uid'
    user.email = 'test@example.com'
    user.display_name = 'Test User'
    user.phone_number = '+11234567890'
    user.photo_url = 'http://example.com/photo.png'
    user.disabled = False
    user.email_verified = True
    user.custom_claims = {'role': 'user'}
    
    # Add missing fields required by the Pydantic User model
    user.provider_id = 'firebase'
    user.tokens_valid_after_timestamp = int(time.time() * 1000)
    
    # Mock user_metadata
    metadata = mock.MagicMock()
    metadata.creation_timestamp = int(time.time() * 1000) - 10000
    metadata.last_sign_in_timestamp = int(time.time() * 1000)
    user.user_metadata = metadata
    
    # Mock provider_data
    provider_data_mock = mock.MagicMock()
    provider_data_mock.uid = 'provider_uid'
    provider_data_mock.email = 'provider_email@example.com'
    provider_data_mock.display_name = 'Provider Display Name'
    provider_data_mock.photo_url = 'http://example.com/provider_photo.png'
    provider_data_mock.provider_id = 'google.com'
    user.provider_data = [provider_data_mock]
    
    return user

class TestFirebaseAuthBackendInitialization:
    def test_initialize_app_with_dict_success(self, mock_firebase_credentials, mock_firebase_initialize_app):
        FirebaseAuthBackend._default_app = None
        backend = FirebaseAuthBackend(service_account_key_dict={'type': 'service_account', 'project_id': 'test-project'})
        mock_firebase_credentials.assert_called_once_with({'type': 'service_account', 'project_id': 'test-project'})
        mock_firebase_initialize_app.assert_called_once()
        assert backend._default_app is not None

    def test_no_credentials_raises_value_error(self):
        FirebaseAuthBackend._default_app = None
        with pytest.raises(ValueError, match="Se debe proporcionar 'service_account_key_path' o 'service_account_key_dict'"):
            FirebaseAuthBackend()

class TestFirebaseAuthBackendVerifyToken:
    @pytest.mark.asyncio
    async def test_verify_token_success(self, firebase_auth_backend, mock_firebase_auth_module):
        expected_decoded_token = {'uid': 'test_uid', 'email': 'test@example.com'}
        mock_firebase_auth_module.verify_id_token.return_value = expected_decoded_token
        
        decoded_token = await firebase_auth_backend.verify_token('valid_token')
        
        mock_firebase_auth_module.verify_id_token.assert_called_once_with(
            'valid_token', app=firebase_auth_backend._default_app, check_revoked=True
        )
        assert decoded_token == expected_decoded_token

    @pytest.mark.asyncio
    async def test_verify_token_revoked(self, firebase_auth_backend, mock_firebase_auth_module):
        mock_firebase_auth_module.verify_id_token.side_effect = mock_firebase_auth_module.RevokedIdTokenError("revoked")
        with pytest.raises(InvalidTokenException, match="El token de ID ha sido revocado."):
            await firebase_auth_backend.verify_token('revoked_token')

class TestFirebaseAuthBackendGetUserFromToken:
    @pytest.mark.asyncio
    async def test_get_user_from_token_success(self, firebase_auth_backend, mock_firebase_auth_module, mock_user_record):
        verified_token = {'uid': 'test_uid'}
        mock_firebase_auth_module.get_user.return_value = mock_user_record

        user = await firebase_auth_backend.get_user_from_token(verified_token)

        mock_firebase_auth_module.get_user.assert_called_once_with('test_uid', app=firebase_auth_backend._default_app)
        assert isinstance(user, User)
        assert user.id == 'test_uid'
        assert user.email == 'test@example.com'

    @pytest.mark.asyncio
    async def test_get_user_from_token_no_uid(self, firebase_auth_backend):
        with pytest.raises(InvalidTokenException, match="Token verificado no contiene UID."):
            await firebase_auth_backend.get_user_from_token({'email': 'test@example.com'})

class TestFirebaseAuthBackendGetUserById:
    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, firebase_auth_backend, mock_firebase_auth_module, mock_user_record):
        mock_firebase_auth_module.get_user.return_value = mock_user_record
        
        user = await firebase_auth_backend.get_user_by_id('test_uid')
        
        mock_firebase_auth_module.get_user.assert_called_once_with('test_uid', app=firebase_auth_backend._default_app)
        assert user.id == 'test_uid'
        assert str(user.photo_url) == 'http://example.com/photo.png'

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, firebase_auth_backend, mock_firebase_auth_module):
        mock_firebase_auth_module.get_user.side_effect = mock_firebase_auth_module.UserNotFoundError('not found')
        user = await firebase_auth_backend.get_user_by_id('unknown_uid')
        assert user is None

class TestFirebaseAuthBackendGetUserByEmail:
    @pytest.mark.asyncio
    async def test_get_user_by_email_success(self, firebase_auth_backend, mock_firebase_auth_module, mock_user_record):
        test_email = 'test@example.com' # Use plain string
        mock_firebase_auth_module.get_user_by_email.return_value = mock_user_record
        
        user = await firebase_auth_backend.get_user_by_email(test_email)
        
        mock_firebase_auth_module.get_user_by_email.assert_called_once_with(test_email, app=firebase_auth_backend._default_app)
        assert user.email == test_email

    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, firebase_auth_backend, mock_firebase_auth_module):
        test_email = 'unknown@example.com'
        mock_firebase_auth_module.get_user_by_email.side_effect = mock_firebase_auth_module.UserNotFoundError('not found')
        user = await firebase_auth_backend.get_user_by_email(test_email)
        assert user is None

class TestFirebaseAuthBackendCreateUser:
    @pytest.mark.asyncio
    async def test_create_user_all_params_success(self, firebase_auth_backend, mock_firebase_auth_module, mock_user_record):
        mock_firebase_auth_module.create_user.return_value = mock_user_record
        
        created_user = await firebase_auth_backend.create_user(
            email='new@example.com',
            password='newPassword123',
            uid='new_uid',
            display_name='New User',
            photo_url='http://example.com/new_photo.png',
            email_verified=True,
            disabled=False,
            phone_number='+11234567890'
        )
        
        mock_firebase_auth_module.create_user.assert_called_once()
        assert created_user.id == mock_user_record.uid

    @pytest.mark.asyncio
    async def test_create_user_email_already_exists(self, firebase_auth_backend, mock_firebase_auth_module):
        mock_firebase_auth_module.create_user.side_effect = mock_firebase_auth_module.EmailAlreadyExistsError('exists')
        with pytest.raises(AuthException, match="Error al crear usuario en Firebase"):
            await firebase_auth_backend.create_user(email='existing@example.com', password='password')

class TestFirebaseAuthBackendUpdateUser:
    @pytest.mark.asyncio
    async def test_update_user_success(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module, mock_user_record):
        # Preparamos el mock_user_record para que refleje los datos actualizados
        mock_user_record.email = 'updated@example.com'
        mock_user_record.display_name = 'Updated User'
        mock_user_record.disabled = True
        mock_firebase_auth_module.update_user.return_value = mock_user_record

        updated_user = await firebase_auth_backend.update_user(
            user_id='test_uid',
            email='updated@example.com',
            display_name='Updated User',
            photo_url='http://example.com/updated_photo.png',
            email_verified=False,
            disabled=True,
            password='newPassword456',
            phone_number='+19876543210'
        )

        mock_firebase_auth_module.update_user.assert_called_once_with(
            'test_uid',
            email='updated@example.com',
            display_name='Updated User',
            photo_url='http://example.com/updated_photo.png',
            email_verified=False,
            disabled=True,
            password='newPassword456',
            phone_number='+19876543210',
            app=firebase_auth_backend._default_app
        )
        assert updated_user is not None
        assert updated_user.id == 'test_uid'
        assert updated_user.email == 'updated@example.com'
        assert updated_user.display_name == 'Updated User'
        assert updated_user.disabled is True

    @pytest.mark.asyncio
    async def test_update_user_not_found(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module):
        mock_firebase_auth_module.update_user.side_effect = mock_firebase_auth_module.UserNotFoundError("User not found")
        
        with pytest.raises(UserNotFoundException, match="Usuario no encontrado para actualizar."):
            await firebase_auth_backend.update_user(user_id='user_to_update_not_found', display_name='New Name')

    @pytest.mark.asyncio
    async def test_update_user_generic_firebase_error(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module):
        mock_firebase_auth_module.update_user.side_effect = mock_firebase_auth_module.AuthError('Error genérico de Firebase.')
        
        with pytest.raises(AuthException, match="Error al actualizar usuario en Firebase: Error genérico de Firebase."):
            await firebase_auth_backend.update_user(user_id='test_uid', display_name='Updated Name', photo_url='http://example.com/new.png')

    @pytest.mark.asyncio
    async def test_update_user_sdk_not_initialized(self, firebase_auth_backend: FirebaseAuthBackend):
        original_app = FirebaseAuthBackend._default_app
        FirebaseAuthBackend._default_app = None
        try:
            with pytest.raises(AuthException, match="Firebase Admin SDK no inicializado."):
                await firebase_auth_backend.update_user(user_id='any_user_sdk_init', display_name='Any Name') 
        finally:
            FirebaseAuthBackend._default_app = original_app



class TestFirebaseAuthBackendDeleteUser:
    @pytest.mark.asyncio
    async def test_delete_user_success(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module):
        uid_to_delete = 'user_to_delete_uid'
        mock_firebase_auth_module.delete_user.return_value = None 

        await firebase_auth_backend.delete_user(uid_to_delete)

        mock_firebase_auth_module.delete_user.assert_called_once_with(
            uid_to_delete,
            app=firebase_auth_backend._default_app
        )

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module):
        uid_not_found = 'unknown_uid'
        mock_firebase_auth_module.delete_user.side_effect = mock_firebase_auth_module.UserNotFoundError("Generic delete error")
        
        with pytest.raises(UserNotFoundException, match=f"Usuario con UID {uid_not_found} no encontrado al intentar eliminar."):
            await firebase_auth_backend.delete_user(uid_not_found)

    @pytest.mark.asyncio
    async def test_delete_user_generic_firebase_error(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module):
        uid_error = 'error_uid'
        mock_firebase_auth_module.delete_user.side_effect = mock_firebase_auth_module.AuthError('Error genérico de Firebase al eliminar.')
        
        with pytest.raises(AuthException, match="Error al eliminar usuario en Firebase: Error genérico de Firebase al eliminar."):
            await firebase_auth_backend.delete_user(uid_error)

    @pytest.mark.asyncio
    async def test_delete_user_sdk_not_initialized(self, firebase_auth_backend: FirebaseAuthBackend):
        original_app = FirebaseAuthBackend._default_app
        FirebaseAuthBackend._default_app = None
        try:
            with pytest.raises(AuthException, match="Firebase Admin SDK no inicializado."):
                await firebase_auth_backend.delete_user('any_uid')
        finally:
            FirebaseAuthBackend._default_app = original_app



class TestFirebaseAuthBackendSetCustomClaims:
    @pytest.mark.asyncio
    async def test_set_custom_claims_success(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module):
        uid = 'test_uid_for_claims'
        claims = {'role': 'admin', 'premium': True}
        mock_firebase_auth_module.set_custom_user_claims.return_value = None

        await firebase_auth_backend.set_custom_user_claims(uid, claims)

        mock_firebase_auth_module.set_custom_user_claims.assert_called_once_with(
            uid,
            claims,
            app=firebase_auth_backend._default_app
        )

    @pytest.mark.asyncio
    async def test_set_custom_claims_user_not_found(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module):
        uid_not_found = 'non_existent_uid'
        claims = {'role': 'admin'}
        mock_firebase_auth_module.set_custom_user_claims.side_effect = mock_firebase_auth_module.UserNotFoundError("User not found")
        
        with pytest.raises(UserNotFoundException, match="Usuario no encontrado para establecer claims."):
            await firebase_auth_backend.set_custom_user_claims(uid_not_found, claims)

    @pytest.mark.asyncio
    async def test_set_custom_claims_generic_firebase_error(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module):
        uid_error = 'error_uid_for_claims'
        claims = {'role': 'guest'}
        mock_firebase_auth_module.set_custom_user_claims.side_effect = mock_firebase_auth_module.AuthError("Generic claims error")
        
        with pytest.raises(AuthException, match=f"Error al establecer custom claims para el usuario {uid_error} en Firebase: Generic claims error"):
            await firebase_auth_backend.set_custom_user_claims(uid_error, claims)

    @pytest.mark.asyncio
    async def test_set_custom_claims_sdk_not_initialized(self, firebase_auth_backend: FirebaseAuthBackend):
        original_app = FirebaseAuthBackend._default_app
        FirebaseAuthBackend._default_app = None
        try:
            with pytest.raises(AuthException, match="Firebase Admin SDK no inicializado."):
                await firebase_auth_backend.set_custom_user_claims('any_uid_for_claims', {'role': 'any'}) 
        finally:
            FirebaseAuthBackend._default_app = original_app

# Fin de las clases de prueba para FirebaseAuthBackend
