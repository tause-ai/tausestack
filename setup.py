from setuptools import setup, find_packages

setup(
    name="tausestack",
    version="0.2.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        # Dependencias base
        "typer>=0.15.0",
        "click>=8.0.0",
        "uvicorn>=0.22.0",
        "fastapi>=0.95.1",
        # Autenticación
        "python-jose[cryptography]>=3.3.0",
        "passlib[bcrypt]>=1.7.4",
        # Supabase
        "httpx>=0.24.0",
        "supabase>=2.4.0",
        # Validación de datos
        "pydantic[email]>=1.10.7,<2.0.0",
        # Herramientas de desarrollo
        "python-dotenv>=1.0.0",
        "python-multipart>=0.0.6",
        # Testing
        "pytest>=7.3.1",
        "pytest-asyncio>=0.21.0"
    ],
    entry_points={
        "console_scripts": [
            "tause = cli.main:cli"
        ]
    },
    author="Tause Team",
    author_email="info@tause.ai",
    description="Framework modular para desarrollo rápido de aplicaciones",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/tause-ai/tausestack",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ],
    python_requires=">=3.8",
)
