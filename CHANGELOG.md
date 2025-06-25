# Changelog

Todos los cambios notables en este proyecto se documentarán en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2025-01-01

### Refactorización Mayor
- **BREAKING CHANGE**: Consolidación completa de la arquitectura del SDK
- Eliminadas duplicaciones de funcionalidad (auth, storage, secrets)
- Estructura simplificada con un solo punto de implementación por funcionalidad
- Nueva clase `StorageManager` como interfaz unificada para storage

### Añadido
- `StorageManager`: Interfaz unificada para JSON, binary y DataFrame storage
- Validación de seguridad en claves de storage (prevención de path traversal)
- Soporte para GCS (Google Cloud Storage) en storage backends
- Soporte para Supabase Storage en storage backends
- Documentación completa del módulo storage (`tausestack/sdk/storage/README.md`)
- 69 tests adicionales para validar la refactorización

### Mejorado
- Arquitectura hexagonal limpia sin duplicaciones
- Validación robusta de claves con regex `^[a-zA-Z0-9._/-]+$`
- Manejo de errores mejorado en todos los backends de storage
- Documentación actualizada del README principal
- Estructura de proyecto más mantenible

### Eliminado
- Directorios duplicados: `core/modules/`, `services/storage/`, `services/secrets/`
- Código legacy de auth y users en core/modules
- Implementaciones redundantes de storage y secrets
- Directorio `testing_and_quality/` redundante

### Técnico
- 202 tests del SDK pasando correctamente
- Migración completa de funcionalidades valiosas al SDK
- Consolidación de serializers en `tausestack/sdk/storage/serializers.py`
- Backends de storage con validación consistente

## [0.3.0] - 2025-05-20

### Mejorado
- Pruebas de integración para orquestación multiagente
- Soporte mejorado para autenticación JWT
- Documentación actualizada

## [0.2.0] - 2025-05-15

### Añadido
- Soporte inicial para MCP (Model-Controller-Presenter)
- Federación básica entre MCPs
- Documentación de la API

## [0.1.0] - 2025-04-29

### Añadido
- Estructura básica del framework
- CLI con comandos esenciales (init, dev, test, format, lint)
- Módulos base: auth y users
- Sistema de configuración por entornos
- Frontend con Next.js y TypeScript estricto
- Linters y formateadores (Black, Ruff, ESLint, Prettier)
- Hooks de pre-commit
- Documentación inicial

## Autor
Felipe Tause (https://www.tause.co)
