"""
Generador de migraciones para Supabase.

Este módulo permite generar scripts SQL para crear y configurar tablas en Supabase
a partir de modelos Pydantic, incluyendo políticas de Row Level Security (RLS).
"""

from typing import List, Dict, Any, Type, Optional, Union
import inspect
import re
from pydantic import BaseModel, Field
from datetime import datetime, date
from uuid import UUID

# Mapeo de tipos Python a tipos PostgreSQL
TYPE_MAPPING = {
    str: "TEXT",
    int: "INTEGER",
    float: "DOUBLE PRECISION",
    bool: "BOOLEAN",
    datetime: "TIMESTAMP WITH TIME ZONE",
    date: "DATE",
    UUID: "UUID",
    dict: "JSONB",
    list: "JSONB",
    # Tipos específicos de Pydantic con Field
    "text": "TEXT",
    "varchar": "VARCHAR",
    "char": "CHAR",
    "integer": "INTEGER",
    "bigint": "BIGINT",
    "smallint": "SMALLINT",
    "uuid": "UUID",
    "json": "JSONB",
    "array": "JSONB"
}

class RLSPolicy:
    """
    Definición de una política de Row Level Security para Supabase.
    """
    
    def __init__(
        self,
        name: str,
        operation: str,  # "SELECT", "INSERT", "UPDATE", "DELETE", "ALL"
        using: Optional[str] = None,
        check: Optional[str] = None,
        table_name: Optional[str] = None,
    ):
        """
        Args:
            name: Nombre descriptivo de la política
            operation: Operación a la que aplica (SELECT, INSERT, etc.)
            using: Condición USING para SELECT, UPDATE, DELETE
            check: Condición WITH CHECK para INSERT, UPDATE
            table_name: Nombre de la tabla (se completa automáticamente)
        """
        self.name = name
        self.operation = operation.upper()
        self.using = using
        self.check = check
        self.table_name = table_name
    
    def to_sql(self) -> str:
        """Convierte la política a una declaración SQL."""
        if not self.table_name:
            raise ValueError("Se requiere el nombre de la tabla para generar SQL")
        
        sql = f"CREATE POLICY \"{self.name}\" ON {self.table_name}\n"
        sql += f"    FOR {self.operation}"
        
        if self.using:
            sql += f" USING ({self.using})"
        
        if self.check:
            sql += f" WITH CHECK ({self.check})"
        
        sql += ";"
        
        return sql


class Index:
    """
    Definición de un índice para una tabla PostgreSQL.
    """
    
    def __init__(
        self,
        name: Optional[str] = None,
        columns: List[str] = None,
        unique: bool = False,
        method: str = "btree",
        table_name: Optional[str] = None
    ):
        """
        Args:
            name: Nombre del índice (opcional, se genera automáticamente)
            columns: Lista de columnas para indexar
            unique: Si es un índice único
            method: Método de indexación (btree, gin, gist, etc.)
            table_name: Nombre de la tabla (se completa automáticamente)
        """
        self.name = name
        self.columns = columns or []
        self.unique = unique
        self.method = method
        self.table_name = table_name
    
    def to_sql(self) -> str:
        """Convierte el índice a una declaración SQL."""
        if not self.table_name:
            raise ValueError("Se requiere el nombre de la tabla para generar SQL")
        
        if not self.columns:
            raise ValueError("Se requiere al menos una columna para el índice")
        
        # Generar nombre si no se proporciona
        if not self.name:
            cols_str = "_".join(self.columns)
            self.name = f"idx_{self.table_name}_{cols_str}"
        
        unique_str = "UNIQUE " if self.unique else ""
        columns_str = ", ".join(self.columns)
        
        sql = f"CREATE {unique_str}INDEX {self.name} ON {self.table_name} "
        sql += f"USING {self.method} ({columns_str});"
        
        return sql


class TableDefinition:
    """
    Definición de una tabla PostgreSQL para Supabase.
    """
    
    def __init__(
        self,
        name: str,
        columns: Dict[str, Dict[str, Any]] = None,
        primary_key: Union[str, List[str]] = "id",
        foreign_keys: Dict[str, Dict[str, Any]] = None,
        indices: List[Index] = None,
        rls_policies: List[RLSPolicy] = None,
        enable_rls: bool = True,
        timestamps: bool = True,
        comment: Optional[str] = None
    ):
        """
        Args:
            name: Nombre de la tabla
            columns: Definición de columnas {nombre: {tipo, nullable, default, ...}}
            primary_key: Columna(s) de clave primaria
            foreign_keys: Definición de claves foráneas
            indices: Lista de índices
            rls_policies: Lista de políticas RLS
            enable_rls: Si se debe habilitar RLS
            timestamps: Si se deben incluir created_at y updated_at
            comment: Comentario para la tabla
        """
        self.name = name
        self.columns = columns or {}
        self.primary_key = primary_key
        self.foreign_keys = foreign_keys or {}
        self.indices = indices or []
        self.rls_policies = rls_policies or []
        self.enable_rls = enable_rls
        self.timestamps = timestamps
        self.comment = comment
        
        # Completar información en índices y políticas
        for index in self.indices:
            index.table_name = self.name
        
        for policy in self.rls_policies:
            policy.table_name = self.name
    
    def to_sql(self) -> str:
        """Genera el script SQL completo para la tabla."""
        sql = []
        
        # Crear la tabla
        sql.append(f"-- Tabla: {self.name}")
        if self.comment:
            sql.append(f"-- {self.comment}")
        
        sql.append(f"CREATE TABLE {self.name} (")
        
        # Columnas
        column_defs = []
        for name, props in self.columns.items():
            col_type = props.get("type", "TEXT")
            nullable = " NOT NULL" if not props.get("nullable", True) else ""
            default = f" DEFAULT {props.get('default')}" if "default" in props else ""
            unique = " UNIQUE" if props.get("unique", False) else ""
            comment = f" -- {props.get('comment')}" if "comment" in props else ""
            
            column_defs.append(f"    {name} {col_type}{nullable}{default}{unique}{comment}")
        
        # Añadir timestamps si se requieren
        if self.timestamps:
            column_defs.append("    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()")
            column_defs.append("    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()")
        
        # Definir clave primaria
        if isinstance(self.primary_key, list):
            pk_cols = ", ".join(self.primary_key)
            column_defs.append(f"    PRIMARY KEY ({pk_cols})")
        elif self.primary_key:
            column_defs.append(f"    PRIMARY KEY ({self.primary_key})")
        
        # Claves foráneas
        for col, fk in self.foreign_keys.items():
            ref_table = fk.get("references", "")
            ref_col = fk.get("column", "id")
            on_delete = fk.get("on_delete", "NO ACTION")
            on_update = fk.get("on_update", "NO ACTION")
            
            fk_def = f"    FOREIGN KEY ({col}) REFERENCES {ref_table}({ref_col})"
            if on_delete:
                fk_def += f" ON DELETE {on_delete}"
            if on_update:
                fk_def += f" ON UPDATE {on_update}"
            
            column_defs.append(fk_def)
        
        sql.append(",\n".join(column_defs))
        sql.append(");")
        
        # Comentario de la tabla si existe
        if self.comment:
            sql.append(f"COMMENT ON TABLE {self.name} IS '{self.comment}';")
        
        # Habilitar RLS si se requiere
        if self.enable_rls:
            sql.append(f"-- Habilitar Row Level Security (RLS)")
            sql.append(f"ALTER TABLE {self.name} ENABLE ROW LEVEL SECURITY;")
        
        # Crear índices
        if self.indices:
            sql.append("\n-- Índices")
            for index in self.indices:
                sql.append(index.to_sql())
        
        # Crear políticas RLS
        if self.rls_policies:
            sql.append("\n-- Políticas de Row Level Security")
            for policy in self.rls_policies:
                sql.append(policy.to_sql())
        
        # Crear trigger para updated_at si hay timestamps
        if self.timestamps:
            sql.append("\n-- Trigger para actualizar el campo updated_at automáticamente")
            sql.append(f"""
CREATE TRIGGER set_updated_at
BEFORE UPDATE ON {self.name}
FOR EACH ROW
EXECUTE FUNCTION update_modified_timestamp();
            """.strip())
        
        return "\n".join(sql)


class MigrationGenerator:
    """
    Genera scripts SQL de migración a partir de modelos Pydantic.
    """
    
    @staticmethod
    def get_table_name(model_class: Type[BaseModel]) -> str:
        """
        Obtiene el nombre de la tabla a partir de la clase del modelo.
        
        Args:
            model_class: Clase del modelo Pydantic.
            
        Returns:
            str: Nombre de la tabla.
        """
        # Buscar atributo explícito __tablename__
        if hasattr(model_class, "__tablename__"):
            return getattr(model_class, "__tablename__")
        
        # Convertir CamelCase a snake_case
        class_name = model_class.__name__
        snake_case = ''.join(['_'+c.lower() if c.isupper() else c for c in class_name]).lstrip('_')
        
        # Pluralizar (regla simple)
        if snake_case.endswith('y'):
            return snake_case[:-1] + 'ies'
        elif snake_case.endswith('s'):
            return snake_case
        else:
            return snake_case + 's'
    
    @staticmethod
    def get_column_type(field_type) -> str:
        """
        Mapea un tipo de Python/Pydantic a un tipo PostgreSQL.
        
        Args:
            field_type: Tipo de campo Python/Pydantic.
            
        Returns:
            str: Tipo PostgreSQL correspondiente.
        """
        # Resolver tipos genéricos (List[str], etc.)
        origin = getattr(field_type, "__origin__", None)
        if origin is not None:
            # Tipo para listas
            if origin == list:
                return "JSONB"
            # Tipo para diccionarios
            elif origin == dict:
                return "JSONB"
            # Tipo para Optional (Union[T, None])
            elif origin == Union:
                args = getattr(field_type, "__args__", [])
                # Si es Optional (Union con None)
                if type(None) in args:
                    # Tomar el otro tipo que no es None
                    other_type = next(arg for arg in args if arg is not type(None))
                    return MigrationGenerator.get_column_type(other_type)
        
        # Tipos básicos
        if field_type in TYPE_MAPPING:
            return TYPE_MAPPING[field_type]
        
        # Tipos no reconocidos, usar texto por defecto
        return "TEXT"
    
    @staticmethod
    def analyze_model(model_class: Type[BaseModel]) -> TableDefinition:
        """
        Analiza un modelo Pydantic y genera la definición de tabla correspondiente.
        
        Args:
            model_class: Clase del modelo Pydantic.
            
        Returns:
            TableDefinition: Definición de la tabla.
        """
        # Obtener nombre de la tabla
        table_name = MigrationGenerator.get_table_name(model_class)
        
        # Analizar campos del modelo
        columns = {}
        foreign_keys = {}
        
        for name, field in model_class.__annotations__.items():
            # Ignorar campos privados (que empiezan con _)
            if name.startswith('_'):
                continue
                
            # Buscar configuración adicional en Field() si existe
            field_info = model_class.__fields__[name].field_info if hasattr(model_class, "__fields__") else None
            field_default = model_class.__fields__[name].default if hasattr(model_class, "__fields__") else None
            
            # Determinar el tipo de columna
            column_type = MigrationGenerator.get_column_type(field)
            
            # Verificar si es una clave foránea por convención (termina en _id)
            is_foreign_key = name.endswith('_id') and not name == 'id'
            
            # Configuración básica de la columna
            column_def = {
                "type": column_type,
                "nullable": True,  # Por defecto todo es nullable
            }
            
            # Aplicar configuración desde Field si existe
            if field_info:
                # Restricción NOT NULL
                if getattr(field_info, "required", False):
                    column_def["nullable"] = False
                
                # Valor por defecto
                if field_default is not None and field_default != ...:
                    if isinstance(field_default, str):
                        column_def["default"] = f"'{field_default}'"
                    elif isinstance(field_default, bool):
                        column_def["default"] = str(field_default).lower()
                    else:
                        column_def["default"] = str(field_default)
                
                # Restricción UNIQUE
                if getattr(field_info, "unique", False):
                    column_def["unique"] = True
                
                # Comentario
                if getattr(field_info, "description", None):
                    column_def["comment"] = field_info.description
            
            # Configurar clave foránea si se detecta
            if is_foreign_key:
                # Detectar tabla referenciada (quitar _id y pluralizar)
                ref_name = name[:-3]  # quitar _id
                if ref_name == "user":
                    # Caso especial: user_id generalmente apunta a auth.users
                    foreign_keys[name] = {
                        "references": "auth.users",
                        "column": "id",
                        "on_delete": "CASCADE"
                    }
                else:
                    # Pluralizar para el nombre de tabla estándar
                    if ref_name.endswith('y'):
                        ref_table = ref_name[:-1] + 'ies'
                    elif ref_name.endswith('s'):
                        ref_table = ref_name
                    else:
                        ref_table = ref_name + 's'
                    
                    foreign_keys[name] = {
                        "references": ref_table,
                        "column": "id",
                        "on_delete": "CASCADE"
                    }
            
            # Añadir la columna
            columns[name] = column_def
        
        # Configurar políticas RLS estándar si hay un campo user_id
        rls_policies = []
        if "user_id" in columns:
            # Política para SELECT
            rls_policies.append(RLSPolicy(
                name="Usuarios pueden ver sus propios registros",
                operation="SELECT",
                using="auth.uid() = user_id"
            ))
            
            # Política para INSERT
            rls_policies.append(RLSPolicy(
                name="Usuarios pueden insertar sus propios registros",
                operation="INSERT",
                check="auth.uid() = user_id"
            ))
            
            # Política para UPDATE
            rls_policies.append(RLSPolicy(
                name="Usuarios pueden actualizar sus propios registros",
                operation="UPDATE",
                using="auth.uid() = user_id"
            ))
            
            # Política para DELETE
            rls_policies.append(RLSPolicy(
                name="Usuarios pueden eliminar sus propios registros",
                operation="DELETE",
                using="auth.uid() = user_id"
            ))
        
        # Crear índices estándar
        indices = []
        
        # Índice para user_id si existe
        if "user_id" in columns:
            indices.append(Index(
                columns=["user_id"]
            ))
        
        # Índice para campos de texto que parecen buscables
        for name, props in columns.items():
            if props.get("type") == "TEXT" and (
                "nombre" in name.lower() or 
                "title" in name.lower() or 
                "name" in name.lower() or 
                "descripcion" in name.lower() or
                "description" in name.lower()
            ):
                indices.append(Index(
                    columns=[name],
                    method="gin",
                    unique=False
                ))
        
        # Crear definición de tabla
        table_def = TableDefinition(
            name=table_name,
            columns=columns,
            primary_key="id",
            foreign_keys=foreign_keys,
            indices=indices,
            rls_policies=rls_policies,
            enable_rls=True,
            timestamps=True,
            comment=f"Generado automáticamente a partir del modelo {model_class.__name__}"
        )
        
        return table_def
    
    @staticmethod
    def generate_migration(models: List[Type[BaseModel]], with_helpers: bool = True) -> str:
        """
        Genera un script SQL de migración completo para una lista de modelos.
        
        Args:
            models: Lista de clases de modelos Pydantic.
            with_helpers: Si se deben incluir funciones auxiliares (como update_modified_timestamp).
            
        Returns:
            str: Script SQL completo para la migración.
        """
        sql = [
            "-- Script de migración generado automáticamente por Tausestack",
            f"-- Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ]
        
        # Añadir helpers si se solicita
        if with_helpers:
            sql.append("-- Funciones auxiliares")
            sql.append("""
-- Función para actualizar automáticamente el campo updated_at
CREATE OR REPLACE FUNCTION update_modified_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
            """.strip())
            sql.append("")
        
        # Generar SQL para cada modelo
        for model in models:
            table_def = MigrationGenerator.analyze_model(model)
            sql.append(table_def.to_sql())
            sql.append("")
        
        return "\n".join(sql)
    
    @staticmethod
    def generate_drop_script(models: List[Type[BaseModel]]) -> str:
        """
        Genera un script SQL para eliminar las tablas de los modelos.
        
        Args:
            models: Lista de clases de modelos Pydantic.
            
        Returns:
            str: Script SQL para eliminar las tablas.
        """
        sql = [
            "-- Script para eliminar tablas generado automáticamente",
            f"-- Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ]
        
        # Generar DROP TABLE para cada modelo (en orden inverso para respetar dependencias)
        for model in reversed(models):
            table_name = MigrationGenerator.get_table_name(model)
            sql.append(f"DROP TABLE IF EXISTS {table_name} CASCADE;")
        
        return "\n".join(sql)
