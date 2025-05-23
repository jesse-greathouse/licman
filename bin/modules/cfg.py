import sys
import os
import re
from pathlib import Path
from dotenv import dotenv_values
import yaml  # PyYAML library for YAML parsing :contentReference[oaicite:4]{index=4}

# Determine project root (assumes this file is in bin/modules/ under the project root)
APP_ROOT = Path(__file__).resolve().parents[2]
BIN_DIR = APP_ROOT / "bin"
MODULES_DIR = BIN_DIR / "modules"

if str(BIN_DIR) not in sys.path:
    sys.path.insert(0, str(BIN_DIR))

# Default file paths for config and env files
CONFIG_FILE_PATH = APP_ROOT / ".licman-cfg.yml"
ENV_FILE_PATH = APP_ROOT / ".env"

def get_config_file():
    """
    Determine the path to the licman YAML configuration file.
    Checks environment variables for overrides, otherwise uses the default path.
    """
    # Check for environment variable override
    env_override = os.getenv("LICMAN_CONFIG_FILE") or os.getenv("CONFIG_FILE")
    if env_override:
        path = Path(env_override).expanduser()
        if not path.is_absolute():
            # Make relative paths absolute relative to project root
            path = (APP_ROOT / path).resolve()
    else:
        path = CONFIG_FILE_PATH

    return path

def get_configuration():
    """
    Load the licman configuration from YAML, creating a default config if needed.
    Performs environment-based section selection and placeholder substitution.
    """
    config_path = get_config_file()
    if not config_path.exists():
        return {}  # ← Let the caller (configure.py) handle population

    # Load the YAML configuration file
    with open(config_path, "r") as f:
        yaml_content = f.read()
    try:
        data = yaml.safe_load(yaml_content)
    except Exception as e:
        raise RuntimeError(f"Failed to parse YAML configuration: {e}")

    if data is None:
        data = {}  # empty file yields None

    # Check for environment-specific sections in YAML
    env_vars = parse_env_file()  # load .env variables (if any)
    current_env = env_vars.get("LICMAN_ENV") or os.getenv("LICMAN_ENV")
    if current_env:
        env_name = current_env
    else:
        env_name = "development"  # default environment if not specified

    config = data
    if isinstance(data, dict) and env_name in data:
        # If YAML has top-level section matching the environment name, use it
        config = data[env_name]
    else:
        # Otherwise, data is either already the config or no specific sections
        config = data

    # Substitute environment placeholders in the config values
    config = _substitute_env_placeholders(config, {**env_vars, **os.environ})

    return config

def _substitute_env_placeholders(config_fragment, env_dict):
    """
    Recursively replace $ENV{VAR} placeholders in the given config fragment (dict, list, or value)
    using the values from env_dict (which should contain environment variables).
    """
    # Pattern to match $ENV{VAR_NAME}
    pattern = re.compile(r"\$ENV\{([^}]+)\}")
    if isinstance(config_fragment, dict):
        return {key: _substitute_env_placeholders(val, env_dict)
                for key, val in config_fragment.items()}
    elif isinstance(config_fragment, list):
        return [_substitute_env_placeholders(item, env_dict) for item in config_fragment]
    elif isinstance(config_fragment, str):
        # Replace all occurrences of the pattern in the string
        def replacer(match):
            var_name = match.group(1)
            return str(env_dict.get(var_name, ""))
        return pattern.sub(replacer, config_fragment)
    else:
        # For numbers, booleans, None, or other types, return as-is
        return config_fragment

def save_configuration(config_data):
    """
    Save the provided configuration dictionary back to the YAML config file.
    """
    config_path = get_config_file()
    write_config_file(config_data, config_path)

def write_config_file(config_data=None, file_path=None):
    """
    Write the given configuration dictionary to a YAML file.
    If config_data is None, writes the DEFAULT_CONFIG.
    If file_path is None, writes to the default config file path.
    """
    if file_path is None:
        file_path = get_config_file()
    data_to_write = config_data if config_data is not None else {}

    # Ensure the directory exists (in case a custom path in a different dir is used)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    # Write YAML content to the file
    with open(file_path, "w") as f:
        yaml.safe_dump(data_to_write, f, default_flow_style=False)

def parse_env_file(path=None):
    from pathlib import Path
    path = path or Path(__file__).resolve().parents[2] / ".env"
    return dotenv_values(path)

def write_env_file(path, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        for key, value in data.items():
            f.write(f"{key}={value}\n")

def write_template_file(src: Path, dst: Path, **values):
    """
    Copy a config template from `src` to `dst`, replacing __PLACEHOLDER__ tokens
    with values from `**values`.
    """
    if not src.exists():
        raise FileNotFoundError(f"Template file not found: {src}")

    content = src.read_text()

    for key, val in values.items():
        placeholder = f"__{key}__"
        content = content.replace(placeholder, str(val))

    unreplaced = re.findall(r"__([A-Z0-9_]+)__", content)
    if unreplaced:
        print(f"⚠️  Warning: Unreplaced placeholders in {src}: {unreplaced}")

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(content)
