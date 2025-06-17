import os
from fastapi import FastAPI
from tausestack.framework.config import settings as tausestack_settings
from tausestack.framework.routing import load_routers_from_directory
# from app.core.config import my_app_settings # Descomentar si se usa config específica

APP_DIR = os.path.dirname(os.path.abspath(__file__))
APIS_DIR = os.path.join(APP_DIR, "apis")

app = FastAPI(
    title=getattr(my_app_settings if 'my_app_settings' in locals() else object(), 'APP_TITLE', tausestack_settings.APP_TITLE),
    version=getattr(my_app_settings if 'my_app_settings' in locals() else object(), 'APP_VERSION', tausestack_settings.APP_VERSION),
)

load_routers_from_directory(app, APIS_DIR)

@app.get("/")
async def root():
    return {"message": f"Bienvenido a {app.title} v{app.version}"}