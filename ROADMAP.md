# Roadmap del Framework TauseStack

Este documento rastrea el progreso del desarrollo del framework TauseStack, diseñado para igualar y superar la funcionalidad de la plataforma anterior construida en Databutton.

## Objetivo 1: Un Sólido Núcleo de Framework (Backend)

- [ ] **Tarea 1.1: Formalizar la Base de FastAPI.**
  - [ ] Definir una estructura de proyecto estándar para aplicaciones TauseStack (ej. `app/`, `main.py`, configuración centralizada).
  - [ ] Establecer patrones para la gestión de dependencias y configuración (ej. Pydantic para settings).
- [ ] **Tarea 1.2: Sistema de Ruteo Dinámico y Configurable.**
  - [ ] Implementar un cargador de rutas dinámico que escanee un directorio específico (ej. `app/routes/` o `app/apis/`).
  - [ ] Desarrollar un decorador (ej. `@tausestack.router(auth_required=True, tags=["mi_tag"])`) para que los `APIRouter` definan sus metadatos y requisitos de autenticación.
- [ ] **Tarea 1.3: Middleware de Autenticación Central.**
  - [ ] Crear un middleware FastAPI que se integre con `sdk.auth`.
  - [ ] Permitir la protección de rutas basada en la configuración del decorador del router o por defecto.

## Objetivo 2: SDK de TauseStack Potenciado

- [ ] **Tarea 2.1: Re-alcance del Módulo `sdk.auth` (Prioridad Máxima).**
  - [ ] **Sub-Tarea 2.1.1: Interfaz `AbstractAuthBackend`.**
    - [ ] Definir métodos para: verificar token, obtener usuario por UID, crear usuario, actualizar usuario, gestionar claims/roles.
  - [ ] **Sub-Tarea 2.1.2: Implementación `FirebaseAuthBackend`.**
    - [ ] Integración con `firebase-admin`.
    - [ ] Implementar todos los métodos de `AbstractAuthBackend`.
    - [ ] Manejo seguro de credenciales de servicio Firebase (vía `sdk.secrets` o variables de entorno).
  - [ ] **Sub-Tarea 2.1.3: Dependencia FastAPI `get_current_user`.**
    - [ ] Crear una dependencia FastAPI (ej. `current_user: User = Depends(sdk.auth.get_current_user)`) que utilice el backend configurado para autenticar y devolver el usuario.
    - [ ] Definir un modelo Pydantic `User` para la información del usuario autenticado.
  - [x] **Sub-Tarea 2.1.4: Pruebas Unitarias Exhaustivas.**
  - [x] **Sub-Tarea 2.1.5: Documentación del Módulo `auth`.**
- [ ] **Tarea 2.2: Creación del Módulo `sdk.database`.**
  - [ ] **Sub-Tarea 2.2.1: Interfaz `AbstractDatabaseBackend`.**
    - [ ] Definir operaciones CRUD básicas, gestión de transacciones, ejecución de consultas raw.
  - [ ] **Sub-Tarea 2.2.2: Implementación `SQLAlchemyBackend`.**
    - [ ] Integración con SQLAlchemy Core y ORM.
    - [ ] Soporte para migraciones (ej. con Alembic).
    - [ ] Configuración de la URL de la base de datos (vía `sdk.secrets` o variables de entorno).
  - [ ] **Sub-Tarea 2.2.3 (Alternativa/Adicional): Implementación `SupabaseBackend`.**
    - [ ] Integración con el cliente Python de Supabase.
  - [ ] **Sub-Tarea 2.2.4: Pruebas Unitarias.**
  - [ ] **Sub-Tarea 2.2.5: Documentación del Módulo `database`.**
- [ ] **Tarea 2.3: Expansión del Módulo `sdk.storage`.**
  - [ ] **Sub-Tarea 2.3.1: Soporte para Almacenamiento de Archivos Binarios.**
    - [ ] API: `sdk.storage.binary.put(key, file_object)`, `sdk.storage.binary.get(key) -> file_object`, `sdk.storage.binary.delete(key)`.
    - [ ] Actualizar `S3StorageBackend` y `LocalStorageBackend` para soportar binarios.
  - [ ] **Sub-Tarea 2.3.2: Soporte para Almacenamiento de DataFrames.**
    - [ ] API: `sdk.storage.dataframe.put(key, df)`, `sdk.storage.dataframe.get(key) -> pd.DataFrame`, `sdk.storage.dataframe.delete(key)`.
    - [ ] Usar Parquet como formato de serialización por defecto.
    - [ ] Actualizar backends.
  - [ ] **Sub-Tarea 2.3.3: Pruebas Unitarias para Nuevas Funcionalidades.**
  - [ ] **Sub-Tarea 2.3.4: Documentación Actualizada del Módulo `storage`.**

## Objetivo 3: Experiencia de Desarrollador (DX) y Herramientas

- [ ] **Tarea 3.1: Crear un TauseStack CLI.**
  - [ ] **Sub-Tarea 3.1.1: Comando `tausestack init`.**
    - [ ] Generar estructura de proyecto base (con `main.py`, `app/`, `ROADMAP.md`, etc.).
    - [ ] Configurar `pyproject.toml` con dependencias TauseStack.
  - [ ] **Sub-Tarea 3.1.2: Comando `tausestack run`.**
    - [ ] Iniciar el servidor de desarrollo FastAPI (uvicorn).
  - [ ] **Sub-Tarea 3.1.3: Comando `tausestack deploy` (Futuro).**
    - [ ] Integración con herramientas de despliegue (ej. Serverless Framework, Docker + ECS/Fargate).
- [ ] **Tarea 3.2: Documentación y Ejemplos Completos.**
  - [ ] Crear un proyecto de ejemplo completo (ej. una API de IA simple) que demuestre el uso de todos los componentes del framework y el SDK.
  - [ ] Mejorar la documentación en `README.md` de cada módulo del SDK y del framework general.

## Módulos del SDK Ya Implementados (Base)

- **`sdk.storage` (JSON):** Completado (S3, Local).
- **`sdk.secrets`:** Completado (AWS Secrets Manager, Env Vars).
- **`sdk.cache`:** Completado (Memory, Disk, Redis).
- **`sdk.notify`:** Completado (SES, Local File, Console).
