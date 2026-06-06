"""Read/write operations against the prompt registry database."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from prompt_registry.db import DEFAULT_DB_PATH, get_connection
from prompt_registry.models import Deployment, Prompt, PromptVersion
from prompt_registry.template import extract_variables


class PromptNotFoundError(LookupError):
    """Raised when a prompt name does not exist in the registry."""


class PromptAlreadyExistsError(ValueError):
    """Raised when creating a prompt that already exists."""


class VersionNotFoundError(LookupError):
    """Raised when a prompt version does not exist."""

    def __init__(self, prompt_name: str, version: int | str) -> None:
        self.prompt_name = prompt_name
        self.version = version
        super().__init__(
            f"Version {version!r} not found for prompt {prompt_name!r}"
        )


def _utcnow() -> datetime:
    return datetime.utcnow()


def _format_dt(dt: datetime) -> str:
    return dt.isoformat()


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _row_to_version(row) -> PromptVersion:
    return PromptVersion(
        id=row["id"],
        prompt_name=row["prompt_name"],
        version=row["version"],
        template=row["template"],
        variables=json.loads(row["variables"]),
        message=row["message"],
        created_at=_parse_dt(row["created_at"]),
    )


def _row_to_prompt(row, versions: list[PromptVersion] | None = None) -> Prompt:
    return Prompt(
        name=row["name"],
        description=row["description"],
        versions=versions or [],
        created_at=_parse_dt(row["created_at"]),
    )


def _row_to_deployment(row) -> Deployment:
    return Deployment(
        id=row["id"],
        prompt_name=row["prompt_name"],
        environment=row["environment"],
        version=row["version"],
        deployed_at=_parse_dt(row["deployed_at"]),
    )


def _require_prompt(conn, name: str) -> None:
    row = conn.execute("SELECT 1 FROM prompts WHERE name = ?", (name,)).fetchone()
    if row is None:
        raise PromptNotFoundError(name)


def _require_version(conn, prompt_name: str, version: int) -> None:
    row = conn.execute(
        """
        SELECT 1 FROM prompt_versions
        WHERE prompt_name = ? AND version = ?
        """,
        (prompt_name, version),
    ).fetchone()
    if row is None:
        raise VersionNotFoundError(prompt_name, version)


def create_prompt(
    name: str,
    description: str,
    *,
    db_path: Path = DEFAULT_DB_PATH,
) -> Prompt:
    """Register a new prompt. Versions are added with push_version."""
    created_at = _utcnow()
    with get_connection(db_path) as conn:
        try:
            conn.execute(
                """
                INSERT INTO prompts (name, description, created_at)
                VALUES (?, ?, ?)
                """,
                (name, description, _format_dt(created_at)),
            )
        except Exception as exc:
            if "UNIQUE constraint failed" in str(exc):
                raise PromptAlreadyExistsError(name) from exc
            raise
    return Prompt(name=name, description=description, created_at=created_at)


def push_version(
    prompt_name: str,
    template: str,
    message: str,
    *,
    db_path: Path = DEFAULT_DB_PATH,
) -> PromptVersion:
    """Append a new immutable version for an existing prompt."""
    variables = extract_variables(template)
    created_at = _utcnow()

    with get_connection(db_path) as conn:
        _require_prompt(conn, prompt_name)
        row = conn.execute(
            """
            SELECT COALESCE(MAX(version), 0) AS latest
            FROM prompt_versions
            WHERE prompt_name = ?
            """,
            (prompt_name,),
        ).fetchone()
        version = row["latest"] + 1

        cursor = conn.execute(
            """
            INSERT INTO prompt_versions (
                prompt_name, version, template, variables, message, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                prompt_name,
                version,
                template,
                json.dumps(variables),
                message,
                _format_dt(created_at),
            ),
        )
        version_id = cursor.lastrowid

    return PromptVersion(
        id=version_id,
        prompt_name=prompt_name,
        version=version,
        template=template,
        variables=variables,
        message=message,
        created_at=created_at,
    )


def get_prompt(
    name: str,
    *,
    include_versions: bool = False,
    db_path: Path = DEFAULT_DB_PATH,
) -> Prompt:
    """Fetch a prompt by name, optionally with its full version history."""
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT name, description, created_at FROM prompts WHERE name = ?",
            (name,),
        ).fetchone()
        if row is None:
            raise PromptNotFoundError(name)

        versions: list[PromptVersion] = []
        if include_versions:
            version_rows = conn.execute(
                """
                SELECT id, prompt_name, version, template, variables, message, created_at
                FROM prompt_versions
                WHERE prompt_name = ?
                ORDER BY version
                """,
                (name,),
            ).fetchall()
            versions = [_row_to_version(r) for r in version_rows]

    return _row_to_prompt(row, versions)


def list_prompts(*, db_path: Path = DEFAULT_DB_PATH) -> list[Prompt]:
    """Return all registered prompts, without version history."""
    with get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT name, description, created_at
            FROM prompts
            ORDER BY name
            """
        ).fetchall()
    return [_row_to_prompt(row) for row in rows]


def list_versions(
    prompt_name: str,
    *,
    db_path: Path = DEFAULT_DB_PATH,
) -> list[PromptVersion]:
    """Return all versions for a prompt, oldest first."""
    with get_connection(db_path) as conn:
        _require_prompt(conn, prompt_name)
        rows = conn.execute(
            """
            SELECT id, prompt_name, version, template, variables, message, created_at
            FROM prompt_versions
            WHERE prompt_name = ?
            ORDER BY version
            """,
            (prompt_name,),
        ).fetchall()
    return [_row_to_version(row) for row in rows]


def get_version(
    prompt_name: str,
    version: int,
    *,
    db_path: Path = DEFAULT_DB_PATH,
) -> PromptVersion:
    """Fetch a specific prompt version."""
    with get_connection(db_path) as conn:
        row = conn.execute(
            """
            SELECT id, prompt_name, version, template, variables, message, created_at
            FROM prompt_versions
            WHERE prompt_name = ? AND version = ?
            """,
            (prompt_name, version),
        ).fetchone()
        if row is None:
            raise VersionNotFoundError(prompt_name, version)
    return _row_to_version(row)


def get_latest(
    prompt_name: str,
    *,
    db_path: Path = DEFAULT_DB_PATH,
) -> PromptVersion:
    """Return the highest version number for a prompt."""
    with get_connection(db_path) as conn:
        row = conn.execute(
            """
            SELECT id, prompt_name, version, template, variables, message, created_at
            FROM prompt_versions
            WHERE prompt_name = ?
            ORDER BY version DESC
            LIMIT 1
            """,
            (prompt_name,),
        ).fetchone()
        if row is None:
            raise VersionNotFoundError(prompt_name, "latest")
    return _row_to_version(row)


def deploy(
    prompt_name: str,
    environment: str,
    version: int,
    *,
    db_path: Path = DEFAULT_DB_PATH,
) -> Deployment:
    """Point an environment at a specific prompt version."""
    deployed_at = _utcnow()
    with get_connection(db_path) as conn:
        _require_prompt(conn, prompt_name)
        _require_version(conn, prompt_name, version)
        conn.execute(
            """
            INSERT INTO deployments (prompt_name, environment, version, deployed_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT (prompt_name, environment) DO UPDATE SET
                version = excluded.version,
                deployed_at = excluded.deployed_at
            """,
            (prompt_name, environment, version, _format_dt(deployed_at)),
        )
        row = conn.execute(
            """
            SELECT id, prompt_name, environment, version, deployed_at
            FROM deployments
            WHERE prompt_name = ? AND environment = ?
            """,
            (prompt_name, environment),
        ).fetchone()

    return _row_to_deployment(row)


def get_deployed(
    prompt_name: str,
    environment: str,
    *,
    db_path: Path = DEFAULT_DB_PATH,
) -> Deployment:
    """Return the deployment record for a prompt in an environment."""
    with get_connection(db_path) as conn:
        row = conn.execute(
            """
            SELECT id, prompt_name, environment, version, deployed_at
            FROM deployments
            WHERE prompt_name = ? AND environment = ?
            """,
            (prompt_name, environment),
        ).fetchone()
        if row is None:
            raise LookupError(f"No deployment for {prompt_name!r} in {environment!r}")
    return _row_to_deployment(row)
