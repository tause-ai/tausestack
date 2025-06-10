import pytest
from unittest import mock
import firebase_admin # Para mockear firebase_admin.auth y firebase_admin.credentials

from tausestack.sdk.auth.backends.firebase_admin import FirebaseAuthBackend
from tausestack.sdk.auth.base import User
from tausestack.sdk.auth.exceptions import (
    AuthException,
    InvalidTokenException,
    UserNotFoundException,
    AccountDisabledException,
)
from pydantic import EmailStr, HttpUrl

# Mock para las credenciales de Firebase
@pytest.fixture
def mock_firebase_credentials():
    with mock.patch('firebase_admin.credentials.Certificate') as mock_cert:
        yield mock_cert

# Mock para la inicialización de la app de Firebase
@pytest.fixture
def mock_firebase_initialize_app(mock_firebase_exceptions): # Depend on mock_firebase_exceptions
    with mock.patch('firebase_admin.initialize_app') as mock_init_app, \
         mock.patch('firebase_admin.get_app') as mock_get_app: # Also mock get_app
        mock_app = mock.MagicMock(spec=firebase_admin.App) # Use MagicMock for attributes like 'name'
        mock_app.name = "[DEFAULT]"  # Set default app name
        mock_init_app.return_value = mock_app
        mock_get_app.return_value = mock_app

        original_default_app = FirebaseAuthBackend._default_app
        FirebaseAuthBackend._default_app = mock_app # Ensure the class property is set to this instance
        
        yield mock_init_app
        
        FirebaseAuthBackend._default_app = original_default_app # Restore for other tests

# Mock para el módulo firebase_admin.auth
@pytest.fixture
def mock_firebase_auth_module(mock_firebase_exceptions): # Depends on mock_firebase_exceptions
    with mock.patch('firebase_admin.auth') as mock_auth:
        # Ensure the mocked auth module has the (mocked) exception classes if needed directly
        mock_auth.RevokedIdTokenError = firebase_admin.auth.RevokedIdTokenError
        mock_auth.UserDisabledError = firebase_admin.auth.UserDisabledError
        mock_auth.InvalidIdTokenError = firebase_admin.auth.InvalidIdTokenError
        mock_auth.UserNotFoundError = firebase_admin.auth.UserNotFoundError
        mock_auth.EmailAlreadyExistsError = firebase_admin.auth.EmailAlreadyExistsError
        mock_auth.UidAlreadyExistsError = firebase_admin.auth.UidAlreadyExistsError
        # mock_auth.FirebaseError = firebase_admin.FirebaseError # If auth module itself has FirebaseError
        yield mock_auth

@pytest.fixture
def firebase_auth_backend(mock_firebase_credentials, mock_firebase_initialize_app):
    """Fixture para obtener una instancia de FirebaseAuthBackend con mocks aplicados."""
    # Reseteamos _default_app antes de cada prueba para asegurar aislamiento
    FirebaseAuthBackend._default_app = None 
    backend = FirebaseAuthBackend(service_account_key_dict={'type': 'service_account'})
    return backend

@pytest.fixture(scope="function")
def mock_firebase_exceptions():
    """Mocks Firebase-specific exceptions used in the tests."""
    class MockFirebaseError(Exception): pass
    class MockRevokedIdTokenError(MockFirebaseError): pass
    class MockUserDisabledError(MockFirebaseError): pass
    class MockInvalidIdTokenError(MockFirebaseError): pass
    class MockUserNotFoundError(MockFirebaseError): pass
    class MockEmailAlreadyExistsError(MockFirebaseError): pass
    class MockUidAlreadyExistsError(MockFirebaseError): pass

    # Patching the actual locations where these exceptions are imported/used by the SUT or tests
    patches = [
        mock.patch('firebase_admin.FirebaseError', MockFirebaseError, create=True),
        mock.patch('firebase_admin.auth.RevokedIdTokenError', MockRevokedIdTokenError, create=True),
        mock.patch('firebase_admin.auth.UserDisabledError', MockUserDisabledError, create=True),
        mock.patch('firebase_admin.auth.InvalidIdTokenError', MockInvalidIdTokenError, create=True),
        mock.patch('firebase_admin.auth.UserNotFoundError', MockUserNotFoundError, create=True),
        mock.patch('firebase_admin.auth.EmailAlreadyExistsError', MockEmailAlreadyExistsError, create=True),
        mock.patch('firebase_admin.auth.UidAlreadyExistsError', MockUidAlreadyExistsError, create=True),
    ]
    for p_item in patches:
        p_item.start()
    yield
    for p_item in patches:
        p_item.stop()

class TestFirebaseAuthBackendInitialization:
    def test_initialize_app_with_dict_success(self, mock_firebase_credentials, mock_firebase_initialize_app):
        FirebaseAuthBackend._default_app = None # Forzar reinicialización
        backend = FirebaseAuthBackend(service_account_key_dict={'type': 'service_account', 'project_id': 'test-project'})
        mock_firebase_credentials.assert_called_once_with({'type': 'service_account', 'project_id': 'test-project'})
        mock_firebase_initialize_app.assert_called_once()
        assert backend._default_app is not None, "Firebase app no fue inicializada"

    def test_initialize_app_with_path_success(self, mock_firebase_credentials, mock_firebase_initialize_app):
        FirebaseAuthBackend._default_app = None # Forzar reinicialización
        backend = FirebaseAuthBackend(service_account_key_path='/fake/path.json')
        mock_firebase_credentials.assert_called_once_with('/fake/path.json')
        mock_firebase_initialize_app.assert_called_once()
        assert backend._default_app is not None, "Firebase app no fue inicializada"

    def test_initialize_app_already_initialized(self, mock_firebase_credentials, mock_firebase_initialize_app):
        FirebaseAuthBackend._default_app = None # Asegurar que partimos de cero
        # Primera inicialización
        FirebaseAuthBackend(service_account_key_dict={'type': 'service_account'})
        first_call_count_creds = mock_firebase_credentials.call_count
        first_call_count_init = mock_firebase_initialize_app.call_count

        # Segunda inicialización no debería llamar a los mocks de nuevo
        FirebaseAuthBackend(service_account_key_dict={'type': 'service_account'})
        assert mock_firebase_credentials.call_count == first_call_count_creds
        assert mock_firebase_initialize_app.call_count == first_call_count_init

    def test_initialize_app_no_credentials_raises_value_error(self):
        FirebaseAuthBackend._default_app = None
        with pytest.raises(ValueError, match="Se debe proporcionar 'service_account_key_path' o 'service_account_key_dict'"):
            FirebaseAuthBackend()

    def test_initialize_app_sdk_error_raises_auth_exception(self, mock_firebase_credentials):
        FirebaseAuthBackend._default_app = None
        mock_firebase_credentials.side_effect = Exception("SDK Error")
        with pytest.raises(AuthException, match="Error al inicializar Firebase Admin SDK: SDK Error"):
            FirebaseAuthBackend(service_account_key_dict={'type': 'service_account'})

class TestFirebaseAuthBackendVerifyToken:
    @pytest.mark.asyncio
    async def test_verify_token_success(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module):
        expected_decoded_token = {'uid': 'test_uid', 'email': 'test@example.com'}
        mock_firebase_auth_module.verify_id_token.return_value = expected_decoded_token
        
        decoded_token = await firebase_auth_backend.verify_token('valid_token_string')
        
        mock_firebase_auth_module.verify_id_token.assert_called_once_with(
            'valid_token_string', 
            app=firebase_auth_backend._default_app, 
            check_revoked=True
        )
        assert decoded_token == expected_decoded_token

    @pytest.mark.asyncio
    async def test_verify_token_revoked(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module):
        mock_firebase_auth_module.verify_id_token.side_effect = firebase_admin.auth.RevokedIdTokenError("Token revocado.")
        
        with pytest.raises(InvalidTokenException, match="El token de ID ha sido revocado."):
            await firebase_auth_backend.verify_token('revoked_token_string')

    @pytest.mark.asyncio
    async def test_verify_token_user_disabled(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module):
        mock_firebase_auth_module.verify_id_token.side_effect = firebase_admin.auth.UserDisabledError("Usuario deshabilitado.")
        
        with pytest.raises(AccountDisabledException, match="La cuenta de usuario asociada con este token ha sido deshabilitada."):
            await firebase_auth_backend.verify_token('disabled_user_token_string')

    @pytest.mark.asyncio
    async def test_verify_token_invalid_token_error(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module):
        mock_firebase_auth_module.verify_id_token.side_effect = firebase_admin.auth.InvalidIdTokenError("Token JWT malformado.")
        
        with pytest.raises(InvalidTokenException, match="Token de ID inválido: Token JWT malformado."):
            await firebase_auth_backend.verify_token('invalid_token_string')

    @pytest.mark.asyncio
    async def test_verify_token_generic_auth_error(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module):
        mock_firebase_auth_module.verify_id_token.side_effect = Exception("Error genérico de Firebase")
        
        with pytest.raises(AuthException, match="Error al verificar el token de Firebase: Error genérico de Firebase"):
            await firebase_auth_backend.verify_token('some_token_string')

    @pytest.mark.asyncio
    async def test_verify_token_sdk_not_initialized(self, firebase_auth_backend: FirebaseAuthBackend):
        # Forzamos que la app no esté inicializada para esta prueba específica
        original_app = FirebaseAuthBackend._default_app
        FirebaseAuthBackend._default_app = None
        try:
            with pytest.raises(AuthException, match="Firebase Admin SDK no inicializado."):
                await firebase_auth_backend.verify_token('any_token')
        finally:
            FirebaseAuthBackend._default_app = original_app # Restaurar para otras pruebas

@pytest.fixture
def mock_user_record():
    """Fixture para un UserRecord de Firebase mockeado."""
    user_record = mock.MagicMock() # Use MagicMock for flexibility
    user_record.uid = 'test_uid'
    user_record.email = 'test@example.com' # Ensure this is a string
    user_record.email_verified = True
    user_record.phone_number = None
    user_record.display_name = 'Test User'
    user_record.photo_url = 'http://example.com/photo.png' # Ensure this is a string
    user_record.disabled = False
    user_record.custom_claims = {'role': 'user'}
    user_record.provider_data = []
    
    user_metadata_mock = mock.MagicMock()
    user_metadata_mock.creation_timestamp = 1678886400000  # ms
    user_metadata_mock.last_sign_in_timestamp = 1678887400000 # ms
    user_record.user_metadata = user_metadata_mock
    return user_record

class TestFirebaseAuthBackendGetUserFromToken:
    @pytest.mark.asyncio
    async def test_get_user_from_token_success(self, firebase_auth_backend: FirebaseAuthBackend, mock_user_record):
        verified_token = {'uid': 'test_uid', 'email': 'test@example.com'}
        expected_user = User(
            id='test_uid', 
            email=EmailStr('test@example.com'), 
            email_verified=True,
            display_name='Test User',
            photo_url=HttpUrl('http://example.com/photo.png'),
            disabled=False,
            custom_claims={'role': 'user'},
            provider_data=[],
            created_at=1678886400,
            last_login_at=1678887400
        )
        
        # Mockeamos el método interno get_user_by_id que es llamado por get_user_from_token
        with mock.patch.object(firebase_auth_backend, 'get_user_by_id', return_value=expected_user) as mock_get_user_by_id:
            user = await firebase_auth_backend.get_user_from_token(verified_token)
            mock_get_user_by_id.assert_called_once_with('test_uid')
            assert user == expected_user

    @pytest.mark.asyncio
    async def test_get_user_from_token_no_uid_in_token(self, firebase_auth_backend: FirebaseAuthBackend):
        verified_token_no_uid = {'email': 'test@example.com'} # Falta 'uid'
        with pytest.raises(InvalidTokenException, match="Token verificado no contiene UID."):
            await firebase_auth_backend.get_user_from_token(verified_token_no_uid)

    @pytest.mark.asyncio
    async def test_get_user_from_token_sdk_not_initialized(self, firebase_auth_backend: FirebaseAuthBackend):
        original_app = FirebaseAuthBackend._default_app
        FirebaseAuthBackend._default_app = None
        try:
            with pytest.raises(AuthException, match="Firebase Admin SDK no inicializado."):
                await firebase_auth_backend.get_user_from_token({'uid': 'any_uid'})
        finally:
            FirebaseAuthBackend._default_app = original_app

class TestFirebaseAuthBackendGetUserById:
    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module, mock_user_record):
        mock_firebase_auth_module.get_user.return_value = mock_user_record
        
        user = await firebase_auth_backend.get_user_by_id('test_uid')
        
        mock_firebase_auth_module.get_user.assert_called_once_with('test_uid', app=firebase_auth_backend._default_app)
        assert user is not None
        assert user.id == 'test_uid'
        assert user.email == 'test@example.com'
        assert user.photo_url == HttpUrl('http://example.com/photo.png')

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module):
        mock_firebase_auth_module.get_user.side_effect = firebase_admin.auth.UserNotFoundError('Usuario no encontrado.')
        
        user = await firebase_auth_backend.get_user_by_id('unknown_uid')
        assert user is None

    @pytest.mark.asyncio
    async def test_get_user_by_id_generic_auth_error(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module):
        mock_firebase_auth_module.get_user.side_effect = Exception("Error de Firebase")
        
        with pytest.raises(AuthException, match="Error al obtener usuario por ID de Firebase: Error de Firebase"):
            await firebase_auth_backend.get_user_by_id('any_uid')

    @pytest.mark.asyncio
    async def test_get_user_by_id_sdk_not_initialized(self, firebase_auth_backend: FirebaseAuthBackend):
        original_app = FirebaseAuthBackend._default_app
        FirebaseAuthBackend._default_app = None
        try:
            with pytest.raises(AuthException, match="Firebase Admin SDK no inicializado."):
                await firebase_auth_backend.get_user_by_id('any_uid')
        finally:
            FirebaseAuthBackend._default_app = original_app

class TestFirebaseAuthBackendGetUserByEmail:
    @pytest.mark.asyncio
    async def test_get_user_by_email_success(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module, mock_user_record):
        test_email = EmailStr('test@example.com')
        mock_firebase_auth_module.get_user_by_email.return_value = mock_user_record
        
        user = await firebase_auth_backend.get_user_by_email(test_email)
        
        mock_firebase_auth_module.get_user_by_email.assert_called_once_with(test_email, app=firebase_auth_backend._default_app)
        assert user is not None
        assert user.id == 'test_uid'
        assert user.email == test_email

    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module):
        test_email = EmailStr('unknown@example.com')
        mock_firebase_auth_module.get_user_by_email.side_effect = firebase_admin.auth.UserNotFoundError('Usuario no encontrado.')
        
        user = await firebase_auth_backend.get_user_by_email(test_email)
        assert user is None

    @pytest.mark.asyncio
    async def test_get_user_by_email_generic_auth_error(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module):
        test_email = EmailStr('error@example.com')
        mock_firebase_auth_module.get_user_by_email.side_effect = Exception("Error de Firebase")
        
        with pytest.raises(AuthException, match="Error al obtener usuario por email de Firebase: Error de Firebase"):
            await firebase_auth_backend.get_user_by_email(test_email)

    @pytest.mark.asyncio
    async def test_get_user_by_email_sdk_not_initialized(self, firebase_auth_backend: FirebaseAuthBackend):
        original_app = FirebaseAuthBackend._default_app
        FirebaseAuthBackend._default_app = None
        try:
            with pytest.raises(AuthException, match="Firebase Admin SDK no inicializado."):
                await firebase_auth_backend.get_user_by_email(EmailStr('any@example.com'))
        finally:
            FirebaseAuthBackend._default_app = original_app

class TestFirebaseAuthBackendCreateUser:
    @pytest.mark.asyncio
    async def test_create_user_all_params_success(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module, mock_user_record):
        mock_firebase_auth_module.create_user.return_value = mock_user_record
        
        created_user_record = await firebase_auth_backend.create_user(
            email=EmailStr('new@example.com'),
            password='newPassword123',
            uid='new_uid',
            display_name='New User',
            photo_url=HttpUrl('http://example.com/new_photo.png'),
            email_verified=True,
            disabled=False,
            phone_number='+11234567890'
        )
        
        mock_firebase_auth_module.create_user.assert_called_once_with(
            email='new@example.com',
            password='newPassword123',
            uid='new_uid',
            display_name='New User',
            photo_url='http://example.com/new_photo.png',
            email_verified=True,
            disabled=False,
            phone_number='+11234567890',
            app=firebase_auth_backend._default_app
        )
        assert created_user_record.id == mock_user_record.uid # Asumimos que el mock_user_record se usa como base

    @pytest.mark.asyncio
    async def test_create_user_minimal_params_success(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module, mock_user_record):
        mock_firebase_auth_module.create_user.return_value = mock_user_record
        mock_user_record.email = 'minimal@example.com' # Ajustar el mock para este caso
        mock_user_record.uid = 'minimal_uid' # Ajustar el mock para este caso

        created_user_record = await firebase_auth_backend.create_user(
            email=EmailStr('minimal@example.com'),
            password='minimalPassword'
        )
        
        mock_firebase_auth_module.create_user.assert_called_once_with(
            email='minimal@example.com',
            password='minimalPassword',
            uid=None, # uid es opcional y debería ser None si no se provee
            display_name=None,
            photo_url=None,
            email_verified=False, # default
            disabled=False, # default
            phone_number=None,
            app=firebase_auth_backend._default_app
        )
        assert created_user_record.id == mock_user_record.uid
        assert created_user_record.email == 'minimal@example.com'

    @pytest.mark.asyncio
    async def test_create_user_email_already_exists(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module):
        mock_firebase_auth_module.create_user.side_effect = firebase_admin.auth.EmailAlreadyExistsError('Email ya existe.', code='auth/email-already-exists')
        
        with pytest.raises(AuthException, match="Error al crear usuario en Firebase: Email ya existe."):
            await firebase_auth_backend.create_user(email=EmailStr('existing@example.com'), password='password')

    @pytest.mark.asyncio
    async def test_create_user_uid_already_exists(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module):
        mock_firebase_auth_module.create_user.side_effect = firebase_admin.auth.UidAlreadyExistsError('UID ya existe.', code='auth/uid-already-exists')
        
        with pytest.raises(AuthException, match="Error al crear usuario en Firebase: UID ya existe."):
            await firebase_auth_backend.create_user(email=EmailStr('another@example.com'), password='password', uid='existing_uid')

    @pytest.mark.asyncio
    async def test_create_user_generic_firebase_error(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module):
        mock_firebase_auth_module.create_user.side_effect = firebase_admin.auth.EmailAlreadyExistsError("Generic Firebase error") # Using a more specific, but still generic, Firebase auth error for testing
        
        with pytest.raises(AuthException, match="Error al crear usuario en Firebase: Error genérico de Firebase."):
            await firebase_auth_backend.create_user(email=EmailStr('error@example.com'), password='password')

    @pytest.mark.asyncio
    async def test_create_user_sdk_not_initialized(self, firebase_auth_backend: FirebaseAuthBackend):
        original_app = FirebaseAuthBackend._default_app
        FirebaseAuthBackend._default_app = None
        try:
            with pytest.raises(AuthException, match="Firebase Admin SDK no inicializado."):
                await firebase_auth_backend.create_user(email=EmailStr('any@example.com'), password='password')
        finally:
            FirebaseAuthBackend._default_app = original_app

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
            email=EmailStr('updated@example.com'),
            display_name='Updated User',
            photo_url=HttpUrl('http://example.com/updated_photo.png'),
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
        mock_firebase_auth_module.update_user.side_effect = firebase_admin.auth.UserNotFoundError("User not found")
        
        with pytest.raises(UserNotFoundException, match="Usuario no encontrado para actualizar."):
            await firebase_auth_backend.update_user(user_id='user_to_update_not_found', display_name='New Name')

    @pytest.mark.asyncio
    async def test_update_user_generic_firebase_error(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module):
        mock_firebase_auth_module.update_user.side_effect = firebase_admin.FirebaseError(code='unknown-error', message='Error genérico de Firebase.')
        
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
        # delete_user no devuelve nada en caso de éxito
        mock_firebase_auth_module.delete_user.return_value = None 

        await firebase_auth_backend.delete_user(uid_to_delete)

        mock_firebase_auth_module.delete_user.assert_called_once_with(
            uid_to_delete,
            app=firebase_auth_backend._default_app
        )

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module):
        uid_not_found = 'unknown_uid'
        mock_firebase_auth_module.delete_user.side_effect = firebase_admin.auth.UserNotFoundError("Generic delete error") # Using a specific Firebase auth error
        
        with pytest.raises(UserNotFoundException, match=f"Usuario con UID {uid_not_found} no encontrado al intentar eliminar."):
            await firebase_auth_backend.delete_user(uid_not_found)

    @pytest.mark.asyncio
    async def test_delete_user_generic_firebase_error(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module):
        uid_error = 'error_uid'
        mock_firebase_auth_module.delete_user.side_effect = firebase_admin.FirebaseError(code='unknown-error', message='Error genérico de Firebase al eliminar.')
        
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
        # set_custom_user_claims no devuelve nada en caso de éxito
        mock_firebase_auth_module.set_custom_user_claims.return_value = None

        await firebase_auth_backend.set_custom_user_claims(uid, claims)

        mock_firebase_auth_module.set_custom_user_claims.assert_called_once_with(
            uid,
            claims,
            app=firebase_auth_backend._default_app
        )

    @pytest.mark.asyncio
    async def test_set_custom_claims_user_not_found(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module):
        uid_not_found = 'unknown_uid_for_claims'
        claims = {'role': 'user'}
        mock_firebase_auth_module.set_custom_user_claims.side_effect = firebase_admin.auth.UserNotFoundError("User not found")
        
        with pytest.raises(UserNotFoundException, match="Usuario no encontrado para establecer claims."):
            await firebase_auth_backend.set_custom_user_claims('non_existent_uid', {'role': 'admin'})

    @pytest.mark.asyncio
    async def test_set_custom_claims_generic_firebase_error(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module):
        uid_error = 'error_uid_for_claims'
        claims = {'role': 'guest'}
        mock_firebase_auth_module.set_custom_user_claims.side_effect = firebase_admin.auth.UserNotFoundError("Generic claims error") # Using a specific Firebase auth error
        
        with pytest.raises(AuthException, match="Error al establecer claims personalizados en Firebase: Generic claims error"):
            await firebase_auth_backend.set_custom_user_claims('any_uid_for_claims', {'role': 'any'})

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
