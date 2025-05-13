#!/bin/bash

# Script de instalación para TauseStack
# Este script instala TauseStack y todas sus dependencias

echo "=== Instalador de TauseStack ==="
echo "Iniciando instalación..."

# Verificar que Python esté instalado
if ! command -v python3 &>/dev/null; then
    echo "Error: Python 3 no está instalado. Por favor, instálalo antes de continuar."
    exit 1
fi

# Crear entorno virtual
echo "Creando entorno virtual..."
python3 -m venv .venv
source .venv/bin/activate

# Actualizar pip
echo "Actualizando pip..."
pip install --upgrade pip

# Instalar TauseStack en modo desarrollo
echo "Instalando TauseStack..."
pip install -e .

# Verificar la instalación
echo "Verificando instalación..."
if command -v tause &>/dev/null; then
    echo "¡TauseStack se ha instalado correctamente!"
    echo "Para activar el entorno virtual en el futuro, ejecuta:"
    echo "source .venv/bin/activate"
    echo ""
    echo "Para crear un nuevo proyecto:"
    echo "tause init mi-proyecto --type fastapi-supabase"
else
    echo "Error: La instalación parece haber fallado."
    echo "Por favor, verifica los errores anteriores e intenta nuevamente."
    exit 1
fi

# Mostrar información adicional
echo ""
echo "=== Información Adicional ==="
echo "Documentación: ./docs/manual_tecnico.md"
echo "Guía de inicio rápido: ./docs/guia_inicio_rapido.md"
echo "Ejemplos: ./examples/"
echo ""
echo "¡Gracias por usar TauseStack!"
