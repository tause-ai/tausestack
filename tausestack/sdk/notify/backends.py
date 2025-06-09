# TauseStack SDK - Notify Module Backends
# Path: tausestack/sdk/notify/backends.py

from .base import AbstractNotifyBackend
from typing import Any, Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)


import os
import datetime
import re

def _sanitize_filename(name: str) -> str:
    """Sanitiza una cadena para que sea un nombre de archivo seguro."""
    replacements = {
        '<': '_', '>': '_', ':': '_', '"': '_',
        '/': '_', '\\': '_', '|': '_', '?': '_', '*': '_'
    }
    for char, replacement in replacements.items():
        name = name.replace(char, replacement)
    
    # Reemplazar secuencias de espacios en blanco con un solo guion bajo
    name = re.sub(r'\s+', '_', name)
    
    # Consolidar múltiples guiones bajos consecutivos que podrían resultar
    # de reemplazos adyacentes o de espacios junto a caracteres reemplazados.
    # Por ejemplo, "a:/b" -> "a__b" -> "a_b". O "a / b" -> "a___b" -> "a_b".
    name = re.sub(r'_+', '_', name)

    return name[:100] # Limitar longitud

class LocalFileNotifyBackend(AbstractNotifyBackend):
    """Backend de notificación que guarda los detalles del mensaje en un archivo local."""

    def __init__(self, base_path: str):
        self.base_path = base_path
        if not os.path.exists(self.base_path):
            try:
                os.makedirs(self.base_path, exist_ok=True)
                logger.info(f"Directorio de notificaciones creado: {self.base_path}")
            except OSError as e:
                logger.error(f"No se pudo crear el directorio de notificaciones {self.base_path}: {e}")
                raise

    def send(
        self,
        to: Union[str, List[str]],
        subject: str,
        body_text: Optional[str] = None,
        body_html: Optional[str] = None,
        **kwargs: Any
    ) -> bool:
        recipients = ", ".join(to) if isinstance(to, list) else to
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        sanitized_subject = _sanitize_filename(subject)
        
        file_extension = '.html' if body_html else '.txt'
        filename = f"{timestamp}_{sanitized_subject}{file_extension}"
        filepath = os.path.join(self.base_path, filename)

        content_to_write = f"To: {recipients}\n"
        content_to_write += f"Subject: {subject}\n"
        content_to_write += f"Date: {datetime.datetime.now().isoformat()}\n\n"

        if body_html:
            content_to_write += "--- Body (HTML) ---\n"
            content_to_write += body_html
        elif body_text:
            content_to_write += "--- Body (Text) ---\n"
            content_to_write += body_text
        else:
            content_to_write += "--- No Body Content ---"
        
        if kwargs:
            content_to_write += "\n\n--- Additional Options ---\n"
            for key, value in kwargs.items():
                content_to_write += f"{key}: {value}\n"

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content_to_write)
            logger.info(f"Notificación guardada en archivo: {filepath}")
            return True
        except IOError as e:
            logger.error(f"Error al escribir notificación en archivo {filepath}: {e}")
            return False

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
