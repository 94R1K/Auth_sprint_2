import asyncio

import typer

from commands import CreateService, LoadService
from db.postgres import async_session

cli_app = typer.Typer(help="CLI сервиса авторизации")

async def _run_load() -> None:
    async with async_session() as session:
        service = LoadService(session)
        await service.load_all()

async def _run_create_superuser():
    async with async_session() as session:
        service = CreateService(session)
        await service.create_superuser()


@cli_app.command("load_data")
def load_data() -> None:
    """Загрузить/обновить справочники прав и ролей (идемпотентно)"""
    typer.echo("Seeding permissions, roles, and links...")
    asyncio.run(_run_load())
    typer.echo("Done.")

@cli_app.command("create_superuser")
def create_superuser() -> None:
    typer.echo("Создание суперпользователя")
    asyncio.run(_run_create_superuser())


if __name__ == "__main__":
    cli_app()