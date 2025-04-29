# Guía de contribución

¡Gracias por tu interés en contribuir a TauseStack! Este documento proporciona las directrices para contribuir al proyecto de manera efectiva.

## Proceso de contribución

1. **Fork y clone**: Haz un fork del repositorio y clónalo localmente.
2. **Rama**: Crea una rama para tu contribución con un nombre descriptivo.
   ```bash
   git checkout -b feature/nombre-descriptivo
   ```
3. **Desarrollo**: Implementa tus cambios siguiendo las convenciones del proyecto.
4. **Tests**: Asegúrate de añadir tests para cualquier nueva funcionalidad.
5. **Pull Request**: Envía un PR con una descripción clara de los cambios y su propósito.

## Reglas básicas

- Sigue la guía de estilo y convenciones del proyecto.
- Ejecuta linters y formateadores antes de cada commit.
- Añade tests para nuevas funcionalidades.
- Documenta tus módulos y cambios.
- Mantén un historial de commits limpio y con mensajes descriptivos.

## Pre-commit hooks
Se recomienda instalar los hooks de pre-commit:
```bash
pre-commit install
```
Para frontend, los hooks de Husky ya están configurados y se activarán automáticamente.

## Convenciones de código
### Backend (Python)
- Seguimos PEP 8 con algunas modificaciones definidas en los archivos de configuración.
- Usamos Black para formateo automático.
- Validamos con Ruff para linting avanzado.
- Todas las funciones y clases deben tener docstrings descriptivos.

### Frontend (TypeScript/React)
- Seguimos las convenciones de ESLint y Prettier configuradas.
- Usamos TypeScript estricto para todos los componentes y funciones.
- Preferimos componentes funcionales y hooks sobre componentes de clase.
- Los componentes deben estar en archivos separados con nombres descriptivos.

## Estructura de los módulos
Cada módulo debe seguir la estructura estándar:
```
module_name/
├── api/              # Endpoints API
├── models/           # Modelos de datos
├── services/         # Lógica de negocio
├── schemas/          # Esquemas Pydantic
├── tests/            # Tests
├── migrations/       # Migraciones específicas
├── config.py         # Configuración del módulo
└── README.md         # Documentación del módulo
```

## Documentación
Cada módulo debe tener su propio README.md con:
- Descripción del propósito del módulo
- Instrucciones de uso
- Dependencias específicas (si las hay)
- Ejemplos básicos

Para cambios en APIs públicas, actualiza la documentación correspondiente en `/docs`.

## Tests
- Los tests unitarios deben estar en la carpeta `tests/` de cada módulo.
- Los tests de integración deben incluirse cuando se añadan nuevas integraciones entre módulos.
- Ejecuta todos los tests antes de enviar un PR:
```bash
tause test
```

## Versionado
Seguimos Semantic Versioning:
- **MAJOR**: Cambios incompatibles con versiones anteriores
- **MINOR**: Funcionalidades nuevas compatibles con versiones anteriores
- **PATCH**: Correcciones de errores compatibles con versiones anteriores

## Proceso de revisión
- Cada PR será revisado por al menos un mantenedor del proyecto.
- Los comentarios de revisión deben ser abordados antes de la fusión.
- CI/CD debe pasar en todos los PRs antes de considerar su fusión.

## Reportando problemas
Si encuentras un error o tienes una sugerencia, por favor abre un issue usando las plantillas proporcionadas, incluyendo:
- Descripción clara del problema o sugerencia
- Pasos para reproducir (si es un error)
- Entorno (sistema operativo, versiones relevantes)
- Capturas de pantalla o logs si es posible

¡Gracias por contribuir a TauseStack y ayudarnos a hacerlo mejor!
