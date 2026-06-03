# prompt-registry

A local prompt registry for versioned prompt templates. Store templates with variable slots, track immutable version history, and pin specific versions to environments (dev, staging, prod).

Inspired by git-style workflows: each prompt has a history of versions, and deployments point an environment at a chosen version.

## Requirements

- Python 3.10+

## Installation

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
```

## Quick start

Initialize the SQLite database (creates `~/.prompt-registry/registry.db` by default):

```bash
python -c "from prompt_registry.db import init_db; init_db(); print('OK')"
```

## Project layout

```
prompt_registry/
  db.py       # SQLite connection and schema
  models.py   # Prompt, PromptVersion, Deployment dataclasses
```

## Data model

| Table | Purpose |
|-------|---------|
| `prompts` | Named prompts with a description |
| `prompt_versions` | Immutable snapshots of a template (version number, variables, commit message) |
| `deployments` | Maps `(prompt_name, environment)` to a specific version |

Templates use `{variable}` placeholders. Variable names are stored alongside each version as a JSON array.

## CLI

A `prompt` CLI entry point is configured in `pyproject.toml` (`prompt_registry.cli:app`). The CLI module is not implemented yet.

## Development

Reinstall after changing package layout or dependencies:

```bash
pip install -e .
```

Run tests (when added):

```bash
pytest
```
