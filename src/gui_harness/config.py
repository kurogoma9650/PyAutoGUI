from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, replace
from pathlib import Path

from .errors import ConfigurationError


@dataclass(frozen=True)
class ApplicationConfig:
    app_id: str
    process_name: str
    title_regex: str | None = None
    executable: str | None = None
    working_directory: str | None = None


def _read_toml(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("rb") as fh:
        return tomllib.load(fh)


def _profile_path(app_id: str) -> Path:
    return Path(__file__).resolve().parent / "profiles" / f"{app_id}.toml"


def load_application_config(
    app_id: str,
    *,
    local_path: Path | None = None,
    executable_override: str | None = None,
) -> ApplicationConfig:
    profile = _read_toml(_profile_path(app_id))
    app = profile.get("application")
    if not app:
        raise ConfigurationError(f"Unknown application profile: {app_id}")

    config = ApplicationConfig(
        app_id=app_id,
        process_name=app["process_name"],
        title_regex=app.get("title_regex"),
        executable=app.get("executable"),
        working_directory=app.get("working_directory"),
    )

    local_path = local_path or Path.cwd() / ".gui-harness.local.toml"
    local = _read_toml(local_path).get("applications", {}).get(app_id, {})
    if local:
        config = replace(
            config,
            executable=local.get("executable", config.executable),
            working_directory=local.get("working_directory", config.working_directory),
        )

    env_prefix = f"GUI_HARNESS_{app_id.upper()}_"
    config = replace(
        config,
        executable=os.getenv(env_prefix + "EXECUTABLE", config.executable),
        working_directory=os.getenv(env_prefix + "WORKING_DIRECTORY", config.working_directory),
    )

    if executable_override:
        config = replace(config, executable=executable_override)

    return config
