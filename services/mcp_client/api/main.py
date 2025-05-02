from fastapi import FastAPI
from services.mcp_client.api.v1 import router as v1_router

app = FastAPI(title="MCP Client Service", version="1.0.0")

# Registrar rutas versión 1
app.include_router(v1_router, prefix="/api/v1")
