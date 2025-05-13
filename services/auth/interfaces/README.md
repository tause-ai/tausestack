# Interfaces de Autenticación y Autorización

Este directorio contiene las interfaces abstractas para implementar sistemas de autenticación y autorización en aplicaciones Tausestack.

## Interfaces Principales

### AuthProvider

La interfaz `AuthProvider` define el contrato que deben implementar todos los proveedores de autenticación, independientemente del mecanismo específico (JWT, OAuth, API Keys, etc.).

```python
from services.auth.interfaces.auth_provider import AuthProvider, UserIdentity

class MiProveedorAuth(AuthProvider):
    # Implementar métodos abstractos aquí
```

Métodos principales:
- `initialize`: Inicializa el proveedor con configuración
- `authenticate`: Autentica un usuario con credenciales
- `validate_token`: Valida un token y devuelve la identidad
- `generate_token`: Genera un token para un usuario
- `refresh_token`: Refresca un token expirado
- `revoke_token`: Revoca un token activo

### PermissionManager

La interfaz `PermissionManager` define el contrato para gestores de permisos y roles.

```python
from services.auth.interfaces.permissions import PermissionManager, Permission, Role

class MiGestorPermisos(PermissionManager):
    # Implementar métodos abstractos aquí
```

Métodos principales:
- `create_permission`: Crea un nuevo permiso
- `get_permission`: Obtiene un permiso por ID
- `list_permissions`: Lista permisos disponibles
- `create_role`: Crea un nuevo rol
- `get_role`: Obtiene un rol por ID
- `assign_role_to_user`: Asigna un rol a un usuario
- `check_permission`: Verifica si un usuario tiene un permiso

## Modelos Estándar

### UserIdentity

Modelo que representa a un usuario autenticado, independiente del mecanismo de autenticación:

```python
from services.auth.interfaces.auth_provider import UserIdentity

# Crear una identidad
user = UserIdentity(
    id="123",
    username="usuario",
    email="usuario@ejemplo.com",
    roles=["admin"],
    is_authenticated=True
)

# Verificar validez
if user.is_valid:
    # Usuario válido y no expirado
    pass
```

### Permission y Role

Modelos para representar permisos y roles en el sistema:

```python
from services.auth.interfaces.permissions import Permission, Role

# Crear un permiso
permiso = Permission(
    id="1",
    name="Ver usuarios",
    resource="usuarios",
    action="leer"
)

# Crear un rol con permisos
rol = Role(
    id="1",
    name="Administrador",
    permissions=[permiso]
)
```

## Recomendaciones de Implementación

1. **Seguridad**: Usa prácticas seguras para manejo de tokens y credenciales
2. **Stateless**: Prefiere métodos stateless cuando sea posible
3. **Expiración**: Implementa expiración y renovación de tokens
4. **Tests**: Prueba los escenarios de seguridad críticos

## Ejemplos de Adaptadores

Consulta `/services/auth/adapters/` para ver ejemplos de implementaciones concretas:

- JWT (implementado)
- Supabase (implementado)
- OAuth2 (pendiente)
- API Keys (pendiente)

### Adaptador Supabase

```python
from services.auth.adapters.supabase_provider import SupabaseAuthProvider

# Inicializar adaptador
auth_provider = SupabaseAuthProvider()
await auth_provider.initialize({
    "supabase_url": "https://tu-proyecto.supabase.co",
    "supabase_key": "tu-api-key-publica-de-supabase"
})

# Autenticar usuario
identity = await auth_provider.authenticate({
    "auth_type": "password",
    "email": "usuario@ejemplo.com",
    "password": "contraseña123"
})

# También soporta magic link, OAuth y teléfono
identity = await auth_provider.authenticate({
    "auth_type": "magic_link",
    "email": "usuario@ejemplo.com"
})
```
