from pathlib import Path

import pytest

from prompt_registry import store


def test_create_prompt(db_path: Path) -> None:
    prompt = store.create_prompt("summarize", "Summarize text", db_path=db_path)

    assert prompt.name == "summarize"
    assert prompt.description == "Summarize text"
    assert prompt.versions == []


def test_create_prompt_duplicate_raises(db_path: Path) -> None:
    store.create_prompt("summarize", "Summarize text", db_path=db_path)

    with pytest.raises(store.PromptAlreadyExistsError):
        store.create_prompt("summarize", "Duplicate", db_path=db_path)


def test_push_version_starts_at_one_and_increments(db_path: Path) -> None:
    store.create_prompt("summarize", "Summarize text", db_path=db_path)

    v1 = store.push_version("summarize", "Version {n}", "first", db_path=db_path)
    v2 = store.push_version("summarize", "Version {n} again", "second", db_path=db_path)

    assert v1.version == 1
    assert v2.version == 2
    assert v1.id is not None
    assert v2.id is not None


def test_push_version_extracts_variables(db_path: Path) -> None:
    store.create_prompt("summarize", "Summarize text", db_path=db_path)

    version = store.push_version(
        "summarize",
        "Summarize {topic} in {tone} tone.",
        "initial",
        db_path=db_path,
    )

    assert version.variables == ["topic", "tone"]
    assert version.template == "Summarize {topic} in {tone} tone."
    assert version.message == "initial"


def test_push_version_unknown_prompt_raises(db_path: Path) -> None:
    with pytest.raises(store.PromptNotFoundError):
        store.push_version("missing", "Hello {name}", "initial", db_path=db_path)


def test_get_latest(db_path: Path) -> None:
    store.create_prompt("summarize", "Summarize text", db_path=db_path)
    store.push_version("summarize", "v1", "first", db_path=db_path)
    store.push_version("summarize", "v2", "second", db_path=db_path)

    latest = store.get_latest("summarize", db_path=db_path)

    assert latest.version == 2
    assert latest.template == "v2"


def test_get_latest_without_versions_raises(db_path: Path) -> None:
    store.create_prompt("summarize", "Summarize text", db_path=db_path)

    with pytest.raises(store.VersionNotFoundError):
        store.get_latest("summarize", db_path=db_path)


def test_get_version(db_path: Path) -> None:
    store.create_prompt("summarize", "Summarize text", db_path=db_path)
    store.push_version("summarize", "v1", "first", db_path=db_path)
    store.push_version("summarize", "v2", "second", db_path=db_path)

    version = store.get_version("summarize", 1, db_path=db_path)

    assert version.version == 1
    assert version.template == "v1"


def test_get_version_missing_raises(db_path: Path) -> None:
    store.create_prompt("summarize", "Summarize text", db_path=db_path)

    with pytest.raises(store.VersionNotFoundError):
        store.get_version("summarize", 99, db_path=db_path)


def test_list_versions_ordered_oldest_first(db_path: Path) -> None:
    store.create_prompt("summarize", "Summarize text", db_path=db_path)
    store.push_version("summarize", "v1", "first", db_path=db_path)
    store.push_version("summarize", "v2", "second", db_path=db_path)

    versions = store.list_versions("summarize", db_path=db_path)

    assert [v.version for v in versions] == [1, 2]


def test_list_versions_unknown_prompt_raises(db_path: Path) -> None:
    with pytest.raises(store.PromptNotFoundError):
        store.list_versions("missing", db_path=db_path)


def test_list_prompts(db_path: Path) -> None:
    store.create_prompt("beta", "Beta prompt", db_path=db_path)
    store.create_prompt("alpha", "Alpha prompt", db_path=db_path)

    prompts = store.list_prompts(db_path=db_path)

    assert [p.name for p in prompts] == ["alpha", "beta"]


def test_get_prompt_without_versions(db_path: Path) -> None:
    store.create_prompt("summarize", "Summarize text", db_path=db_path)
    store.push_version("summarize", "v1", "first", db_path=db_path)

    prompt = store.get_prompt("summarize", db_path=db_path)

    assert prompt.name == "summarize"
    assert prompt.versions == []


def test_get_prompt_with_versions(db_path: Path) -> None:
    store.create_prompt("summarize", "Summarize text", db_path=db_path)
    store.push_version("summarize", "v1", "first", db_path=db_path)
    store.push_version("summarize", "v2", "second", db_path=db_path)

    prompt = store.get_prompt("summarize", include_versions=True, db_path=db_path)

    assert prompt.name == "summarize"
    assert [v.version for v in prompt.versions] == [1, 2]


def test_get_prompt_missing_raises(db_path: Path) -> None:
    with pytest.raises(store.PromptNotFoundError):
        store.get_prompt("missing", db_path=db_path)


def test_deploy_and_get_deployed(db_path: Path) -> None:
    store.create_prompt("summarize", "Summarize text", db_path=db_path)
    store.push_version("summarize", "v1", "first", db_path=db_path)
    store.push_version("summarize", "v2", "second", db_path=db_path)

    deployment = store.deploy("summarize", "prod", 1, db_path=db_path)

    assert deployment.prompt_name == "summarize"
    assert deployment.environment == "prod"
    assert deployment.version == 1

    fetched = store.get_deployed("summarize", "prod", db_path=db_path)
    assert fetched.version == 1


def test_deploy_updates_existing_environment(db_path: Path) -> None:
    store.create_prompt("summarize", "Summarize text", db_path=db_path)
    store.push_version("summarize", "v1", "first", db_path=db_path)
    store.push_version("summarize", "v2", "second", db_path=db_path)

    store.deploy("summarize", "prod", 1, db_path=db_path)
    store.deploy("summarize", "prod", 2, db_path=db_path)

    fetched = store.get_deployed("summarize", "prod", db_path=db_path)
    assert fetched.version == 2


def test_deploy_invalid_version_raises(db_path: Path) -> None:
    store.create_prompt("summarize", "Summarize text", db_path=db_path)

    with pytest.raises(store.VersionNotFoundError):
        store.deploy("summarize", "prod", 1, db_path=db_path)


def test_get_deployed_missing_raises(db_path: Path) -> None:
    store.create_prompt("summarize", "Summarize text", db_path=db_path)

    with pytest.raises(LookupError):
        store.get_deployed("summarize", "prod", db_path=db_path)
