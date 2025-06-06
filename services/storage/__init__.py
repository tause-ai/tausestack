"""
Módulo de almacenamiento para TauseStack.
Provee interfaces y utilidades para guardar, leer y gestionar archivos en distintos backends.
"""

from .provider import StorageProvider, LocalStorageProvider
from .supabase_provider import SupabaseStorageProvider
