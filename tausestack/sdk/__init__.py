import logging

# Configure base logger for the SDK
# This prevents "No handlers could be found" warnings if the using application
# does not configure logging. It's up to the application to add handlers if it
# wants to see SDK logs.
_sdk_logger = logging.getLogger(__name__) # __name__ will be 'tausestack.sdk'
if not _sdk_logger.hasHandlers():
    _sdk_logger.addHandler(logging.NullHandler())

# TauseStack SDK

# Import and expose sub-modules or specific clients

# Option 1: Allow direct import of clients if preferred
# from .storage import json_client as storage_json_client # Example alias

# Option 2: Create namespace objects similar to Databutton
# This makes it usable like: from tausestack import sdk; sdk.storage.json.put(...)

class StorageNamespace:
    def __init__(self):
        from .storage import json_client as json_storage_client
        self.json = json_storage_client
        # In the future, you can add other storage types here:
        # from .storage import text_client
        # self.text = text_client

storage = StorageNamespace()

class SecretsNamespace:
    def __init__(self):
        from .secrets import get_secret as _get_secret
        # Expose get_secret directly as a method of the namespace instance
        self.get = _get_secret

secrets = SecretsNamespace()

class NotifyNamespace:
    def __init__(self):
        from .notify import send_email as _send_email
        self.email = _send_email # Permite sdk.notify.email(...)
        # Podríamos hacer self.send = _send_email si queremos sdk.notify.send(...)
        # Pero sdk.notify.email.send(...) es más explícito si tenemos otros tipos de notificaciones.
        # Por ahora, como solo es email, sdk.notify.email(...) es conciso.

notify = NotifyNamespace()

__all__ = [
    'storage',
    'secrets',
    'notify',
]
