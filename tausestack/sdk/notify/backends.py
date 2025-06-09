# TauseStack SDK - Notify Module Backends
# Path: tausestack/sdk/notify/backends.py

from .base import AbstractNotifyBackend
from typing import Any, Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)

class ConsoleNotifyBackend(AbstractNotifyBackend):
    """Backend de notificación que imprime los detalles del mensaje en la consola."""

    def send(
        self,
        to: Union[str, List[str]],
        subject: str,
        body_text: Optional[str] = None,
        body_html: Optional[str] = None,
        # attachments: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any
    ) -> bool:
        recipients = ", ".join(to) if isinstance(to, list) else to
        print("---- Nueva Notificación (Consola) ----")
        print(f"Para: {recipients}")
        print(f"Asunto: {subject}")
        if body_text:
            print("--- Cuerpo (Texto) ---")
            print(body_text)
        if body_html:
            print("--- Cuerpo (HTML) ---")
            print(body_html)
        # if attachments:
        #     print(f"Adjuntos: {len(attachments)} archivo(s)")
        if kwargs:
            print(f"Opciones adicionales: {kwargs}")
        print("--------------------------------------")
        logger.info(f"Notificación enviada a la consola para: {recipients}, Asunto: {subject}")
        return True
