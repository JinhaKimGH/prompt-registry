from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class PromptVersion:
    """A single, immutable version snapshot of a prompt template."""
    id: int | None          # set by DB on insert
    prompt_name: str
    version: int
    template: str           # the raw template string with {variable} slots
    variables: list[str]    # extracted variable names, e.g. ["topic", "tone"]
    message: str            # commit-style message describing the change
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class Prompt:
    """A named prompt with its full version history."""
    name: str
    description: str
    versions: list[PromptVersion] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def latest(self) -> PromptVersion | None:
        """Return the highest version snapshot."""
        if not self.versions:
            return None
        return max(self.versions, key=lambda v: v.version)

    @property
    def latest_version_number(self) -> int:
        """Return the next version number to use on push."""
        if not self.versions:
            return 0
        return self.latest.version

@dataclass
class Deployment:
    """A pointer from (prompt_name, environment) to a specific version."""
    id: int | None
    prompt_name: str
    environment: str        # e.g. "prod", "staging", "dev"
    version: int            # which PromptVersion this env points to
    deployed_at: datetime = field(default_factory=datetime.utcnow)