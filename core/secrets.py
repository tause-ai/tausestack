import os
from pathlib import Path
from dotenv import load_dotenv, set_key

SECRETS_FILE = Path(__file__).parent.parent / ".env"

# Cargar variables de entorno desde .env
load_dotenv(dotenv_path=SECRETS_FILE, override=True)

def get_secret(key: str, default=None):
    """Obtiene el valor de un secret (variable de entorno o .env)."""
    return os.getenv(key, default)


def set_secret(key: str, value: str):
    """Guarda o actualiza un secret en el archivo .env."""
    set_key(str(SECRETS_FILE), key, value)


def list_secrets():
    """Lista todos los secrets definidos en el archivo .env."""
    if not SECRETS_FILE.exists():
        return {}
    with open(SECRETS_FILE) as f:
        lines = f.readlines()
    secrets = {}
    for line in lines:
        if line.strip() and not line.startswith('#') and '=' in line:
            k, v = line.strip().split('=', 1)
            secrets[k] = v
    return secrets
