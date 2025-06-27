# Changelog

Todos los cambios notables en este proyecto se documentarán en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2024-06-27

### FASE 3 COMPLETADA: Servicios Multi-Tenant Avanzados
- **NUEVO**: Analytics Service Multi-Tenant con dashboards por tenant
- **NUEVO**: Communications Service Multi-Tenant (Email, SMS, Push)
- **NUEVO**: Billing Service Multi-Tenant con automatización completa
- **NUEVO**: Integración de servicios multi-tenant avanzada
- **NUEVO**: Demo integral de todos los servicios funcionando juntos

### Añadido
- Analytics Service con métricas aisladas por tenant
- Communications Service con templates y proveedores por tenant
- Billing Service con suscripciones y facturación automatizada
- Health checks avanzados para todos los servicios
- Configuración granular por tenant en cada servicio
- Storage aislado para cada servicio por tenant
- Rate limiting específico por tenant y servicio
- Estadísticas detalladas por tenant

### Mejorado
- Arquitectura multi-tenant de clase enterprise (~90% completada)
- Aislamiento completo entre tenants en todos los servicios
- Configuración centralizada para servicios multi-tenant
- Documentación completa de la arquitectura implementada
- Demos standalone que no requieren dependencias externas

### Técnico
- 3 servicios multi-tenant completamente funcionales
- 4 demos integrales implementadas
- Progreso del proyecto: 65% → 90% hacia arquitectura objetivo
- Compatibilidad 100% hacia atrás mantenida
- Testing robusto para todos los servicios

## [0.4.1] - 2024-06-24

### Optimización y Limpieza
- **LIMPIEZA MASIVA**: Eliminación de 800MB de archivos innecesarios (-44% tamaño total)
- Eliminados directorios duplicados: `ui/` (345MB), `venv/` (451MB), `payments_and_billing/`, `cli/` obsoleto
- Eliminados archivos temporales: `*.db`, `*.tmp`, `.DS_Store`, cache directories
- Eliminado directorio `shared/` vacío y `cli_test_area/` de pruebas
- Actualizado `.gitignore` con patrones completos para prevenir archivos innecesarios

### Mejorado
- Estructura del proyecto optimizada sin duplicaciones
- Rendimiento mejorado en builds y deployments
- Mantenibilidad del código aumentada
- Claridad en la organización de archivos

### Eliminado
- 21 archivos duplicados o innecesarios
- CLI obsoleto (mantenido el moderno en `tausestack/cli/`)
- Directorios de cache y temporales
- Implementación duplicada de Wompi payments (consolidada en SDK)

## [0.4.0] - 2024-06-23

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

## [0.3.0] - 2024-05-20

### Mejorado
- Pruebas de integración para orquestación multiagente
- Soporte mejorado para autenticación JWT
- Documentación actualizada

## [0.2.0] - 2024-05-15

### Añadido
- Soporte inicial para MCP (Model-Controller-Presenter)
- Federación básica entre MCPs
- Documentación de la API

## [0.1.0] - 2024-04-29

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
