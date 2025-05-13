-- Script de migración generado automáticamente por Tausestack
-- Fecha: 2025-05-12 21:52:00

-- Funciones auxiliares
-- Función para actualizar automáticamente el campo updated_at
CREATE OR REPLACE FUNCTION update_modified_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Tabla: perfiles
-- Generado automáticamente a partir del modelo Perfil
CREATE TABLE perfiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL, -- ID del usuario en auth.users
    nombre TEXT NOT NULL, -- Nombre completo
    biografia TEXT, -- Biografía del usuario
    foto_url TEXT, -- URL de la foto de perfil
    verificado BOOLEAN DEFAULT false, -- Si el perfil está verificado
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE
);
COMMENT ON TABLE perfiles IS 'Generado automáticamente a partir del modelo Perfil';

-- Habilitar Row Level Security (RLS)
ALTER TABLE perfiles ENABLE ROW LEVEL SECURITY;

-- Índices
CREATE INDEX idx_perfiles_user_id ON perfiles USING btree (user_id);
CREATE INDEX idx_perfiles_nombre ON perfiles USING gin (nombre);

-- Políticas de Row Level Security
CREATE POLICY "Usuarios pueden ver sus propios registros" ON perfiles
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Usuarios pueden insertar sus propios registros" ON perfiles
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Usuarios pueden actualizar sus propios registros" ON perfiles
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Usuarios pueden eliminar sus propios registros" ON perfiles
    FOR DELETE USING (auth.uid() = user_id);

-- Trigger para actualizar el campo updated_at automáticamente
CREATE TRIGGER set_updated_at
BEFORE UPDATE ON perfiles
FOR EACH ROW
EXECUTE FUNCTION update_modified_timestamp();

-- Tabla: categorias
-- Generado automáticamente a partir del modelo Categoria
CREATE TABLE categorias (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre TEXT NOT NULL UNIQUE, -- Nombre de la categoría
    descripcion TEXT, -- Descripción de la categoría
    icono TEXT, -- Nombre del icono
    color TEXT DEFAULT '#3B82F6', -- Color en formato hexadecimal
    orden INTEGER DEFAULT 0, -- Orden de visualización
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
COMMENT ON TABLE categorias IS 'Generado automáticamente a partir del modelo Categoria';

-- Habilitar Row Level Security (RLS)
ALTER TABLE categorias ENABLE ROW LEVEL SECURITY;

-- Índices
CREATE INDEX idx_categorias_nombre ON categorias USING gin (nombre);
CREATE INDEX idx_categorias_descripcion ON categorias USING gin (descripcion);

-- Políticas de Row Level Security
CREATE POLICY "Todos pueden ver categorías" ON categorias
    FOR SELECT USING (true);
CREATE POLICY "Solo administradores pueden modificar categorías" ON categorias
    FOR ALL USING (auth.uid() IN (SELECT user_id FROM perfiles WHERE rol = 'admin'));

-- Trigger para actualizar el campo updated_at automáticamente
CREATE TRIGGER set_updated_at
BEFORE UPDATE ON categorias
FOR EACH ROW
EXECUTE FUNCTION update_modified_timestamp();

-- Tabla: proyectos
-- Generado automáticamente a partir del modelo Proyecto
CREATE TABLE proyectos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    titulo TEXT NOT NULL, -- Título del proyecto
    descripcion TEXT NOT NULL, -- Descripción del proyecto
    contenido JSONB DEFAULT '{}', -- Contenido JSON del proyecto
    usuario_id UUID NOT NULL, -- ID del usuario propietario
    categoria_id UUID, -- ID de la categoría
    publico BOOLEAN DEFAULT false, -- Si el proyecto es público
    destacado BOOLEAN DEFAULT false, -- Si el proyecto está destacado
    metadatos JSONB DEFAULT '{}', -- Metadatos adicionales
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    FOREIGN KEY (usuario_id) REFERENCES auth.users(id) ON DELETE CASCADE,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE SET NULL
);
COMMENT ON TABLE proyectos IS 'Generado automáticamente a partir del modelo Proyecto';

-- Habilitar Row Level Security (RLS)
ALTER TABLE proyectos ENABLE ROW LEVEL SECURITY;

-- Índices
CREATE INDEX idx_proyectos_usuario_id ON proyectos USING btree (usuario_id);
CREATE INDEX idx_proyectos_categoria_id ON proyectos USING btree (categoria_id);
CREATE INDEX idx_proyectos_titulo ON proyectos USING gin (titulo);
CREATE INDEX idx_proyectos_descripcion ON proyectos USING gin (descripcion);

-- Políticas de Row Level Security
CREATE POLICY "Los administradores pueden ver todos los proyectos" ON proyectos
    FOR SELECT USING (auth.uid() IN (SELECT user_id FROM perfiles WHERE rol = 'admin'));
CREATE POLICY "Usuarios pueden ver proyectos públicos o propios" ON proyectos
    FOR SELECT USING (publico = true OR auth.uid() = usuario_id);
CREATE POLICY "Usuarios pueden insertar sus propios proyectos" ON proyectos
    FOR INSERT WITH CHECK (auth.uid() = usuario_id);
CREATE POLICY "Usuarios pueden actualizar sus propios proyectos" ON proyectos
    FOR UPDATE USING (auth.uid() = usuario_id);
CREATE POLICY "Usuarios pueden eliminar sus propios proyectos" ON proyectos
    FOR DELETE USING (auth.uid() = usuario_id);

-- Trigger para actualizar el campo updated_at automáticamente
CREATE TRIGGER set_updated_at
BEFORE UPDATE ON proyectos
FOR EACH ROW
EXECUTE FUNCTION update_modified_timestamp();

-- Tabla: colaboraciones
-- Generado automáticamente a partir del modelo Colaboracion
CREATE TABLE colaboraciones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    proyecto_id UUID NOT NULL, -- ID del proyecto
    usuario_id UUID NOT NULL, -- ID del usuario colaborador
    rol TEXT DEFAULT 'editor', -- Rol del colaborador (viewer, editor, admin)
    invitado_por UUID NOT NULL, -- ID del usuario que invitó
    aceptada BOOLEAN DEFAULT false, -- Si la invitación fue aceptada
    fecha_invitacion TIMESTAMP WITH TIME ZONE DEFAULT now(), -- Fecha de invitación
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES auth.users(id) ON DELETE CASCADE,
    FOREIGN KEY (invitado_por) REFERENCES auth.users(id) ON DELETE CASCADE
);
COMMENT ON TABLE colaboraciones IS 'Generado automáticamente a partir del modelo Colaboracion';

-- Habilitar Row Level Security (RLS)
ALTER TABLE colaboraciones ENABLE ROW LEVEL SECURITY;

-- Índices
CREATE UNIQUE INDEX idx_colaboraciones_proyecto_id_usuario_id ON colaboraciones USING btree (proyecto_id, usuario_id);
CREATE INDEX idx_colaboraciones_usuario_id ON colaboraciones USING btree (usuario_id);
CREATE INDEX idx_colaboraciones_proyecto_id ON colaboraciones USING btree (proyecto_id);

-- Políticas de Row Level Security
CREATE POLICY "Usuarios pueden ver colaboraciones de sus proyectos" ON colaboraciones
    FOR SELECT USING (
        auth.uid() = usuario_id OR 
        auth.uid() IN (SELECT usuario_id FROM proyectos WHERE id = proyecto_id)
    );
CREATE POLICY "Propietarios de proyectos pueden insertar colaboraciones" ON colaboraciones
    FOR INSERT WITH CHECK (
        auth.uid() = (SELECT usuario_id FROM proyectos WHERE id = proyecto_id)
    );
CREATE POLICY "Colaboradores pueden actualizar su estado de aceptación" ON colaboraciones
    FOR UPDATE USING (
        (auth.uid() = usuario_id AND NEW.aceptada != OLD.aceptada) OR
        auth.uid() = (SELECT usuario_id FROM proyectos WHERE id = proyecto_id)
    );
CREATE POLICY "Propietarios del proyecto pueden eliminar colaboraciones" ON colaboraciones
    FOR DELETE USING (
        auth.uid() = (SELECT usuario_id FROM proyectos WHERE id = proyecto_id)
    );

-- Trigger para actualizar el campo updated_at automáticamente
CREATE TRIGGER set_updated_at
BEFORE UPDATE ON colaboraciones
FOR EACH ROW
EXECUTE FUNCTION update_modified_timestamp();

-- Tabla: comentarios
-- Generado automáticamente a partir del modelo Comentario
CREATE TABLE comentarios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    proyecto_id UUID NOT NULL, -- ID del proyecto comentado
    usuario_id UUID NOT NULL, -- ID del usuario que comenta
    contenido TEXT NOT NULL, -- Texto del comentario
    respuesta_a_id UUID, -- ID del comentario al que responde
    editado BOOLEAN DEFAULT false, -- Si el comentario fue editado
    FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES auth.users(id) ON DELETE CASCADE,
    FOREIGN KEY (respuesta_a_id) REFERENCES comentarios(id) ON DELETE SET NULL
);
COMMENT ON TABLE comentarios IS 'Generado automáticamente a partir del modelo Comentario';

-- Habilitar Row Level Security (RLS)
ALTER TABLE comentarios ENABLE ROW LEVEL SECURITY;

-- Índices
CREATE INDEX idx_comentarios_proyecto_id ON comentarios USING btree (proyecto_id);
CREATE INDEX idx_comentarios_usuario_id ON comentarios USING btree (usuario_id);
CREATE INDEX idx_comentarios_respuesta_a_id ON comentarios USING btree (respuesta_a_id);
CREATE INDEX idx_comentarios_contenido ON comentarios USING gin (contenido);

-- Políticas de Row Level Security
CREATE POLICY "Usuarios pueden ver comentarios en proyectos públicos o propios" ON comentarios
    FOR SELECT USING (
        proyecto_id IN (
            SELECT id FROM proyectos WHERE 
                publico = true OR 
                usuario_id = auth.uid() OR
                id IN (SELECT proyecto_id FROM colaboraciones WHERE usuario_id = auth.uid() AND aceptada = true)
        )
    );
CREATE POLICY "Usuarios pueden insertar comentarios en proyectos a los que tienen acceso" ON comentarios
    FOR INSERT WITH CHECK (
        proyecto_id IN (
            SELECT id FROM proyectos WHERE 
                publico = true OR 
                usuario_id = auth.uid() OR
                id IN (SELECT proyecto_id FROM colaboraciones WHERE usuario_id = auth.uid() AND aceptada = true)
        )
    );
CREATE POLICY "Usuarios pueden editar sus propios comentarios" ON comentarios
    FOR UPDATE USING (auth.uid() = usuario_id);
CREATE POLICY "Usuarios pueden eliminar sus propios comentarios" ON comentarios
    FOR DELETE USING (auth.uid() = usuario_id);
CREATE POLICY "Propietarios del proyecto pueden eliminar cualquier comentario" ON comentarios
    FOR DELETE USING (
        auth.uid() = (SELECT usuario_id FROM proyectos WHERE id = proyecto_id)
    );
