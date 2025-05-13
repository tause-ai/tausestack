"""
CLI para generación de migraciones SQL para Supabase.

Este módulo proporciona una interfaz de línea de comandos para generar
scripts SQL de migración a partir de modelos Pydantic.
"""

import argparse
import os
import sys
import importlib.util
import inspect
from typing import List, Type, Dict, Any
from pydantic import BaseModel

from services.database.migrations.generator import MigrationGenerator

def find_models_in_module(module, base_class=BaseModel) -> List[Type[BaseModel]]:
    """
    Encuentra todas las clases de modelo en un módulo que heredan de base_class.
    
    Args:
        module: Módulo Python a analizar
        base_class: Clase base que deben heredar los modelos (por defecto BaseModel)
        
    Returns:
        List[Type[BaseModel]]: Lista de clases de modelos
    """
    models = []
    
    for name, obj in inspect.getmembers(module):
        # Verificar si es una clase, no es la clase base y hereda de la clase base
        if (
            inspect.isclass(obj) and 
            obj != base_class and 
            issubclass(obj, base_class) and
            obj.__module__ == module.__name__  # Solo clases definidas en este módulo
        ):
            models.append(obj)
    
    return models

def load_module_from_path(path: str):
    """
    Carga un módulo Python desde una ruta de archivo.
    
    Args:
        path: Ruta al archivo Python
        
    Returns:
        Módulo cargado o None si hay error
    """
    try:
        module_name = os.path.basename(path).replace('.py', '')
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        print(f"Error al cargar el módulo {path}: {e}")
        return None

def main():
    """Función principal del CLI."""
    parser = argparse.ArgumentParser(
        description="Generador de migraciones SQL para Supabase a partir de modelos Pydantic"
    )
    
    parser.add_argument(
        "archivo_modelos",
        help="Ruta al archivo Python que contiene los modelos Pydantic"
    )
    
    parser.add_argument(
        "-o", "--output",
        help="Archivo de salida (por defecto stdout)",
        default=None
    )
    
    parser.add_argument(
        "--drop",
        help="Generar script para eliminar tablas",
        action="store_true"
    )
    
    parser.add_argument(
        "--no-helpers",
        help="No incluir funciones auxiliares en el script SQL",
        action="store_true"
    )
    
    args = parser.parse_args()
    
    # Verificar que el archivo existe
    if not os.path.exists(args.archivo_modelos):
        print(f"Error: El archivo {args.archivo_modelos} no existe")
        sys.exit(1)
    
    # Cargar módulo
    module = load_module_from_path(args.archivo_modelos)
    if not module:
        sys.exit(1)
    
    # Encontrar modelos
    models = find_models_in_module(module)
    
    if not models:
        print(f"No se encontraron modelos Pydantic en {args.archivo_modelos}")
        sys.exit(1)
    
    print(f"Se encontraron {len(models)} modelos: {', '.join(m.__name__ for m in models)}")
    
    # Generar script SQL
    if args.drop:
        sql = MigrationGenerator.generate_drop_script(models)
    else:
        sql = MigrationGenerator.generate_migration(models, not args.no_helpers)
    
    # Escribir resultado
    if args.output:
        with open(args.output, 'w') as f:
            f.write(sql)
        print(f"Script SQL generado en {args.output}")
    else:
        print("\n--- SCRIPT SQL ---\n")
        print(sql)

if __name__ == "__main__":
    main()
