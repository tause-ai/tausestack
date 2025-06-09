# TauseStack SDK - Notify Module Main Logic
# Path: tausestack/sdk/notify/main.py

from typing import Any, Dict, List, Optional, Union
import os
import logging

from .base import AbstractNotifyBackend
from .backends import ConsoleNotifyBackend
# Importar otros backends aquí cuando se implementen
# from .exceptions import NotifyError, BackendNotConfiguredError

logger = logging.getLogger(__name__)

_notify_backend_instances: Dict[str, AbstractNotifyBackend] = {}

DEFAULT_NOTIFY_BACKEND = 'console'
# DEFAULT_NOTIFY_BACKEND_CONFIG: Dict[str, Dict[str, Any]] = {
#     'console': {},
#     'local_file': {'base_path': './.tausestack_notifications'},
#     'ses': {},
#     'smtp': {'host': '', 'port': 587, 'username': '', 'password': '', 'use_tls': True}
# }

def _get_notify_backend(backend_name: Optional[str] = None, config: Optional[Dict[str, Any]] = None) -> AbstractNotifyBackend:
    effective_backend_name = backend_name or os.getenv('TAUSESTACK_NOTIFY_BACKEND', DEFAULT_NOTIFY_BACKEND)
    # config_to_use = config or DEFAULT_NOTIFY_BACKEND_CONFIG.get(effective_backend_name, {})

    # Por ahora, solo instanciamos Console sin configuraciones complejas
    instance_key = effective_backend_name 

    if instance_key not in _notify_backend_instances:
        logger.debug(f"Creando nueva instancia para backend de notificación: {instance_key}")
        if effective_backend_name == 'console':
            _notify_backend_instances[instance_key] = ConsoleNotifyBackend()
        # elif effective_backend_name == 'local_file':
        #     from .backends import LocalFileNotifyBackend # Importación tardía
        #     _notify_backend_instances[instance_key] = LocalFileNotifyBackend(**config_to_use)
        # elif effective_backend_name == 'ses':
        #     # Lógica para SES
        #     pass
        # elif effective_backend_name == 'smtp':
        #     # Lógica para SMTP
        #     pass
        else:
            # raise BackendNotConfiguredError(f"Backend de notificación '{effective_backend_name}' no reconocido o no implementado.")
            logger.error(f"Backend de notificación '{effective_backend_name}' no reconocido o no implementado. Usando ConsoleBackend por defecto.")
            _notify_backend_instances[instance_key] = ConsoleNotifyBackend() # Fallback a consola
    
    return _notify_backend_instances[instance_key]

def send_email(
    to: Union[str, List[str]],
    subject: str,
    body_text: Optional[str] = None,
    body_html: Optional[str] = None,
    # attachments: Optional[List[Dict[str, Any]]] = None,
    backend: Optional[str] = None,
    backend_config: Optional[Dict[str, Any]] = None,
    **kwargs: Any
) -> bool:
    """Envía un correo electrónico utilizando el backend de notificación configurado.

    Args:
        to: Destinatario o lista de destinatarios del correo.
        subject: Asunto del correo.
        body_text: Cuerpo del correo en formato de texto plano.
        body_html: Cuerpo del correo en formato HTML.
        # attachments: Lista de adjuntos. Cada adjunto es un dict con 'filename' y 'content'.
        backend: Nombre del backend a utilizar (e.g., 'console', 'ses', 'smtp').
                 Si es None, usa el backend por defecto.
        backend_config: Configuración específica para el backend seleccionado.
        **kwargs: Argumentos adicionales para pasar al método send del backend.

    Returns:
        True si el correo fue enviado exitosamente, False en caso contrario.
    """
    if not body_text and not body_html:
        logger.warning("Se intentó enviar un correo sin body_text ni body_html.")
        # raise ValueError("Se debe proporcionar al menos body_text o body_html.")
        return False

    try:
        selected_backend = _get_notify_backend(backend_name=backend, config=backend_config)
        return selected_backend.send(
            to=to,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            # attachments=attachments,
            **kwargs
        )
    except Exception as e:
        logger.error(f"Error al enviar notificación: {e}", exc_info=True)
        # raise NotifyError(f"Error al enviar notificación: {e}") from e
        return False

