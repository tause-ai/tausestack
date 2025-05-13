# TauseStack Framework

![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

---

## 🚀 Resumen Ejecutivo

**Versión:** 0.1.0  
**Fecha:** 2025-05-12  
**Repositorio:** [github.com/felipetause/tausestack](https://github.com/felipetause/tausestack)  
**Documentación:** [docs.tause.co](https://docs.tause.co)  
**Contacto:** [felipe@tause.co](mailto:felipe@tause.co)

TauseStack es un **framework de desarrollo** modular y flexible diseñado para crear aplicaciones de cualquier tipo. A diferencia de una aplicación específica, TauseStack proporciona las abstracciones, interfaces y utilidades necesarias para construir soluciones personalizadas de forma rápida y mantenible.

- **Interfaces abstractas:** Define contratos claros para implementaciones concretas
- **Modularidad:** Componentes independientes pero integrables
- **CLI potente:** Automatiza tareas comunes de desarrollo
- **Extensibilidad:** Fácil de adaptar a necesidades específicas
- **Stack moderno:** FastAPI, Next.js, Docker, TypeScript
- **Calidad de código:** Linters, formateadores y pruebas automatizadas

## Componentes Principales

### Core
- **CLI:** Herramientas de línea de comandos para gestionar proyectos
- **Secrets:** Sistema seguro para gestionar credenciales
- **Utilidades:** Funciones y clases de ayuda comunes

### MCP (Multi-Call Protocol)
- **Interfaces:** Contratos para clientes y servidores MCP
- **Adaptadores:** Implementaciones para proveedores específicos
- **Mensajería:** Modelos estándar para comunicación

### Pasarelas de Pago
- **Interfaces:** Abstracciones para diferentes proveedores de pago
- **Adaptadores:** Implementaciones para pasarelas específicas
- **Transacciones:** Modelos estándar independientes del proveedor

---

**Autor:** [Felipe Tause](https://www.tause.co)  
**Contacto:** [felipe@tause.co](mailto:felipe@tause.co)  
**Documentación:** [docs.tause.co](https://docs.tause.co)  
**Versión:** 0.1.0

## Requisitos
- Docker y Docker Compose
- Python 3.11+
- Node.js 18+

## Instalación del CLI

Instala el CLI de TauseStack globalmente desde el directorio raíz del repositorio:

```bash
pip install .
```

Esto habilitará el comando global `tause` en tu terminal.

## Inicio rápido
Consulta la [Guía Rápida](docs/guides/quickstart.md) para empezar en minutos, o ejecuta:

```bash
tause init my-app --type website
cd my-app
tause dev
```

## Estructura del proyecto
Ver documentación en `/docs` y comentarios en cada carpeta.

## Licencia
Este proyecto está bajo la licencia MIT. Consulta el archivo [LICENSE](LICENSE) y la [documentación de licencia](docs/about/license.md) para más información.
