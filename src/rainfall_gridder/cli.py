"""Console script for rainfall_gridder."""

import typer
from rich.console import Console

from rainfall_gridder import utils

app = typer.Typer()
console = Console()


@app.command()
def main() -> None:
    """Console script for rainfall_gridder."""
    console.print("Replace this message by putting your code into "
               "rainfall_gridder.cli.main")
    console.print("See Typer documentation at https://typer.tiangolo.com/")
    utils.do_something_useful()


if __name__ == "__main__":
    app()
