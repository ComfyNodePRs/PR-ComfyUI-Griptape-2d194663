import json
import os

from app.app_settings import AppSettings
from app.user_manager import UserManager
from server import PromptServer

# Constants for file paths
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(THIS_DIR)
DEFAULT_CONFIG_FILE = os.path.join(PARENT_DIR, "griptape_config.json.default")
USER_CONFIG_FILE = os.path.join(PARENT_DIR, "griptape_config.json")

id = "Comfy.Settings.gtUI"


def load_json_file(file_path):
    """
    Safely load a JSON file, returning an empty dictionary if the file does not exist or is invalid.
    """
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return {}

    try:
        with open(file_path, "r") as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from file: {file_path}, Error: {e}")
    except Exception as e:
        print(
            f"Unexpected error occurred while loading JSON file: {file_path}, Error: {e}"
        )

    return {}


def merge_configs(default_config, user_config):
    """
    Recursively merge user configuration into the default configuration.
    """
    for key, value in default_config.items():
        if isinstance(value, dict):
            user_config[key] = merge_configs(value, user_config.get(key, {}))
        elif key not in user_config:
            user_config[key] = value
    return user_config


def update_config_with_env(config):
    """
    Update the configuration dictionary with environment variables where relevant.
    """
    for key in config:
        if isinstance(config[key], dict):
            update_config_with_env(
                config[key]
            )  # Recursive call for nested dictionaries
        else:
            env_value = os.getenv(key)  # Get environment variable
            if config[key] == "" and env_value is not None:
                config[key] = env_value
                print(f"Updated {key} from environment variable.")


def save_config(config, file_path):
    """
    Save a configuration dictionary to a JSON file.
    """
    with open(file_path, "w") as file:
        json.dump(config, file, indent=4)


def load_and_prepare_config(default_file, user_file):
    """
    Load the default and user configurations, merge them, and return the merged config.
    """
    print("   \033[34m- Loading configuration\033[0m")
    default_config = load_json_file(default_file)
    user_config = load_json_file(user_file)
    final_config = merge_configs(default_config, user_config)
    update_config_with_env(final_config)
    save_config(final_config, user_file)
    print("  \033[34m- Sending environment variables to JavaScript\033[0m")
    set_custom_settings(final_config)
    # send_config_to_js(final_config)
    return final_config


def set_environment_variables_from_config(config):
    """
    Set environment variables based on a given configuration dictionary.
    """
    print("   \033[34m- Setting Environment Variables\033[0m")
    env_config = config.get("env", {})
    for key, value in env_config.items():
        os.environ[key] = str(value)


def set_custom_settings(config):
    user_manager = UserManager()

    app_settings = AppSettings(user_manager)
    request = None
    custom_settings = app_settings.get_settings(request)

    # Add Griptape API keys to custom settings
    custom_settings[id] = config["env"]

    # Save the updated settings
    app_settings.save_settings(request, custom_settings)


def send_config_to_js(config):
    """
    Send a specific part of the configuration ('env' section) to the JavaScript frontend.
    """
    PromptServer.instance.send_sync("config-update", config.get("env", {}))


def get_config(key, default=None):
    """
    Retrieve a configuration value using a dot-separated key path from the user config file.
    """
    config = load_json_file(USER_CONFIG_FILE)
    parts = key.split(".")
    for part in parts:
        if part in config:
            config = config[part]
        else:
            return default
    return config
