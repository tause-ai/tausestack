# Guía de Inicio Rápido de TauseStack

Esta guía te ayudará a dar tus primeros pasos con TauseStack, desde la instalación hasta la creación de tu primera aplicación funcional.

## Instalación

Para instalar TauseStack, sigue estos pasos:

```bash
# Clonar el repositorio
git clone https://github.com/tause-ai/tausestack.git
cd tausestack

# Instalar dependencias
pip install -e .
```

## Crear tu primera aplicación

La forma más rápida de empezar es creando una aplicación con FastAPI y Supabase:

```bash
# Crear un nuevo proyecto
tause init mi-primera-app --type fastapi-supabase
cd mi-primera-app
```

## Configurar Supabase

1. Crea una cuenta gratuita en [Supabase](https://supabase.com)
2. Crea un nuevo proyecto
3. Obtén la URL y la API key de Supabase
4. Configura estas credenciales en el archivo `.env`:

```
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu-api-key-publica-de-supabase
```

## Crear las tablas en Supabase

Ejecuta el siguiente SQL en el Editor SQL de Supabase:

```sql
-- Crear tablas principales
CREATE TABLE usuarios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    nombre TEXT NOT NULL,
    biografia TEXT,
    es_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE recursos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    titulo TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    usuario_id UUID NOT NULL REFERENCES auth.users(id),
    datos JSONB DEFAULT '{}',
    publico BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Configurar Row Level Security
ALTER TABLE usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE recursos ENABLE ROW LEVEL SECURITY;

-- Políticas para usuarios
CREATE POLICY "Cualquiera puede ver perfiles públicos" ON usuarios
    FOR SELECT USING (true);
CREATE POLICY "Solo propietarios pueden editar perfil" ON usuarios
    FOR UPDATE USING (auth.uid() = user_id);

-- Políticas para recursos
CREATE POLICY "Ver recursos públicos o propios" ON recursos
    FOR SELECT USING (publico = true OR auth.uid() = usuario_id);
CREATE POLICY "Editar solo recursos propios" ON recursos
    FOR ALL USING (auth.uid() = usuario_id);
```

## Iniciar la aplicación

```bash
# Ejecutar la aplicación
uvicorn app.main:app --reload
```

Accede a [http://localhost:8000/docs](http://localhost:8000/docs) para ver la documentación interactiva de la API.

## Probar la API

### 1. Registrar un usuario

```bash
curl -X POST http://localhost:8000/auth/registro \
  -H "Content-Type: application/json" \
  -d '{"email": "usuario@ejemplo.com", "password": "Contraseña123", "nombre": "Usuario Ejemplo"}'
```

### 2. Iniciar sesión para obtener un token

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "usuario@ejemplo.com", "password": "Contraseña123"}'
```

Guarda el `access_token` de la respuesta.

### 3. Crear un recurso

```bash
curl -X POST http://localhost:8000/recursos/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TU_ACCESS_TOKEN" \
  -d '{"titulo": "Mi primer recurso", "descripcion": "Descripción del recurso", "publico": true}'
```

### 4. Obtener recursos

```bash
curl -X GET http://localhost:8000/recursos/ \
  -H "Authorization: Bearer TU_ACCESS_TOKEN"
```

## Personalizar la aplicación

Para personalizar tu aplicación, puedes:

1. Modificar los modelos en `app/models.py`
2. Añadir nuevas rutas en `app/routes.py`
3. Actualizar la estructura de la base de datos en Supabase

## Próximos pasos

- Explora la [documentación técnica completa](./manual_tecnico.md)
- Mira los ejemplos en la carpeta `/examples`
- Aprende sobre el [generador de migraciones](../services/database/migrations/README.md)
- Implementa pruebas con las [herramientas de testing](../services/testing/README.md)

## Soporte

Si tienes problemas o preguntas, revisa:
- La documentación en la carpeta `/docs`
- Los ejemplos prácticos en `/examples`
- El código fuente de los servicios en `/services`
