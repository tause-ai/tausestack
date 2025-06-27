from fastapi import FastAPI, Request, HTTPException
from tausestack import sdk
from tausestack.framework.middleware.tenant_resolver import add_tenant_middlewares

app = FastAPI(
    title="TauseStack Framework",
    version="0.1.0",
    description="Multi-tenant FastAPI application for TauseStack."
)

# Add tenant middlewares
add_tenant_middlewares(app)

@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint for load balancer."""
    return {"status": "healthy", "service": "tausestack"}

@app.get("/", tags=["General"])
async def read_root(request: Request):
    """Devuelve un mensaje de bienvenida basado en el tenant."""
    tenant_id = getattr(request.state, 'tenant_id', 'unknown')
    host = request.headers.get("host", "unknown")
    
    # Different responses based on subdomain
    if tenant_id == "landing":
        return {
            "message": "¡Bienvenido a TauseStack!",
            "description": "Plataforma multi-tenant para aplicaciones modernas",
            "host": host
        }
    elif tenant_id == "api_service":
        return {
            "message": "TauseStack API",
            "version": "1.0.0",
            "endpoints": ["/health", "/docs", "/openapi.json"]
        }
    elif tenant_id == "admin_panel":
        return {
            "message": "TauseStack Admin Panel",
            "tenant": tenant_id,
            "host": host
        }
    elif tenant_id == "documentation":
        return {
            "message": "TauseStack Documentation",
            "version": "1.0.0"
        }
    else:
        return {
            "message": f"¡Bienvenido a TauseStack!",
            "tenant": tenant_id,
            "host": host
        }

@app.post("/test-storage/{key}")
async def test_put_storage(key: str, request: Request):
    try:
        data = await request.json()
        sdk.storage.json.put(key, data)
        return {"message": f"Datos guardados en la clave '{key}' correctamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test-storage/{key}")
async def test_get_storage(key: str):
    try:
        data = sdk.storage.json.get(key)
        if data is None:
            raise HTTPException(status_code=404, detail=f"No se encontraron datos para la clave '{key}'.")
        return data
    except HTTPException:
        raise # Re-raise HTTPException para que FastAPI la maneje
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test-secret/{secret_name}")
async def test_get_secret(secret_name: str):
    try:
        secret_value = sdk.secrets.get(secret_name)
        if secret_value is None:
            raise HTTPException(status_code=404, detail=f"No se encontró el secreto '{secret_name}'.")
        return {"secret_name": secret_name, "value": secret_value}
    except HTTPException:
        raise # Re-raise HTTPException para que FastAPI la maneje
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Para ejecutar la aplicación localmente (opcional, si no se usa el CLI):
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
