# My_new_app_module_test_env

Un nuevo proyecto generado con TauseStack.

## Para empezar

1.  Crea y activa un entorno virtual:
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```
2.  Instala las dependencias:
    ```bash
    pip install -r requirements.txt # O pip install -e . si usas hatch
    ```
3.  Configura tus variables de entorno en `.env` (copia de `.env.example`).
4.  Ejecuta la aplicación:
    ```bash
    uvicorn app.main:app --reload
    ```