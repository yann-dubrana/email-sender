from typer import Typer

from modules.commands import commands

app = Typer()
app.add_typer(commands)


if __name__ == '__main__':
    app()
