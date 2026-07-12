"""Central config loader for Sigma AI Guardian.

File path: `src/config.py`
Input: optional TOML file at `PROJECT_ROOT/SAG-config.toml`.
Output: immutable `AppConfig` object used by other modules.

The idea:
All modules that need config should call one stable API: `get_config()`.
The config file is stored at `PROJECT_ROOT/SAG-config.toml`.

TOML references:
- Vietnamese: https://docs.fileformat.com/vi/programming/toml/
- English: https://toml.io/en/

Note cho nguoi moi build app:
Config system nen lam 3 viec that chac: co default de app chay duoc, doc file
ngoai de user tuy bien, va co override de test khong cham vao config that. Khong
nen de tung module tu doc file config rieng, vi sau nay rat kho debug khi moi noi
fallback mot kieu.

Mental model de doc file nay:
1. `DEFAULT_CONFIG_TEXT` la ban config mau cho nguoi dung va cho app fallback.
2. `_load_config_from_file()` chi doc TOML va tra ve dict raw.
3. `_flatten_config()` bien cau truc TOML co table thanh dict phang de xu ly de.
4. `_build_config()` validate tung gia tri va tao `AppConfig` type-safe.
5. `Config` giu `AppConfig` hien hanh cho toan process.
6. Module khac chi nen goi `get_config()`, khong nen dung cac ham bat dau bang `_`.

Tai sao dung TOML thay JSON:
- TOML de doc voi nguoi cau hinh app hon JSON.
- TOML ho tro comment, nen co the tao file config tu giai thich tung option.
- Python 3.11+ co san `tomllib` de doc TOML, khong can them dependency.

Nguyen tac cross-platform:
- Dung `pathlib.Path`, khong noi path bang chuoi.
- Cho phep path tuong doi trong config de project copy sang thu muc khac van chay.
- Chi resolve path sau khi biet `project_root`.
- Khong hard-code `/` hay `C:\\` trong config loader.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, cast

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_FILE_PATH = PROJECT_ROOT / "SAG-config.toml"


DEFAULT_CONFIG_TEXT = """# Sigma AI Guardian config
# This file is generated automatically when it does not exist or is invalid.
# Paths can be absolute or relative to project_root.

# Project root is the base directory used to resolve relative paths.
project_root = "."

[logging]
# Directory that stores all log files.
logs_dir = "logs"

# Root log level for app.log and normal console output.
log_level = "INFO"

# Combined log file for the whole app.
log_file_name = "app.log"

# Error-only log file. Logger writes ERROR and CRITICAL records here.
error_log_file_name = "error.log"

# Print normal logs to console. Turn off for cleaner CLI/test output.
log_to_console = true

# Create one extra log file per source module, like src/foo.py.log.
module_log_enabled = true

# Module logs are usually more verbose because they are used for debugging.
module_log_level = "DEBUG"

# Critical logs should still be visible even when normal console logs are off.
critical_log_to_console = true
"""


@dataclass(frozen=True)
class AppConfig:
    """Validated config used by the running process.

    This object is the safe version of config. TOML values can be missing, wrong
    type, or relative paths; fields here should already be converted to the type
    modules expect.

    Field guide:
    - `project_root`: base folder for portable relative paths.
    - `logs_dir`: final absolute/usable log directory.
    - `log_level`: root logger level, usually INFO.
    - `module_log_level`: per-source-file log level, usually DEBUG.
    - `config_path`: actual TOML path used to create this object.
    """

    project_root: Path
    logs_dir: Path
    log_level: str
    log_file_name: str
    error_log_file_name: str
    log_to_console: bool
    module_log_enabled: bool
    module_log_level: str
    critical_log_to_console: bool
    config_path: Path


class Config:
    """Small process-wide config registry.

    First call builds config from TOML/defaults. Later calls return the same
    object so every module sees one consistent configuration.
    """

    _config: ClassVar[AppConfig | None] = None

    @classmethod
    def setup(
        cls,
        config_path: str | Path = CONFIG_FILE_PATH,
        overrides: dict[str, object] | None = None,
    ) -> AppConfig:
        """Build and store the active config.

        Use this from app entry points, tests, or scripts that need to control
        where config comes from. `overrides` is intentionally last so tests can
        force values without editing `SAG-config.toml`.
        """

        selected_path = Path(config_path)
        raw_config = _load_config_from_file(selected_path)
        if overrides is not None:
            raw_config.update(overrides)

        config = _build_config(raw_config, selected_path)
        config.logs_dir.mkdir(parents=True, exist_ok=True)
        cls._config = config
        return config

    @classmethod
    def getconfig(cls) -> AppConfig:
        """Return current config, creating default config on first use.

        This makes simple modules easy to write: they can call `get_config()` and
        do not need to know whether the main app already called `setup_config()`.
        """

        if cls._config is None:
            return cls.setup()
        return cls._config


def _load_config_from_file(file_path: str | Path = CONFIG_FILE_PATH) -> dict[str, object]:
    """Read TOML config and return a flat raw config dict.

    Missing config is not an error: the function creates a default config file.
    Invalid TOML is also handled by recreating the default file, because a broken
    config should not stop early development.

    Important: this function still returns raw values. Do not trust types here;
    `_build_config()` is the place that validates each option.
    """

    path = Path(file_path)
    if not path.exists():
        _create_default_config(path)

    try:
        with path.open("rb") as file:
            loaded_data = tomllib.load(file)
    except (OSError, tomllib.TOMLDecodeError):
        _create_default_config(path)
        with path.open("rb") as file:
            loaded_data = tomllib.load(file)

    data = cast(dict[str, object], loaded_data)
    return _flatten_config(data)


def _create_default_config(file_path: str | Path = CONFIG_FILE_PATH) -> None:
    """Create a readable default TOML config file.

    Only this function writes the config file. Keeping write logic in one place
    avoids hidden side effects when other functions only need to read config.

    The generated file is meant to be human-editable. Comments in
    `DEFAULT_CONFIG_TEXT` are part of the user experience, not just decoration.
    """

    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(DEFAULT_CONFIG_TEXT, encoding="utf-8")


def get_config() -> AppConfig:
    """Public stable API for modules that need config.

    Use this in normal source modules:

        from config import get_config
        config = get_config()

    Do not call `_load_config_from_file()` or `_build_config()` from feature
    modules. Those are implementation details of the config system.
    """

    return Config.getconfig()


def setup_config(
    config_path: str | Path = CONFIG_FILE_PATH,
    overrides: dict[str, object] | None = None,
) -> AppConfig:
    """Public API for app entry points and tests that need explicit setup.

    Example for tests:

        setup_config(overrides={"logs_dir": temp_path / "logs"})

    This keeps tests isolated from the real developer config file.
    """

    return Config.setup(config_path=config_path, overrides=overrides)


def _flatten_config(data: dict[str, object]) -> dict[str, object]:
    """Flatten supported TOML tables into keys used by `AppConfig`.

    Current TOML supports top-level `project_root` and a `[logging]` table. The
    rest of the app should not care about TOML nesting; it only receives the
    final `AppConfig` object.

    Why flatten? It keeps `_build_config()` simple. Instead of passing nested
    dicts around, `_build_config()` can say `raw_config.get("logs_dir")` for every
    option.
    """

    raw_config: dict[str, object] = {}
    project_root = data.get("project_root")
    if project_root is not None:
        raw_config["project_root"] = project_root

    logging_config = data.get("logging")
    if isinstance(logging_config, dict):
        logging_items = cast(dict[object, object], logging_config)
        raw_config.update({str(key): value for key, value in logging_items.items()})

    return raw_config


def _build_config(raw_config: dict[str, object], config_path: Path) -> AppConfig:
    """Convert raw values into a typed config object with safe defaults.

    This is the most important function in the file. It protects the rest of the
    app from bad config input. If a TOML value has the wrong type, this function
    ignores it and uses a default.

    Rule of thumb for adding a new option:
    1. Add it to `DEFAULT_CONFIG_TEXT`.
    2. Add a typed field to `AppConfig`.
    3. Read the raw value here.
    4. Validate type and fallback to default here.
    """

    project_root_config = raw_config.get("project_root")
    # Resolve project_root first because other relative paths depend on it.
    if isinstance(project_root_config, str) and project_root_config.strip():
        configured_project_root = Path(project_root_config).expanduser()
        project_root = (
            configured_project_root
            if configured_project_root.is_absolute()
            else PROJECT_ROOT / configured_project_root
        ).resolve()
    elif isinstance(project_root_config, Path):
        project_root = project_root_config.expanduser().resolve()
    else:
        project_root = PROJECT_ROOT

    logs_dir_config = raw_config.get("logs_dir")
    # logs_dir may be relative so the whole project stays portable.
    if isinstance(logs_dir_config, str) and logs_dir_config.strip():
        logs_dir = Path(logs_dir_config).expanduser()
    elif isinstance(logs_dir_config, Path):
        logs_dir = logs_dir_config.expanduser()
    else:
        logs_dir = Path("logs")

    if not logs_dir.is_absolute():
        logs_dir = project_root / logs_dir

    log_level_config = raw_config.get("log_level")
    log_file_name_config = raw_config.get("log_file_name")
    error_log_file_name_config = raw_config.get("error_log_file_name")
    log_to_console_config = raw_config.get("log_to_console")
    module_log_enabled_config = raw_config.get("module_log_enabled")
    module_log_level_config = raw_config.get("module_log_level")
    critical_log_to_console_config = raw_config.get("critical_log_to_console")

    return AppConfig(
        project_root=project_root,
        logs_dir=logs_dir,
        log_level=(
            log_level_config.strip().upper()
            if isinstance(log_level_config, str) and log_level_config.strip()
            else "INFO"
        ),
        log_file_name=(
            log_file_name_config.strip()
            if isinstance(log_file_name_config, str) and log_file_name_config.strip()
            else "app.log"
        ),
        error_log_file_name=(
            error_log_file_name_config.strip()
            if isinstance(error_log_file_name_config, str)
            and error_log_file_name_config.strip()
            else "error.log"
        ),
        log_to_console=(
            log_to_console_config if isinstance(log_to_console_config, bool) else True
        ),
        module_log_enabled=(
            module_log_enabled_config
            if isinstance(module_log_enabled_config, bool)
            else True
        ),
        module_log_level=(
            module_log_level_config.strip().upper()
            if isinstance(module_log_level_config, str)
            and module_log_level_config.strip()
            else "DEBUG"
        ),
        critical_log_to_console=(
            critical_log_to_console_config
            if isinstance(critical_log_to_console_config, bool)
            else True
        ),
        config_path=config_path,
    )
