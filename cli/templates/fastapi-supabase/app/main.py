"""
Aplicación FastAPI con integración de Supabase usando TauseStack.

Este archivo es parte del template generado automáticamente por el CLI de TauseStack.
"""

import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# Importaciones de TauseStack
from services.integrations.fastapi.supabase_fastapi import SupabaseFastAPI, SupabaseConfig
from services.auth.interfaces.auth_provider import UserIdentity
from services.database.interfaces.db_adapter import DatabaseAdapter

# Configurar aplicación
app = FastAPI(
    title="API TauseStack",
    description="API generada con TauseStack y Supabase",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, restringe a dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar Supabase
config = SupabaseConfig(
    supabase_url=os.environ.get("SUPABASE_URL", ""),
    supabase_key=os.environ.get("SUPABASE_KEY", ""),
    debug_mode=True
)

# Inicializar integración con Supabase
supabase = SupabaseFastAPI(app, config=config)

# Endpoint público
@app.get("/", tags=["General"])
async def root():
    """Endpoint raíz de la API."""
    return {
        "mensaje": "API TauseStack funcionando correctamente",
        "documentacion": "/docs",
        "health": "/health"
    }

# Endpoint de estado
@app.get("/health", tags=["General"])
async def health():
    """Endpoint para verificar el estado de la API."""
    return {
        "status": "ok",
        "version": "1.0.0"
    }

# Endpoint protegido por autenticación
@app.get("/me", tags=["Usuario"])
async def me(
    current_user: UserIdentity = Depends(supabase.get_current_user),
    db_adapter: DatabaseAdapter = Depends(supabase.get_db_adapter)
):
    """Obtiene información del usuario autenticado."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "autenticado": current_user.is_authenticated
    }

# Ejecutar la aplicación directamente con uvicorn si se llama como script
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
