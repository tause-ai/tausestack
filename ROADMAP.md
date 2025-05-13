# Roadmap Tausestack: Framework para desarrollo modular

Este documento centraliza el control de avance, prioridades y próximos pasos. La visión de Tausestack es crear un framework/toolkit para desarrollar aplicaciones modulares, no una plataforma específica.

---

## 1. Framework Core
- [x] CLI y scaffolding de proyectos
- [x] Gestión de secrets
- [x] Modularidad plug-and-play
- [x] Sistema de autenticación abstracto y extensible
  - [x] Interfaz `AuthProvider` 
  - [x] Proveedor JWT básico (`JWTAuthProvider`)
  - [x] Integración con Supabase (`SupabaseAuthProvider`)
- [x] Manejo de permisos y roles (multiempresa)

## 2. Librerías y Abstracciones
- [x] Estructura base de módulos
- [x] Interfaces abstractas para integraciones MCP (cliente y servidor)
    - [x] Cliente MCP (unificado en `interfaces/mcp_client.py`)
    - [x] Servidor MCP (`interfaces/mcp_server.py`)
    - [x] Modelos de mensajería (`interfaces/mcp_message.py`)
    - [x] Documentación de patrones de uso (README)
- [x] Interfaces abstractas para pasarelas de pago
    - [x] Clase base `PaymentGateway` (en `interfaces/payment_gateway.py`)
    - [x] Adaptador de ejemplo Wompi (`adapters/wompi/client.py`)
    - [x] Documentación de patrones de integración (README)
- [x] Interfaces abstractas para bases de datos
    - [x] Clase base `DatabaseAdapter` (en `interfaces/db_adapter.py`)
    - [x] Adaptador para Supabase (`adapters/supabase/client.py`)
    - [x] Documentación de patrones de uso (README)

## 3. Herramientas de Desarrollo
- [x] Generadores de código y plantillas
    - [x] Generador de migraciones SQL para Supabase
    - [x] CLI para convertir modelos Pydantic a SQL
- [ ] Testing helpers
- [ ] Herramientas de depuración
- [x] Utilidades para migraciones y upgrades
    - [x] Generación de políticas RLS para Supabase
    - [x] Generación de índices optimizados

## 4. Documentación
- [x] README principal del framework
- [x] Documentación de componentes MCP
- [x] Documentación de componentes de Pagos
- [x] Documentación de componentes de Base de datos
- [ ] Guías de arquitectura completas
- [ ] Tutoriales paso a paso
- [ ] Documentación técnica de API

## 5. Ejemplos y Templates
- [x] Estructura de directorio de ejemplos
- [x] Cliente MCP personalizado de ejemplo
- [x] Adaptador de pasarela Wompi de ejemplo
- [x] Aplicación CRUD con autenticación Supabase
- [ ] Aplicación SaaS modular de ejemplo
    - [ ] Panel de administración
    - [ ] Marketplace de módulos
    - [ ] Integración MCP funcional
    - [ ] Integración de pagos funcional
- [ ] Biolinks (ejemplo de módulo)
- [ ] Landing Pages (ejemplo de módulo)
- [ ] Automatización WhatsApp/Email (ejemplo de módulo)

## 6. QA y DevOps
- [ ] Tests unitarios del framework
- [ ] Tests de integración
- [ ] CI/CD para el framework
- [ ] Herramientas de debugging

---

**Notas y próximos pasos:**
* Probar la implementación en proyectos reales
* Desarrollar ejemplos más completos de aplicaciones basadas en Tausestack
* Implementar más módulos específicos (Biolinks, Landing Pages)
* Crear un marketplace de módulos funcional

### Versión 0.2.0 (Mayo 2025)
* Integración completa con Supabase para autenticación y base de datos
* Generador de migraciones SQL funcional
* Herramientas de testing para todos los componentes
* Template FastAPI-Supabase listo para usar
* Documentación técnica completa

### Prioridades altas (Fase actual)
- **Sistema de autenticación abstracto**: Desarrollar interfaces para auth que permita diferentes estrategias de autenticación.
- **Testing helpers**: Crear utilidades para facilitar pruebas de adaptadores MCP y pasarelas.
- **Tutoriales paso a paso**: Documentar flujos completos para implementar nuevos adaptadores.

### Prioridades medias
- **Herramientas de desarrollo**: Desarrollar generadores de código y plantillas.
- **Ejemplos de aplicación**: Crear una pequeña aplicación de ejemplo que use múltiples componentes del framework.

### Notas importantes
- El framework debe mantenerse modular y extensible.
- Todos los componentes deben tener interfaces bien definidas.
- La documentación debe actualizarse al mismo tiempo que el código.
