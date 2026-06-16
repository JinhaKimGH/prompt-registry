import prompt_registry.store as store
from prompt_registry.cli import app
from typer.testing import CliRunner

runner = CliRunner()


def test_create_success(db_path, monkeypatch) -> None:
    monkeypatch.setattr(
        "prompt_registry.cli.create_prompt",
        lambda name, description: store.create_prompt(
            name, description, db_path=db_path
        ),
    )

    result = runner.invoke(app, ["create", "summarize", "-d", "Summarize text"])

    assert result.exit_code == 0
    assert "Prompt 'summarize' created successfully." in result.output
    prompts = store.list_prompts(db_path=db_path)
    assert len(prompts) == 1
    assert prompts[0].name == "summarize"
    assert prompts[0].description == "Summarize text"


def test_create_duplicate_exits_with_error(db_path, monkeypatch) -> None:
    store.create_prompt("summarize", "Summarize text", db_path=db_path)
    monkeypatch.setattr(
        "prompt_registry.cli.create_prompt",
        lambda name, description: store.create_prompt(
            name, description, db_path=db_path
        ),
    )

    result = runner.invoke(app, ["create", "summarize", "-d", "Duplicate"])

    assert result.exit_code == 1
    assert "Prompt 'summarize' already exists." in result.output


def test_create_requires_description(db_path, monkeypatch) -> None:
    monkeypatch.setattr(
        "prompt_registry.cli.create_prompt",
        lambda name, description: store.create_prompt(
            name, description, db_path=db_path
        ),
    )

    result = runner.invoke(app, ["create", "summarize"])

    assert result.exit_code != 0
    assert "description" in result.output.lower()
