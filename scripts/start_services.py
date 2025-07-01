#!/usr/bin/env python3
"""
Script para lanzar todos los servicios de TauseStack v0.6.0
"""

import subprocess
import time
import sys
import os
from pathlib import Path

# Configuración de servicios
SERVICES = [
    {
        "name": "Analytics Service",
        "port": 8001,
        "path": "services/analytics/api/main.py",
        "app": "services.analytics.api.main:app"
    },
    {
        "name": "Communications Service", 
        "port": 8002,
        "path": "services/communications/api/main.py",
        "app": "services.communications.api.main:app"
    },
    {
        "name": "Billing Service",
        "port": 8003,
        "path": "services/billing/api/main.py", 
        "app": "services.billing.api.main:app"
    },
    {
        "name": "MCP Server",
        "port": 8000,
        "path": "services/mcp_server_api.py",
        "app": "services.mcp_server_api:app"
    }
]

def check_service_exists(service_path):
    """Verificar si el archivo del servicio existe."""
    return Path(service_path).exists()

def start_service(service):
    """Iniciar un servicio específico."""
    print(f"🚀 Iniciando {service['name']} en puerto {service['port']}...")
    
    if not check_service_exists(service['path']):
        print(f"❌ Archivo no encontrado: {service['path']}")
        return None
    
    try:
        cmd = [
            "uvicorn",
            service['app'],
            "--host", "127.0.0.1",
            "--port", str(service['port']),
            "--reload"
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print(f"✅ {service['name']} iniciado (PID: {process.pid})")
        return process
        
    except Exception as e:
        print(f"❌ Error iniciando {service['name']}: {e}")
        return None

def start_api_gateway():
    """Iniciar el API Gateway."""
    print("🌐 Iniciando API Gateway en puerto 9000...")
    
    try:
        cmd = [
            "uvicorn",
            "services.simple_gateway:app",
            "--host", "127.0.0.1", 
            "--port", "9000",
            "--reload"
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print(f"✅ API Gateway iniciado (PID: {process.pid})")
        return process
        
    except Exception as e:
        print(f"❌ Error iniciando API Gateway: {e}")
        return None

def main():
    """Función principal."""
    print("🚀 TauseStack v0.6.0 - Iniciando todos los servicios")
    print("=" * 60)
    
    # Verificar que estamos en el directorio correcto
    if not Path("services").exists():
        print("❌ Error: Ejecutar desde el directorio raíz de TauseStack")
        sys.exit(1)
    
    processes = []
    
    # Iniciar servicios individuales
    for service in SERVICES:
        process = start_service(service)
        if process:
            processes.append((service['name'], process))
        time.sleep(2)  # Esperar entre servicios
    
    # Iniciar API Gateway
    gateway_process = start_api_gateway()
    if gateway_process:
        processes.append(("API Gateway", gateway_process))
    
    print("\n" + "=" * 60)
    print(f"✅ Servicios iniciados: {len(processes)}")
    
    for name, process in processes:
        print(f"   • {name}: PID {process.pid}")
    
    print("\n🌐 URLs disponibles:")
    print("   • API Gateway: http://localhost:9000")
    print("   • Gateway Docs: http://localhost:9000/docs")
    print("   • Analytics: http://localhost:8001")
    print("   • Communications: http://localhost:8002") 
    print("   • Billing: http://localhost:8003")
    print("   • MCP Server: http://localhost:8000")
    
    print("\n💡 Para el frontend:")
    print("   cd frontend && npm run dev")
    print("   Luego visita: http://localhost:3000")
    
    print("\n⚠️  Presiona Ctrl+C para detener todos los servicios")
    
    try:
        # Mantener el script corriendo
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo servicios...")
        for name, process in processes:
            try:
                process.terminate()
                print(f"   ✅ {name} detenido")
            except:
                print(f"   ❌ Error deteniendo {name}")
        print("✅ Todos los servicios detenidos")

if __name__ == "__main__":
    main() 