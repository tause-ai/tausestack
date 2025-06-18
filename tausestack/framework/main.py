from fastapi import FastAPI, Request, HTTPException
from tausestack import sdk

app = FastAPI(
    title="TauseStack Framework",
    version="0.1.0",
    description="Esqueleto de la aplicación FastAPI para TauseStack."
)

@app.get("/", tags=["General"])
async def read_root():
    """Devuelve un mensaje de bienvenida para la ruta raíz."""
    return {"message": "TauseStack Framework Base"}

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
