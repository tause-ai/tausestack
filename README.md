# TauseStack

![Version](https://img.shields.io/badge/version-0.5.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

---

## 🚀 Resumen Ejecutivo

**Versión:** 0.5.0  
**Fecha:** 2024-06-27  
**Repositorio:** [github.com/felipetause/tausestack](https://github.com/felipetause/tausestack)  
**Documentación:** [docs.tause.co](https://docs.tause.co)  
**Contacto:** [felipe@tause.co](mailto:felipe@tause.co)

TauseStack es un framework modular y flexible diseñado para acelerar el desarrollo de aplicaciones web, CRMs, e-commerce, chatbots y agentes IA. Construido con tecnologías modernas y siguiendo las mejores prácticas de la industria, proporciona una base sólida para proyectos de cualquier escala.

- **SDK Completo:** Autenticación, storage, database, cache, notificaciones
- **CLI potente:** Automatiza tareas comunes de desarrollo y despliegue
- **Templates preconstruidos:** Para distintos tipos de aplicaciones
- **Stack moderno:** FastAPI, Next.js, Docker, TypeScript
- **Arquitectura limpia:** Patrones hexagonales y backends intercambiables
- **Calidad de código:** Linters, formateadores y pruebas automatizadas
- **Documentación completa:** Para desarrolladores y usuarios finales

## 🎯 Características Principales

### SDK Modular
- **Auth:** Firebase Admin, backends personalizables
- **Storage:** Local, S3, GCS, Supabase con soporte JSON/Binary/DataFrame
- **Database:** SQLAlchemy con migraciones Alembic
- **Cache:** Memory, Disk, Redis
- **Notificaciones:** Console, File, SES
- **Secrets:** Variables de entorno, AWS Secrets Manager

---

**Autor:** [Felipe Tause](https://www.tause.co)  
**Contacto:** [felipe@tause.co](mailto:felipe@tause.co)  
**Documentación:** [docs.tause.co](https://docs.tause.co)  
**Versión:** 0.5.0

## Requisitos
- Docker y Docker Compose
- Python 3.11+
- Node.js 18+

## Instalación del CLI

Para usar el TauseStack CLI, se recomienda instalar el paquete `tausestack` dentro de un entorno virtual.

1.  **Crea y activa un entorno virtual** (si aún no tienes uno para tu proyecto o para usar el CLI globalmente):
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # En macOS/Linux
    # .\.venv\Scripts\activate # En Windows
    ```

2.  **Instala TauseStack**:
    *   **Para desarrollo del framework (desde el clon del repositorio `tausestack`):**
        ```bash
        pip install -e .[dev]
        ```
        Esto instala el paquete en modo editable, junto con todas las dependencias necesarias para el desarrollo del framework (como `pytest`, linters, etc.). El comando `tausestack` estará disponible si tu entorno virtual está activo.
    *   **Como dependencia en tu proyecto (cuando esté disponible en PyPI):**
        ```bash
        pip install tausestack
        ```

Una vez instalado y con el entorno virtual activo, el comando `tausestack` estará disponible en tu terminal.

## Inicio Rápido con el CLI

Una vez que el [CLI de TauseStack esté instalado](#instalación-del-cli) y tu entorno virtual activado:

1.  **Crea un nuevo proyecto TauseStack:**
    ```bash
    tausestack init project mi-nuevo-proyecto
    ```
    Por defecto, este comando también inicializará un repositorio Git. Para omitir este paso, usa la opción `--no-git`:
    ```bash
    tausestack init project mi-nuevo-proyecto --no-git
    ```
    Esto generará una estructura de proyecto base en un nuevo directorio llamado `mi-nuevo-proyecto`.

    Por defecto, también se creará un archivo `.env` a partir de `.env.example`. Puedes omitir la creación del archivo `.env` con la opción `--no-env`:
    ```bash
    tausestack init project mi-proyecto-sin-env --no-env
    ```

2.  **Navega al directorio de tu proyecto:**
    ```bash
    cd mi-nueva-app
    ```

3.  **Configura tu entorno:**
    *   Si no lo hiciste antes, crea y activa un entorno virtual específico para este proyecto.
    *   Instala las dependencias del proyecto (que incluirán `tausestack` y `fastapi`):
        ```bash
        pip install -e .
        ```
    *   Copia `.env.example` a `.env` y configura las variables necesarias.

4.  **Ejecuta la aplicación:**
    Puedes iniciar el servidor de desarrollo directamente con Uvicorn:
    ```bash
    uvicorn app.main:app --reload
    ```
    O, de forma más conveniente, usando el comando del CLI de TauseStack:
    ```bash
    tausestack run dev
    ```
    Esto iniciará el servidor Uvicorn con recarga automática activada por defecto. Puedes personalizar el host y el puerto:
    ```bash
    tausestack run dev --host 0.0.0.0 --port 8080
    ```
    Para ver todas las opciones, ejecuta:
    ```bash
    tausestack run dev --help
    ```

5.  **Despliega tu aplicación (placeholder):**
    El CLI incluye un comando de despliegue que actualmente sirve como guía.
    ```bash
    tausestack deploy target production
    ```
    Este comando verificará tu proyecto y te dará sugerencias sobre los siguientes pasos para el despliegue. La integración con plataformas específicas (AWS, Google Cloud, etc.) se añadirá en futuras versiones.

    Si tu proyecto contiene un `Dockerfile`, puedes usar la opción `--build` para construir automáticamente la imagen Docker antes del despliegue (simulado):
    ```bash
    tausestack deploy target staging --build
    ```
    Esto intentará ejecutar `docker build -t <nombre-proyecto>:<entorno> .`.

Consulta `PROJECT_STRUCTURE.md` para más detalles sobre la estructura generada.

## 📁 Estructura del Proyecto

```
tausestack/
├── cli/                 # Command Line Interface
├── framework/           # Core framework components
├── sdk/                 # Software Development Kit
│   ├── auth/           # Authentication backends
│   ├── cache/          # Caching systems
│   ├── database/       # Database adapters
│   ├── gateways/       # Payment gateways (Wompi, etc.)
│   ├── notify/         # Notification systems
│   ├── secrets/        # Secret management
│   └── storage/        # Storage backends
├── templates/          # Project templates
├── services/           # Microservices
└── tests/             # Test suite
```

### Uso del SDK

```python
from tausestack.sdk.storage.main import StorageManager
from tausestack.sdk.auth.main import AuthManager
from tausestack.sdk.cache.main import CacheManager

# Storage con múltiples backends
storage = StorageManager()
storage.put_json("user/123", {"name": "John", "email": "john@example.com"})
storage.put_binary("files/image.jpg", image_bytes)

# También puedes acceder a clientes específicos
user_data = storage.json.get("user/123")
file_data = storage.binary.get("files/image.jpg")

# Autenticación
auth = AuthManager()
user = await auth.verify_token(token)

# Cache
cache = CacheManager()
await cache.set("key", "value", ttl=3600)
```

Ver documentación completa en `/docs` y `ESTRUCTURA_RECOMENDADA.md`.

## Licencia
Este proyecto está bajo la licencia MIT. Consulta el archivo [LICENSE](LICENSE) y la [documentación de licencia](docs/about/license.md) para más información.
