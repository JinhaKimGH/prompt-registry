import typer

from prompt_registry.db import init_db
from prompt_registry.store import PromptAlreadyExistsError, create_prompt

app = typer.Typer(help="Git-style versioning for LLM prompts.")

@app.command()
def init() -> None:
    """Initialize the local registry database."""
    init_db()
    typer.echo("Registry initialized at ~/.prompt-registry/registry.db")

@app.command()
def create(name: str, description: str = typer.Option(..., "--description", "-d")) -> None:
    """Create a new prompt."""
    try:
        create_prompt(name, description)
    except PromptAlreadyExistsError as e:
        typer.echo(f"Prompt {name!r} already exists.", err=True)
        raise typer.Exit(1)
    typer.echo(f"Prompt {name!r} created successfully.")

if __name__ == "__main__":
    app()