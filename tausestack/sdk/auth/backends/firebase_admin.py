import firebase_admin
from firebase_admin import auth, credentials
from typing import Any, Dict, Optional, Type

from pydantic import EmailStr, HttpUrl

from ..base import AbstractAuthBackend, User
from ..exceptions import (
    AuthException,
    UserNotFoundException,
    InvalidTokenException,
    AccountDisabledException,
)

# El token verificado por Firebase Admin SDK es un diccionario.
FirebaseVerifiedToken = Dict[str, Any]


class FirebaseAuthBackend(AbstractAuthBackend[FirebaseVerifiedToken]):
    _default_app: Optional[firebase_admin.App] = None

    def __init__(
        self,
        service_account_key_path: Optional[str] = None,
        service_account_key_dict: Optional[Dict[str, Any]] = None,
        project_id: Optional[str] = None, # Puede ser inferido de las credenciales
    ):
        """
        Inicializa el backend de Firebase Auth.

        Args:
            service_account_key_path: Ruta al archivo JSON de la cuenta de servicio.
            service_account_key_dict: Diccionario con el contenido de la cuenta de servicio.
            project_id: ID del proyecto Firebase (opcional si está en las credenciales).
        
        Se debe proporcionar service_account_key_path o service_account_key_dict.
        """
        if FirebaseAuthBackend._default_app:
            return

        if not service_account_key_path and not service_account_key_dict:
            raise ValueError(
                "Se debe proporcionar 'service_account_key_path' o 'service_account_key_dict' para inicializar Firebase."
            )
        
        try:
            if service_account_key_dict:
                cred = credentials.Certificate(service_account_key_dict)
            else:
                cred = credentials.Certificate(service_account_key_path)
            
            options = {'projectId': project_id} if project_id else {}
            FirebaseAuthBackend._default_app = firebase_admin.initialize_app(credential=cred, options=options, name="tausestack-firebase-auth")
        except Exception as e:
            # Considerar loggear el error 'e' aquí
            raise AuthException(f"Error al inicializar Firebase Admin SDK: {e}")

    async def _map_firebase_user_to_sdk_user(self, firebase_user: auth.UserRecord) -> User:
        """Mapea un UserRecord de Firebase a nuestro modelo User."""
        provider_data_list = [
            {
                "provider_id": p.provider_id,
                "uid": p.uid,
                "email": p.email,
                "display_name": p.display_name,
                "photo_url": str(p.photo_url) if p.photo_url else None,
            }
            for p in firebase_user.provider_data
        ] if firebase_user.provider_data else []

        return User(
            id=firebase_user.uid,
            email=firebase_user.email,
            email_verified=firebase_user.email_verified,
            phone_number=firebase_user.phone_number,
            display_name=firebase_user.display_name,
            photo_url=firebase_user.photo_url,
            disabled=firebase_user.disabled,
            custom_claims=firebase_user.custom_claims or {},
            provider_data=provider_data_list,
            created_at=int(firebase_user.user_metadata.creation_timestamp / 1000) if firebase_user.user_metadata else None,
            last_login_at=int(firebase_user.user_metadata.last_sign_in_timestamp / 1000) if firebase_user.user_metadata and firebase_user.user_metadata.last_sign_in_timestamp else None,
        )

    async def verify_token(self, token: str, request: Optional[Any] = None) -> FirebaseVerifiedToken:
        if not FirebaseAuthBackend._default_app:
            raise AuthException("Firebase Admin SDK no inicializado.")
        try:
            # El argumento check_revoked=True es importante para seguridad
            decoded_token = auth.verify_id_token(token, app=FirebaseAuthBackend._default_app, check_revoked=True)
            return decoded_token
        except auth.RevokedIdTokenError:
            raise InvalidTokenException("El token de ID ha sido revocado.")
        except auth.UserDisabledError:
            raise AccountDisabledException("La cuenta de usuario asociada con este token ha sido deshabilitada.")
        except auth.InvalidIdTokenError as e:
            raise InvalidTokenException(f"Token de ID inválido: {e}")
        except Exception as e:
            # Considerar loggear el error 'e' aquí
            raise AuthException(f"Error al verificar el token de Firebase: {e}")

    async def get_user_from_token(self, verified_token: FirebaseVerifiedToken) -> Optional[User]:
        if not FirebaseAuthBackend._default_app:
            raise AuthException("Firebase Admin SDK no inicializado.")
        uid = verified_token.get("uid")
        if not uid:
            raise InvalidTokenException("Token verificado no contiene UID.")
        return await self.get_user_by_id(uid)

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        if not FirebaseAuthBackend._default_app:
            raise AuthException("Firebase Admin SDK no inicializado.")
        try:
            firebase_user = auth.get_user(user_id, app=FirebaseAuthBackend._default_app)
            return await self._map_firebase_user_to_sdk_user(firebase_user)
        except auth.UserNotFoundError:
            return None
        except Exception as e:
            raise AuthException(f"Error al obtener usuario por ID de Firebase: {e}")

    async def get_user_by_email(self, email: EmailStr) -> Optional[User]:
        if not FirebaseAuthBackend._default_app:
            raise AuthException("Firebase Admin SDK no inicializado.")
        try:
            firebase_user = auth.get_user_by_email(email, app=FirebaseAuthBackend._default_app)
            return await self._map_firebase_user_to_sdk_user(firebase_user)
        except auth.UserNotFoundError:
            return None
        except Exception as e:
            raise AuthException(f"Error al obtener usuario por email de Firebase: {e}")

    async def create_user(
        self,
        email: Optional[EmailStr] = None,
        phone_number: Optional[str] = None,
        password: Optional[str] = None,
        display_name: Optional[str] = None,
        photo_url: Optional[HttpUrl] = None,
        email_verified: bool = False,
        disabled: bool = False,
        uid: Optional[str] = None,
        **kwargs: Any,
    ) -> User:
        if not FirebaseAuthBackend._default_app:
            raise AuthException("Firebase Admin SDK no inicializado.")
        try:
            create_kwargs = {k: v for k, v in kwargs.items() if v is not None}
            if email: create_kwargs['email'] = email
            if phone_number: create_kwargs['phone_number'] = phone_number
            if password: create_kwargs['password'] = password
            if display_name: create_kwargs['display_name'] = display_name
            if photo_url: create_kwargs['photo_url'] = str(photo_url) # Firebase SDK espera str
            if uid: create_kwargs['uid'] = uid
            create_kwargs['email_verified'] = email_verified
            create_kwargs['disabled'] = disabled
            
            firebase_user = auth.create_user(**create_kwargs, app=FirebaseAuthBackend._default_app)
            return await self._map_firebase_user_to_sdk_user(firebase_user)
        except Exception as e:
            raise AuthException(f"Error al crear usuario en Firebase: {e}")

    async def update_user(
        self,
        user_id: str,
        email: Optional[EmailStr] = None,
        phone_number: Optional[str] = None,
        password: Optional[str] = None,
        display_name: Optional[str] = None,
        photo_url: Optional[HttpUrl] = None,
        email_verified: Optional[bool] = None,
        disabled: Optional[bool] = None,
        custom_claims: Optional[Dict[str, Any]] = None, # Se maneja con set_custom_user_claims
        **kwargs: Any,
    ) -> User:
        if not FirebaseAuthBackend._default_app:
            raise AuthException("Firebase Admin SDK no inicializado.")
        try:
            update_kwargs = {k: v for k, v in kwargs.items() if v is not None}
            if email: update_kwargs['email'] = email
            if phone_number is not None: update_kwargs['phone_number'] = phone_number # Permitir borrar con None
            if password: update_kwargs['password'] = password
            if display_name is not None: update_kwargs['display_name'] = display_name
            if photo_url is not None: update_kwargs['photo_url'] = str(photo_url) # Permitir borrar con None o actualizar
            if email_verified is not None: update_kwargs['email_verified'] = email_verified
            if disabled is not None: update_kwargs['disabled'] = disabled

            firebase_user = auth.update_user(user_id, **update_kwargs, app=FirebaseAuthBackend._default_app)
            
            # Manejar custom_claims por separado si se proporcionan
            if custom_claims is not None:
                await self.set_custom_user_claims(user_id, custom_claims)
                # Recargar el usuario para obtener los claims actualizados si es necesario
                # o asumir que el cliente los manejará. Por simplicidad, no recargamos aquí.

            return await self._map_firebase_user_to_sdk_user(firebase_user)
        except auth.UserNotFoundError as e:
            raise UserNotFoundException("Usuario no encontrado para actualizar.") from e
        except Exception as e:
            raise AuthException(f"Error al actualizar usuario en Firebase: {e}")

    async def delete_user(self, user_id: str) -> None:
        if not FirebaseAuthBackend._default_app:
            raise AuthException("Firebase Admin SDK no inicializado.")
        try:
            auth.delete_user(user_id, app=FirebaseAuthBackend._default_app)
        except auth.UserNotFoundError as e:
            raise UserNotFoundException(f"Usuario con UID {user_id} no encontrado al intentar eliminar.") from e
        except Exception as e:
            raise AuthException(f"Error al eliminar usuario en Firebase: {e}")

    async def set_custom_user_claims(
        self, user_id: str, claims: Dict[str, Any]
    ) -> None:
        if not FirebaseAuthBackend._default_app:
            raise AuthException("Firebase Admin SDK no inicializado.")
        try:
            # Firebase espera que los claims no sean None. Si es None, pasamos un diccionario vacío.
            # Esto reemplazará todos los claims existentes del usuario.
            auth.set_custom_user_claims(user_id, claims if claims is not None else {}, app=FirebaseAuthBackend._default_app)
        except auth.UserNotFoundError as e:
            raise UserNotFoundException("Usuario no encontrado para establecer claims.") from e
        except Exception as e:
            raise AuthException(f"Error al establecer custom claims para el usuario {user_id} en Firebase: {e}")
