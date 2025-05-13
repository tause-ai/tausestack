# API con FastAPI y Supabase

Este proyecto fue generado con el CLI de TauseStack. Proporciona una API RESTful con autenticación y base de datos utilizando FastAPI y Supabase.

## Características

- 🔐 **Autenticación completa** con Supabase
- 📊 **Base de datos PostgreSQL** a través de Supabase
- 🚀 **API RESTful** con FastAPI
- 📝 **Documentación interactiva** con Swagger/OpenAPI
- 🧪 **Herramientas de testing** incluidas

## Configuración

### 1. Requisitos

- Python 3.8+
- Una cuenta de Supabase (gratis en [supabase.com](https://supabase.com))

### 2. Variables de entorno

Crea un archivo `.env` en la raíz del proyecto con el siguiente contenido:

```
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu-anon-key-de-supabase
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar la base de datos

1. Crea un proyecto en Supabase
2. Ejecuta el siguiente SQL en el Editor SQL de Supabase:

```sql
-- Crear tablas
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

-- Configurar RLS (Row Level Security)
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

## Ejecución

### Modo desarrollo

```bash
uvicorn app.main:app --reload
```

Visita [http://localhost:8000/docs](http://localhost:8000/docs) para ver la documentación interactiva.

### Despliegue con Docker

```bash
docker build -t api-tausestack .
docker run -p 8000:8000 api-tausestack
```

## Estructura del proyecto

```
.
├── app/
│   ├── __init__.py
│   ├── main.py          # Punto de entrada de la aplicación
│   ├── models.py        # Modelos de datos (Pydantic)
│   └── routes.py        # Definición de rutas API
├── services/            # Framework TauseStack
├── Dockerfile
├── README.md
└── requirements.txt
```

## Autenticación

La API utiliza autenticación con tokens JWT a través de Supabase. Para autenticarte:

1. Registra un usuario en `/auth/registro`
2. Inicia sesión en `/auth/login` para obtener un token
3. Usa el token en el header `Authorization: Bearer {token}`

## Testing

Para ejecutar las pruebas:

```bash
pytest
```

## Próximos pasos

- Personaliza los modelos de datos según tus necesidades
- Añade más endpoints y lógica de negocio
- Configura políticas RLS adicionales en Supabase
- Implementa un frontend (sugerencia: Next.js o SvelteKit)

## Ayuda y soporte

Para más información sobre TauseStack, visita [documentación oficial]().
