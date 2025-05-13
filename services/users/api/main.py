from fastapi import FastAPI
from services.users.api.v1 import router as v1_router
from services.users.api.v1_roles import router as v1_roles_router

app = FastAPI(title="User Management Service", version="1.0.0")

@app.get("/", tags=["root"])
def root():
    return {"message": "Bienvenido a User Management Service"}

@app.get("/health", tags=["root"])
def health():
    return {"status": "ok"}

# Registrar rutas versión 1
app.include_router(v1_router, prefix="/api/v1")
app.include_router(v1_roles_router, prefix="/api/v1")
