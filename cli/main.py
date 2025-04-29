import click
import os
import shutil
import subprocess

@click.group()
def cli():
    """TauseStack - Framework modular para desarrollo rápido."""
    pass

def check_dependencies():
    import shutil
    import sys
    missing = []
    if shutil.which("docker") is None:
        missing.append("Docker")
    if shutil.which("docker-compose") is None:
        missing.append("Docker Compose")
    if shutil.which("python3") is None and shutil.which("python") is None:
        missing.append("Python 3")
    if shutil.which("node") is None:
        missing.append("Node.js")
    if missing:
        click.echo(f"Dependencias faltantes: {', '.join(missing)}")
        click.echo("Por favor instala los requisitos antes de continuar.")
        sys.exit(1)

@cli.command()
@click.argument('name')
@click.option('--type', default='website', 
              type=click.Choice(['website', 'crm', 'ecommerce', 'chatbot', 'agent']),
              help='Tipo de proyecto a crear')
def init(name, type):
    check_dependencies()
    click.echo(f"Creando proyecto {name} de tipo {type}...")
    # Copiar template base
    template_path = os.path.join(os.path.dirname(__file__), f"../templates/{type}")
    shutil.copytree(template_path, name)
    click.echo(f"Proyecto {name} creado exitosamente!")
    click.echo(f"Para iniciar: cd {name} && tause dev")

@cli.command()
def dev():
    check_dependencies()
    click.echo("Iniciando entorno de desarrollo...")
    if not os.path.exists("docker-compose.yml"):
        click.echo("Error: No se encontró docker-compose.yml")
        return
    subprocess.run(["docker-compose", "up", "-d"])
    click.echo("Ambiente de desarrollo activo en http://localhost:3000")
    subprocess.run(["docker-compose", "logs", "-f"])

@cli.command()
@click.option('--unit', is_flag=True, help='Ejecutar solo tests unitarios')
@click.option('--integration', is_flag=True, help='Ejecutar solo tests de integración')
def test(unit, integration):
    """Ejecuta las pruebas del proyecto."""
    if not unit and not integration:
        click.echo("Ejecutando todas las pruebas...")
        subprocess.run(["pytest"])
    elif unit:
        click.echo("Ejecutando pruebas unitarias...")
        subprocess.run(["pytest", "-m", "unit"])
    elif integration:
        click.echo("Ejecutando pruebas de integración...")
        subprocess.run(["pytest", "-m", "integration"])

@cli.command()
def format():
    """Formatea el código según los estándares del proyecto."""
    click.echo("Formateando código backend...")
    subprocess.run(["black", "."])
    click.echo("Formateando código frontend...")
    subprocess.run(["yarn", "format"], cwd="./frontend")

@cli.command()
def lint():
    """Ejecuta linters para verificar la calidad del código."""
    click.echo("Ejecutando linters para backend...")
    subprocess.run(["ruff", "check", "."])
    click.echo("Ejecutando linters para frontend...")
    subprocess.run(["yarn", "lint"], cwd="./frontend")

if __name__ == '__main__':
    cli()
